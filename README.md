# Master Repo

Shared instructions, project structure and the Project Workflow skill for
MojoTheApe repositories.

## Start here

1. Read the [shared workflow](standard.md) for ordinary development.
2. Follow the project's short `AGENTS.md` reading map and local commands.
3. Use [efficient verification](docs/verification.md) to select checks and avoid
   unnecessary GitHub Actions runs.
4. For a new project, follow [setup and connection](docs/adoption.md#new-project-procedure).

GitHub holds each project's Issues, code, reviews and checks. Master describes how
to work. The existing Task Tracker displays that work. Coordination uses the
existing task and tools; adopting these instructions does not require a new agent
controller, permission service, script or database.

## Find the right document

| Need | Read |
| --- | --- |
| Task, review, completion and short templates | [Shared workflow](standard.md) |
| Checks, reuse, retries and cost measurement | [Verification](docs/verification.md) |
| Existing fast/full check plans and CI event behavior | [Submission](docs/verification-submission.md) |
| New or existing project setup | [Adoption](docs/adoption.md) |
| Repository rules versus product and runtime knowledge | [Ownership](docs/ownership.md) and [layout](templates/workflow/LAYOUT.md) |
| Agent instructions and their distribution | [Project Workflow](.agents/skills/project-workflow/SKILL.md) and [distribution](docs/repository/SKILL-DISTRIBUTION.md) |
| Current implementation and history | [System](docs/system/PROJECT.md) and [changes](docs/system/CHANGELOG.md) |
| Work on Master itself | [Repository workflow](docs/repository/WORKFLOW.md) |

## Existing project support

Projects already using generated clients, descriptors, staged delivery, batches or
other selected mechanisms keep their local rules. Consult their pinned guide and
only the relevant [compatibility references](docs/adoption.md#existing-generated-workflow-support).
Installing a newer skill does not migrate a project.

The existing initializer and validators remain available with their documented
behavior; this documentation update does not change their defaults or promise a
new execution mode. Consumer changes, standard releases, skill distribution and
running Tracker updates are separate results.

Master's own completed candidate uses its existing checks:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/standard.py validate --root .
python3 scripts/check_links.py
```

Validation supports Python 3.9+. Existing Tracker export/client operations require
Python 3.11+ and the compatible pinned checkout. Read the relevant procedure only
when that operation is actually part of the task.
