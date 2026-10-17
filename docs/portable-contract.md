# Portable Tracker contract

Master owns descriptor/profile validation and common workflow policy. Tracker owns
the executable portable helpers, CI policy validator and their fixed raw/separated
layouts. Master requests `export-template --helper-layout separated` and consumes
the emitted helper bytes unchanged; documentation moves remain Master-owned.
The default standalone export keeps raw `scripts/` implementations.

`compatibility.json` binds the official exact engine, export format 1 and SHA-256
of the source-owned `scripts/vendor/tracker-export-contract.json`. That static
record declares actual capabilities, runtime floors and all twelve raw/twenty-four
separated helper hashes for the selected modern engine. Older pinned manifests
retain their actual inventories. The consumer's `tracker/export-contract.json` must equal
the trusted record byte-for-byte. Installed helpers must match its fixed layout.
Missing files, changed bytes, unsafe paths, duplicate keys, unsupported formats
and unsupported selected policy versions fail before transport. Rehashing a
changed consumer cannot establish trust.

Structural CI-policy validation calls only `policy()` in the exact canonical
Tracker module snapshotted at `scripts/vendor/tracker_ci_evidence.py`. Master
verifies those source-owned bytes before execution and never loads a consumer's
validator, searches for a replacement or bootstraps a private engine. Master
descriptor concerns remain separate. No third CI-policy implementation is kept.
The fixed `retry_validator` slot likewise binds `tracker/ci_retry.py` to the
source-owned `scripts/vendor/tracker_ci_retry.py`; structural retry selection
calls only that verified module's `policy()`. Generic accounting is a separate
self-contained exported helper with no retry/state activation dependency.

Modern descriptor3 uses one additional fixed `route_validator` slot binding the
actual canonical `tracker/direct_policy.py` to the mechanically copied
`scripts/vendor/tracker_direct_policy.py`. Master verifies its bytes and delegates
execution/context/capture cross-validation to that module; it never imports a
consumer validator or keeps another state algorithm. A missing provider,
unsupported selected contract, redirected source or changed snapshot fails before
export/target writes. The actual pinned manifest owns the helper inventory;
adding source support is not a published pin, state activation or lifecycle proof.

Python 3.11+ remains required for the author engine/exporter; portable helpers and
Master validation support Python 3.9+. Public CI uses exported files, stdlib and
the consumer's own read token. It needs no private Tracker credential or checkout.
The raw direct producer and separated `.workflow/tools/tracker_ci_evidence.py`
ship the same canonical module for the selected engine. The scripts paths in
separated projects remain compatible forwarders. Helper bytes are UTF-8/LF and
narrow `.gitattributes` rules preserve them through Windows checkout; local
attribute conflicts follow normal three-way conflict handling without writes.

A module-byte change also changes its native producer identity. In a reviewed
consumer upgrade, refresh each actual producer copy and its `producer_files` Git
blob pin; review the workflow blob pin when that workflow changes. This native
Git blob identity is distinct from the export manifest's SHA256. Master preserves
explicit policy choices; structural validation alone cannot certify an old
producer pin against new helper bytes. Retain old receipts with their original
identity and obtain applicable fresh native proof instead of relabelling them.

## Maintainer refresh

From this source, with a clean official engine at an exact immutable revision:

```sh
python3 scripts/update_tracker_contract.py --tracker-root /path/to/tracker \
  --revision FULL_ENGINE_SHA --engine-python /path/to/python311
```

Preview first, then repeat with `--apply`. The command runs both real exports,
checks their byte-identical static manifests and actual file hashes, and copies
all canonical validator modules, generated helpers and offline proof artifacts.
`tests/fixtures/portable-contract/provenance.json` records the exact engine/source
paths and hashes of the canonical runner, native context data, synthetic
accounting snapshot and, when execution4 is advertised, the four direct task/capture
Stage-on/off rows. This pin also requires the four canonical one-policy package
selection rows; fixture provenance cannot remove this part of the proof closure. Those files
contain no live state, credentials or consumer captures. Do not edit generated
copies by hand. Refreshing artifacts grants no release or acceptance.

