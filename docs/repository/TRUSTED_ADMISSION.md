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

PR/body/readiness, task, main, state-dispatch and source-check events recompute
current PRs. One cancellation group replaces stale evaluations; the gate never
waits for itself. GitHub event processing is asynchronous, so inspect the current
final operator result immediately before merge.

## Protected publisher and refresh

Use the compatible Tracker's reviewed repository admission setup for the private
`Mojo Source Admission` authentication-only App. Its only write is commit statuses;
no webhook/server/database or agent identity system is introduced. Registration,
installation and credential placement require one-time owner approval. Initially
install only in this protected public Master; keep the key out of unprotected
private Tracker until its actual protection/plan dependency is resolved.

The `source-admission` environment must restrict secrets to exactly branch `main`
(custom Branch rule, no tags/wildcards/PR/state refs). Keep its private key as an
environment secret and client ID as an environment variable. No repository-level
key or generic Protected branches option is acceptable. No per-job human approval
is needed. `deployment: false` prevents a fake application deployment record.
Accepted main alone runs the verified canonical snapshot. The normal GitHub token
reads; a pinned official action mints the distinct App's status-only token for this
repository. There is no fallback to Actions App15368. App ownership/key rotation,
administrators and already accepted main are the remaining trust boundary.

Explicitly allow only this trusted workflow in GitHub's pull_request_target event
policy before the announced November9/16 2026 brownouts and December2 default
block. See [GitHub announcement](https://github.blog/changelog/2026-11-02-pull_request_target-blocked-by-default-december-2/).

After compatible writers/workflow exist, `source_admission_refresh: true` selects
post-CAS repository_dispatch to accepted main. It does not rely on the actual
tracker-state branch having a workflow or executing skip-ci commits. The event
contains no trusted evidence; the evaluator reads current data. A failed dispatch
leaves state committed and reports refresh unconfirmed; repeat only the compatible
engine's refresh-admission command, never a review or ownership write. A crash
between CAS and notification needs the same recovery; no outbox guarantee is made.
The current final operator read remains mandatory before merge.

Use one owner-controlled bootstrap window without other integration and retain
main's exact SHA. After published compatible Tracker, review the real bootstrap
PR and its exact policy preserving validate, portable-runtime, tracker-link and
skill-impact; confirm all four actual checks. Keep the approved App key outside
GitHub environments. Use the published canonical engine locally with accepted
Master config and that separately inspected policy to publish the real admission
for this PR; never run candidate code or fabricate a result/run. Read back the App
producer and require admission from its exact distinct ID, retaining all current
protections. Re-read settings and unchanged main. Only then store the key in the
exact-main environment, perform fresh final admission and merge bootstrap. A main
advance requires reassessment before secret placement. This is one-time bootstrap
trust in the owner/administrator, not a routine bypass.

On the next genuine MR-91 common-process PR, verify automatic refusal without
review, success after current independent review and review-after-CI refresh.
Preserve strict freshness, enforced admins, PR-only main and no force/deletion.
Local tests do not prove these hosted outcomes. The App/key stays out of Tracker
until its actual protections and eligible private environment are verified.

Tracker's private-repository tariff restriction remains open until actually solved.
No plan/visibility change is authorized. Standard publication, skill distribution
and consumer adoption retain their separate actual outcomes. This task changes
no consumer settings or live service.
