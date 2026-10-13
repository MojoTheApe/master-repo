#!/usr/bin/env python3
"""Read-only audit of classic GitHub branch controls; never configure or merge."""
import argparse
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import quote, urlparse

import standard

REPO = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*\Z")


class LookupError(ValueError):
    """An unavailable response is not evidence that a control is absent."""


def request(path):
    result = subprocess.run(["gh", "api", "--hostname", "github.com", path],
                            capture_output=True, text=True, timeout=30)
    if result.returncode:
        status = re.search(r"HTTP (\d{3})", result.stderr)
        # Do not publish raw CLI output, credentials or private response bodies.
        raise LookupError("GitHub lookup unavailable" +
                          (" (HTTP " + status.group(1) + ")" if status else ""))
    try:
        return json.loads(result.stdout)
    except (ValueError, TypeError) as error:
        raise LookupError("GitHub lookup returned invalid JSON") from error


def selection(root):
    data = standard.read_descriptor(root)
    parsed = urlparse(data["project"]["repository"])
    repository = parsed.path.strip("/")
    if (parsed.scheme != "https" or parsed.netloc != "github.com" or
            parsed.query or parsed.fragment or not REPO.fullmatch(repository)):
        raise ValueError("Use the project's actual github.com repository URL")
    if data.get("schema_version") == 2:
        workflow = data["workflow"]
        branches = [workflow["main_branch"]]
        if workflow["staging"]:
            branches.append(workflow["stage_branch"])
        checks = workflow["required_checks"]
    elif data.get("schema_version") == 1 and data.get("profile") == "standard":
        branches, checks = ["main"], ["validate", "tracker-link", "skill-impact"]
    else:
        raise ValueError("Legacy consumers need explicit --branch and --check selections")
    return repository, branches, checks


def audit(repository, branches, checks, lookup=request):
    if not REPO.fullmatch(repository):
        raise ValueError("Expected owner/repository")
    if (not branches or any(not isinstance(b, str) or not b.strip() for b in branches)
            or not checks or any(not isinstance(c, str) or not c.strip() for c in checks)):
        raise ValueError("Select real branches and required check names")
    rows = []
    for branch in dict.fromkeys(branches):
        row = {"branch": branch, "verified": False, "findings": []}
        try:
            prefix = "repos/" + repository + "/branches/" + quote(branch, safe="")
            actual = lookup(prefix)
            if (not isinstance(actual, dict) or actual.get("name") != branch
                    or type(actual.get("protected")) is not bool):
                raise LookupError("Branch identity/protection response is incomplete")
            protection = lookup(prefix + "/protection")
            if not isinstance(protection, dict):
                raise LookupError("Classic protection response is incomplete")
            if actual["protected"] is not True:
                raise LookupError("Branch and classic protection responses disagree")
            status = protection.get("required_status_checks")
            reviews = protection.get("required_pull_request_reviews")
            if not isinstance(status, dict):
                row["findings"].append("Required status checks are not configured")
                status = {}
            contexts = status.get("contexts", [])
            bound = status.get("checks", [])
            if (not isinstance(contexts, list) or any(not isinstance(c, str) for c in contexts)
                    or not isinstance(bound, list)
                    or any(not isinstance(c, dict) or not isinstance(c.get("context"), str) for c in bound)):
                raise LookupError("Required status check response is incomplete")
            required = set(contexts) | {c["context"] for c in bound}
            row["required_checks"] = sorted(required)
            row["missing_checks"] = sorted(set(checks) - required)
            if row["missing_checks"]:
                row["findings"].append("Missing required checks: " + ", ".join(row["missing_checks"]))
            if status.get("strict") is not True:
                row["findings"].append("Up-to-date branch checks are not enforced")
            if not isinstance(reviews, dict):
                row["findings"].append("Native pull-request requirement is not configured")
            else:
                count = reviews.get("required_approving_review_count")
                if type(count) is not int or not 0 <= count <= 6:
                    raise LookupError("Native review-count response is incomplete")
                row["native_approving_review_count"] = count
                bypass = reviews.get("bypass_pull_request_allowances", {})
                if not isinstance(bypass, dict) or any(bypass.get(k) for k in ("users", "teams", "apps")):
                    row["findings"].append("Native pull-request bypass allowances need explicit review")
            for key, expected, finding in (
                    ("enforce_admins", True, "Administrators can bypass configured controls"),
                    ("allow_force_pushes", False, "Force-push restriction is absent or unverified"),
                    ("allow_deletions", False, "Branch-deletion restriction is absent or unverified")):
                value = protection.get(key)
                if not isinstance(value, dict) or value.get("enabled") is not expected:
                    row["findings"].append(finding)
            row["verified"] = not row["findings"]
            row["state"] = "verified-classic-controls" if row["verified"] else "missing-controls"
        except (LookupError, OSError, subprocess.SubprocessError) as error:
            row["state"] = "unverified"
            row["findings"].append(str(error))
        rows.append(row)
    return {"repository": repository, "verified": all(row["verified"] for row in rows),
            "coverage": "Classic branch controls only; independently verify rulesets, check producers and agent review.",
            "branches": rows}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--repository")
    parser.add_argument("--branch", action="append")
    parser.add_argument("--check", action="append")
    args = parser.parse_args(argv)
    try:
        if args.repository and args.branch and args.check:
            repository, branches, checks = args.repository, args.branch, args.check
        else:
            repository, branches, checks = selection(args.root)
            repository = args.repository or repository
            branches, checks = args.branch or branches, args.check or checks
        result = audit(repository, branches, checks)
        print(json.dumps(result, indent=2))
        return 0 if result["verified"] else 1
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({"verified": False, "error": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
