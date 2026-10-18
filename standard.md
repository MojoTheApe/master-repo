# Shared project workflow

Use GitHub for the project's tasks, code, reviews and checks. Master Repo supplies
the common instructions and structure; Task Tracker shows the recorded work.
The agent follows this process using the tools already available to the project.

Existing projects retain their checked-in instructions, required checks and
delivery controls. Updating this standard or the installed skill does not change
their selected execution mode, capacity, pins or running state. Read specialized
instructions only when the project actually uses them.

## Start with the project

Read `AGENTS.md`, the task's current requirements and the relevant local workflow,
product and delivery instructions. Where `delivery.json` pins a standard, use that
revision and its reading map rather than guessing from a newer release.

Establish the intended result and completion condition before editing. Check for
existing work on the same task and reuse it where appropriate. Age alone is not a
reason to reject a task or seek a new permission. Check whether its requirements,
source or dependencies changed.

Ordinary feature work does not include upgrading the project's standard or
redesigning its development infrastructure. Existing authorization carries through
the actions it covers; ask about a genuinely missing decision or access, not
every routine step.

## Ticket lifecycle

1. **Describe the task.** Use its existing project Issue. Record the problem,
   intended result and observable acceptance criteria; keep progress comments
   separate from requirements.
2. **Start the work.** Record the responsible implementer and a short plan. Check
   for overlapping work. Use an isolated task branch/worktree and the project's
   existing naming and ownership procedure.
3. **Implement and self-check.** Make the needed change, update affected product
   knowledge and use meaningful early checks. Group related corrections before
   another expensive run.
4. **Request independent review.** Link the PR and Issue both ways. A different,
   non-implementing agent reviews the actual change, full requirements and existing
   test evidence. Sharing a GitHub account does not make self-review independent.
5. **Resolve findings.** Fix the same task branch, obtain the required updated
   review and run checks affected by the changes. Reuse valid unchanged evidence.
6. **Integrate and deliver.** Follow the project's existing merge and delivery
   procedure with the required review and checks. Continue already authorized
   delivery until verified or concretely blocked.
7. **Record the result.** State what was included, how it was checked and what was
   actually delivered. Close only the scope that meets the project's completion
   condition; leave partial or failed work visible.

Status is a report of facts. Planning does not mean implementation is running;
waiting for review differs from active review; merged code differs from a
published or installed result. Use the project's supported status vocabulary.
The Tracker's categories are a presentation concern, not new permissions.

## Pause and resume existing work

An owner's direct confirmation that an agent has stopped establishes that fact.
Do not require an unavailable computer to come online just to confirm it again.
Age, silence or an occupied slot alone does not establish a stop. Record the
request and use the project's existing stop or stopped-owner transfer procedure
under the actual acting identity; never impersonate the previous owner or edit
ownership state by hand. A real command refusal remains a concrete limitation.

Preserve the task, scope, dependencies, history and known branch/commit/work-location
references. Uninspected local files and implementation readiness remain unknown;
an administrative pause does not require inventing a copied checkout or a backup.
Verify that only the requested assignments were released and report any remaining
reservation. Paused means intentionally stopped; Blocked means a concrete obstacle.
If the existing stop command adds a conservative blocker, use the supported status
correction only after confirming no real obstacle is being hidden.

On resumption, inspect the retained work and handoff, current requirements, main
and dependencies, then acquire or resume ownership through the local procedure.
Continue the existing task and branch where appropriate. Keep valid evidence and
the project's required independent review, integration and delivery.

When a requirement changes, assess the result against that requirement. Preserve
the old work and decision history. A progress note alone is not a changed
requirement. If an operation's result is uncertain, inspect GitHub or the target
before repeating it.

## Names and links

Use the project's public task ID, validated Issue-reference line and branch
convention. An Issue number and a PR number are different. Keep existing aliases
and links. Avoid automatic closing keywords where delivery remains outstanding.

A task description can be this short:

```text
Description
What problem should be solved and for whom?

Specifications
- Expected result and boundaries.
- Acceptance: what observation will show that it works?
- Relevant existing context or dependency.
```

Put progress, check results and handoff in comments or the existing work journal.
A PR explains the problem and resulting behavior, links its task, records checks
and independent review, and names remaining delivery or concerns. Use the
repository's existing PR template and required machine-readable fields; do not
create a second task database.

