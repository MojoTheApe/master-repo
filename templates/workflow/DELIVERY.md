# Project delivery

`delivery.json` is the project-specific delivery description. `tracker/config.json`
is the matching Tracker configuration. The standard and engine use exact commit
pins; neither automatically follows main. Populate actual procedures and verify
registration before changing adoption from draft to ready.

An explicitly matching `process_instructions` option permits one source PR limited
to proven regular process instructions (AGENTS.md, CLAUDE.md and Markdown under
docs/repository) to go Review -> main -> Merged after independent review and its
configured checks. When execution is adopted, keep its real review lane through main completion. No stage,
batch, installer or delivery receipt is created. The full immutable diff, not a
title/label, selects it; mixed/unknown/unsafe or incomplete evidence never does.
Wait for reserved integration/unpromoted stage ownership before changing main.
Application, build, configuration, CI, automation and system/runtime changes keep
their ordinary route and actual delivery requirements.

For other work, execution schema 2 selects Review -> Approved -> Stage -> Merged.
Independent source approval releases the review lane; one separate Coordinator
integration claim covers a frozen batch of 1..batch_limit tasks. The recommended
limit is five, independent of Worker capacity. Preserve each member's author,
source PR/current approval and scope; verify the combined stage candidate before
unchanged promotion. Ship-all snapshots intake and processes sequential batches,
rechecking remaining approvals after each main change. A single task may ship
without filling the batch. The v1 single-task lane instructions below apply only
to schema 1. Completion and runtime authorization remain project-specific.

## Path from request to completion

Idea -> Backlog -> To Do are planning steps under the owner's direction. An
explicit development request starts In Progress and a ticket branch. The author
implements, self-checks and creates the linked PR, then sets Review. A separate
subagent reviews; fixes stay on the same branch and require fresh approval.
Opted-in execution v1 uses exactly one task per source PR and the single
review/integration lane. Use explicit handoff and review claims from the pinned
guide; follow the [workflow](WORKFLOW.md) for author claims before post-handoff edits.

Outside the adopted instruction-only exception, with staging enabled:
working branch -> permanent stage, record Stage, test the
configured target, then stage -> main with the same task and content. Use
merge or squash with an unchanged tree and reviewed first parent. Keep one active
task on stage; a related task set is permitted only under legacy execution.
Reconcile with current main before the next task. If main changes during testing,
opted-in execution requires `execution review-return --keep-lane`, a fresh author
implementation claim, branch updates/checks and handoff before resuming independent
review and staging a fresh candidate. Legacy execution follows its adopted slot rules.
Do not add fixes to the promotion PR or delete the working branch prematurely.

Without staging: working branch -> main after review and checks. No Stage column.
Run the pinned client's `check-pr N`, `record-review`, `check-merge N`, `stage`,
`verify-stage` and `merged ... --reviewed-complete --apply` as appropriate; see its
`guide`. Commands record verified actions; they do not deploy or run a reviewer.
Configure branch protection separately and verify that the required checks exist.

Merged records inclusion in main. A proven instruction-only task completes its
fully reviewed instruction scope at that admitted merge, including in a package
project. Legacy projects use their slot and independent attestation; execution
lane commands require an adopted execution policy. A local manual-pull project
also completes at verified merge. For other work, VPS/n8n/package profiles require their actual delivery and checks,
recorded with `record-delivery`. Failed or pending delivery remains unfinished.
The explicitly selected n8n-source profile completes the Git source task after
the admitted main merge. n8n transfer/publication is a separate process and must
never be claimed from Git evidence. Existing runtime acceptance criteria survive
adoption. For repository-only work, label stage evidence as Git checks; consult the project runtime guide when runtime verification is required;
branch-to-environment connections require their own explicit setup.
A partially implemented ticket stays active. Never substitute a closed Issue or
non-code completion for missing code/delivery evidence.

## Procedure references

Use `docs/runtime/DELIVERY.md` for actual environment identities, access,
release authorization, rollback and backup. The descriptor links those procedures. A disabled
stage is an explicit project choice. Production delivery is a separate operation
using the project's maintained mechanism; Git storage gives no new deploy access.
For n8n distinguish workflow publication from server upgrade. For local manual
pull, no installer or automated update mechanism is required.

## Onboarding proof

Record the shared workspace project ID and a durable verification reference after
labels, branch configuration, registry publication and a fresh live board have been
verified. A generated directory or local registry edit is not a connected project.
Document pending setup honestly. Never put credentials or sensitive logs in these
files or in published Tracker evidence.
