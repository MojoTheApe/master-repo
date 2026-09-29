# Parallel implementation with one review/integration lane

Use only when the project's pinned standard and compatible Tracker support it and
`delivery.json` `workflow.execution` matches `tracker/config.json` `execution_policy`.
Version 1 accepts `implementation_limit` from 1 to 16 and `review_limit: 1`; the
initial rollout is two Workers. Absence keeps the adopted legacy slot lifecycle.
Read the pinned Tracker guide for exact commands and recovery semantics; do not
infer syntax from a newer checkout or replace claims with GitHub labels.
This mode requires the compatible delivery policy and reviewed PR admission,
with exactly one task per source PR and the same task on any stage promotion;
non-code work uses a report PR rather than a legacy completion bypass. Use neutral
`work/<task-id>-<short-name>` branch names unless a host/user requires another
accepted prefix; preserve the compatibility of existing `codex/` branches.

## Coordinate several requested tasks

1. Remain the Coordinator in the current conversation. Read each complete task,
   dependencies and project rules. Screen overlapping files/logic and shared
   runtime resources; queue dependent/conflicting work rather than promise unsafe
   parallelism. Prioritize outstanding review fixes over new work.
2. Prepare a distinct branch/worktree and isolated runtime/test resources for each
   independent task. Check shared Tracker capacity across all conversations. Use
   durable claims with the actual agent/session, coordinator, task and workspace;
   reject duplicate ownership of the same task.
3. Use the platform's available delegation mechanism to start one Worker per task,
   up to free implementation capacity. For two independent tasks and two free
   slots, delegate to two Workers and coordinate their results. Give each the exact
   worktree, scope, relevant instructions, claim and handoff obligations. Never let
   Workers mutate a shared checkout. New user-owned conversations require an
   explicit request. If delegation is unavailable, explain and work serially.
4. A Worker self-checks, documents its result, prepares its PR and explicitly hands
   off to the review queue, releasing implementation capacity. Keep author, branch,
   worktree, PR and evidence references. Ready/Review status alone is not a handoff.
5. Acquire the single review/integration lane and invoke a separate non-implementing
   Reviewer. Check whether the candidate includes the current base; any required
   branch update follows step 6 before approval. Start no other review while this
   lane is held. The same Reviewer can review later tasks in sequence. Other Workers
   may continue independent implementation.
6. For findings, a stale base or conflicts, the Reviewer uses `execution review-return`
   with the lane claim and report. Add `--keep-lane` to retain integration ownership;
   it is mandatory once the source entered stage. The author takes a fresh `work`
   or `start` implementation claim before updating/rebasing/fixing the original
   branch, runs checks and calls `execution handoff` again. Without a retained lane,
   reacquire it; with one, handoff resumes its Reviewer. Independently re-review
   current source/base/scope/policy. Coordinators and Reviewers never edit an
   unclaimed branch; a Reviewer who implements cannot give final independent approval.
7. Hold the lane through review, admission checks, optional stage and main merge.
   Preserve exact evidence and one active stage task. Release through the
   pinned completion/recovery command, then select the next eligible task. A task
   needing production/package delivery remains unfinished after its main merge.

## Identify agents and recover

Roles are Coordinator, Worker and Reviewer; use opaque distinct actor and session
IDs, for example `Worker-B3K8`. Names must not depend on vendor/model. The task's
implementation owner is its Worker; coordinator and reviewer are separate metadata.
Real GitHub Assignees remain real accounts. Record transfers and authorship history;
renaming an author or taking a new role does not create independent review.

On interruption inspect the persisted claim and actual worktree, PR/head and stage
state before resuming/transferring. Use the existing claim identity; timeouts alone
do not permit takeover or deletion of ownership. If independent review is
unavailable, report that limitation and retain the ready work for a real reviewer.
Do not fabricate delegation, identity or review evidence. Changing execution
settings requires an authorized project upgrade and safe state migration; this
skill update supplies neither consumer activation nor deployment permission.
