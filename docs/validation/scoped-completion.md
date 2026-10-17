# Scoped-completion source pair

MR-45 selects Tracker merge `95079e71d454c8a6e2216b76ae86c0f87d522897`, whose tree
and parents exactly preserve independently reviewed PR149. Its final source
checks passed 1076 Python tests, syntax and all 15 canonical browser scripts.
[TT-142](https://github.com/MojoTheApe/task-tracker/issues/142) retains the complete
independent report, findings/fixes and actual-main/release/reader/pilot boundaries.
No consumer has been activated by this source change.

Master's eight focused regressions and complete 117-test suite pass on Python3.9.
The actual candidate pair was also exercised across 144 exports and 72 isolated
Python3.9 portable assessments, plus four upgrades from genuine old source using
no-write previews, retained system/runtime/installer content and idempotence. The
candidate record identifies its uncommitted Master/override honestly; final clean
pin evidence is recorded on [MR-45](https://github.com/MojoTheApe/master-repo/issues/45)
before integration, separately from immutable publication and installed behavior.

Reproduce the actual pair from clean official checkouts, using Python3.11+ to run
the exporter and a real Python3.9 interpreter to check the portable closure:

```sh
python3.12 tests/verify_completion_pair.py \
  --master /path/to/clean-selected-master \
  --tracker /path/to/exact-compatible-tracker \
  --old-master /path/to/clean-recorded-old-master \
  --old-tracker /path/to/its-exact-compatible-tracker \
  --python39 /path/to/python3.9 --require-pinned \
  --output /tmp/completion-pair.json
```

The helper uses temporary synthetic consumers and invokes real selected exporters;
it makes no service, registry, Issue or consumer-state mutation. `--require-pinned`
rejects dirty Master content or a selected engine different from compatibility.json.
Without that flag, explicitly identified candidate-pair checks are possible, but
their JSON records the override and cannot establish final immutable-pin acceptance.

All six delivery profiles, Stage on/off, legacy/v1/v2/v3 and optional adopted task
context are covered with completion selected and absent. Exact guide/helper bytes,
changed/unknown/missing-receipt scope and ordinary unmerged pending assessment are
checked without importing the engine from the portable Python3.9 process. The old
source pair is used to create a genuine prior template, rather than inventing one.
