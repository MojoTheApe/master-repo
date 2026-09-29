# Shared project workflow

This is the canonical process for new projects. Task Tracker owns its application
and command guide; every project's Issues stay in that project's repository.
Project settings choose staging and delivery. Existing projects adopt changes in
separate reviewed migrations, preserving their local controls and history.

## Ticket lifecycle

| Event | Responsible actor | Status and required result |
| --- | --- | --- |
| Owner asks for an idea | Agent | Idea; record context under Tracker's intake rules |
| Owner asks for a task | Agent | Backlog; description, scope and acceptance criteria |
| Owner selects work | Owner directs agent | To Do; prioritization is not permission to implement |
| Owner requests development | Implementer | In Progress; claim Tracker implementation slot, linked working branch |
| Implementation and self-check ready | Implementer | Review; ready PR, two-way ticket links, applicable checks |
| Review requests fixes | Implementer | In Progress while editing the same branch; then Review again |
| Reviewed source PR enters stage | Agent/explicit automation | Stage; exact candidate recorded, when enabled |
| Stage passes and promotion merges | Agent/explicit automation | Merged; verified main integration |
| Staging disabled, reviewed PR merges | Agent/explicit automation | Merged; verified main integration |
| Required delivery is verified | Authorized delivery actor | Complete according to the project rule; no extra Done column |

An agent may move planning statuses on the owner's request. Preserve Tracker
classification, dependency, duplication and execution-slot rules. A ready PR may
enter Review while CI runs; Review does not itself authorize merge. A failed check
or delivery records the reason and next action without declaring completion.
An abandoned unmerged PR returns its ticket to planning or explicit cancellation.
Partial implementation stays unfinished, including a partly delivered parent task.
Legacy projects may cover several tasks in one PR; evaluate each task's full scope
separately. Opted-in execution v1 requires exactly one task per source PR.

Task bodies use Tracker's Description and Specifications structure. Read the whole
task, including prior decisions; retain scope/history when requirements change.
Include relevant specs, branch, PR and current handoff links. Do not create a second
ticket system alongside project Issues.

## Names and links

| Object | Format | Example |
| --- | --- | --- |
| Public task ID | Project prefix + GitHub Issue number | RF-67 for Issue #67 |
| Issue title | Clear result, without manually adding the ID | Fix project search |
| Working branch | Adopted prefix + `<public-id-lowercase>-<short-name>` | `work/rf-67-fix-project-search` for opted-in execution; legacy `codex/` remains supported |
| PR title | Linked task ID + summary | `[RF-67] Improve search` |
| PR body | Exactly one explicit link line | `Tracker issues: RF-67` |

Opted-in execution v1 requires one task per source PR and the same one task on its
stage promotion. Under legacy execution, multiple related IDs may appear in the
title/link line and the branch names the primary task. PR numbers are
assigned separately: PR #79 may implement RF-67. Do not put a speculative PR number
in the branch. Validate the repository, task existence, IDs, classification and
status. Link each PR back from all its Issues. Use no automatic closing keywords
in PR text or commit messages: stage/main integration must not prematurely close
work awaiting delivery. Preserve historical aliases, links and open branches during
adoption; finish existing open PRs before activating new validation.

## Optional parallel implementation, sequential review

Projects explicitly opt in with matching `delivery.json` `workflow.execution`
and `tracker/config.json` `execution_policy`:

```json
{"schema_version": 1, "implementation_limit": 2, "review_limit": 1}
```

The implementation limit is an integer from 1 to 16; review limit is exactly 1
in this version. Absence retains the pinned legacy execution behavior, including
its slot lifetime. Installing a skill, upgrading templates or adding In Progress
labels does not enable parallelism. See [adoption](docs/adoption.md) for activation
and [the descriptor contract](docs/descriptor.md) for validation.
This mode requires the compatible Tracker delivery policy and reviewed PR
admission, including report PRs for non-code work; legacy non-code completion
cannot bypass the review lane. Use neutral `work/<task-id>-<short-name>` branches
where the host/user has no required prefix; preserve accepted `codex/` branches
and an explicit host/user prefix policy.

The shared Tracker arbitrates claims across conversations and agent platforms;
per-chat counters and GitHub labels cannot reserve work. A task has at most one
implementation owner, with an opaque actor/session identity, branch and worktree.
Roles are platform-neutral: **Coordinator**, **Worker**, **Reviewer**. Display
names such as `Worker-B3K8` distinguish actual agents; they do not encode a vendor
or model. Record the implementing Worker on the task and coordinator/reviewer
separately. Keep real GitHub Assignees separate; synthetic agents are not accounts.
Transfers retain history and never turn an author into an independent reviewer.

