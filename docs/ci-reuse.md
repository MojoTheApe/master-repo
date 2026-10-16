# Shared CI result reuse

MR-32 / TT-140 implement WFO-05–08. Product commands and actual delivery acceptance
remain project-owned; consumer-specific collectors are not copied into the standard.

## Adoption and proof

Explicitly mirror `workflow.ci_evidence` in delivery.json with
`ci_evidence_policy` in tracker/config.json. `init --ci-evidence-policy FILE`
selects a reviewed policy; exports/upgrades never inherit one implicitly.
Read the exact pinned engine's CI_REUSE.md, exported to docs/repository, before
configuring jobs. Validation never executes consumer-owned code.

Protocol 1 retains source/integration semantics. Explicit protocol 2 additionally
supports conditional fixed jobs and retained evidence for the actual main merge.
Its exact direct producer binds the native Git ref in the timestamped job log,
so GitHub clearing a merged run’s PR list does not discard genuine original proof.
Reuse requires successful native jobs/attempts, reviewed immutable workflow,
producer and container, exact toolchain and resolved Git-bound inputs, explicit
lifetime and metadata sensitivity. Unsupported platforms, installers, mutable
dependencies and external acceptance stay fresh. Tree equality cannot prove a
metadata-sensitive build.

## CI runtime and author client

Generated `scripts/tracker_ci_gate.py plan|gate` uses only exported portable
helpers, Python/gh and the current repository's read token. It never clones the
private shared engine or writes Tracker state. The actual maintained state ref
is resolved and read by immutable commit; invalid state/transport fails closed.
The full `scripts/task_tracker.py ci-evidence ...` commands in the pinned engine
guide are for author environments with authenticated access to that exact engine.
Use the portable CI entry point in fresh runners; no cross-repository secret or
prewarmed engine cache is required. Retain actual successful producers before
merge through the full author's supported CAS collection command.

## Candidate recipe

The maintained [JSON workflow example](../templates/workflow/ci-reuse.example.json.yml)
shows conditional jobs and an always-running native aggregate. It is deliberately
not enabled or copied as a ready product workflow: fill real commands, reviewed
digest-pinned environment and policy blobs first. Preserve actual platform jobs;
make `Verification` required and do not retain skippable product names as required
success contexts. Review bootstrap/adoption under the old working checks.

1. `ci-evidence plan` for the actual candidate lists covered native producers and
   every missing job. New/changed candidates normally run all checks.
2. Run missing jobs under their real environments, preserving product commands
   and exact check names. A failed new result cannot be hidden by older success.
3. Run `ci-evidence gate` after all jobs, including failures/skips. It revalidates
   evidence and actual current native outcomes. Missing, failed, cancelled or
   ambiguous coverage cannot become success. Make the aggregate a required check
   through the project's reviewed CI/config upgrade, preserving existing controls.
4. After successful source/integration CI, collect the actual native run into
   durable Tracker evidence before merge. Every reuse revalidates the producer;
   uploaded manifests and cache hits grant no coverage.
5. Main may use retained protocol-2 proof only for its exact admitted PR merge and
   identical candidate content/context. Missing proof runs fresh. Preserve
   independent combined review and combined-candidate coverage; different source
   trees cannot be combined to prove the integrated result.

Refresh scope, composition and admission. Supported `check-merge` already includes
linkage; immediately repeating `check-pr` adds no admission proof. Keep the latter
for early feedback and old pins that require it. Reviewers inspect author/CI
evidence and add checks for findings, missing coverage and uncertainty.

PR body edits run metadata/linkage checks without repeating code suites. Separate
their concurrency groups so edits cannot cancel pending code validation. Cancel
superseded candidates within a PR; retain every integration/main push.

## Measurement and delivery

Measure comparable first feedback, wall-clock cycle, native job seconds,
covered/missing names and retry reasons. Label synthetic/local measurements;
parallel job cost is not wall time. Unsupported cases can have zero savings.
Do not claim fleet savings before consumer adoption and observation. See the
[measured validation report](validation/wfo-05-08.md) for the isolated native case
and the cost of checking real proof; short checks can be cheaper to rerun.

`scripts/measure_verification.py` accepts fresh and verified-reuse JSON argv
commands, alternates their order, and reports repeated local source/main feedback
and cycle timings. It never interprets a fast command as proof, never labels local
process time as native job billing, and produces no valid result after a failed
or timed-out command. Record the actual proof fixture/native context separately.

Reuse never publishes a package, verifies installation/VPS behavior, or publishes
an n8n workflow. Preserve actual delivery, authorization, target/revision binding,
recovery and unfinished delivery state.

Publish reviewed Tracker first, pin its merged revision, then publish Master after
paired validation and actual-main checks. Consumers retain their adopted pins.
Compatible writers/projection and owned activation precede live use of new state
protocols. Releases do not deploy the service, install a global skill or upgrade
existing consumers.