## Verification and publication

Public source CI verifies actual artifacts and runs all eight canonical offline
native cases: raw/separated layouts across source, frozen integration, main and
promotion. The real CLI runs on Python 3.9, with both separated entry points,
strict same-repository GET fixtures, no private engine import and no consumer
writes. The isolated bootstrap freezes only the fixture clock; actual native
workflow/job/attempt/producer/content validation still executes. Promotion and
other unsupported reuse contexts retain fresh checks.
The same source-owned runner executes the real accounting CLI against wholly
synthetic saved GETs in raw and separated layouts, including both separated paths.
It proves the twenty-row/twelve-interval, 212-versus-112 rounded-estimate shape,
unknown billing and no consumer writes without native requests or an engine.
The same verified runner executes the four exact direct rows in raw/separated
layouts on Python3.9, including held admission, released receipts and meaningful
refusals. These engine-owned saved rows are distinct from actual Master-generated
configurations and the separate engine-backed generated-config lifecycle proof.
The canonical selection runner likewise uses the real receipt CLI, validators and
CAS payload builder in all three raw/separated entry locations. Its four saved
v2/v3 cases cover context, completion, retry and completion retaining retry. Each
replays pending package, one exact synthetic receipt write, recorded idempotence
and genuinely owned-adopted state. Only fixture transport and clock are replaced;
there is no engine import, authenticated transport or consumer write. This proves
the portable boundary, not a live package, policy activation or rollback.

The final source-pair gate is this single maintained harness:

```sh
python3 tests/verify_completion_pair.py --master /path/to/master \
  --tracker /path/to/released-tracker --old-master /path/to/old-master \
  --old-tracker /path/to/old-tracker --python39 /path/to/python39 \
  --output /path/to/evidence.json --bounded --portable-contract \
  --selected-instructions --retry-contract --direct-contract \
  --selection-delivery-contract --require-pinned
```

It records the head, tree, origin and dirty status of all four current/old source
inputs. Final admission requires every input to be clean and official and the old
Master compatibility pin to match the actual old engine. It verifies six
representative outputs and both separated import/CLI paths, exercises the eight
native fixture cases against exact engine-owned artifacts, and performs four
genuine old-source upgrades. Explicit retry selection covers both supported limits
and retains absence on the other representative outputs and one genuine upgrade.
With `--direct-contract`, it also validates nine actual modern Master output/
guide/provider combinations, the eight canonical direct layout replays, and four
explicit modern conversions from genuine legacy/v1/v2/v3 old-source templates.
With `--selection-delivery-contract`, it requires all eight canonical selection
layout replays and their package/recorded/adopted phases. This flag requires
`--portable-contract` and cannot be combined with `--upgrades-only`.
Previews preserve bytes/mtimes/modes; actual local system/runtime and installer
controls survive; repeat apply is unchanged. The final native pair uses this full
route and never `--upgrades-only`.
It also commits real CI-evidence, retry-rule and route-rule changes in isolated clones and
proves that matching new identity metadata cannot make the
stale trusted contract pass. Local knowledge, controls, preview no-write behavior
and idempotence remain checked. A provisional dirty/overridden pair is disclosed
as preparation and cannot satisfy final acceptance.

Tracker's source-conformance gate retains real self-exports/runtime checks and
must show that the previous trusted Master rejects a changed source contract.
A positive provisional public peer check is separate and never rewrites an old
trust record. The final native pair gate takes the exact public Master
candidate and released Tracker revision, invokes this harness and records the
actual result. It adds no reciprocal runtime pin or cross-repository write secret.
Successful public checks alone do not replace this final private-engine pair gate.

Publish the reviewed Tracker merge after actual-main checks, refresh/pin that
released engine in Master, then independently review and verify the clean final
pair and Master native/actual-main checks before publication. Existing consumer
pins, policies, receipts, capacities and targets remain under their adopted rules;
source publication performs no fleet migration, service activation or skill
installation. See [versioning](versioning.md) and [verification](verification.md).
