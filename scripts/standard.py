#!/usr/bin/env python3
"""Scaffold and inspect delivery descriptions. Never execute their commands."""

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlparse

SOURCE = Path(__file__).resolve().parents[1]
REPOSITORY = "https://github.com/MojoTheApe/master-repo"
SHA = re.compile(r"[0-9a-f]{40}\Z")
MARKER = re.compile(r"__[A-Z_]+__")
PROFILES = {"vps": "verified-production", "n8n": "verified-production",
            "local": "verified-stable-package", "standard": "reviewed-merge"}
TOP = {"schema_version", "project", "standard", "profile", "adoption", "tracker",
       "checks", "environments", "delivery", "completion", "exceptions"}
FILES = {"AGENTS.md": "AGENTS.md", "DELIVERY.md": "docs/DELIVERY.md",
         "PULL_REQUEST_TEMPLATE.md": ".github/PULL_REQUEST_TEMPLATE.md",
         "delivery-check.yml": ".github/workflows/delivery-check.yml"}


def safe_path(root, relative):
    """Reject links within the selected project before reading or creating files."""
    root = Path(root).expanduser().absolute()
    relative = Path(relative)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Project paths must be relative and stay within the project")
    if root.is_symlink():
        raise ValueError("The selected project root must not be a symlink")
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise ValueError("Refusing symlink: " + str(current.relative_to(root)))
    return current


def object_keys(value, keys, label, findings):
    if not isinstance(value, dict):
        findings.append(("error", label + " must be an object"))
        return False
    missing, unknown = keys - value.keys(), value.keys() - keys
    if missing:
        findings.append(("error", label + " missing keys: " + ", ".join(sorted(missing))))
    if unknown:
        findings.append(("error", label + " has unknown keys: " + ", ".join(sorted(unknown))))
    return not missing and not unknown


def text_fields(value, keys, label, findings):
    if not object_keys(value, keys, label, findings):
        return False
    for key in keys:
        if not isinstance(value[key], str):
            findings.append(("error", label + "." + key + " must be text"))
    return all(isinstance(value[key], str) for key in keys)


def placeholders(value, label, findings):
    if isinstance(value, dict):
        for key, item in value.items():
            placeholders(item, label + "." + key, findings)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            placeholders(item, "{}[{}]".format(label, index), findings)
    elif isinstance(value, str) and (not value.strip() or MARKER.search(value)):
        findings.append(("setup", label + " needs a real project value"))


def read_descriptor(root):
    path = safe_path(root, "delivery.json")
    if path.stat().st_size > 1024 * 1024:
        raise ValueError("delivery.json exceeds the 1 MiB size limit")
    return json.loads(path.read_text(encoding="utf-8"))


