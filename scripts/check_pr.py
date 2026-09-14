#!/usr/bin/env python3
"""Validate this repository's ticket links; other projects retain their tracker."""

import argparse
import json
import os
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def issue_numbers(body):
    if not isinstance(body, str) or len(body) > 65536:
        raise ValueError("PR body must be text within the supported size limit")
    lines = re.findall(r"(?m)^Tracker issues:[ \t]*(.*)$", body)
    if len(lines) != 1:
        raise ValueError("Include exactly one Tracker issues: #NUMBER line")
    refs = [item.strip() for item in lines[0].split(",")]
    if not 1 <= len(refs) <= 10 or any(not re.fullmatch(r"#[1-9][0-9]*", ref) for ref in refs):
        raise ValueError("Use one to ten local issue numbers, for example Tracker issues: #1, #2")
    if len(refs) != len(set(refs)):
        raise ValueError("Ticket references must not be duplicated")
    return [int(ref[1:]) for ref in refs]


def verify_issues(numbers, repository, token, opener=urlopen):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Expected owner/repository")
    if not token:
        raise ValueError("GITHUB_TOKEN is required for read-only issue verification")
    for number in numbers:
        request = Request("https://api.github.com/repos/{}/issues/{}".format(repository, number),
                          headers={"Authorization": "Bearer " + token,
                                   "Accept": "application/vnd.github+json",
                                   "User-Agent": "master-repo-ticket-check"})
        with opener(request, timeout=15) as response:
            payload = json.load(response)
        if payload.get("number") != number or "pull_request" in payload:
            raise ValueError("Reference #{} must identify a real issue, not a PR".format(number))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    args = parser.parse_args(argv)
    try:
        event = json.loads(args.event.read_text())
        numbers = issue_numbers(event.get("pull_request", {}).get("body"))
        verify_issues(numbers, args.repository, os.environ.get("GITHUB_TOKEN", ""))
        print("Verified real ticket references: " + ", ".join("#" + str(n) for n in numbers))
        return 0
    except HTTPError as error:
        print("Ticket lookup failed with HTTP {}".format(error.code), file=sys.stderr)
    except (OSError, ValueError, URLError) as error:
        print("Ticket validation failed: " + str(error), file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
