# Master Repo system

Current navigation: [verification](../verification.md),
[coordinated upgrades](../workflow-upgrades.md) and
[optional Tracker companion](../tracker-companion.md).
Execution versions remain explicit choices; schema 3 permits up to five source
reviews with single combined integration. VERSION1.0.0 remains unreleased, which
is distinct from an existing consumer's recorded active workflow.

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

MR-26 selects the reviewed TT-107 maintenance/native-CI companion. The separated
export preserves its optional producer byte-for-byte in `.workflow/tools/`, with
the existing compatibility entry point. Actual producer trust binds that
implementation through the pinned engine's exact self-contained/isolated protocol.
No CI-evidence policy is inherited or enabled by the initializer. Owned maintenance
requires compatible published writers; CI coverage requires explicit reviewed
consumer adoption and retains every unsupported/missing job as fresh. This source
selection does not change consumer execution capacity, state or runtime delivery.

New projects default to permanent main/stage branches. Staging can be disabled,
including execution-v2/v3 frozen batches with Approved and independent combined
review retained. The reserved combined candidate enters main directly; ordinary
sources remain approval-only. The [continuation contract](../delivery-continuation.md)
carries one selected integration/main-merge authorization through project-owned
delivery, verification and the exact Tracker receipt. Templates/skill guide the
agent and require a maintained consumer adapter; they do not create executable
deployment or activate a consumer.
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

MR-9 selects the compatible Tracker historical-completion extension (TT-61).
Existing-project adoption may retain a reviewed, owner-approved list of completed
tasks without inventing old delivery evidence. This is an opt-in project-local
configuration; new projects and existing pinned consumers receive no exemption.
The adoption guide explains exact scope matching, restarted work and cutover
review. Release/installation verification and new task admission stay unchanged.

