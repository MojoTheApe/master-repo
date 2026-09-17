# System changes

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
