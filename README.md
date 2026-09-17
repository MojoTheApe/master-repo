# Master Repo

Shared project workflow, templates and agent skill for MojoTheApe repositories.
Start with [the full workflow](standard.md): ticket intake, naming, self-check,
independent review, optional stage, main integration and verified delivery.

- [System overview](docs/system/PROJECT.md) and [meaningful changes](docs/system/CHANGELOG.md)
- [Create/connect/adopt a project](docs/adoption.md)
- [Safe upgrades and versioning](docs/versioning.md)
- [Descriptor and compatibility](docs/descriptor.md)
- [VPS](profiles/vps.md), [n8n](profiles/n8n.md), [local/package](profiles/local.md)
- [Canonical agent skill](.agents/skills/project-workflow/SKILL.md)

New projects default to Stage before main and receive a small pinned Task Tracker
client. Their Issues stay in their own repository. The shared Tracker owns the
application and commands; Master Repo owns the general process. Both repositories
assess reciprocal impact when that process changes.

The skill installs once per agent environment; each project keeps short local
instructions, settings and system docs. Existing projects retain their adopted
version and unique behavior until an explicit reviewed upgrade.

Source version 1.0.0 is proposed until a reviewed release is published. A VERSION
file is not a release. No app deployment, consumer migration or global skill
installation is performed automatically by this repository.

For an explicitly Git-only n8n project, select `n8n-source`: source delivery ends
after reviewed stage/main promotion, and n8n transfer remains a separate process.
The regular `n8n` profile continues to require verified production delivery.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/standard.py validate --root .
python3 scripts/check_links.py
```

Validation supports Python 3.9+. Tracker export/client requires Python 3.11+ and
GitHub CLI access. See adoption for actual commands and private Action setup.

Repository maintenance rules: [workflow](docs/repository/WORKFLOW.md). Consumer
[file ownership](templates/workflow/LAYOUT.md) separates Git rules, product
knowledge and runtime procedures; upgrades preserve project-owned content.