MR-11 adds opt-in execution settings to schema 2: configurable implementation
capacity (1..16, initial rollout 2) and one review/integration lane. The initializer
accepts `--implementation-limit`, validates mirrored descriptor/Tracker policy and
passes it explicitly to the compatible exporter. Omitted policy preserves legacy
behavior; three-way upgrades retain local capacity and original template ancestry.
The standard and canonical skill coordinate platform-neutral Workers in isolated
worktrees and one independent Reviewer, with honest serial fallback if delegation
is unavailable. The lane covers review, checks, stage and main integration.
Task Tracker companion [TT-67](https://github.com/MojoTheApe/task-tracker/issues/67)
owns persisted claims, queue/admission, recovery and display; it does not launch
models. Master [MR-11](https://github.com/MojoTheApe/master-repo/issues/11) activates
no consumer. Compatibility selects the reviewed TT-67 merge
`a4ea3cfb0c1be1760ae0923c8232779532c25a7b`; separately install the authorized canonical skill after Master integration. ACL
adoption follows in its own task. Standard release publication is separate.

MR-14 adds explicit execution-v2 validation, initialization and upgrade support
for independently approved tasks and integration batches. `--batch-limit 5` with
an explicit implementation limit selects the mirrored policy and Approved phase;
legacy and execution-v1 workflows remain unchanged. Batch size is independent of
Worker capacity and local settings survive three-way upgrades. The canonical skill
routes by the adopted version and preserves per-task author/reviewer evidence,
fixed ship-all intake, one integration candidate and separate delivery obligations.
Companion [TT-77](https://github.com/MojoTheApe/task-tracker/issues/77) owns command,
state, admission and UI support. Compatibility pins its reviewed integrated revision
`e6013f8ad641bd99061f7db82bceeb705f8c150a` (Tracker PR 78), including TT-73's
large-state read fix. The real exporter was checked for legacy, v1 and v2 consumers;
the new portable batch helper follows the existing relocated-helper layout.
The authorized rollout includes
local skill installation and separate [ACL-1566](https://github.com/MojoTheApe/adopy-campaing-launcher/issues/566)
adoption, with max five per batch. Source work here does not itself activate ACL.

MR-16 adds an explicit instruction-only route distinct from file ownership.
Schema-2 generation and validation mirror workflow.process_instructions with
Tracker's top-level object and require its exported portable helper. Eligible
regular process instructions retain genuine task ownership/current independent
review and explicit checks, then complete at admitted main integration. Automation,
configuration, application and mixed work retain the ordinary staged/delivery
route. Existing delivery fingerprints, execution defaults, consumer pins and
project-owned knowledge are preserved. The canonical skill routes only after
actual project opt-in; Task Tracker owns immutable diff admission and completion.

## MR-18 — Preserve closed historical review handoffs

Pin the independently reviewed compatible Tracker at `086aaa98f2e807d640105be2929714d0b7331f21`
(Tracker task #85). Explain the explicit paired migration flags for
genuine closed, unmerged historical sources. Queue order, authors and handoffs
are retained without reopening or approving those unfinished tasks; normal
review, Approved and batch admission retain current-open checks. Activation
requires preserved-state and fresh-board proof; first-batch proof follows real
approved work instead of manufactured demonstration features. Consumer pins and
state activation remain separately reviewed operations.

Master task: https://github.com/MojoTheApe/master-repo/issues/18
Tracker task: https://github.com/MojoTheApe/task-tracker/issues/85

## MR-22 — Parallel source reviews

Explicit execution schema 3 supports 1..5 source-review slots and batches of 1..5,
with one separate integration Coordinator/Reviewer. `--review-limit N` requires
explicit implementation/batch choices and staging; omitted input retains v1/v2.
Mirrored policies, exact compatible export and required batch helpers are validated.
Conservative upgrades preserve local capacities and pristine template ancestry;
inconsistent settings fail before any write. The canonical skill and templates
describe source-specific ownership, current evidence and idle queue-preserving
consumer activation. Task Tracker companion TT-97 expands its reviewed TT-93 pool.
Compatibility pins independently reviewed Tracker TT-97 / PR98 merge
`46283b8a6fe444065838e136c89ef4ed64bd1528`. Source integration here does not
deploy the service or activate an existing project.

## MR-20 — Skill ownership and central distribution

Project Workflow remains canonical in this source repository and is distributed
through a verified read-only mirror in the AI Skills library. Standard/process PRs
include an explicit updated/no-impact assessment, with any affected instructions
changed in the same PR. CI validates the declaration; independent review evaluates
its substance. The library owns synchronization and Codex plugin publication.
Agency Builder and AIO remain library-owned. No consumer pins, Tracker contracts,
source release tags or runtime settings change.
Task Tracker impact: no application/engine change; this is source skill maintenance
and distribution. Master task: https://github.com/MojoTheApe/master-repo/issues/20

## MR-28 — Delivery continuation and deliberate no-stage batches

Generation and validation allow explicit `workflow.staging: false` with execution
schema 2/3 while retaining real source authors, Approved, independent combined
review, bounded frozen composition and all applicable CI. Export postconditions
reject mismatched phases or delivery policy. Three-way upgrades preserve deliberate
local choices and pristine template ancestry; defaults and legacy/schema-1 consumers
are unchanged. The generated delivery continuation reading map and runtime seed
cover exact merged tasks/revision/target, trusted project adapter/CI, serialized
mutations, durable failures/retries and verified receipts. No universal deployer
or new descriptor key is introduced.

One selected integration/main-merge approval covers the maintained chain after
main without routine second approval or a separate “and deliver” request. Agents
persist `--deliver` by default for eligible runtime/package batches; explicit
source-only/skip-release instructions defer delivery without declaring completion.
Starting development still ends at Approved in v2/v3. Master itself is tooling: its running agent verifies the full
reviewed merged scope and successful main checks, records evidence and closes the
Issue; source publication and consumer rollout remain separate.

Task Tracker companion [TT-127](https://github.com/MojoTheApe/task-tracker/issues/127)
owns direct-main batch admission and the explicit idle delivery-policy migration.
Staging changes retain old policy proof as history; verified delivery can survive
only through the supported audited reconciliation with unchanged target/completion/
checks and exact original receipt/scope/source binding. ACL adoption is a separate
authorized consumer task. Compatibility selects the independently reviewed
Tracker [PR 128](https://github.com/MojoTheApe/task-tracker/pull/128) merge
`e775c624e0323e69ed891926691c3dee6587081a`. Consumer publication, policy activation
and package delivery remain separate verified operations; source selection alone
is not readiness.
Master task: [MR-28](https://github.com/MojoTheApe/master-repo/issues/28).

MR-28 follow-through: preserve the TT-127 standalone delivery recorder byte-for-byte
in separated exports, with a compatible scripts entry point; required v2/v3
production/package delivery validates both paths. Explicit `--deliver` binds the
real authorized batch and configured native verification producer. The maintained
project CI owns delivery; the recorder revalidates real Merged handoff and native
job/log evidence before writing the receipt.
ACL [parent 1923](https://github.com/MojoTheApe/adopy-campaing-launcher/issues/923)
and [source 1924](https://github.com/MojoTheApe/adopy-campaing-launcher/issues/924)
retain separate old-stage source integration and authorized live activation.
