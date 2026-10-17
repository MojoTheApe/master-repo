# Bounded CI retry

Retry control is an explicit project choice. Mirror `workflow.ci_retry` in
`delivery.json` with `ci_retry_policy` in Tracker configuration:

```json
{"schema_version": 1, "max_executions": 2}
```

Version1 supports an explicit limit of1 or2 total executions per unchanged
episode:1 permits only the original,2 permits the original plus at most one
automatic retry. Select2 only in a reviewed explicit policy. Omission preserves
existing behavior; missing or malformed fields do not acquire defaults. Master
uses Tracker's exact structural snapshot rather than maintaining another schema.
Use `init|upgrade --ci-retry-policy FILE` for explicit selection. Exporting or
installing files neither activates state nor starts a retry.
An ordinary upgrade preserves local choices. If three-way merging would retain a
different local policy from the explicitly requested file, the upgrade stops
without writes; reconcile descriptor and Tracker configuration in the project PR.

Read the exact pinned engine's generated CI_RETRY.md for maintained commands,
policy/state adoption, diagnosis, reconciliation and recovery. Supporting readers
and all actual writers must be published and available before the real owned idle
activation. Retain other selected policy fences, task/claim/batch/history and
completion receipts. Source release, service deployment, selection and actual
consumer activation are separate outcomes. Existing projects retain their pins.

## Diagnose before dispatch

Product defects, configuration, billing/access/quota and unknown failures do not
authorize automatic reruns. A native `failure` or `startup_failure`, a changed
cause label or a log substring does not prove transient infrastructure failure.
The supported operator path records a separate durable diagnosis review by an
API-authenticated maintainer/admin with bounded redacted evidence, exact native
run/attempt/content/workflow identity and evidence digest/links. Call this
operator-attested: the authenticated principal is not proof that the human owner
personally reviewed it, and a digest identifies reviewed evidence without proving
its cause objectively. Retry consumes the persisted reviewed record, not a bare
caller-provided transient flag.

The plan must be explicitly reviewed as verification-only and bound to the actual
immutable workflow and applicable full coverage. A budget grants no release,
deployment or product-operation permission. Preserve project-owned commands,
timeouts, platform/installer requirements and current admission. Public portable
CI gates retain their own-repository read token and gain no dispatch permission.

Unresolved account/infrastructure/configuration causes persist across unrelated
heads, policy edits or successes in a different affected environment. A verified
relevant fix or an explicitly authorized recorded resolution may clear the
blocker; keep its original evidence and history. A successful execution does not
replenish the unchanged episode's budget. Unknown cause/history stays conservative.

## Two identities and one durable budget

Strict verification identity retains actual repository/route, accepted scope,
head/base/composition/tested tree, trusted workflow/producer/profile and required
jobs/platforms, resolved relevant environment/dependency/build inputs and native
run/job/attempt proof. A reservation is not successful coverage or admission.

Budget equivalence retains the logical verification purpose and relevant inputs
across chats, sessions, native run IDs, equivalent empty commits and editable
cause/plan names. Scope or plan renaming cannot manufacture new budget. A real
relevant product correction creates a new candidate through actual changed input
and recorded fix relation; disjoint files or a different SHA alone prove no fix.
Persist unresolved causes separately from candidate identity. Count equivalent
native executions started outside the wrapper, preserving ambiguous attribution.

Native reruns retain the original event SHA/ref and original triggering actor's
privileges. They cannot test a newly fixed head by relabelling an old run. Start
appropriate new-candidate verification for genuine fixes. Partial retry requires
the adopted gate's actual original-job and dependent-coverage proof. The common
single-attempt collector does not supply that extended proof: use a supported
bounded full attempt or stop, preserving stronger reviewed project adapters.
See [GitHub's native rerun rules](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs).

## Uncertain writes and recovery

The existing durable Tracker state owns episodes, consumption, diagnoses,
reservations and native observations. Before dispatch, reconcile available native
work and CAS-reserve the unique intent. Only the caller that freshly wins its
separate dispatch-barrier CAS may send the native POST, including when two
processes share owner/session credentials. Reading a stored barrier after restart
never authorizes sending again. Recheck policy, actual candidate relevance and
native attempt immediately before POST; external work or changed inputs stop stale
dispatch and are reconciled into the budget.

Send once with transport retries disabled. Accepted but not yet visible work and
lost response/crash/ambiguous CAS or POST remain held. A restart uses GET-only
reconciliation; one empty response, timeout or elapsed age cannot free budget.
An unattributed external attempt cannot automatically prove whether an uncertain
own request also took effect. Only an attributable native outcome or a
method-specific proven no-side-effect outcome with fresh native reconciliation
can settle it. Human instructions, permission and resolution text cannot clear
an uncertain dispatch. A definitive no-side-effect rejection still retains any
applicable permission/account blocker and reconciles outside execution; it is
not permission to retry blindly.

The native API has no documented request idempotency key for reruns. A crash
between the winning barrier and POST can remain indistinguishable from a lost
successful response. The safe result is held uncertainty; do not claim exactly
once execution. Direct human Actions access is outside the wrapper's lock and can
race its final GET. Observe/report excess outside attempts and stop automation,
without claiming technical prevention of human reruns. Read-only API request
retries are not execution attempts or permission for a native retry.
See [GitHub's REST rerun contract](https://docs.github.com/en/rest/actions/workflow-runs).

Use the project-owned [fast/full submission plan](verification-submission.md) and
[on-demand accounting](ci-accounting.md) to retain useful feedback and comparable
ordinary-work measurements. Reservations hold retry budget without inventing
observed job minutes or actual billing. This policy adds no background retry
service, paid demonstration run or automatic consumer migration.
