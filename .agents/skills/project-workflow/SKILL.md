---
name: project-workflow
description: Apply MojoTheApe's shared delivery standard when creating or onboarding a repository, upgrading its adopted standard, or performing engineering/release work in a project that already has delivery.json. Preserve the project's tracker and deployment controls. Do not turn ordinary feature work into a standard migration.
---

# Project workflow

## Locate the right instructions

Read the project's AGENTS.md, `delivery.json` and `docs/DELIVERY.md`, plus the
existing tracker guide. The standard source is
`https://github.com/MojoTheApe/master-repo`; the descriptor pins its exact commit.
Use an existing clean checkout at that revision or fetch the authorized source
into a task-local directory. Read `standard.md` and only the relevant profile.

For a new/unconfigured project, inspect its current structure and the user's
intended delivery. Use a reviewed published standard revision; if none exists,
report that status and use a specifically selected candidate only as a draft.
Do not invent a released tag, project environment, tracker or deployment command.

This skill is installed independently of the standards checkout. Do not assume
files outside the skill directory exist. If the pinned source cannot be obtained,
continue independent project work from checked-in guidance and identify the
missing dependency before dependent setup/deployment. Never silently use latest.

## Choose the task

- **Ordinary work:** follow the adopted project workflow and current tracker.
  Link the real ticket/branch/PR and run applicable checks. No standard upgrade.
- **New project:** preview `scripts/standard.py init --root PROJECT --profile
  vps|n8n|local` from the pinned source, then apply within the authorized project.
  Configure the generated draft using verified facts; validate before readiness.
- **Existing project adoption:** audit first. Preview scaffolding and integrate
  conflicts in a project PR. Never overwrite working AGENTS.md, CI, tracker or
  deployment configuration from a template. Preserve local exceptions explicitly.
- **Standard upgrade:** compare adopted and selected revisions. Update descriptor,
  action pin and affected guidance in a focused PR; verify migration requirements.
- **Release:** use the project's maintained procedure, exact verified candidate,
  existing approval and operational safeguards. A descriptor is not runtime proof.

Keep each project's existing tracker. Map the shared lifecycle to it; never create
a second task just to satisfy a different template. Keep partial/deployment-pending
work out of Done. For local apps, follow their explicit stable-package completion
policy instead of assuming a server deployment or waiting for every user's update.

## Delivery differences

VPS: separate stage/prod configuration and data; bounded artifacts and compatible
rollback; preserve independent native admission. n8n: distinguish workflow release
from server upgrade, inspect the existing integration and authoritative live state,
protect production IDs/credentials and verify publication. Local: test/pilot package
then an approved stable distribution; preserve user data.

Git storage does not authorize deployment. Complete all independent preparation
before any missing approval. Do not remove required gates or redesign ReactForge
hotfix/update behavior as part of adoption. Do not install global skills or change
unrelated projects unless that operation is within the user's request.

Report briefly: changed files/PR, adopted revision, checks, verified environment
facts and specific remaining setup. Never present scaffolding as a live migration.
