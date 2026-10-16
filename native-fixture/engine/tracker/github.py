"""GitHub CLI transport; credentials and raw command errors never enter the UI."""
from __future__ import annotations
import json
import re
import subprocess
from urllib.parse import quote
from .delivery_policy import file_bytes  # noqa: F401  (stdlib-only home; shipped standalone)


class APIError(RuntimeError):
    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


class GitHub:
    def __init__(self, repository, command=None):
        if not re.fullmatch(r"[\w.-]+/[\w.-]+", repository):
            raise ValueError("Invalid repository")
        self.repository = repository
        self.root = f"repos/{repository}"
        self.command = command or ["gh"]

    def request(self, path, method="GET", payload=None, paginate=False, optional=False):
        command = self.command + ["api", "--method", method, path]
        if paginate:
            command += ["--paginate", "--slurp"]
        if payload is not None:
            command += ["--input", "-"]
        try:
            result = subprocess.run(command, input=json.dumps(payload) if payload is not None else None,
                                    text=True, capture_output=True, timeout=90)
        except (OSError, subprocess.TimeoutExpired):
            raise APIError("GitHub request unavailable") from None
        if result.returncode:
            match = re.search(r"HTTP (\d{3})", result.stderr)
            status = int(match[1]) if match else None
            if optional and status == 404:
                return None
            raise APIError(f"GitHub {method} failed" + (f" (HTTP {status})" if status else ""), status)
        value = json.loads(result.stdout) if result.stdout.strip() else None
        if paginate:
            if not isinstance(value, list) or not value or any(not isinstance(p, list) for p in value):
                raise ValueError("Expected complete GitHub issue pages")
            return [item for page in value for item in page]
        return value

    def issues(self):
        data = self.request(self.root + "/issues?state=all&per_page=100&sort=created&direction=asc", paginate=True)
        if any(not isinstance(i, dict) or not isinstance(i.get("number"), int)
               or not isinstance(i.get("title"), str) or i.get("state") not in ("open", "closed") for i in data):
            raise ValueError("Invalid GitHub issue response")
        numbers = [i["number"] for i in data]
        if len(numbers) != len(set(numbers)):
            raise ValueError("Duplicate issues in paginated response; retry sync")
        return [i for i in data if "pull_request" not in i]

    def action_job_log(self, job_id):
        """Native job-specific log, never an uploaded artifact or public output."""
        command = self.command + ['api', '--method', 'GET', self.root + f'/actions/jobs/{int(job_id)}/logs']
        try:
            result = subprocess.run(command, capture_output=True, timeout=90)
            if result.returncode and b'pass --allow-escape-sequences' in result.stderr:
                # Match the portable recorder's gh compatibility route. Capture
                # privately; never print terminal escapes or retry other errors.
                result = subprocess.run(command + ['--allow-escape-sequences'],
                                        capture_output=True, timeout=90)
        except (OSError, subprocess.TimeoutExpired):
            raise APIError('Native Actions job log unavailable') from None
        if result.returncode or len(result.stdout) > 8 * 1024 * 1024:
            raise APIError('Native Actions job log unavailable or exceeds proof bound')
        try:
            return result.stdout.decode('utf-8')
        except UnicodeError:
            raise APIError('Native Actions job log is not UTF-8') from None

    def issue(self, number):
        data = self.request(self.root + f"/issues/{int(number)}")
        if "pull_request" in data:
            raise ValueError("Expected an Issue, not a pull request")
        return data

    def labels(self, number, add=(), remove=()):
        path = self.root + f"/issues/{int(number)}/labels"
        current = {x["name"] for x in self.issue(number)["labels"]}
        missing = sorted(set(add) - current)
        if missing:
            self.request(path, "POST", {"labels": missing})
        for name in sorted(set(remove) & current - set(add)):
            self.request(path + "/" + quote(name, safe=""), "DELETE")
        result = self.issue(number)
        final = {x["name"] for x in result["labels"]}
        if not set(add) <= final or (set(remove) - set(add)) & final:
            raise APIError("Label verification failed; retry after checking concurrent edits")
        return result


def label_definitions(config):
    from .workflow import stages
    result = [{"name": "status:" + s['id'], "color": s['color'], "description": s['name'] + ' · ' + s['phase']}
              for s in stages(config)]
    result += [{"name": "module:" + m["id"], "color": "7B8994", "description": m["name"]} for m in config["modules"]]
    result += [{"name": "priority:" + p, "color": c, "description": "Priority: " + p}
               for p, c in (("high", "B15E4C"), ("medium", "B18E4C"), ("low", "81918E"))]
    result += [{"name": "type:" + t, "color": "9097A6", "description": "Work type: " + t}
               for t in ("bug", "feature", "improvement", "research", "operations")]
    result += [{"name": n, "color": c, "description": d} for n, c, d in (
        ("facet:design", "B895AF", "UI or UX work within its owning module"),
        ("flag:blocked", "C76A5C", "Blocked; see the task for the reason or dependency"),
        ("flag:needs_classification", "B7A88B", "Needs module classification"),
        ("flag:archived", "808080", "Archived; original workflow status and history retained"),
        ("release:included", "6B9571", "Included in the current Release scope"),
        ("kind:initiative", "808080", "Parent initiative, excluded from leaf-task release totals"),
        ("resolution:non_code", "6B9571", "Verified non-code result; evidence is in the issue"),
        ("tracker:control", "808080", "Internal tracker control record, not a product task"))]
    return result


def install_labels(api, config):
    existing = {x["name"] for x in api.request(api.root + "/labels?per_page=100", paginate=True)}
    for row in label_definitions(config):
        if row["name"] not in existing:
            api.request(api.root + "/labels", "POST", row)
