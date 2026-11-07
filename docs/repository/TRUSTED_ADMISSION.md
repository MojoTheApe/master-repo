# Trusted source admission

MR-91 consumes canonical Tracker admission and existing independent-review records.
tracker/admission-policy.json selects only own-source review/CI. Actual display
config, manual Issue status/closure, schema1 descriptor and history stay intact.

The genuine independent Reviewer records the complete Issue/head/base/tree with
the exact compatible Tracker record-review command, this repository's config and
admission policy. See that engine's repository admission guide for fields/command.
The report identifies the actual separate reviewer session; a label is insufficient.

check_admission.py verifies the full manifest and every helper in the already
mechanically refreshed portable snapshot before loading the canonical adapter.
Candidate code/config is never imported with the status-writing token. From a
current accepted main checkout, use one read-only final admission:

```sh
python3 scripts/check_admission.py --config tracker/config.json --admission-policy tracker/admission-policy.json --trusted-revision "$(git rev-parse HEAD)" --pr PR_NUMBER --check-only
```

Keep candidate work isolated and use its real PR number. The genuine review record
must already exist. This includes linkage; do not repeat a separate final link
check. Missing/stale/self-review, changed scope, unsuccessful source CI or changing
decision inputs block. The GitHub workflow uses the same canonical implementation.

PR/body/readiness, task, tracker-state, main and source-check events recompute
current PRs. One cancellation group replaces stale evaluations; the gate never
waits for itself. GitHub event processing is asynchronous, so inspect the current
final operator result immediately before merge.

Install via a reviewed bootstrap PR under old controls. After accepted compatible
code/policy/checks exist, require admission with validate, portable-runtime,
tracker-link and skill-impact. Preserve strict freshness, observed GitHub Actions
producer15368, enforced admins, PR-only main and disabled force/deletion. Read back
effective settings; source tests alone never establish protection.

Tracker's private-repository tariff restriction remains open until actually solved.
No plan/visibility change is authorized. Standard publication, skill distribution
and consumer adoption retain their separate actual outcomes. This task changes
no consumer settings or live service.
