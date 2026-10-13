# Tracker companion for maintenance and CI evidence

Status: proposed requirements from
[MR-24](https://github.com/MojoTheApe/master-repo/issues/24), not commands/features
in the current pin. This Master update changes no engine, client, service or live
state. Implement and review the companion in Tracker before publishing compatible
support and separately adopting it in consumers.

## Maintenance admission

Provide one centrally persisted, recoverable owner of a maintenance interval.
All compatible admission writers consult its CAS record before granting new
Worker/source-review/intake/integration ownership. Explicitly preserve the
already-owned drain/recovery/completion operations needed to reach idleness.
Interrupted/uncertain writes retain ownership until supported resume/transfer.

Old incompatible writers must fail closed, not ignore a flag. Preserve task/queue
order, approvals, author/reviewer history, existing ownership and delivery receipts.
Pause, idle migration and resume are separate transitions; none grants permission
to discard claims, reset stage or complete unfinished work. Project safe status
without private identities/reports; keep one compatible projection writer.

Acceptance: simultaneous clients cannot grant a new claim after gate reservation;
existing owners can finish allowed handoffs; restart/retry cannot silently release
maintenance; incompatible clients cannot bypass it; migration retains unrelated
state; supported resume restores only normal authorized admission.

## Reusable verification evidence

Define versioned context for repository/tested content, trusted workflow/profile,
successful job attempts, resolved dependencies, runner/toolchain/build inputs and
actual artifact/provenance references. Product matrices/runtime acceptance stay
consumer-owned. Arbitrary annotations/uploaded JSON are not producer trust.

An open Approved source is eligible only through its actual unchanged PR, retained
approval and current scope/base/policy. Compare actual tested content with the
frozen combined candidate; keep independent composition review for one member too.
Union covered jobs, run missing ones, and preserve release/manual policies and
actual stage/delivery freshness. Separate source trees cannot prove a changed batch.

Acceptance: matching tested candidate/context avoids duplicate covered jobs;
changed code/workflow/environment/build inputs and missing platforms require fresh
relevant proof; failed/skipped/cancelled/untrusted results cannot admit a candidate;
Git metadata-dependent behavior is not assumed tree-identical; logs name reused
producers/jobs. Legacy/v1/v2/v3 retain adopted behavior until reviewed migration.

## Rollout

Review engine/client/evidence support, publish compatible writers, select the
reviewed pin in Master, then adopt in separate consumer PRs under existing rules.
ACL is the first adapter candidate: its collector already implements bounded
exact-tree/merged-PR reuse. Installer process control and measured shard costs
are ACL product work, not shared Tracker engine changes.
