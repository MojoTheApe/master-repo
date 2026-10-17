# Portable Tracker contract

Master owns descriptor/profile validation and common workflow policy. Tracker owns
the executable portable helpers, CI policy validator and their fixed raw/separated
layouts. Master requests `export-template --helper-layout separated` and consumes
the emitted helper bytes unchanged; documentation moves remain Master-owned.
The default standalone export keeps raw `scripts/` implementations.

`compatibility.json` binds the official exact engine, export format 1 and SHA-256
of the source-owned `scripts/vendor/tracker-export-contract.json`. That static
record declares actual capabilities, runtime floors and all nine raw/eighteen
separated helper hashes. The consumer's `tracker/export-contract.json` must equal
the trusted record byte-for-byte. Installed helpers must match its fixed layout.
Missing files, changed bytes, unsafe paths, duplicate keys, unsupported formats
and unsupported selected policy versions fail before transport. Rehashing a
changed consumer cannot establish trust.

Structural CI-policy validation calls only `policy()` in the exact canonical
Tracker module snapshotted at `scripts/vendor/tracker_ci_evidence.py`. Master
verifies those source-owned bytes before execution and never loads a consumer's
validator, searches for a replacement or bootstraps a private engine. Master
descriptor concerns remain separate. No third CI-policy implementation is kept.

Python 3.11+ remains required for the author engine/exporter; portable helpers and
Master validation support Python 3.9+. Public CI uses exported files, stdlib and
the consumer's own read token. It needs no private Tracker credential or checkout.
The raw direct producer and separated `.workflow/tools/tracker_ci_evidence.py`
retain canonical bytes and their existing producer identity. The scripts paths in
separated projects remain compatible forwarders. Helper bytes are UTF-8/LF and
narrow `.gitattributes` rules preserve them through Windows checkout; local
attribute conflicts follow normal three-way conflict handling without writes.

## Maintainer refresh

From this source, with a clean official engine at an exact immutable revision:

```sh
python3 scripts/update_tracker_contract.py --tracker-root /path/to/tracker \
  --revision FULL_ENGINE_SHA --engine-python /path/to/python311
```

Preview first, then repeat with `--apply`. The command runs both real exports,
checks their byte-identical static manifests and actual file hashes, and copies
the whole canonical validator, generated helpers and offline proof artifacts.
`tests/fixtures/portable-contract/provenance.json` records the exact engine/source
paths and hashes of the canonical runner and synthetic native data. Those files
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

The final source-pair gate is this single maintained harness:

```sh
python3 tests/verify_completion_pair.py --master /path/to/master \
  --tracker /path/to/released-tracker --old-master /path/to/old-master \
  --old-tracker /path/to/old-tracker --python39 /path/to/python39 \
  --output /path/to/evidence.json --bounded --portable-contract \
  --selected-instructions --require-pinned
```

It requires clean exact sources and the actual compatibility pin, verifies six
representative outputs and both separated import/CLI paths, exercises the eight
native fixture cases against exact engine-owned artifacts, and performs four
genuine old-source upgrades. It also commits a real canonical rule change in an
isolated clone and proves that matching new identity metadata cannot make the
stale trusted contract pass. Local knowledge, controls, preview no-write behavior
and idempotence remain checked. A provisional dirty/overridden pair is disclosed
as preparation and cannot satisfy final acceptance.

Tracker's source-conformance gate can test an immutable accepted public Master
peer provisionally. Its final native pair gate takes the exact public Master
candidate and released Tracker revision, invokes this harness and records the
actual result. It adds no reciprocal runtime pin or cross-repository write secret.
Successful public checks alone do not replace this final private-engine pair gate.

Publish the reviewed Tracker merge after actual-main checks, refresh/pin that
released engine in Master, then independently review and verify the clean final
pair and Master native/actual-main checks before publication. Existing consumer
pins, policies, receipts, capacities and targets remain under their adopted rules;
source publication performs no fleet migration, service activation or skill
installation. See [versioning](versioning.md) and [verification](verification.md).