For an authorized request to implement several tasks, the active agent coordinates
in the current conversation. Read all task scopes and screen dependencies, shared
files/logic and runtime resources before reserving slots. Queue dependent or
conflicting tasks; coordinate any safe overlap explicitly. Prepare a separate
branch and worktree for every independent task, with isolated test data, ports and
external resources where needed. Delegate up to the available implementation
capacity through the environment's real subagent mechanism. Two independent tasks
with two free slots use two Workers; the Coordinator collects progress and owns
handoffs. Do not create new user-owned conversations without an explicit request.
If delegation is unavailable, disclose it and implement serially; capacity is a
maximum, not evidence that parallel execution occurred.

A completed implementation, its ready PR and check/handoff evidence enter the
review queue explicitly. This releases its implementation claim while preserving
authorship and branch history. Multiple tasks can display Review while only one
is actively reviewed. The Coordinator selects eligible work in queue order,
respecting dependencies and giving review fixes priority over new implementation.
Claims cannot be acquired by changing labels alone.

Acquire the single **review/integration lane** before starting a separate
non-implementing Reviewer. Hold that lane for the selected single task through
current review, checks, optional stage and main merge.
The same Reviewer may check successive tasks, one at a time. The next review starts
only after the lane is released through the pinned Tracker's completion or explicit
return-to-work procedure. During fixes, reacquire implementation capacity for the
author before editing; preserve lane ownership unless explicitly returned. Other
Workers may continue independent development, but no second review or competing
stage candidate begins. A blocked lane may be handed back only with durable state
and the Tracker's stage ownership/recovery safeguards; never discard a live stage
candidate merely to free the lane.

Before approval, check the candidate against the current integration base. If a
base update, conflict resolution or code fix is needed after handoff, the Reviewer
uses `execution review-return` with its lane claim and report. Use `--keep-lane`
to retain ownership; it is mandatory after the source entered stage. The author
takes a fresh implementation claim, updates the original working branch, runs
checks and hands it off again. Reacquire or resume the review lane as appropriate,
then independently review the current candidate. Coordinators and Reviewers do
not edit an unclaimed branch. Changes to source, base, scope or policy invalidate
approval as usual. Reserve/record/recheck
through the pinned Tracker commands; actual current review, CI, one stage candidate
and project merge/deployment admission remain mandatory. Tasks awaiting required
post-merge delivery remain unfinished even after the review lane is free.

On interruption, inspect durable claims, PR/head, worktree and stage state; resume
the existing claim or explicitly transfer it. A timeout or missing conversation
alone does not authorize takeover. Never erase state to force a new claim. Policy
activation, capacity reductions and return to legacy mode must reconcile active
work through the compatible Tracker's migration procedure, with no lost ownership.
The Tracker records and enforces workflow state; it does not spawn models.

## Independent review and merge

The author implements, self-checks, updates affected docs and prepares the PR.
The Coordinator (or active implementer under legacy execution) automatically
starts a **different subagent** for independent
review; the owner need not ask again. It reads the ticket, project instructions,
affected system description and full change. It reports exact head/base, findings,
checks and verdict. It does not implement its own fixes. If it edits code, another
reviewer must provide the final independent approval.

Fixes use the original branch, followed by self-check and re-review of current
content. Changed head/base, task scope or policy invalidates earlier approval.
Record the durable review through Tracker's `record-review`; run `check-merge N`
immediately before merging. A missing reviewer is a reported limitation, not a
reason to substitute self-review. Distinct identity strings record the real review;
they do not prove that a subagent actually ran.

Under the optional execution policy, reserve the review/integration lane first;
ready PRs wait for it. Delegated Workers hand off to the Coordinator instead of
launching their own reviews. Without that policy, keep the project's adopted slot rules.

A skill file or PR creation does not launch a model on GitHub. Automatic review
here means the running agent invokes its available subagent mechanism. The
Tracker's evidence commands do not merge or deploy. Configure and verify actual
branch rules separately; `tracker-link` CI only checks links. Never claim an agent
admission check is a GitHub-enforced protection. Merge after independent approval
and required checks within the authorized task; do not add an unnecessary manual
approval round. Existing production authorization still applies.

