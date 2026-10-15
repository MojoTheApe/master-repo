# Optional maintenance and CI evidence support

The compatible Tracker selected in `compatibility.json` supplies the bounded
[TT-107](https://github.com/MojoTheApe/task-tracker/issues/107) companion. Read its
`docs/MAINTENANCE_AND_CI_EVIDENCE.md` in a clean checkout at that exact engine
revision for protocol, supported flags and recovery. This standard exports its
portable producer, but does not enable a consumer policy or reserve live state.

## Owned maintenance

The supported `maintenance show|reserve|resume|transfer` commands use the same
persisted compare-and-swap as admission. Publish all compatible admission clients
and the single projection writer before reserving an interval. Retain the actual
owner, private claim and report; a chat pause or elapsed time cannot replace them.

Reservation stops new ownership. Existing owners retain supported drain/recovery
operations; show whether the interval is draining or idle before migration.
Execution migration still checks actual idleness and preserved history. Under a
held interval its apply additionally requires the real Maintainer credentials and
retains the fence. Resume restores admission; it does not approve or finish tasks.

The held outer state protocol makes incompatible engines fail closed. It retains
the underlying legacy/execution format and private recovery history. Only paused
status, draining/idle and validated reservation time appear in public projections.
No capacity, execution schema, task owner or consumer setting changes implicitly.

## Bounded CI coverage

`ci-evidence collect` records successful native GitHub job attempts through state
CAS. `ci-evidence coverage` revalidates their producers and reports actual covered
run/job IDs and missing job names. Coverage advises consumer CI; it cannot replace
required checks, current independent review, merge admission or delivery receipts.

Adoption is an explicit reviewed current-main `ci_evidence_policy` in the
consumer's Tracker configuration. Export strips upstream policy by default. This
Master revision has no descriptor CI-policy field, initializer opt-in or automatic
product-CI adapter. A consumer adopting coverage must define its actual trust
profile and run missing jobs while preserving its required check names.

The first protocol supports reviewed static JSON-formatted Actions workflows,
immutable container/userland, explicitly host-independent jobs, exact toolchain
versions and Git-bound dependencies/inputs. It checks actual tested content,
latest job attempts, successful steps, producer provenance and evidence lifetime.
Commit metadata mode is conservative; tree mode needs explicit review excluding
commit/branch/history-sensitive behavior. An individual source tree does not prove
a different combined batch. Even one member needs independent composition review.

Unsupported dynamic YAML/matrices, mutable or external inputs, unproven hosts,
installer/platform acceptance and missing/expired proof require fresh relevant
jobs. Manual, release, promotion and runtime contexts retain full/fresh gates.
This version supplies no package/artifact-to-job provenance or runtime attestation.
Existing project collectors retain their own adopted behavior.

For the separated layout, the actual implementation lives at
`.workflow/tools/tracker_ci_evidence.py`; `scripts/tracker_ci_evidence.py` is a
compatibility entry point. Bind the actual implementation and its supported
protocol in the reviewed trust profile. V1 accepts only the self-contained helper
bytes from the actual pinned engine and its exact `python3 -I PATH ...` command;
compatibility wrappers or arbitrary imported producer dependencies require a
separately reviewed protocol. A stable wrapper hash is insufficient when its
imported implementation changes. Run from the project root;
the producer's default `tracker/config.json` is relative to that working directory.

## Rollout boundary

Review engine support, select it in Master, upgrade authorized consumer source
under its old rules, publish compatible writers, then perform any explicitly
adopted policy/state change. Source merge, standard release, service publication
and activation are separate results. Preserve stronger local controls, actual
delivery obligations and private before/after evidence. Product test restructuring
and ACL/React Forge adapters require their own authorized implementation.

## Direct-main frozen batches and Stage policy migration

[TT-127](https://github.com/MojoTheApe/task-tracker/issues/127), coordinated with
[MR-28](https://github.com/MojoTheApe/master-repo/issues/28), supports the same
execution-v2/v3 object with explicit staging disabled. Approved sources remain
approval-only. Only the live reserved frozen batch with current combined review,
CI, `batch` direction, supported batch branch and matching batch line can enter
main. There is no synthetic Stage receipt; real merged inclusion and subsequent
profile-specific delivery remain required. Read the exact compatible engine guide.

`delivery-policy migrate --previous-config FILE --report-file FILE [--apply]`
previews/applies an idle compare-and-swap policy transition. Under owned maintenance
use its actual required credentials. Preserve original queue/authors/history and
receipts; old-policy approvals remain history and need supported author-return/
handoff/review/approval under the new policy. Explicit staging-only audited
reconciliation can retain successful completion only for unchanged target/completion/
checks and exact original receipt/scope/source binding. Pending delivery stays
pending. Preserve historical task allowlists and all provenance; a policy edit
alone grants no completion or admission. Consumer config/registry and fresh board
verification are separately reviewed activation steps.
