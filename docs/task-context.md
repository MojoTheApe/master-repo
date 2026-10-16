# Shared lifecycle and task context

All profiles share task relevance, ownership, independent review, integration and
completion semantics. Settings choose product checks, optional Stage and delivery
adapters. This is MR-30 / WFO-01–04; Task Tracker TT-136 owns its executable
companion. ACL is one consumer, with no special task workflow.

## Responsibilities and checks

| Moment | Actor and result | Verification |
| --- | --- | --- |
| Idea / Backlog | Agent records the requested outcome | Classification, duplicates and dependencies; no implementation |
| To Do | Owner selects priority/order | Selection alone does not start work |
| Before implementation | Agent assesses current relevance | Complete requirements, code/decisions, related work, dependencies and baseline |
| In Progress | Genuine Worker claims an isolated branch | Applicable source self-checks; preserve scope and decisions |
| Review | Independent non-implementing Reviewer inspects exact scope/head/base | Inspect author evidence; add checks for findings or missing scope |
| Approved in execution v2/v3 | Source review/checks retained; lane released | Waiting is not completion or integration authorization |
| Main changed while waiting | Independent Reviewer assesses compatibility or requests fixes | Actual semantic delta/dependencies; disjoint paths are insufficient |
| Frozen batch | Coordinator assembles exact approved members | Independent combined review, composition and all applicable candidate checks |
| Optional Stage | Verify exact admitted candidate/target | Current tree/members/baseline and actual stage evidence |
| Main admission / merge | Agent verifies admission and actual GitHub controls | Required review/checks/composition and Stage when enabled |
| Required delivery | Authorized maintained adapter and verifier | Actual target/revision/task evidence; failures remain unfinished |

| Profile | Product-owned checks and completion |
| --- | --- |
| VPS | Logic/API/UI/data compatibility; deploy and verified production behavior |
| Package | Product/platform/build checks; immutable publication and agreed install/update/recovery acceptance |
| n8n | Workflow/schema/integration checks; authorized publication and verified behavior |
| n8n-source | Checked reviewed source merge; runtime transfer remains separate |
| Local manual pull | Checked admitted merge; owner may pull later |
| Tooling | Checked admitted merge; no application deployment |

The bounded instruction-only route retains its full-diff classifier, independent
review and direct-main completion. No new status or routine owner approval round
is added. This matrix does not implement WFO-05/06 CI reuse or remove product
checks; use [verification](verification.md). Agent admission and server-enforced
branch protection are separate. Report configured/enforced/unsupported controls
honestly; repeated human confirmation is not protection.

## Explicit compatible policy

Mirror `workflow.task_context: {"schema_version": 1}` in delivery.json with
`task_context_policy: {"schema_version": 1}` in tracker/config.json. V1 requires
execution schema 2 or 3 and a compatible pinned engine. Initializer flag
`--task-context` explicitly selects it with batch execution. Absent-policy projects
retain their adopted behavior. New defaults, releases and rollout remain WFO-08–10.

Read the exact engine's `guide` and TASK_CONTEXT.md for commands/evidence. Separated
exports put the guide in docs/repository and the read-only helper in
`.workflow/tools/tracker_task_context.py`, retaining a scripts entry point.
A newer global skill cannot activate unsupported commands or consumer policy.

## Relevance before editing

Read the whole Issue and authoritative context. Determine whether the outcome is
still needed, already implemented, superseded or inconsistent with current code
and owner decisions. Do not infer relevance from age, labels or a matching title.
Record repository/Issue, requirements digest, current main and real Worker/session
with concrete code, decision, related-work and dependency findings.

`ready` permits otherwise authorized work through normal admission.
`needs-clarification` and `superseded` are durable assessments, not new statuses or
claims. Machine checks establish binding/completeness, not semantic truth. Ask the
owner only for an unresolved material outcome change or genuine authorization
boundary. Same-owner resume reuses unchanged scope/main evidence; changed context
or a replacement needs current assessment. Obtain the real planning Issue ID
before assessing new work; never fabricate readiness for a speculative ID.

## Requirements and working history

All text remains authoritative except one explicitly paired terminal block:

```text
<!-- tracker-journal:start -->
### Handoff
Branch, PR and dated progress or verification observations.
<!-- tracker-journal:end -->
```

Markers are exact standalone lines, unique, ordered and terminal. Criteria,
checkboxes, dependencies and blocker records stay outside. Ordinary History or
Verification headings have no special meaning. Removing a requirement or moving
it inside changes scope; checkbox state is never normalized away.

New scope has an opaque `v2:` prefix. Old hashes retain whole-body meaning;
historical receipts are never silently rehashed. Permitted journal edits do not
revoke new-policy approval or shift outside acceptance line identities. Invalid
journals make their own task ineligible without disabling other tasks.

## Compatibility while retaining source review

After a forward main change, a genuine independent Reviewer reserves an existing
bounded source lane to inspect unchanged Approved source compatibility. Inspect
the actual delta and semantic dependencies. Preserve original source scope,
head/tree, checks, author and review; append a separate exact-bound receipt.

The receipt binds original approval, previous/current main, content, scope, policy
and real owner. Status stays Approved; held compatibility blocks selecting that
task into a batch. Changed scope/head, failed checks, divergent main or necessary
code/conflict fixes use normal author return/checks/handoff/source review.
Unchanged source needs no invented author edit merely to refresh a baseline.

Independent combined review, composition and all applicable candidate checks
remain required. Separate source trees cannot prove a batch; old source tests
never become tests of new main. Frozen batches and Stage retain owned recovery;
reconcile Stage with main before the next staged batch.

## Activation and history

Initial explicit execution adoption creates fenced outer protocol 4 with retained
execution state 2; old writers reject it. Maintenance wraps/restores that fence.
Existing adoption uses the exact engine's inspected idle `task-context adopt`
under genuine owned maintenance after reviewed official current-main config and
compatible writer/projection publication. Preserve queues, old approvals, delivery
receipts, authors and history. Old proof stays conservative until a genuine new
review records new-protocol scope. Actual consumer activation and fresh-board
verification belong to its upgrade, not this source implementation.
