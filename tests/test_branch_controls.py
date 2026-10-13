import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check_branch_controls as controls


PROTECTION = {
    "required_status_checks": {"strict": True, "contexts": ["descriptor"],
                               "checks": [{"context": "tests", "app_id": 15368}]},
    "required_pull_request_reviews": {"required_approving_review_count": 0},
    "enforce_admins": {"enabled": True},
    "allow_force_pushes": {"enabled": False},
    "allow_deletions": {"enabled": False},
}


class ControlsTest(unittest.TestCase):
    def audit(self, protection=PROTECTION, branches=("main",)):
        def lookup(path):
            if path.endswith("/protection"):
                return copy.deepcopy(protection)
            return {"name": path.rsplit("/", 1)[1], "protected": True}
        return controls.audit("owner/project", branches, ["descriptor", "tests"], lookup)

    def test_matching_controls_are_verified_without_implying_native_agent_approval(self):
        result = self.audit()
        self.assertTrue(result["verified"])
        self.assertEqual(result["branches"][0]["native_approving_review_count"], 0)
        self.assertIn("agent review", result["coverage"])

    def test_missing_required_job_loose_checks_or_admin_bypass_fail(self):
        mutations = [
            lambda p: p["required_status_checks"].update(checks=[]),
            lambda p: p["required_status_checks"].update(strict=False),
            lambda p: p["enforce_admins"].update(enabled=False),
            lambda p: p.update(required_pull_request_reviews=None),
            lambda p: p["allow_force_pushes"].update(enabled=True),
            lambda p: p.pop("allow_deletions"),
            lambda p: p["required_pull_request_reviews"].update(bypass_pull_request_allowances={"apps": [{"slug": "bypass"}]}),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                data = copy.deepcopy(PROTECTION)
                mutate(data)
                self.assertFalse(self.audit(data)["verified"])

    def test_a_missing_hidden_or_ruleset_only_protection_is_unverified(self):
        for code in (403, 404, 500):
            with self.subTest(code=code):
                lookup = mock.Mock(side_effect=controls.LookupError("GitHub lookup unavailable (HTTP %d)" % code))
                result = controls.audit("owner/project", ["main"], ["tests"], lookup)
                self.assertFalse(result["verified"])
                self.assertEqual(result["branches"][0]["state"], "unverified")

    def test_wrong_branch_identity_and_malformed_check_response_fail_closed(self):
        lookup = mock.Mock(return_value={"name": "different", "protected": True})
        self.assertFalse(controls.audit("owner/project", ["main"], ["tests"], lookup)["verified"])
        data = copy.deepcopy(PROTECTION)
        data["required_status_checks"]["checks"] = ["tests"]
        self.assertEqual(self.audit(data)["branches"][0]["state"], "unverified")
        lookup = mock.Mock(side_effect=[{"name": "main", "protected": False}, PROTECTION])
        self.assertFalse(controls.audit("owner/project", ["main"], ["tests"], lookup)["verified"])

    def test_stage_controls_are_checked_separately(self):
        lookup = mock.Mock(side_effect=[{"name": "main", "protected": True}, PROTECTION,
                                       {"name": "stage", "protected": True}, controls.LookupError("unavailable")])
        result = controls.audit("owner/project", ["main", "stage"], ["tests"], lookup)
        self.assertFalse(result["verified"])
        self.assertTrue(result["branches"][0]["verified"])
        self.assertFalse(result["branches"][1]["verified"])

    def test_cli_adapter_only_reads_and_sanitizes_failed_lookup_output(self):
        with mock.patch.object(controls.subprocess, "run", return_value=subprocess.CompletedProcess(
                [], 1, '{"message":"private body"}', "private detail (HTTP 403)")) as run:
            with self.assertRaisesRegex(controls.LookupError, "HTTP 403") as raised:
                controls.request("repos/owner/project/branches/main/protection")
            self.assertNotIn("private", str(raised.exception))
            self.assertEqual(run.call_args.args[0], ["gh", "api", "--hostname", "github.com",
                                                    "repos/owner/project/branches/main/protection"])
            self.assertNotIn("input", run.call_args.kwargs)

    def test_descriptor_selects_real_stage_and_required_names(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            data = {"schema_version": 2, "project": {"repository": "https://github.com/owner/project"},
                    "workflow": {"main_branch": "main", "stage_branch": "stage", "staging": True,
                                 "required_checks": ["descriptor", "tests"]}}
            (root / "delivery.json").write_text(json.dumps(data))
            self.assertEqual(controls.selection(root), ("owner/project", ["main", "stage"], ["descriptor", "tests"]))
            data["workflow"]["staging"] = False
            (root / "delivery.json").write_text(json.dumps(data))
            self.assertEqual(controls.selection(root)[1], ["main"])
            data["project"]["repository"] = "https://github.com.evil/owner/project"
            (root / "delivery.json").write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                controls.selection(root)


if __name__ == "__main__":
    unittest.main()
