# Versioning and safe upgrades

## Simplified instructions release 1.5.2

Candidate1.5.2 packages the simplified common instructions and canonical skill
already reviewed in [MR-57](https://github.com/MojoTheApe/master-repo/pull/58).
It changes the source version and self descriptor together. The compatible Tracker
remains published3.7.1 at `be87599d1b5e625058bbddc33c35bda86687b5bf`;
validators, generated templates, portable artifacts and policies are unchanged.
Consumers retain their exact pins and existing behavior.

[MR-59](https://github.com/MojoTheApe/master-repo/issues/59) tracks the authorized
publication. Complete the repository checks and existing clean compatible-pair
release check, independent review, protected main integration and actual-main
checks before publishing tag `v1.5.2` at that exact merge. Verify the accessible
release and tag target before completing the task. Keep existing tags unchanged.
The source version alone does not claim publication or consumer adoption.
The unchanged canonical skill remains distributed through AI Skills; verify the
complete copy rather than creating a duplicate authored change or reinstalling it.


## One-policy package continuation

Source candidate1.5.1 corrects the optional-policy package/adoption order and
requires the canonical engine-owned selection receipt fixtures in the portable
pair. It adds no consumer policy default, state protocol or admission authority.
Its compatible Tracker3.7.1 source is published at
`be87599d1b5e625058bbddc33c35bda86687b5bf`, tag `v3.7.1`, release415992924,
after successful checks on that actual merged commit. The exact source pin and
complete53-file artifact closure were refreshed mechanically. The native release
has `immutable:false`; exact tag/commit verification remains required. Master1.5.1
is still a source candidate until its own final checks and publication succeed.

For this patch, require the clean final pair with `--portable-contract --retry-contract
--direct-contract --selection-delivery-contract --require-pinned` and the genuine
previous Master1.5.0 `37090f0cf11eca5203a40932e2192f7eb47e2566` /
Tracker3.7.0 `0b317d99997a4d3ef35b637bd6d19244630539f9` inputs. Final independent
Master review, actual Source/main checks, stable publication and the exact
canonical skill mirror remain separate gates. No reader/service installation,
policy selection, activation or live recovery follows from these publications.

## Explicit project choices and modern routes

Source version1.5.0 adds descriptor3, independent role/profile/completion/Stage
choices, explicit direct/batch execution4 and optional ordinary knowledge capture.
Its exact Tracker3.7.0 dependency is published at
`0b317d99997a4d3ef35b637bd6d19244630539f9`, tag `v3.7.0`, release415924055.
Actual main checks and the stable-release guard precede this mechanical pin.
The native release has `immutable:false`; exact tag/commit verification and the
never-move-tag rule remain required without claiming native enforcement.

The selected canonical provider owns the complete12raw/24separated closure,
modern direct native fixture/runner, selected guide and owned state/admission.
Verify the full actual Python3.9 Master suite and the final exact clean source pair
with `--portable-contract --direct-contract` before standard publication; its
original pair used genuine previous Master31daf/Tracker03e inputs. Master1.5.0 is
published at `37090f0cf11eca5203a40932e2192f7eb47e2566`, tag `v1.5.0`,
release415935589. Publication does not establish an installed reader or complete
the separate consumer outcomes. New patch publication follows the current
one-policy source-pair boundary above and the maintained exact skill mirror path.

Preserve existing project settings and old policy absence. New modern config is
not activation: compatible readers/all writers and owned idle outer7 migration
must precede actual use. Consumer producer blob pins need separately reviewed
refresh when canonical producer bytes change. Task08's explicit publication
completion/verified mirror authority is not introduced by Task07.

## Existing-topology capacity slice

Master1.4.0 adds the [capacity contract](capacity.md) and canonical operational
navigation for Tracker3.6.0 current-topology projection. These are source versions
until the exact reviewed merges, actual-main checks, stable releases and compatible
pair are verified. Select the actual published engine through the maintained
contract refresh; never substitute an overridden or dirty preparation for the
clean final pair. Publish Tracker first, then the checked exact Master pin and
canonical skill mirror. Installed reader/live reservation comparison remains a
separate Task09 outcome, and its later modern-direct extension remains Task07.
Consumer settings, capacities, state, Stage and delivery targets are preserved.

## Portable baseline and retry/accounting publication

Master 1.2.0 and Tracker 3.4.0 are published portable-contract releases at
`864ca7a5814e703dd6e61207362d24cbc26dc9ad` and
`866baf6dec2bd82d8ca052002cc3dc6f4805e247`. Their successful actual-main checks and
real paired export/upgrade evidence precede publication. Source publication is
separate from installed readers, owned consumer activation and live outcome proof.

Master 1.3.0 adds [bounded retry](ci-retry.md), explicit policy selection,
[fast/full submission guidance](verification-submission.md) and
[on-demand accounting](ci-accounting.md) with Tracker 3.5.0. The portable contract
adds the source-owned retry validator snapshot and generic accounting helper.
The selected Tracker technical source is its reviewed merge
`df0154b96410296b50bc9d7a00af7847d9a97700`. Source versions and a selected commit
do not prove publication. Verify the actual stable Tracker release at that exact
commit before the final native paired gate and Master publication. Preparation
against a merged candidate remains provisional until that release guard succeeds.
Run the single clean final source-pair gate before Master publication. Existing projects
retain selected policies, execution limits, targets and state until reviewed adoption.

The observed Master1.2.0 and Tracker3.4.0 releases have GitHub's native immutable flag false.
Exact verified commit/tag identities and the never-move-tag rule are recorded
without claiming native immutable-release enforcement.

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

Execution parallelism is an explicit project setting. Omitted policy remains
omitted during upgrade; an opted-in project's local capacity is retained in both
descriptor and Tracker config. The baseline remains the pristine upstream render,
not the merged local capacity. Enable/change it in a reviewed consumer PR only
after compatible Tracker support and safe claim-state migration. Execution v1
retains its sole review/integration lane. Explicit execution v2 adds a configurable
batch limit (recommended five), Approved and separate review/integration ownership.
Both sides must agree on the policy and workflow phases; upgrades preserve local
limits and do not silently change versions. Existing stage/delivery controls remain.

Review config/engine/Action pins together, check docs, modules, historical IDs,
completion evidence and open PRs. Activate changed semantics only after their
migration prerequisites are satisfied. Run strict descriptor and actual project
checks plus independent review. A successful textual merge is not proof that
runtime settings or delivery still work.

## Several projects

Use [coordinated upgrades](workflow-upgrades.md) for dependencies, cutover admission
and reuse of unchanged verified facts, and [verification](verification.md) for
actual check selection. Maintenance/CI-evidence extensions need reviewed compatible
Tracker support; new instructions cannot implement or silently activate them.

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

MR-16's optional process_instructions route is another reviewed compatible
contract extension, not an automatic consumer migration or standard publication.
Integrate the matching Tracker first, pin its immutable reviewed revision, review
and integrate Master, install the canonical skill when authorized, then adopt in
each consumer under its existing route. Omitted options preserve older consumers.


## WFO-05–08 compatible source publication

The coordinated source versions are Tracker 3.2.0 and Master 1.0.0. Publish the
independently reviewed Tracker merge after its actual-main checks, then select
that exact merged engine in compatibility.json, validate all profile exports/
upgrades, independently review Master and publish its checked merge. Keep tags
immutable and consult the actual release catalog before claiming publication.
The [validation report](validation/wfo-05-08.md) records native reuse, measurements
and limits. Verify the canonical skill through AI Skills' maintained mirror sync;
never author its generated mirror by hand. None of these source releases opts
existing consumers in or performs a live state/service upgrade.
