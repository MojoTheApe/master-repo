---
name: project-workflow
description: Follow MojoTheApe's shared project workflow when creating or onboarding a repository, explicitly upgrading its standard, or doing engineering/release work in a project with delivery.json. Locate the project's pinned rules, use its Tracker, preserve local controls, and arrange independent review. Ordinary feature work is not a standard migration.
---

# Project workflow

## Find the adopted instructions

Read project `AGENTS.md` and `delivery.json`, then follow their reading map.
Separated projects keep Git/Tracker rules in `docs/repository/`, product knowledge
in `docs/system/` and operational safeguards in `docs/runtime/`. Earlier pins may
use forwarding or legacy paths; follow their own checked-in contract. Master source: `https://github.com/MojoTheApe/master-repo`.
Use a clean checkout at the descriptor's exact commit and read `standard.md` plus
the relevant profile. For schema 1, follow that pinned version's semantics. Never
silently apply newer schema 2 rules to an old project.

This skill is installed once per agent environment. Its canonical copy lives at
`.agents/skills/project-workflow/SKILL.md` in Master Repo. Project AGENTS files are
short reading maps; they are not copies of this global skill.
Do not assume files outside the installed skill directory exist. Locate or obtain
authorized pinned source checkouts explicitly. An updated skill is a navigator,
not permission to upgrade project pins or replace unique project behavior.

If the source is unavailable, continue independent work from checked-in project
guidance and identify the missing dependency before dependent operations. For new
projects use a reviewed released revision; if only a specifically selected
candidate exists, disclose it and keep adoption draft. Do not invent releases,
environments, check commands or live registration proof.

## Select the operation

- **Ordinary work:** follow current project pins, Tracker and local deployment
  controls. No standard migration or unrelated refactor.
- **New project:** read the pinned `docs/adoption.md`. Choose profile, public ID
  prefix, workspace ID and actual targets. Stage defaults on; local means manual
  pull, package is separate. Preview/apply the initializer with a clean compatible
  Tracker checkout. Preserve supplied specs, configure the draft, publish initial
  main, run onboarding for branches/labels/registry, complete the maintained
  registry publication and verify the fresh live project board. Record actual
  onboarding proof and validate before marking ready. A local scaffold is not a
  connected project. Keep the application in Task Tracker, only its client locally.
- **Existing adoption:** audit IDs/history, modules, open PRs, release state,
  deployment, installers and exceptions. Preserve them. Finish pre-adoption open
  PRs under original rules before activating new checks; reconcile historical
  completion. Integrate a preview in a project PR; never delete local files to make
  a template fit. Without a trusted old template base, do not invent one.
- **Upgrade:** use the selected new standard's `upgrade` preview and its compatible
  engine. Compare old template, new template and local project; preserve local
  fixes, resolve conflicts explicitly, keep pins/config/CI consistent, test and
  independently review. Bulk requests use an inventory and one project PR each.
- **Release:** follow the local maintained mechanism, exact verified content and
  current authorization. Descriptor/merge are not installation or behavior proof.

## Execute the ticket lifecycle

Idea request -> Idea; task request -> Backlog. Planning and To Do do not start code.
On explicit development, read the full Issue, claim the Tracker slot with its
`work` command and create `codex/<public-id-lowercase>-<short-name>`. Preserve
classification, dependencies and existing queue semantics. PR title lists IDs:
`[RF-67, RF-68] Summary`; exactly one `Tracker issues:` line and links back from
Issues. PR numbers are different from Issue IDs. Avoid automatic closing keywords
in both PR text and commits. Keep partial tasks and abandoned PRs unfinished.

Implement and self-check, update affected system docs/history or explain no impact,
create a ready PR and set Review. Automatically invoke a different subagent for
independent review of the actual head/base, full task scope and changed files.
The reviewer reports findings/checks/verdict; the implementer fixes on the same
branch. If the reviewer edited code, use another final reviewer. A missing
independent reviewer is a limitation to report, not self-approval. Changed code,
base, task scope or policy needs fresh approval. Preserve the durable report and
record it using the pinned Tracker evidence command when supported.

Run `check-pr N` for links and `check-merge N` for admission immediately before
merge in the new contract. The latter verifies current review, required checks and
stage; a link check alone does not authorize merge. Verify actual GitHub branch
protections separately. Merge after valid review/checks within the existing task
authorization; no additional routine owner-confirmation step is needed.

## Stage, merge and completion

If enabled: working branch -> permanent stage -> permanent main. Same task set,
one active stage candidate, exact approved content. Keep the working branch for
fixes after its first PR; new fix PRs use that branch. Do not delete permanent
branches. Record Stage after the source merge, verify the real stage target, and
promote only matching content. Use merge/squash with the approved baseline, not
rebase merge. If main changes, reconcile in the working branch and repeat review,
stage and verification. If disabled: working branch -> main, no Stage column.

Record Merged only for fully implemented ticket scope actually included in main.
Local manual-pull/tooling completes after admitted merge. VPS/n8n need verified
production delivery; package needs its stable release and installation check.
Pending/failed delivery is unfinished in dependencies and release readiness.
Record actual receipts against the configured target; never relabel stage evidence
as production success or change completion merely to bypass a failure.

Preserve local approvals, credentials, backups, compatible rollback and data.
n8n workflow publication is distinct from upgrading the n8n server. ReactForge's
installer/hotfix redesign is separate scope. Do not deploy, install global skills
or migrate other consumers merely as a test.

## Keep shared and local knowledge current

`docs/system/PROJECT.md` describes the implemented system; `docs/system/CHANGELOG.md` explains
meaningful changes and reasons with ticket/PR links. Preserve original specs and
distinguish plans from implemented features. Documentation changes belong in the
implementation PR and independent review.

For process changes in Master Repo, assess Task Tracker impact; for Tracker
changes, assess Master Repo impact. Record no impact with a reason, or propose a
concrete linked fix and compatible release/migration order. Implement a matching
change when already within the user's authorized scope; otherwise present the
prepared proposal. Do not impose an automatic consumer upgrade.

Report briefly: result, issue/PR, pins and checks, actual stage/delivery/connection
proof, preserved exceptions and any concrete remaining setup. Keep explanations
readable for a nontechnical owner.

Keep process history in `docs/repository/CHANGELOG.md`. System/runtime files are
project-owned; never refresh their contents from an upstream template. Shared
upgrades of a legacy mixed layout require an audited split, not a bulk overwrite.
