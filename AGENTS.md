# Master Repo instructions

Read `delivery.json` and the relevant guidance before implementation:

- [Repository workflow](docs/repository/WORKFLOW.md) and [delivery](docs/repository/DELIVERY.md).
- [System overview](docs/system/PROJECT.md), [engineering context](docs/system/AGENT_CONTEXT.md)
  and [shared standard](standard.md).
- [Runtime boundary](docs/runtime/DELIVERY.md) and [file ownership](docs/repository/LAYOUT.md).

The canonical navigation skill is [.agents/skills/project-workflow/SKILL.md](.agents/skills/project-workflow/SKILL.md).
When changing standards or process contracts, follow the
[skill impact and distribution rule](docs/repository/SKILL-DISTRIBUTION.md).
Update affected skill instructions in the same PR or record a concrete no-impact
assessment. Edit this canonical source; AI Skills receives its verified mirror.

[Tracker display configuration](tracker/config.json) preserves the existing manual
Issue workflow described in [repository delivery](docs/repository/DELIVERY.md#shared-task-display).
It preserves the existing manual workflow. The separate repository-owned
source-admission policy controls review/CI only; see repository delivery.
