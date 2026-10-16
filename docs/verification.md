# Efficient verification

For the executable shared recipe, explicit policy mirroring and missing-job
adapter, read [CI result reuse](ci-reuse.md) and the pinned engine's CI_REUSE.md.
Use one supported final `check-merge`: it already validates linkage. Keep early
link feedback; do not immediately repeat it solely as a second admission step.

This is the shared verification policy. Product commands, supported platforms and
runtime acceptance remain project-owned. Adopt it through a reviewed standard
upgrade; it does not change an existing project's required checks or engine pin.

## Select checks by the changed risk

Use the cheapest meaningful check that can detect the changed behavior. Separate
fast source feedback, combined-candidate integration and real delivery acceptance.
Run applicable checks before admission; a quick source check is not full release
proof. Aim for first useful feedback within 5–10 minutes, measured against the
actual workload; this is an improvement target, not a universal timeout.

| Delivery profile | Source and integration focus | Delivery acceptance |
| --- | --- | --- |
| `tooling` / `local` | Changed logic, CLI/UI, links/configuration and supported runtimes | Admitted reviewed merge; manual pull stays manual |
| `vps` | Logic/API/UI, isolated integration and data compatibility | Maintained deploy, configured behavior checks and recovery |
| `n8n` | Workflow logic, SDK/schema evidence, DEV isolation and integration | Authorized workflow publication and production verification |
| `n8n-source` | Relevant source checks; declared CI or DEV stage target | Reviewed source merge; runtime handoff stays separate |
| `package` | Logic/UI, supported OS/runtime matrix and combined build | Immutable package, actual install/update/recovery |

Choose actual commands during onboarding and retain their scope and exact CI job
names in `delivery.json` and the matching Tracker policy. Validation never executes
descriptor commands. Unknown/mixed changes keep full applicable verification.
Instruction-only selection requires the adopted complete-diff classifier, not
labels, titles or guessed path lists.

Prune or move a test only when its risk is preserved by another meaningful check;
test counts alone do not establish redundancy. Preserve isolated synthetic data.
Use observable events for asynchronous waits and controlled clocks when time is
the behavior. Bound owned child processes, preserving cleanup/diagnostics; an
outer CI timeout alone may not resolve an installer or runner hang.

## Reuse proven results, not green labels

Keep existing bounded reuse supported by the adopted project. The optional
[Tracker companion](tracker-companion.md) supplies a narrowly supported native CI
protocol; it is not enabled by this guidance or exported defaults. Expanding reuse
requires a maintained collector proving all relevant inputs:

- Repository and actual tested content from Git or trusted producer evidence.
- Trusted immutable workflow/check producer and profile, required jobs/platforms,
  actual successful attempts and retained provenance.
- Compatible resolved dependencies, toolchain, runner/OS and relevant external
  fixture/configuration/build inputs. Include Git metadata/version derivation when
  it affects behavior or package identity; a tree hash is not the whole environment.
- Current scope/base/composition/policy admission and a link to the actual source
  PR, retained approval or integration candidate. Changed review context still
  needs fresh relevant review even when tests can be reused.

Reuse covered jobs; run missing ones. A 3.13 source run does not cover 3.11.
Different individual source trees do not prove a combined candidate. Even an
identical one-source batch requires independent composition review. An unmerged
Approved source supplies evidence only when the adopted collector explicitly
validates its actual approval and tested combined content. Never bypass a current
merged-PR-only collector or invent that broader support.

Missing/partial/stale/untrusted evidence runs the affected full checks. Skipped or
cancelled jobs do not prove untested behavior. Stage and production/package
acceptance retain their own target/freshness rules; CI cannot be relabeled as
delivery. Preserve explicit manual/release full-verification rules. A review-limit
change alone does not require revalidating unrelated historical delivery receipts.

## Avoid duplicate work and measure results

Run source suites on PR content events and actual integration-branch pushes. Keep
linkage/metadata checks on body edits and ready handoff. Cancel superseded runs of
the same PR, but preserve each admitted stage/main push's evidence. Dependency
caches accelerate setup; they are not test-result evidence.

Implementers self-check the relevant candidate. Reviewers inspect those results
and add checks for findings, missing scope or unresolved concerns. Refresh evidence
when a dependent input changes, and current admission immediately before merge.
Retry supported failed jobs of an unchanged candidate instead of repeating passing
ones without cause. Diagnose recurring infrastructure/test failures; retries must
not conceal a product defect.

Measure first-feedback and full-cycle time separately from summed job minutes.
Retain slow-test/setup timings and retry causes. Balance shards by measured cost
while preserving deterministic complete platform membership. Compare similar
candidates before/after: parallel jobs and review cannot be summed as elapsed time.

Sources: [DORA](https://dora.dev/capabilities/test-automation/),
[risk-based testing](https://bmad-code-org.github.io/bmad-method-test-architecture-enterprise/explanation/risk-based-testing/),
[release engineering](https://sre.google/sre-book/release-engineering/).
