# Project delivery

`delivery.json` is the project-specific delivery description. `tracker/config.json`
is the matching Tracker configuration. The standard and engine use exact commit
pins; neither automatically follows main. Populate actual procedures and verify
registration before changing adoption from draft to ready.

## Path from request to completion

Idea -> Backlog -> To Do are planning steps under the owner's direction. An
explicit development request starts In Progress and a ticket branch. The author
implements, self-checks and creates the linked PR, then sets Review. A separate
subagent reviews; fixes stay on the same branch and require fresh approval.

With staging enabled: working branch -> permanent stage, record Stage, test the
configured target, then stage -> main with the same ticket set and content. Use
merge or squash with an unchanged tree and reviewed first parent. Keep one active
task set on stage. Reconcile with current main before the next set. If main changes
during testing, update the working branch, re-review and stage a fresh candidate.
Do not add fixes to the promotion PR or delete the working branch prematurely.

Without staging: working branch -> main after review and checks. No Stage column.
Run the pinned client's `check-pr N`, `record-review`, `check-merge N`, `stage`,
`verify-stage` and `merged ... --reviewed-complete --apply` as appropriate; see its
`guide`. Commands record verified actions; they do not deploy or run a reviewer.
Configure branch protection separately and verify that the required checks exist.

Merged records inclusion in main. A local manual-pull project completes at that
verified merge. VPS/n8n/package profiles require their actual delivery and checks,
recorded with `record-delivery`. Failed or pending delivery remains unfinished.
A partially implemented ticket stays active. Never substitute a closed Issue or
non-code completion for missing code/delivery evidence.

## Project-specific procedures

Complete the descriptor with actual check commands, environment identities,
release procedure, existing authorization, rollback and backup rules. A disabled
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
