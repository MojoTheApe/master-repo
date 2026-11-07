# Common project documents

Use the same document responsibilities and, for new generated projects, these
paths. Product code follows its own technology; this is a documentation map.
Existing projects keep equivalent documents until an explicitly scoped migration.

| Location | What it contains | When to update |
| --- | --- | --- |
| `README.md` | Purpose, users, current state, startup entry and useful links | When the entry points or purpose change |
| `AGENTS.md` | Short reading map, selected standard and local instructions | When navigation or selected rules change |
| `docs/system/PROJECT.md` | Implemented capabilities, components, data flow and limitations | With a change to product behavior |
| `docs/system/AGENT_CONTEXT.md` | Business rules, engineering constraints and important decisions | With a relevant design decision |
| `docs/repository/WORKFLOW.md` | How to start, review, integrate and finish work here | With an authorized process change |
| `docs/repository/VERIFICATION.md` | Actual checks, their coverage and when they are needed | With changed risks or checks |
| `docs/repository/DELIVERY.md` | Git integration and the selected completion condition | With changed integration or completion |
| `docs/runtime/DELIVERY.md` | Actual targets, release, operational verification, backup and recovery | With changed runtime procedures; say explicitly when no runtime exists |
| `docs/system/specs/` | Larger agreed specifications and their decision links | Before substantial work and when accepted requirements change |
| `docs/system/CHANGELOG.md` | Meaningful product changes with task/PR links | With a significant product change |
| `docs/repository/CHANGELOG.md` | Meaningful process changes, reason and evidence links | With a process change |
| Project Issues and PRs | Task requirements, progress, failures, reviews and actual results | During the relevant work |

A small task needs an Issue, not a separate specification document. Larger specs
link their implementation tasks; tasks link back to the spec. Keep plans separate
from implemented behavior. Preserve original decisions and mark superseded material
as history. A changelog is a short explanation, not a copy of every commit or log.

Keep one authoritative copy of a rule. The reading map and README link to it.
The [common engineering standards](engineering-standards.md) govern scope and
proportionate design. Local context records actual technology, ownership, useful
examples and verification references; it does not duplicate those common rules.
Use existing Issues/PRs for error and recovery history; no second incident register
or per-save engineering ticket is required. Ordinary data/notes keep the project's
already adopted capture procedure.

The selected Tracker guide and machine files remain generated technical support.
`delivery.json` records intent; matching `tracker/config.json` and the pinned engine
execute it. Do not maintain a second manual settings list in a new project passport.
The brief project summary belongs in WORKFLOW and links these existing sources.

New scaffolds seed these documents. Fill them from real project facts, leaving
unknown setup visibly pending; empty outlines are not completed onboarding.
README, system and runtime knowledge are project-owned and preserved on upgrade.
Older projects without a generated README are not forced through a file migration.
See the [ownership contract](../templates/workflow/LAYOUT.md).