Routine notes, ad copy and working-data saves do not need a new engineering Issue
just to document each save. Changes to technical rules, automation or application
behavior use the development workflow. Preserve any already adopted local capture
procedure; this common distinction does not remove an existing project's controls.

## Independent review and merge

Use a separate non-implementing subagent for the final review where available.
Give it the current requirements, actual source and relevant check results.
If it changes the implementation, arrange another final reviewer. Report an
unavailable reviewer honestly rather than recording self-approval.

Reviewers inspect valid existing evidence and add checks for a finding, missing
scope, changed input or unresolved risk. A new agent, session or comment alone
does not justify repeating all tests.
When main moves, assess actual compatibility: conflicts and changed behavior
need reconciliation and appropriate review; an unchanged compatible result does
not need a rewrite solely to restart CI. Preserve required current-base checks.

Parallel work is useful for independent tasks with available real sessions.
Coordinate overlap and check launches in the existing task; do not build a
scheduler. Where a project already uses claims or a queue, follow its exact local
procedure. Capacity is a limit, not proof that an agent is currently running.
A missing independent reviewer or unresolved check is a concrete unfinished item.

Use the supported final merge check once; when it includes linkage, do not repeat
a separate link check immediately before it. Preserve actual GitHub protections.
A label or local command is not evidence that GitHub enforces a branch rule.

## Delivery is separate from merge

The project defines what finishes its task:

| Intended result | Completion evidence |
| --- | --- |
| Source-only tooling, instructions or manual-pull work | Reviewed, checked change included in main |
| Running service or runtime n8n workflow | Required version and behavior verified on the intended target |
| Distributed package | Required release published and agreed installation/update checks passed |
| Publication-specific task | The requested artifact or catalog is accessible and matches the approved source |

Use existing project runbooks, installers and CI. A successful build is not a
deployment; a tested installer does not prove installation on every employee
machine. A release-specific task cannot be closed merely because its source merged.
Retain separate local authorization boundaries and source-only instructions.

If delivery fails, record the failure and next action on the original task.
Inspect the target before retrying an uncertain operation. Archive means hidden
from active work; it does not mean successful completion. Returning visibility
does not restore an old approval or fabricate a new completion.

Staging, integration batches and operational recovery remain project-specific.
Do not add those steps to a simple project merely to make every repository alike.

## Living documentation

Keep one authoritative copy of each rule and short links from other entry points:

| Location or existing equivalent | Purpose |
| --- | --- |
| `AGENTS.md` | Short reading map to common rules and local specifics |
| `docs/repository/` | How to work here, check changes and deliver them |
| `docs/system/` | Product meaning, important decisions and implemented behavior |
| `docs/runtime/` | Environment, delivery, recovery and data procedures |
| Project Issues and PRs | Requirements, work history, reviews and results |

Use existing files; a small project need not create an empty document for every
row. Preserve original specifications and distinguish planned from implemented
behavior. Update affected knowledge with the implementation, or state no impact.
Keep secrets out of these documents. Existing generated layouts keep their
[layout contract](templates/workflow/LAYOUT.md).

Master owns the common standard and canonical
[Project Workflow skill](.agents/skills/project-workflow/SKILL.md). AI Skills
distributes its verified copy through the existing process. A shared rule change
updates the skill and affected references in the same PR; do not maintain an
independent edited mirror. Project-specific product and runtime knowledge stays local.

An existing parent project's data or release repositories can remain related
resources. Follow the parent's delivery process and each resource's local controls
for actual changes. A link does not imply an independent task queue, active agent
or completed release; do not create separate adoption merely to align instructions.

## Checks and project setup

Use [efficient verification](docs/verification.md) for grouped ready submissions,
required coverage and supported reuse. Agents can avoid their own redundant
launches; GitHub still runs the checks selected by existing configuration. Compatible
instruction clarifications require no pin/helper upgrade. Actions/settings changes
need explicit task scope; existing authorization suffices. Observe ordinary work
through existing links without extra demonstrations or scheduled audits merely to
prove a prose edit. Do not claim unmeasured savings.

For a new project use the short [setup procedure](docs/adoption.md#new-project-procedure).
For an existing one, change only the needed instructions and supported display;
preserve useful tests, history, local commands, data and delivery behavior.

Detailed [existing workflow support](docs/adoption.md#existing-generated-workflow-support)
remains available for projects that already selected it. Its versioned commands
and activation procedures are compatibility references, not additional mandatory
steps for every task.
