# Versioning and safe upgrades

`VERSION` is a proposed source version, not proof of a published release. Version
1.0.0 introduces the complete workflow and descriptor schema 2. Schema 1 validation
remains available for pinned existing consumers; it is not silently migrated.
Local manual pull now has its own completion rule, separate from package delivery.

Publish only a reviewed merged candidate with passing checks, compatible Tracker
pin and explicit release authorization where still missing. Tags/releases identify
immutable commits; never move a published tag. This repository does not automatically
publish releases. Consumer app versions are independent.

## Pinned dependencies

A consumer pins the exact Master commit in `delivery.json` and its CI Action;
`compatibility.json` pins the compatible Tracker engine. Its small client pins the
same engine. An upstream commit alone changes no consumer. The self-standard uses
`revision: self` only in its own schema 1 descriptor because it has no app runtime.

## Three-way upgrade

Run from a clean selected new standard checkout:

```sh
python3 scripts/standard.py upgrade --root /path/to/project \
  --tracker-root /path/to/new-compatible-tracker
```

Preview first, then `--apply`. The tool compares recorded old template, newly
rendered template and current project. It updates untouched shared files, preserves
local-only changes and attempts disjoint text/JSON merges. Overlapping edits or
competing additions/removals produce a conflict list and **no writes**. Unmanaged
project code, installers and local files are never part of the replacement set.
The applied base is the newly rendered upstream template, not the locally merged
result, so subsequent upgrades retain knowledge of project differences.

Resolve conflicts in a project PR: inspect each old/new/current version, preserve
the intended local behavior and document exceptions. Do not bypass conflicts by
copying the new template wholesale. If no trusted base exists (including schema 1
adoption), use the audited adoption procedure. Template updates cannot silently
change the selected stage option or project-specific deployment target.

Review config/engine/Action pins together, check docs, modules, historical IDs,
completion evidence and open PRs. Activate changed semantics only after their
migration prerequisites are satisfied. Run strict descriptor and actual project
checks plus independent review. A successful textual merge is not proof that
runtime settings or delivery still work.

## Several projects

On an explicit bulk update request, inventory repositories, current pins, local
exceptions, open work and readiness. Create one issue/branch/PR per project, report
conflicts separately, and verify its local behavior. No new Master release, skill
installation or ordinary feature task triggers an automatic fleet migration.

Every Master change assesses Task Tracker impact and vice versa. Link coupled
issues/PRs, state release order and compatible revisions, and report a concrete fix
when synchronization is needed. Deploy engine support before opting consumers in.

## Knowledge ownership

Use the [layout contract](../templates/workflow/LAYOUT.md). New repositories get
separate `docs/repository/`, `docs/system/` and `docs/runtime/` areas. System/runtime
outlines become project-owned at creation; upgrades never overwrite or merge them.
An earlier mixed baseline stops without writes: audit and split local documents,
keep safeguards and forwarding paths, record the move map and validate the final
candidate. Retain the pristine newly rendered template as the new baseline.
Shared helper implementations live in `.workflow/tools/`; old `scripts/` paths
remain compatible. No layout change implies new deployment or task semantics.
