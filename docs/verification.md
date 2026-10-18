# Efficient verification

This is the shared verification policy. Product commands, supported platforms and
runtime acceptance remain project-owned. Adopt it through a reviewed standard
upgrade; it does not change an existing project's required checks or engine pin.

Use existing checks and GitHub features. This policy requires no new retry service,
collector, scheduler or script. Where a project already selects executable reuse,
read [CI result reuse](ci-reuse.md) and its pinned CI_REUSE.md. A supported final
`check-merge` already validates linkage; retain early link feedback without an
immediate duplicate final check.

Use the [submission plan](verification-submission.md) for distinct project-owned
fast feedback and full ready-candidate checks, grouped corrections, observed
heavy-run reasons and preserved native trigger/cancellation boundaries. Fast
feedback never substitutes for missing full admission coverage.

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

Choose actual commands during onboarding and record their scope and exact CI job
names in the project's local verification instructions. Where the project already
uses `delivery.json` and a matching Tracker policy, keep those settings consistent.
This guidance does not require adding either file. Validation never executes
descriptor commands. Unknown/mixed changes keep full applicable verification.
Use lighter documentation checks only when the actual change cannot affect program,
build or operational behavior and the project's rules support that coverage.
Where a project selects a special instruction-only admission route, its existing
complete-diff classifier still applies; labels or titles cannot select it.

Prune or move a test only when its risk is preserved by another meaningful check;
test counts alone do not establish redundancy. Preserve isolated synthetic data.
Use observable events for asynchronous waits and controlled clocks when time is
the behavior. Bound owned child processes, preserving cleanup/diagnostics; an
outer CI timeout alone may not resolve an installer or runner hang.

## Reuse proven results, not green labels

Keep existing bounded reuse supported by the adopted project. The optional
[Tracker companion](tracker-companion.md) applies only where already selected.
Do not build a new collector to implement this instruction. When judging whether
an available result is suitable, consider the inputs relevant to its coverage:

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

For a confirmed temporary problem, make one justified repeat of the needed part;
another failure needs diagnosis. Preserve any stricter existing retry policy.
If the result of dispatch is unknown, observe the current run before requesting
another one. If the project's final check cannot account for successful original
jobs after a partial rerun, use its supported complete run and explain why.

Keep a short list of concrete waste: duplicate source triggers, unchanged reviewer
reruns, heavy setup before quick failures, or rebuilding an unchanged package.
For each, name the cause, a correction using existing tools, expected benefit and
how to verify it. Existing Actions configuration changes are separate concrete
changes; documenting the rule does not mean the configuration is already fixed.

Measure first-feedback and full-cycle time separately from summed job minutes.
Retain slow-test/setup timings and retry causes. Balance shards by measured cost
while preserving deterministic complete platform membership. Compare similar
candidates before/after: parallel jobs and review cannot be summed as elapsed time.

Use ordinary necessary work and existing history rather than paid demonstration
runs. Keep platform minutes separate and unavailable billing explicit. Estimated
minutes are not an invoice; fewer runs alone do not establish a money saving.
Report instruction readiness separately from measured time or cost improvements.

Sources: [DORA](https://dora.dev/capabilities/test-automation/),
[risk-based testing](https://bmad-code-org.github.io/bmad-method-test-architecture-enterprise/explanation/risk-based-testing/),
[release engineering](https://sre.google/sre-book/release-engineering/).
