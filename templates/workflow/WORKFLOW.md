# Repository workflow

Read `delivery.json`, `docs/system/PROJECT.md`, `docs/repository/DELIVERY.md` and
`docs/repository/TRACKER.md` before work. They define this project's adopted
standard, system, tracker, stage option, completion rule and local exceptions.
Use `python scripts/task_tracker.py guide` for the pinned Tracker commands.

Create an Issue before implementation. Idea requests stay Idea; task requests
start Backlog. Start development only when requested; claim the Tracker slot and
use `codex/<public-id>-<short-name>`. PR title: `[EX-12] Summary`; one
`Tracker issues: EX-12` line, with links back from the Issues. Multiple IDs are
allowed for a related task set. No automatic closing keywords.

After implementation and self-check, prepare the PR and set Review. Automatically
start a separate non-implementing subagent for independent review of the actual
head/base, requirements and docs. Fix on the same branch and obtain fresh approval.
Run `check-merge PR_NUMBER` immediately before merging. If staging is enabled,
working branch -> stage -> main, using the same task set and unchanged verified
content. Preserve the working branch for fixes. Use evidence commands from the
Tracker guide; labels and merge alone do not prove a required delivery.

Update current-system docs and meaningful change history in the same PR, or explain
no documentation impact. Preserve original specifications and local deployment
controls. Assess Master Repo / Task Tracker impact for process changes and propose
linked fixes when needed. Ordinary feature work does not upgrade the standard.

The optional installed `project-workflow` skill helps navigate these instructions.
Its canonical source lives in Master Repo; updating that skill never changes this
project's pinned contract. Record project-specific exceptions in `delivery.json`.

File ownership and placement: see `docs/repository/LAYOUT.md`.
