import io
import json
from pathlib import Path
import sys
import unittest
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check_pr


class TicketLinkTests(unittest.TestCase):
    def test_real_reference_format(self):
        self.assertEqual(check_pr.issue_numbers("Summary\nTracker issues: #1, #42\nValidation"), [1, 42])

    def test_missing_duplicate_and_nonlocal_references_rejected(self):
        for body in (None, "No ticket", "Tracker issues: #1\nTracker issues: #2",
                     "Tracker issues: #1, #1", "Tracker issues: #0", "Tracker issues:",
                     "Tracker issues: evil/repo#1", "Tracker issues: #1; do something"):
            with self.subTest(body=body):
                with self.assertRaises(ValueError):
                    check_pr.issue_numbers(body)

    def test_lookup_accepts_real_issues(self):
        requests = []

        def open_fixture(request, timeout):
            requests.append(request.full_url)
            self.assertEqual(timeout, 15)
            number = int(request.full_url.rsplit("/", 1)[1])
            return io.BytesIO(json.dumps({"number": number}).encode())

        check_pr.verify_issues([1, 2], "example/repo", "fixture-token", opener=open_fixture)
        self.assertEqual(requests, ["https://api.github.com/repos/example/repo/issues/1",
                                    "https://api.github.com/repos/example/repo/issues/2"])

    def test_pull_request_is_not_accepted_as_ticket(self):
        def open_fixture(request, timeout):
            return io.BytesIO(b'{"number": 1, "pull_request": {}}')
        with self.assertRaisesRegex(ValueError, "not a PR"):
            check_pr.verify_issues([1], "example/repo", "fixture-token", opener=open_fixture)

    def test_failed_lookup_is_not_a_pass(self):
        def open_fixture(request, timeout):
            raise HTTPError(request.full_url, 404, "Not Found", {}, None)
        with self.assertRaises(HTTPError):
            check_pr.verify_issues([1], "example/repo", "fixture-token", opener=open_fixture)

    def test_missing_token_and_invalid_repository_do_not_make_requests(self):
        def never_open(*args, **kwargs):
            self.fail("No network request expected")
        for repo, token in (("example/repo", ""), ("example/repo/../../other", "token")):
            with self.assertRaises(ValueError):
                check_pr.verify_issues([1], repo, token, opener=never_open)


if __name__ == "__main__":
    unittest.main()
