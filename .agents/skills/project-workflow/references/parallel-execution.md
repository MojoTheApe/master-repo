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

An explicitly adopted [instruction-only route](process-instructions.md) keeps
the real review lane through direct main completion, including in package
projects, without stage or package delivery. Stage/delivery requirements in this
guide apply to other work.

## Read actual capacity

Legacy retains one shared slot; it does not acquire the parallel pools from this
guide. Execution v1 counts real Worker claims and its one shared review/integration
lane. Pending handoff, returning, fixing and uncertain writes retain their actual
reservations until supported release. Activity, task labels and filtered views do
not create or release slots. A held fixing lane is not necessarily actively
reviewing. Show review waiting separately; an observed free number never replaces
fresh dependency, policy, ownership and CAS admission. Missing or stale authority
means current capacity is unknown, even when a last saved count remains visible.

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
7. Hold the lane through review, admission checks and main merge. Proven adopted
   instruction-only work uses direct main completion; other work retains optional stage.
   Preserve exact evidence and one active stage task. Release through the
   pinned completion/recovery command, then select the next eligible task. A task
   needing production/package delivery remains unfinished after its main merge;
   a proven instruction-only outcome completes at the admitted merge.

## Identify agents and recover

Roles are Coordinator, Worker and Reviewer; use opaque distinct actor and session
IDs, for example `Worker-B3K8`. Names must not depend on vendor/model. The task's
implementation owner is its Worker; coordinator and reviewer are separate metadata.
Real GitHub Assignees remain real accounts. Record transfers and authorship history;
renaming an author or taking a new role does not create independent review.

On interruption inspect the persisted claim and available branch/PR/stage evidence.
The owner's direct confirmation that the old agent stopped is sufficient for that
fact; do not demand access to its host merely to repeat the confirmation. Use the
pinned stopped-owner transfer with the new actual actor/session when required,
then its supported stop. Preserve the old claim/history and original work location;
record inaccessible local contents as unknown rather than claiming they were copied.
Never impersonate the former owner or bypass a real command refusal.

Verify only the requested claims were released. A voluntary pause is not itself a
product blocker: use the existing supported flag correction if stop adds Blocked,
while retaining actual obstacles and dependencies. Resume implementation only after
inspecting retained work and current scope/main/dependencies under valid ownership.
Timeouts alone do not permit takeover or deletion of ownership. If independent
review is unavailable, retain ready work for a real reviewer and report the limit.
Do not fabricate delegation, identity or review evidence. Changing execution
settings requires an authorized project upgrade and safe state migration; this
skill update supplies neither consumer activation nor deployment permission.
