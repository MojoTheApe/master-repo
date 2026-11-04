# Shared project workflow

Master defines common development guarantees and document responsibilities.
Each project chooses its checks, integration and delivery. GitHub holds tasks,
source and review history; Tracker records work and enforces its selected rules.
Existing projects keep their adopted pins, settings and live ownership.

## Start with the project

Read its short AGENTS map, current task and relevant product, workflow and runtime
instructions. Use the selected standard revision and local Tracker guide. Establish
what result is required and what completes it before changing code. Reuse existing
work and authorization; ordinary feature work is not a standard migration.

## Ticket lifecycle

1. **Describe the result.** Use the original task: problem, scope and observable
   acceptance. Keep progress comments separate from requirements.
2. **Start responsibly.** Record the actual implementer and a short plan, inspect
   overlap, and use the project's isolated branch and ownership procedure.
3. **Implement and check.** Update affected knowledge and run meaningful checks.
   Group related fixes; reuse still-valid evidence instead of repeating it.
4. **Hand off and review.** Complete the actual selected task handoff and verify
   its state. A separate non-implementing reviewer assesses the current full scope,
   source and evidence. Link the PR and task both ways.
5. **Resolve and integrate.** Return findings through the adopted author procedure.
   Keep required review/checks, use the supported final admission once, then merge.
6. **Deliver and record.** Continue the authorized delivery to its verified result
   or a concrete blocker. Record what actually shipped and leave partial work open.

Follow the pinned [submission order](docs/verification-submission.md#task-handoff-and-github-readiness).
A ready PR alone is not a task handoff. Changed requirements need assessment;
new requirements for accepted work normally belong in a linked follow-up.
Age or a different agent alone does not invalidate existing work or evidence.

## Names and links

Use the project's task IDs, branch convention and exact Issue-reference fields.
Keep original links and aliases. Avoid automatic closing keywords while delivery
is outstanding. A small task can contain just:

```text
Description
What problem should be solved and for whom?

Specifications
- Expected result and boundaries.
- Observable acceptance.
- Relevant context, dependency and verification.
```

Larger specifications link their tasks from the common
[document structure](docs/project-documents.md). Progress, failures, reviews and
recovery stay in the original Issue/PR. Ordinary notes/data saves follow the
adopted capture procedure; they do not require a new engineering ticket per save.
Technical rules, automation and product behavior use tracked engineering work.

## Independent review and merge

Use a genuine separate non-implementing agent for final review where available;
if it changes implementation, arrange a different final reviewer. Report missing
review honestly. A shared GitHub account does not make self-review independent.
Inspect actual scope, source, relevant tests and compatibility with current main.
A main advance needs assessment, not an automatic rewrite of unchanged work.

Keep existing branch protections and delivery controls. A label or local check is
not evidence that GitHub enforces a protection. The supported final admission may
include linkage; do not immediately duplicate it. Parallel work, batches, Stage
and capacity are explicit local choices, not requirements on every project.

## Delivery is separate from merge

| Accepted outcome | Completion |
| --- | --- |
| Instructions or source-only work | Independently reviewed, checked, accepted change in main |
| Running service or runtime n8n workflow | Required version and behavior verified on the intended target |
| Distributed package | Required publication and agreed installation/update checks passed |
| Publication-specific work | Requested artifact/catalog accessible and matching approved source |

Keep actual local authorization and the whole accepted scope. A build is not a
production deployment; installer acceptance does not prove every employee updated.
Use maintained project delivery and recovery tools. Inspect an uncertain operation
before repeating it. Archive preserves visibility/history; it is not completion.

## Process and product updates

Deliver proven isolated instructions, tests and process tooling against their own
accepted scope and relevant checks. Do not inherit an application release solely
from the repository's delivery profile. Product/build/install/update effects and
explicit publication requests retain their actual obligations. Mixed or unknown
changes need investigation and appropriate coverage.

The [process/product contract](docs/process-product-separation.md) defines supported
proof. Instructions cannot grant an unsupported completion exception. Tracker owns
executable recording; preserve original scope, reviews and delivery history.

## Living documentation

Use the common [document map](docs/project-documents.md). Keep one authoritative
copy of each rule, short navigation links, original specifications, and a clear
separation between plans and implemented behavior. Update affected knowledge with
the change; meaningful history links its task rather than duplicating logs.
Secrets never belong in these documents. Preserve project-owned knowledge during
upgrades and follow the [layout contract](templates/workflow/LAYOUT.md).

## Checks and project setup

Start new projects with the [setup procedure](docs/adoption.md#new-project-procedure).
Use simple/direct work unless a concrete need justifies another route; choose
Stage, actual capacity and delivery independently. The preset does not assess risk.
Use real commands/targets and verify the actual Tracker connection. A generated
outline or local registry edit is not completed onboarding.

Develop the project process through [bounded improvements](docs/workflow-evolution.md).
Recommend the smallest useful change, implement existing authorization, update
rules/settings together and record relevant verification. Generalize reusable
lessons; keep unique product/runtime behavior local. Existing projects adopt only
through separately scoped compatible changes.

Use [efficient verification](docs/verification.md): meaningful changed-risk checks,
valid evidence reuse and diagnosis before retries. Instructions alone do not alter
GitHub events or suppress automatic checks. Do not invent extra demonstrations,
reports or measured savings for a prose change.

## Status and actual work

Status reports facts: queued, actually working, under review, awaiting delivery
and complete are different. Use the selected vocabulary and
[task lifecycle](docs/task-lifecycle.md). Preserve correction origin and authorized
continuation; a free slot/status does not launch an agent or grant new work.

Where supported, report only your own actual activity using the pinned
[executor procedure](docs/executor-activity.md). Missing activity does not release
ownership. Stage residence, confirmed work and waiting are different measurements;
unknown history stays unknown. Detailed clocks and commands belong in that guide.

## Pause and resume existing work

Use the selected [pause procedure](docs/task-pause.md). Direct owner confirmation
that an agent stopped is sufficient; unavailable hardware need not reconfirm it.
Silence alone is not a stop. Preserve phase, work, history and real blockers.
Resume with actual capacity, fresh authority and current evidence. Never clear a
foreign claim or impersonate an earlier owner. New instructions activate no state.

## Specialized support and ownership

Read detailed mechanisms only when the project selects them:
[project choices](docs/project-choices.md), [ownership](docs/ownership.md),
[existing generated support](docs/adoption.md#existing-generated-workflow-support),
[compatible upgrades](docs/workflow-upgrades.md).
Master owns common policy/templates and the canonical Project Workflow skill;
Tracker owns commands and technical enforcement; each project owns its product
and operational procedures. AI Skills distributes the approved canonical skill.
Update affected skill instructions with a shared rule change; never edit a mirror
independently or treat its installation as project activation.

Related data/release repositories may remain resources of their parent project.
A link alone does not require separate adoption or prove an independently supported
resource board. Preserve their actual local controls.
