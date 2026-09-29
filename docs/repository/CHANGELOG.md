# Repository process history

## MR-11 — Parallel implementation with sequential review and integration

Add explicit execution policy to schema-2 creation, validation and upgrades without
changing existing consumer defaults. The shared workflow and canonical skill keep
the Coordinator in one conversation, delegate independent task work to isolated
Workers and serialize independent review through main integration. Actor identities
are platform-neutral and separate from real GitHub Assignees. Preserve exact review
evidence, stage ownership, project safeguards and pristine upgrade baselines.

Master task: https://github.com/MojoTheApe/master-repo/issues/11
Companion: https://github.com/MojoTheApe/task-tracker/issues/67

Rollout order: reviewed Tracker merge and compatibility pin, reviewed Master merge,
authorized canonical skill installation with backup, then separate consumer
adoption. Compatibility pins the reviewed TT-67 merge
`a4ea3cfb0c1be1760ae0923c8232779532c25a7b` (Tracker PR 68). This implementation
does not migrate ACL, publish a standard release or deploy a consumer. Recovery
uses explicit recorded takeovers; initial adoption and capacity changes require
an idle repository rather than discarding active claims or stage work.

## MR-9 — Preserve explicitly approved historical completion

Adoption may keep an audited list of completed tasks when the owner chooses to
retain history. Update the compatible Tracker pin and explain its read-only audit,
exact scope comparison and revocation on restarted work. This avoids both losing
accepted work and inventing old delivery evidence. New-project defaults and new
task admission remain unchanged; no consumer is automatically migrated.

Master task: https://github.com/MojoTheApe/master-repo/issues/9
Companion: https://github.com/MojoTheApe/task-tracker/issues/61
Initial consumer: https://github.com/MojoTheApe/adopy-campaing-launcher/issues/248

## MR-7 — Separate repository, system and runtime knowledge

AGENTS is a reading map. This repository's maintenance rules live under
`docs/repository/`; product implementation/context live under `docs/system/`;
`docs/runtime/` states the non-deployed boundary. Compatibility paths are pointers.
Historical standard product changes remain in system history.
