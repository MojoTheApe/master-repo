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
| Owner requests development | Implementer | In Progress; claim Tracker slot, linked working branch |
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
For a PR covering several tasks, evaluate each task's full scope separately.

Task bodies use Tracker's Description and Specifications structure. Read the whole
task, including prior decisions; retain scope/history when requirements change.
Include relevant specs, branch, PR and current handoff links. Do not create a second
ticket system alongside project Issues.

## Names and links

| Object | Format | Example |
| --- | --- | --- |
| Public task ID | Project prefix + GitHub Issue number | RF-67 for Issue #67 |
| Issue title | Clear result, without manually adding the ID | Fix project search |
| Working branch | `codex/<public-id-lowercase>-<short-name>` | `codex/rf-67-fix-project-search` |
| PR title | All related IDs + summary | `[RF-67, RF-68] Improve search` |
| PR body | Exactly one explicit link line | `Tracker issues: RF-67, RF-68` |

For multiple related tasks, the branch names the primary one. PR numbers are
assigned separately: PR #79 may implement RF-67. Do not put a speculative PR number
in the branch. Validate the repository, task existence, IDs, classification and
status. Link each PR back from all its Issues. Use no automatic closing keywords
in PR text or commit messages: stage/main integration must not prematurely close
work awaiting delivery. Preserve historical aliases, links and open branches during
adoption; finish existing open PRs before activating new validation.

## Independent review and merge

The author implements, self-checks, updates affected docs and prepares the PR.
The active agent automatically starts a **different subagent** for independent
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

Use one active task or deliberately related task set on stage. Keep the original
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
repeat review and create a fresh same-task stage candidate and verification.
Changes cannot be smuggled into a promotion PR or main. A later failure/retry cannot
release another task's stage ownership. With staging disabled, use working branch
-> main and omit Stage from the board; independent review and CI remain required.

## Delivery is separate from merge

| Profile | Completion condition after review and main merge |
| --- | --- |
| VPS | Installed version and required production behavior verified |
| n8n | Intended workflow updated/published and its result verified |
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

`docs/PROJECT.md` describes the current implemented system, components, important
choices, dependencies and limitations. `docs/CHANGELOG.md` records meaningful
changes and why they were chosen, linked to tickets/PRs. Original specifications
remain under `docs/specs/` or existing locations; plans are distinguished from
implemented behavior. Update affected documentation in the same implementation PR,
or explain no impact. Independent review checks this obligation.

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
