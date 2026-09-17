# Master Repo system

Master Repo defines the shared path from project creation and ticket intake to
review, optional staging, main integration and verified delivery. It owns the
[standard](../../standard.md), templates, validator, onboarding/upgrade tools and the
canonical agent skill. Task Tracker owns the shared task application and commands;
Issues remain in each consumer repository.

`scripts/standard.py` validates schema 1 and 2 without running descriptor commands.
Its initializer exports a small client from the exact compatible Tracker commit
and writes the project docs/settings/CI plus a template baseline. `scripts/project.py`
implements rendering and three-way upgrades. `scripts/onboard.py` prepares branches,
labels and workspace registration; publishing the registry and proving live board
readiness use the Tracker's maintained delivery process.

New projects default to permanent main/stage branches. Staging can be disabled.
The descriptor selects local manual pull, VPS, n8n, package or tooling completion.
Reviews are performed by a separate subagent invoked by the running implementer;
files alone do not start agents. The Tracker records evidence and checks admission;
GitHub protections and deployment controls must be configured and verified locally.

This repository is itself process tooling, with no application stage or production
service. Its current schema 1 self descriptor is retained as a compatibility test
and explicit local exception. Other repositories are not migrated by changing this
source. ReactForge installer/deployment redesign remains separate.

Read [adoption](../adoption.md), [descriptor](../descriptor.md), [versioning](../versioning.md)
and [change history](../CHANGELOG.md). Original agreed requirements are preserved in
`docs/specs/shared-workflow.md`; implemented current behavior is described here.

The explicit schema-2 n8n-source profile ends source work at an admitted main
merge, with runtime transfer owned by a separate process. It reuses Tracker's
existing reviewed-merge policy; no Tracker engine change is needed. The ordinary
n8n profile still requires verified production. The Action's opt-in draft mode
supports audited adoption feedback without claiming completed setup.

MR-7 adds separated repository/system/runtime guidance. New schema-2 projects
receive project-owned knowledge seeds plus shared helpers in `.workflow/tools/`
with compatible `scripts/` entry points. Upgrades preserve project knowledge even
if an upstream seed changes, and stop for audited migration of earlier layouts.
The validator checks the layout contract and required canonical files.
Task Tracker impact: no engine or policy change. Exported helpers change only their
filesystem-root calculation; CLI/import compatibility is retained and tested.