def inspect(root, expected_revision=None):
    root = Path(root).expanduser().absolute()
    config = read_descriptor(root)
    if not isinstance(config, dict):
        return [("error", "delivery must be an object")]
    if config.get("schema_version") == 2:
        import project
        return project.inspect(root, expected_revision)
    findings = []
    if not object_keys(config, TOP, "delivery", findings):
        return findings
    if type(config["schema_version"]) is not int or config["schema_version"] != 1:
        findings.append(("error", "Unsupported schema_version; expected 1"))
    project_ok = text_fields(config["project"], {"name", "repository"}, "project", findings)
    standard_ok = text_fields(config["standard"], {"repository", "revision", "version"}, "standard", findings)
    text_fields(config["tracker"], {"system", "url", "pr_reference", "validation"}, "tracker", findings)
    profile = config["profile"]
    if not isinstance(profile, str) or profile not in PROFILES:
        findings.append(("error", "Unknown delivery profile"))
        return findings
    if config["completion"] != PROFILES[profile]:
        findings.append(("error", "Completion policy does not match the selected profile"))
    if config["adoption"] == "draft":
        findings.append(("setup", "Adoption is draft; verify real setup before marking ready"))
    elif config["adoption"] != "ready":
        findings.append(("error", "adoption must be draft or ready"))
    if (not isinstance(config["checks"], list) or not config["checks"]
            or not all(isinstance(item, str) for item in config["checks"])):
        findings.append(("error", "checks must be a nonempty list of verification procedures"))
    if not isinstance(config["exceptions"], list):
        findings.append(("error", "exceptions must be a list"))
    else:
        for index, item in enumerate(config["exceptions"]):
            text_fields(item, {"scope", "reason", "reference"}, "exceptions[{}]".format(index), findings)
    is_self = (root.resolve() == SOURCE.resolve() and profile == "standard")
    if profile == "standard":
        if not is_self:
            findings.append(("error", "The standard profile is reserved for the validator's own repository"))
        object_keys(config["environments"], set(), "environments", findings)
        object_keys(config["delivery"], set(), "delivery procedures", findings)
    else:
        if object_keys(config["environments"], {"stage", "production"}, "environments", findings):
            for name, env in config["environments"].items():
                text_fields(env, {"target", "verify"}, "environments." + name, findings)
        if text_fields(config["delivery"], {"candidate", "approval", "approver", "stage", "promote", "rollback", "backup"}, "delivery procedures", findings):
            if config["delivery"]["approval"] != "explicit":
                findings.append(("error", "Delivery requires explicit approval of the candidate and target"))
    if project_ok and not MARKER.search(config["project"]["repository"]):
        parsed = urlparse(config["project"]["repository"])
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
            findings.append(("error", "project.repository must be an HTTPS URL without credentials"))
    if standard_ok:
        standard = config["standard"]
        if standard["repository"] != REPOSITORY:
            findings.append(("error", "standard.repository must identify MojoTheApe/master-repo"))
        if not re.fullmatch(r"\d+\.\d+\.\d+", standard["version"]):
            findings.append(("error", "standard.version must be a numeric X.Y.Z version"))
        revision = standard["revision"]
        if revision == "self":
            if not is_self:
                findings.append(("error", "Consumers cannot use the self revision"))
        elif not SHA.fullmatch(revision):
            findings.append(("error", "standard.revision must be a full immutable commit SHA"))
        if expected_revision:
            if not SHA.fullmatch(expected_revision) or revision != expected_revision:
                findings.append(("error", "Running action revision does not match the immutable descriptor pin"))
            if standard["version"] != (SOURCE / "VERSION").read_text().strip():
                findings.append(("error", "Descriptor version differs from the running standard's VERSION"))
        if is_self and standard["version"] != (SOURCE / "VERSION").read_text().strip():
            findings.append(("error", "Self descriptor version differs from VERSION"))
        if not is_self:
            workflow = safe_path(root, ".github/workflows/delivery-check.yml")
            if not workflow.is_file():
                findings.append(("error", "Missing .github/workflows/delivery-check.yml"))
            else:
                uses = re.findall(r"(?m)^\s*-?\s*uses:\s*[\"']?MojoTheApe/master-repo@([^\s\"'#]+)", workflow.read_text())
                if uses != [revision]:
                    findings.append(("error", "Delivery check must call master-repo once at the descriptor's exact revision"))
    for name in ("AGENTS.md", "docs/DELIVERY.md"):
        path = safe_path(root, name)
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            findings.append(("error", "Missing or empty " + name))
    agents = safe_path(root, "AGENTS.md")
    if agents.is_file() and "delivery.json" not in agents.read_text(encoding="utf-8"):
        findings.append(("error", "AGENTS.md must point to delivery.json"))
    placeholders(config, "delivery", findings)
    return findings


def source_revision():
    result = subprocess.run(["git", "-C", str(SOURCE), "status", "--porcelain"], capture_output=True, text=True)
    if result.returncode or result.stdout.strip():
        raise ValueError("Onboarding requires a clean Git checkout of the selected standard")
    revision = subprocess.check_output(["git", "-C", str(SOURCE), "rev-parse", "HEAD"], text=True).strip()
    if not SHA.fullmatch(revision):
        raise ValueError("Cannot identify the standard source commit")
    return revision


