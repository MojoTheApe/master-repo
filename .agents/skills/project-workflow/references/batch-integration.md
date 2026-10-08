# Independently approved tasks, frozen integration batches

Use only when the project's pinned standard and Tracker support execution policy
schema 2, the descriptor/config policies match, and the supported shared-state
migration has actually completed. Installing this skill never enables the mode.
Keep execution-v1 and legacy consumers on their own pinned lifecycle.

An explicitly adopted [instruction-only route](process-instructions.md) is checked
before batch approval. Eligible sources retain independent review through direct
main completion and never enter Approved/intake; other work follows this guide.

For an existing execution-v1 project, finish the adoption task through its old
pinned stage/main handoff before changing durable state. Use the supported
`execution migrate --preserve-review-queue` only after all active claims and
stage candidates are finished. It preserves ready queued source PRs, authors,
tasks and handoffs; it does not approve them. Read the new pinned guide before
the next independent review. Existing stage-targeted source PRs become
approval-only and may not merge directly into stage.

When original queued handoffs reference genuinely closed, unmerged nondraft PRs,
first verify that the exact pinned engine supports the flag in its guide. Older
engines retain their supported commands; a newer skill does not upgrade them. Use
the compatible engine's explicit
`execution migrate --preserve-review-queue --preserve-closed-review-handoffs`
preview/apply option. Both flags are mandatory; preserve idle ownership, unchanged
capacity, the original queue order/tasks/authors/branches/handoffs and actual
reported Issue/PR pairs. Closed records remain unfinished history for separate
owner resolution. They acquire no ready, Approved, admission or completion proof;
normal source review and batch admission still require a current ready open PR.
Verify the preserved state and fresh board without creating demonstration features.


## Individual implementation and approval

The Coordinator screens dependencies and overlap, delegates only authorized
independent work, and preserves each Worker's isolated branch, worktree and claim.
Keep one task per source PR and the task's genuine Worker history. A Worker hands
off to Review; a separate non-implementing Reviewer acquires the single review
lane, reviews actual source/base/scope and records the durable report. All required
source checks stay enabled. Use the pinned Tracker's approval command to verify
current evidence and move the task to Approved, releasing the review lane.
Approved is waiting for integration, never completion or authorization to edit.

For source edits, changed scope/base or stale approval, use the supported return
command, then a fresh author implementation claim on the original branch, checks,
handoff and independent review. Labels alone cannot approve or reserve work.
Do not impersonate all Workers as the Coordinator or reuse a reviewer identity
for someone who actually wrote a member's changes.

## Ship a fixed intake

On an authorized "ship all Approved" request, snapshot the currently eligible
Approved tasks. New arrivals wait for another intake. Respect dependencies and
priority; report ineligible/stale tasks without silently completing or discarding
them. Partition that fixed intake into sequential batches no larger than the
project's batch_limit (initial ACL setting: five). One task is a valid urgent batch;
never wait to fill all five. Implementation capacity and batch size are independent.

Acquire the separate Coordinator integration claim for one frozen batch. Preserve
each member's task, source PR/head/base, approval/scope/policy evidence and current
main baseline. Assemble approved source revisions in an isolated integration
branch. Conflict resolution is code: return affected tasks to their authors and
independent review rather than inventing unreviewed fixes in the batch branch.

Arrange independent integration review of the actual combined candidate and its
composition; the Reviewer must be independent of every implementing member. Run
the complete applicable integration checks. Merge the admitted candidate into
permanent stage, record every member as Stage, and verify the actual configured
stage target and exact tree. No new task or content joins a testing batch.

Promote only the same passed tree/member set into main. Reuse valid exact-content
proof, not checks of separate source trees. Record Merged per fully included task
and release the integration claim only after the durable handoff succeeds.
Close superseded source PRs only with actual inclusion evidence, retaining their
branches, links and review history. Required package/production delivery remains
unfinished until its own verified receipt.

## Failure and recovery

Inspect persisted intake/batch ownership, PR/head, main/stage and receipts before
resuming. A timeout is not takeover permission. Only the owning session, or an
explicitly supported transfer after the old session stopped, resumes mutations.
Before stage entry, cancellation may return unchanged members to Approved with
history. After stage entry, retain exclusive integration ownership through any
author fix, fresh approval, rebuilt candidate, integration review and verification.
Do not reset stage, drop already integrated work, smuggle fixes into promotion or
reuse old proof after main/candidate/membership changes. Before stage entry,
cancel the batch and select a smaller subset of the same fixed intake to leave
a failed member for later. After stage entry, retain the same members for the
supported author-fix/rebuild path. Selective recovery after stage requires a
separately supported and reviewed recovery procedure. Preserve all actual authors
and history.

Before the next batch, reconcile stage/main and recheck each source approval against
the new baseline. Do not automatically repeat a passing unchanged CI run. Use the
project's actual installer/release controls after main; merging does not deliver
an update to employee machines.
