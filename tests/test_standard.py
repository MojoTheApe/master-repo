import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import standard

PIN = "a" * 40


class ProjectFixture(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name) / "project"

    def prepare(self, profile="vps"):
        standard.scaffold(self.root, profile, PIN, apply=True)
        path = self.root / "delivery.json"
        config = json.loads(path.read_text())

        def configure(value):
            if isinstance(value, dict):
                return {key: configure(item) for key, item in value.items()}
            if isinstance(value, list):
                return [configure(item) for item in value]
            return "docs/DELIVERY.md#verified-fixture-procedure" if value == "__CONFIGURE__" else value

        config = configure(config)
        config["project"]["repository"] = "https://github.com/example/project"
        config["adoption"] = "ready"
        path.write_text(json.dumps(config))
        return config

    def write(self, config):
        (self.root / "delivery.json").write_text(json.dumps(config))

    def test_preview_does_not_create_project(self):
        files = standard.scaffold(self.root, "n8n", PIN)
        self.assertIn("docs/DELIVERY.md", files)
        self.assertFalse(self.root.exists())

    def test_existing_file_aborts_before_any_new_file(self):
        self.root.mkdir()
        existing = self.root / "AGENTS.md"
        existing.write_text("Existing tracker rules must remain.")
        with self.assertRaisesRegex(ValueError, "Existing files preserved"):
            standard.scaffold(self.root, "vps", PIN, apply=True)
        self.assertEqual(existing.read_text(), "Existing tracker rules must remain.")
        self.assertEqual([p.name for p in self.root.iterdir()], ["AGENTS.md"])

    def test_symlink_parent_cannot_write_outside_project(self):
        self.root.mkdir()
        outside = Path(self.directory.name) / "outside"
        outside.mkdir()
        (self.root / "docs").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            standard.scaffold(self.root, "vps", PIN, apply=True)
        self.assertEqual(list(outside.iterdir()), [])
        self.assertFalse((self.root / "delivery.json").exists())

    def test_existing_parent_file_is_preserved(self):
        self.root.mkdir()
        (self.root / ".github").write_text("not a directory")
        with self.assertRaisesRegex(ValueError, "not a directory"):
            standard.scaffold(self.root, "local", PIN, apply=True)
        self.assertFalse((self.root / "delivery.json").exists())

    def test_scaffold_is_incomplete_and_pinned_for_each_profile(self):
        for profile in ("vps", "n8n", "local"):
            with self.subTest(profile=profile):
                project = self.root / profile
                standard.scaffold(project, profile, PIN, apply=True)
                config = json.loads((project / "delivery.json").read_text())
                self.assertEqual(config["standard"]["revision"], PIN)
                self.assertEqual(config["completion"], standard.PROFILES[profile])
                findings = standard.inspect(project, PIN)
                self.assertTrue(any(kind == "setup" for kind, _ in findings))
                self.assertFalse(any(kind == "error" for kind, _ in findings), findings)

    def test_project_name_is_json_escaped(self):
        project = self.root / 'app "with quotes"'
        standard.scaffold(project, "local", PIN, apply=True)
        self.assertEqual(json.loads((project / "delivery.json").read_text())["project"]["name"], project.name)

    def test_ready_fixture_passes_without_executing_commands(self):
        config = self.prepare()
        sentinel = self.root / "MUST_NOT_EXIST"
        config["checks"] = ["touch " + str(sentinel)]
        config["delivery"]["promote"] = "touch " + str(sentinel)
        self.write(config)
        before = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(standard.inspect(self.root, PIN), [])
        self.assertFalse(sentinel.exists())
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()})

    def test_mutable_reference_is_invalid_even_for_draft(self):
        config = self.prepare()
        config["adoption"] = "draft"
        config["standard"]["revision"] = "main"
        self.write(config)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(standard.main(["validate", "--root", str(self.root), "--allow-draft"]), 1)

    def test_action_and_descriptor_must_match(self):
        self.prepare()
        workflow = self.root / ".github/workflows/delivery-check.yml"
        workflow.write_text(workflow.read_text().replace(PIN, "b" * 40))
        self.assertTrue(any("exact revision" in message for _, message in standard.inspect(self.root)))

    def test_running_action_must_match_descriptor(self):
        self.prepare()
        for actual in ("main", "v0.1.0", "b" * 40):
            with self.subTest(actual=actual):
                self.assertTrue(any("Running action revision" in message for _, message in standard.inspect(self.root, actual)))

    def test_running_standard_version_must_match_descriptor(self):
        config = self.prepare()
        config["standard"]["version"] = "99.0.0"
        self.write(config)
        self.assertTrue(any("running standard's VERSION" in message for _, message in standard.inspect(self.root, PIN)))

    def test_consumer_cannot_claim_self_or_internal_profile(self):
        config = self.prepare()
        config["standard"]["revision"] = "self"
        self.write(config)
        self.assertTrue(any("Consumers cannot" in message for _, message in standard.inspect(self.root)))
        config["profile"] = "standard"
        config["completion"] = "reviewed-merge"
        config["environments"] = {}
        config["delivery"] = {}
        self.write(config)
        self.assertTrue(any("reserved" in message for _, message in standard.inspect(self.root)))

    def test_missing_approval_and_wrong_completion_are_rejected(self):
        config = self.prepare("n8n")
        config["delivery"]["approval"] = "automatic"
        config["completion"] = "reviewed-merge"
        self.write(config)
        findings = standard.inspect(self.root)
        self.assertTrue(any("explicit approval" in message for _, message in findings))
        self.assertTrue(any("Completion policy" in message for _, message in findings))

    def test_malformed_fields_return_findings_instead_of_crashing(self):
        original = self.prepare()
        for key in ("profile", "standard", "tracker", "checks", "exceptions", "project", "environments", "delivery"):
            with self.subTest(key=key):
                config = dict(original)
                config[key] = None
                self.write(config)
                self.assertTrue(any(kind == "error" for kind, _ in standard.inspect(self.root)))

    def test_unknown_and_empty_values_cannot_claim_ready(self):
        config = self.prepare()
        config["tracker"]["validation"] = "  "
        self.write(config)
        self.assertTrue(any(kind == "setup" for kind, _ in standard.inspect(self.root)))
        config["unknown_setting"] = True
        self.write(config)
        self.assertTrue(any("unknown keys" in message for _, message in standard.inspect(self.root)))

    def test_descriptor_symlink_is_not_read(self):
        self.prepare()
        target = self.root / "delivery.json"
        target.unlink()
        target.symlink_to(Path(self.directory.name) / "outside-secret")
        with self.assertRaisesRegex(ValueError, "symlink"):
            standard.inspect(self.root)

    def test_cli_draft_is_not_readiness_success(self):
        standard.scaffold(self.root, "vps", PIN, apply=True)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(standard.main(["audit", "--root", str(self.root)]), 1)
            self.assertEqual(standard.main(["validate", "--root", str(self.root), "--allow-draft"]), 0)
        result = subprocess.run([sys.executable, str(standard.SOURCE / "scripts/standard.py"),
                                 "validate", "--root", str(self.root)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("not ready", result.stdout)

    def test_uncommitted_standard_cannot_generate_misleading_pin(self):
        result = subprocess.CompletedProcess([], 0, stdout=" M standard.md\n", stderr="")
        with mock.patch.object(standard.subprocess, "run", return_value=result):
            with self.assertRaisesRegex(ValueError, "clean Git checkout"):
                standard.source_revision()

    def test_credential_bearing_repository_url_is_rejected_without_echo(self):
        config = self.prepare()
        config["project"]["repository"] = "https://private-token@github.com/example/project"
        self.write(config)
        findings = standard.inspect(self.root)
        self.assertTrue(any("without credentials" in message for _, message in findings))
        self.assertNotIn("private-token", str(findings))


if __name__ == "__main__":
    unittest.main()
