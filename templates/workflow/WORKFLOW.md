# Repository workflow

Read `delivery.json`, `docs/system/PROJECT.md`, `docs/repository/DELIVERY.md` and
`docs/repository/TRACKER.md` before work. They define this project's adopted
standard, system, tracker, stage option, completion rule and local exceptions.
Use `python scripts/task_tracker.py guide` for the pinned Tracker commands.

If matching descriptor/Tracker `process_instructions` is explicitly adopted,
one source PR changing only regular AGENTS.md, CLAUDE.md or Markdown under
docs/repository goes through independent review and its instruction checks directly
to main. The complete actual diff must qualify, including both rename paths;
mixed, unknown, unsafe or incomplete proof keeps the normal route. Keep the genuine
author claim/handoff and, when execution is adopted, its review lane through admitted main completion. Do not move
this source to Approved, stage or a batch or invent installation proof. Wait for
any reserved integration/unpromoted stage ownership to finish before changing main.
Configuration, helpers, CI, system/runtime knowledge and application/build changes
remain on the ordinary route. Installing a skill alone never selects the exception.

If matching execution policies use schema 2, follow the pinned guide's Approved
and batch-integration lifecycle for all other work. Each source PR still represents one task; current
independent review and required source checks move it to Approved and release the
review lane. A separate Coordinator claim owns one frozen integration batch of
1..batch_limit members (recommended limit five), retaining every real Worker and
reviewer. Ship-all snapshots current Approved intake; new arrivals wait. An urgent
single task may ship alone. Independently review/check the combined candidate,
verify its exact stage target/tree, then promote the unchanged member set to main.
Keep failed post-stage batches owned through claimed author fixes and fresh proof.
The execution-v1 lane lifetime and single-task staging instructions below apply
only to schema 1. Installing a skill or changing upstream pins does not enable v2.

Create an Issue before implementation. Idea requests stay Idea; task requests
start Backlog. Start development only when requested; claim the Tracker slot and
use the pinned task-branch rules (`codex/<public-id>-<short-name>` remains
compatible; opted-in execution also accepts `work/<public-id>-<short-name>`).
Honor a host/user prefix requirement. PR title: `[EX-12] Summary`; one
`Tracker issues: EX-12` line, with a link back from the Issue. Opted-in execution v1
requires exactly one task per source PR. Multiple related IDs in one PR are allowed
only under legacy execution. No automatic closing keywords.

If `workflow.execution` and Tracker `execution_policy` are explicitly enabled and
equal, use their implementation capacity and version-specific ownership. Schema 1
has one review/integration lane; schema 2 separates source review from a Coordinator
integration batch. Otherwise
keep the pinned legacy slot behavior. A Coordinator stays in the current
conversation, screens task dependencies/overlap and delegates independent tasks to
Workers in separate branches/worktrees using available subagents. Two independent
tasks with two free slots use two Workers. Use platform-neutral opaque actor and
session IDs; record Worker ownership separately from coordinator/reviewer metadata
and real GitHub Assignees. No new user-owned conversations without an explicit
request. If delegation is unavailable, disclose serial implementation; never
substitute self-review for an independent Reviewer.

Use the pinned Tracker guide to claim, resume, hand off and recover work. In schema 1, handoff
to the review queue releases implementation capacity. Multiple tasks may wait in
Review; acquire the sole review/integration lane before launching a Reviewer. Hold
it through current review, checks, optional stage and main merge. The next task
waits until explicit release. Review fixes take priority and reacquire implementation
capacity. Preserve current source/base/policy evidence and stage ownership when
returning work or recovering; no timeout or label change permits duplicate claims.
Any post-handoff branch edit, including base updates and conflict resolution,
requires the Reviewer to call `execution review-return`, followed by a fresh author
implementation claim, checks and another handoff. Use `--keep-lane` to retain review
ownership; it is mandatory after entering stage. Reacquire or resume the lane and
review current content. Coordinators and Reviewers never edit an unclaimed branch.

After implementation and self-check, prepare the PR and set Review. Automatically
arrange a separate non-implementing subagent for independent review when the lane
is available. Delegated Workers hand off to the Coordinator, who starts the review
of the actual
head/base, requirements and docs. Fix on the same branch and obtain fresh approval.
Run `check-merge PR_NUMBER` immediately before merging. For a proven adopted
instruction-only source, main integration completes the fully reviewed task scope,
including in a package project; supply no Stage or installation receipt. Legacy
projects keep their slot and independent attestation without unsupported execution
lane commands. For other work, in schema 1 or legacy mode, if staging is enabled,
working branch -> stage -> main, using the same single task in execution v1
(related task sets are legacy-only) and unchanged verified
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
