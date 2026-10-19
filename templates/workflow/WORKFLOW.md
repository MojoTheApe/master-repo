# Repository workflow

Read `delivery.json`, the [system description](../system/PROJECT.md),
[delivery rules](DELIVERY.md), [selected Tracker guide](TRACKER.md) and
[verification](VERIFICATION.md) before work. These checked-in files describe this
project's actual immutable standard/engine pair, selected route and local controls.
Use `python scripts/task_tracker.py guide` for the same pinned command guidance.

## Selected route

__SELECTED_WORKFLOW__

__TASK_CONTEXT_GUIDANCE__

__PROCESS_GUIDANCE__

## Work and independent review

__SOURCE_GUIDANCE__

The Coordinator checks dependencies, overlap and actual ownership, and delegates
independent eligible work to Workers in isolated branches/worktrees through
available subagents. Respect the selected capacity and any tighter commissioned
work limit. Keep roles separate from GitHub assignees and use genuine opaque
actor/session identities. Do not create new user-owned chats without an explicit
request. If delegation is unavailable, record serial implementation; independent
review still cannot be replaced by self-review.

__PR_REFERENCE_GUIDANCE__ Update
current system knowledge and meaningful history in the same PR, or explain the
specific no-impact result. Preserve original specifications and local safeguards.

Follow the selected Tracker guide for the genuine handoff and review ownership.
Arrange a separate non-implementing subagent to review the actual head/base, full
requirements, changed files and checks. Delegated Workers hand off to their
Coordinator, who starts the independent review. Keep fixes on the task branch;
reclaim author ownership through the adopted return procedure before editing after
handoff, including base updates or conflict resolution. Reviewers and coordinators
must not edit an unclaimed branch. Changed code, base, scope or policy requires
fresh appropriate proof. A missing independent reviewer is an explicit limitation,
never self-approval.

Use `check-pr` for early linkage feedback and the supported `check-merge` once for
final admission; final admission already includes linkage. Verify actual branch
protection and required checks rather than inferring them from a label or guide.
Preserve exact reviewed content through admitted integration. Use the selected
Tracker guide for evidence, return/takeover, recovery and optional Stage commands;
no timeout or status-label edit clears a genuine owner.

## Local knowledge and delivery

A selected integration/main-merge request includes the maintained delivery and
verification required by this project's adopted target. Continue through
[delivery continuation](DELIVERY_CONTINUATION.md) without a routine second approval;
read [runtime procedures](../runtime/DELIVERY.md) for actual authorization, access,
backup and compatible recovery. Instructions do not create a background producer.
A partial ticket, pending/failed delivery or unknown accepted outcome stays
unfinished. Merge, publication, installation and verified behavior are separate
facts. Do not reduce a completion obligation to bypass missing proof.

Use the [ownership map](LAYOUT.md) for repository/system/runtime files. Shared
upgrades preserve project-owned system/runtime knowledge, unique commands,
installers, data and deployment controls. Ordinary feature work does not upgrade
standard or engine pins. For process changes assess Master Repo / Task Tracker
impact and link the matching fix or concrete no-impact result.

The installed `project-workflow` skill is navigation. Its canonical Master source
and verified AI Skills mirror do not activate this project's policies or replace
its adopted local instructions. Record actual exceptions in `delivery.json`.

## Executor activity

Follow the selected pinned Tracker guide for `activity report` and the foreground
`activity run --exec` wrapper when supported. Only the current owner/session/claim
reports running, waiting and stopped. Confirm once a minute while running; five
minutes without a running/waiting report freezes work time and means activity
unconfirmed. A recorded stop remains while that owner is assigned. Neither
condition releases ownership. No detached endless reporter or coordinator heartbeat
for another executor. Existing runs without a producer remain unknown.