def scaffold(root, profile, revision, apply=False):
    if profile not in {"vps", "n8n", "local"} or not SHA.fullmatch(revision):
        raise ValueError("Scaffolding requires a supported consumer profile and immutable source revision")
    root = Path(root).expanduser().absolute()
    template = SOURCE / "templates/project"
    values = {"__PROJECT_NAME__": root.name, "__PROFILE__": profile,
              "__STANDARD_REVISION__": revision,
              "__STANDARD_VERSION__": (SOURCE / "VERSION").read_text().strip(),
              "__COMPLETION__": PROFILES[profile]}

    def replace(value):
        if isinstance(value, dict):
            return {key: replace(item) for key, item in value.items()}
        if isinstance(value, list):
            return [replace(item) for item in value]
        return values.get(value, value) if isinstance(value, str) else value

    data = replace(json.loads((template / "delivery.json").read_text()))
    planned = {"delivery.json": json.dumps(data, indent=2, ensure_ascii=False) + "\n"}
    for source, destination in FILES.items():
        contents = (template / source).read_text(encoding="utf-8")
        for token, value in values.items():
            contents = contents.replace(token, value)
        planned[destination] = contents
    collisions = []
    for name in planned:
        path = safe_path(root, name)
        if path.exists():
            collisions.append(name)
        for parent in path.parents:
            if parent == root.parent:
                break
            if parent.exists() and not parent.is_dir():
                raise ValueError("A required parent is not a directory: " + str(parent))
    if collisions:
        raise ValueError("Existing files preserved; integrate manually: " + ", ".join(collisions))
    if apply:
        for name, contents in planned.items():
            path = safe_path(root, name)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8") as output:
                output.write(contents)
    return list(planned)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("audit", "validate"):
        command = commands.add_parser(name)
        command.add_argument("--root", type=Path, default=Path.cwd())
        command.add_argument("--expected-revision", default=None)
        command.add_argument("--allow-draft", action="store_true")
    init = commands.add_parser("init")
    init.add_argument("--root", type=Path, required=True)
    init.add_argument("--profile", choices=("vps", "n8n", "local", "package", "tooling"), required=True)
    init.add_argument("--repository", required=True)
    init.add_argument("--name", required=True)
    init.add_argument("--id-prefix", required=True)
    init.add_argument("--workspace-id", required=True)
    init.add_argument("--no-staging", action="store_true")
    for cmd in (init, commands.add_parser("upgrade")):
        if cmd is not init: cmd.add_argument("--root", type=Path, required=True)
        cmd.add_argument("--tracker-root", type=Path, required=True)
        cmd.add_argument("--python", default=sys.executable, help="Python 3.11+ for the pinned Tracker exporter")
        cmd.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command in ("init", "upgrade"):
            import project
            revision = source_revision()
            if args.command == "init":
                inputs = {"profile": args.profile, "repository": args.repository, "name": args.name,
                          "prefix": args.id_prefix, "workspace_id": args.workspace_id, "staging": not args.no_staging}
                result = project.init(args.root, inputs, revision, args.tracker_root, args.python, args.apply)
            else:
                result = project.upgrade(args.root, revision, args.tracker_root, args.python, args.apply)
            print(json.dumps(result, indent=2))
            return 1 if result.get("conflicts") else 0
        findings = inspect(args.root, args.expected_revision)
        for kind, message in findings:
            print(kind.upper() + ": " + message)
        blocking = [item for item in findings if item[0] == "error" or not args.allow_draft]
        if blocking:
            print("Delivery setup is not ready; {} finding(s)".format(len(blocking)))
            return 1
        print("Draft structure valid; setup still incomplete" if findings else "Delivery description valid; runtime verification remains project-specific")
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print("Cannot complete check: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