## Optional stage before main

Staging defaults to enabled. Permanent branches are `stage` and `main`:

1. Working branch -> stage PR: implementation and independent review.
2. Record Stage only after its actual merge; deploy/test the configured stage target.
3. Stage -> main PR: same tickets and exactly the passed content.

Opted-in execution v1 uses one task per source PR and one active task on stage.
Legacy execution may use one deliberately related task set. Keep the original
working branch until promotion finishes. If the first PR already merged, fixes
get another linked PR from that same branch. Disable automatic deletion of it;
never delete permanent branches as task cleanup. Stage starts from current main
plus only the intended task set. Reconcile stage with main before the next task.

Record exact source/tree identities and results. A different service merge commit
is acceptable if the resulting tree matches approved content and its first parent
matches the reviewed baseline. Use merge or squash, not rebase merge. Promotion
reuses the valid review of unchanged stage content; a second full review solely
because a promotion PR exists is unnecessary. Check links, task set, required CI,
main baseline and passing stage evidence again.

If main changes, integrate it in the working branch, resolve conflicts there,
repeat review and create a fresh same-task stage candidate and verification. In
opted-in execution, return review with `--keep-lane` and obtain a fresh author
implementation claim before any such branch edits; hand off to resume review.
Changes cannot be smuggled into a promotion PR or main. A later failure/retry cannot
release another task's stage ownership. With staging disabled, use working branch
-> main and omit Stage from the board; independent review and CI remain required.

## Delivery is separate from merge

| Profile | Completion condition after review and main merge |
| --- | --- |
| VPS | Installed version and required production behavior verified |
| n8n | Intended workflow updated/published and its result verified |
| n8n-source, explicitly selected | Reviewed and checked source merged into main; n8n delivery is a separate process |
| Local manual pull | Admitted main merge; owner may pull later |
| Package, explicitly selected | Stable package published and agreed installation check passed |
| Tooling/docs | Admitted main merge; no service deployment |

Merged is an integration fact. Required delivery pending/failed does not count as
complete in task views, dependencies or release readiness. Record delivery against
actual merged revisions and configured target. Closing an Issue, repeating sync or
calling a non-code completion command must not bypass that requirement. Decide
completion and task scope before implementation, not after a failed release.

Project runbooks own actual installers, n8n synchronization, credentials, approvals,
backup and compatible rollback. Git storage does not authorize deployment. Use
existing authorization where it covers the action. Stage evidence is not production
proof; avoid unreviewed changes and arbitrary PR execution on production runners.
Keep deployments serialized and prevent stale jobs replacing newer versions.
Preserve operational data, native admission and update/hotfix behavior, including
ReactForge's installer, which is outside this standard migration's scope.

## Living documentation

`docs/system/PROJECT.md` describes the current implemented system, components, important
choices, dependencies and limitations. `docs/system/CHANGELOG.md` records meaningful
changes and why they were chosen, linked to tickets/PRs. Original specifications
remain under `docs/system/specs/` or existing locations; plans are distinguished from
implemented behavior. Update affected documentation in the same implementation PR,
or explain no impact. Independent review checks this obligation.

Repository rules and process history live in `docs/repository/`; environment
access, deployment and recovery live in `docs/runtime/`. `AGENTS.md` is a short
reading map. Shared helper implementations live in `.workflow/tools/`, apart from
product scripts. System/runtime documents become project-owned at creation and
are never overwritten or merged by template upgrades. See the
[layout contract](templates/workflow/LAYOUT.md). Legacy paths may be forwarding
files; maintain one authoritative copy of each rule.

## Ownership and synchronized evolution

Master Repo owns this process, templates, descriptor, adoption/upgrade tooling and
the canonical shared skill. Task Tracker owns command semantics, configuration,
Issue transitions, board and release completion. Each process change checks the
other repository: record no impact with a reason, or propose a concrete linked fix
and compatible migration. Do not silently change another repo without task scope.

Compatible standard and Tracker revisions are pinned. Project instructions and
exceptions remain local; updating the globally installed skill cannot replace them.
A standard upgrade compares the previous template, new template and current
project, preserves unique code/installers, and reports conflicts for explicit
resolution. Bulk upgrades use an inventory and a separate reviewed PR per project.
See [adoption](docs/adoption.md), [versioning](docs/versioning.md) and the
[descriptor contract](docs/descriptor.md) for executable procedures.
