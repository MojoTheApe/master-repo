# Master Repo

Shared project workflow, templates and agent skill for MojoTheApe repositories.
Start with [the full workflow](standard.md): ticket intake, naming, self-check,
independent review, optional stage, main integration and verified delivery.

- [System overview](docs/system/PROJECT.md) and [meaningful changes](docs/system/CHANGELOG.md)
- [Create/connect/adopt a project](docs/adoption.md)
- [Safe upgrades and versioning](docs/versioning.md)
- [Workflow ownership and generated instructions](docs/ownership.md)
- [Descriptor and compatibility](docs/descriptor.md)
- [Efficient verification](docs/verification.md) and [coordinated upgrades](docs/workflow-upgrades.md)
- [VPS](profiles/vps.md), [n8n](profiles/n8n.md), [local/package](profiles/local.md)
- [Canonical agent skill](.agents/skills/project-workflow/SKILL.md)

New projects default to Stage before main and receive a small pinned Task Tracker
client. Their Issues stay in their own repository. The shared Tracker owns the
application and commands; Master Repo owns the general process. Both repositories
assess reciprocal impact when that process changes.

The skill installs once per agent environment; each project keeps short local
instructions, settings and system docs. Existing projects retain their adopted
version and unique behavior until an explicit reviewed upgrade.

The new-project Master initializer defaults to execution schema 2 (five Workers,
one source review, batches up to five) with task context; Stage defaults on.
Explicit `--legacy-execution` selects only the supplied older choices. Standalone
Tracker export and existing-project upgrades preserve absent policies.

Projects can explicitly select their execution version: schema 1 has one combined
review/integration lane; schema 2 adds Approved and separate batch integration;
schema 3 permits up to five independent source reviews and one combined reviewer.
For five Workers/reviews and batches up to five, use `--implementation-limit 5
--batch-limit 5 --review-limit 5`. Omitted settings retain legacy execution only in the explicit legacy selection
and standalone engine export; upgrades preserve the real recorded input.
See [activation and recovery](docs/adoption.md#enabling-parallel-implementation).

Verification separates source feedback, combined integration and actual delivery.
Descriptor templates avoid duplicate feature-push/PR runs and cancel obsolete PR
runs only. Products retain actual commands and platform matrices. The read-only
branch-controls audit reports platform limitations; `check-merge` is not native
protection. Durable maintenance and broader CI evidence transfer are a concrete
Tracker companion, not features activated by this source update.

Source version 1.1.1 proposes selected primary instructions and complete local
reference navigation. The published completion pair is Master 1.1.0 / Tracker
3.3.0; consult immutable releases for publication proof. A VERSION file is not a release. No app deployment, consumer migration or global skill
installation is performed automatically by this repository.

For an explicitly Git-only n8n project, select `n8n-source`: source delivery ends
after reviewed main integration (through stage when enabled), and n8n transfer
remains a separate process. One explicitly authorized selected integration/main-merge
request follows the [continuation contract](docs/delivery-continuation.md) through
verified project completion; actual deployment adapters remain project-owned.
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
