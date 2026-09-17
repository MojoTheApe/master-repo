# System changes

## Git-only n8n source delivery (MR-5)

Added explicit n8n-source selection for projects whose owner separates reviewed
Git delivery from n8n installation. Permanent stage/main, independent review,
exact-content promotion and task acceptance remain mandatory. Runtime DEV is the
counterpart of stage; Git-only checks never claim runtime verification.

Added an explicit draft-validation Action input, strict by default, so incomplete
audited adoption can receive CI feedback without masquerading as ready. Existing
n8n production completion and schema-1 behavior are unchanged. Tracker impact:
no engine/schema change; its existing reviewed-merge policy supports this scope.
Consumers still require explicit migration and historical evidence reconciliation.

Issue: https://github.com/MojoTheApe/master-repo/issues/5
Consumer pilot: https://github.com/MojoTheApe/n8n-namari-automation/issues/9

## Proposed 1.0.0 — complete shared workflow (MR-3)

Expanded delivery-only guidance into the complete project and ticket lifecycle:
Idea/Backlog intake, linked IDs/branches/PRs, independent subagent review, optional
pre-main stage, distinct merge and delivery completion, and living project docs.
Local manual pull no longer implies building an installer; package delivery is an
explicit profile. These distinctions match how the owner actually works.

Added pinned Tracker integration, registration preparation and compatible policy
validation so Stage and completion behave consistently in the board. Three-way
upgrades preserve project-specific fixes and report conflicts. The shared skill
navigates pinned project rules instead of silently imposing its newest version.
Both repositories now assess reciprocal impact on process changes.

Issue: https://github.com/MojoTheApe/master-repo/issues/3
Companion: https://github.com/MojoTheApe/task-tracker/issues/59
No consumer migration, deployment, global skill installation or standard release
is implied by this source change.
