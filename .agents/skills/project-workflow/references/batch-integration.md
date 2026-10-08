# Independently approved tasks, frozen integration batches

Use only when the project's pinned standard and Tracker support execution policy
schema 2, the descriptor/config policies match, and the supported shared-state
migration has actually completed. Installing this skill never enables the mode.
Keep execution-v1 and legacy consumers on their own pinned lifecycle.

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
reuse old proof after main/candidate/membership changes. A failed member may be
excluded only through a supported, explicit rebuild whose final content and scope
are reviewed; the remaining members keep their actual authors and history.

Before the next batch, reconcile stage/main and recheck each source approval against
the new baseline. Do not automatically repeat a passing unchanged CI run. Use the
project's actual installer/release controls after main; merging does not deliver
an update to employee machines.
