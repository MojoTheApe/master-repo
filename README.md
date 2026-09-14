# Master Repo

One shared way to develop and release projects, with different delivery methods
for servers, n8n workflows and local applications.

**First version: 0.1.0, pending review and release.** This repository supplies
rules, an onboarding tool, a reusable validation action and an agent skill. It
does not deploy ReactForge or n8n and does not register production runners.

## The process

Ticket → branch → linked PR → review and CI → main → test the candidate →
approve that candidate → deliver it → verify → Done.

Every project keeps its existing tracker. Each project's `delivery.json` says
how that process applies to it; `docs/DELIVERY.md` explains the operations.
GitHub templates start new projects. Reviewed upgrade PRs update existing ones.

| Start here | Purpose |
| --- | --- |
| [Shared rules](standard.md) | Tickets, PRs, release identity and completion |
| [Adoption](docs/adoption.md) | New/existing projects and agent discovery |
| [VPS](profiles/vps.md) | Separate stage/prod and bounded rollback artifacts |
| [n8n](profiles/n8n.md) | Workflow delivery, credentials and IP restrictions |
| [Local apps](profiles/local.md) | Pilot installs and stable packages |
| [Standard upgrades](docs/versioning.md) | Pinning, release and upgrade PRs |
| [Delivery descriptor](docs/descriptor.md) | Fields, validation and limitations |
| [Project index](docs/projects.md) | Known candidates and adoption status |
| [Agent skill](.agents/skills/project-workflow/SKILL.md) | Apply the standard |

## Try the onboarding tool

Use Python 3.9+ and a clean checkout of a reviewed, published master-repo commit.
The tool writes only to the project you select; it never calls a deployment API.

```sh
# Preview new files. No changes are made without --apply.
python3 scripts/standard.py init --root /path/to/project --profile n8n

# Create a DRAFT setup; existing files are never overwritten.
python3 scripts/standard.py init --root /path/to/project --profile n8n --apply

# Read-only: see what remains to configure.
python3 scripts/standard.py audit --root /path/to/project

# After filling the descriptor/runbook and verifying the setup:
python3 scripts/standard.py validate --root /path/to/project
```

Profiles: `vps`, `n8n`, `local`. Choose hosting separately: n8n can itself run
on a VPS. The internal `standard` profile applies only to this repository.

A generated project intentionally fails readiness validation until its real
tracker, checks, delivery procedures and approval details are configured. The
validator checks the description, not whether a server has actually deployed.

## Reuse the check in GitHub

The generated `delivery-check.yml` checks out the consumer and calls this
repository's composite action at an exact commit. Set private Actions access so
the approved consumer repository can use master-repo; credentials are not copied
into project files. See [adoption](docs/adoption.md#github-access).

No deployment runs on a PR. Consumer CI, independent review and production
approval remain separate requirements. A passing descriptor check cannot replace
application tests or a deployment receipt.

## Maintain this repository

```sh
python3 -m unittest discover -s tests -v
python3 scripts/standard.py validate --root .
python3 scripts/check_links.py
```

Track work in [GitHub issues](https://github.com/MojoTheApe/master-repo/issues).
The initial implementation is [issue #1](https://github.com/MojoTheApe/master-repo/issues/1).
There is no released tag until the reviewed release procedure is completed.
