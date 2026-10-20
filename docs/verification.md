# Efficient verification

This is shared verification guidance. Product commands, supported platforms and
runtime acceptance remain project-owned. Compatible prose clarifications can be
reviewed in local instructions without upgrading a standard pin or helper. They
cannot change adopted required checks, proof capabilities or delivery authority;
a technical upgrade follows the separate existing upgrade procedure.

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

Apply [process/product separation](process-product-separation.md) before inheriting
a product release from the repository profile. Process verification remains
required; testing a build or installer does not itself authorize its publication.
Product input changes retain the relevant checks and actual product delivery.

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

## Avoid agent-controlled repetition

Implementers group related fixes into a meaningful ready candidate on the existing
task branch. Keep useful intermediate feedback; this is not a one-push limit or
a waiting period. Reviewers inspect valid existing results before adding checks
for findings, missing scope, changed inputs or unresolved concerns. A new agent,
session or review comment alone does not reset that evidence. Refresh current
review/admission as required without discarding tests that still prove their scope.

Use one supported final admission check where it already includes linkage or other
checks. Keep useful early feedback and separately required delivery operations.
After an uncertain write or dispatch, inspect the actual result before repeating it.

Diagnose failures before retrying. For a confirmed temporary problem, make one
justified repeat of the needed part; another failure needs diagnosis. Preserve
stricter adopted retry limits. Use native failed-job reruns only when the project's
final check accounts for original successful jobs and dependencies. Otherwise use
its supported complete run and explain the missing coverage.

## Automatic runs and configuration changes

Existing GitHub events select automatic runs and their cancellation. An agent can
avoid duplicate manual launches, but written guidance does not suppress those
automatic runs. Leave required native source, integration/main and release checks
intact; use existing supported cancellation only for superseded work where allowed.

Trigger separation, concurrency, caches, sharding and other workflow/settings
optimizations need their own explicit task scope. Existing authorization for that
work is sufficient; no routine new approval is required. Do not implement them
merely to follow this prose. Dependency caches provide no test-result evidence.

## Observe ordinary work

Use existing Issue/PR comments and run links for brief observations of an unexpected
repeat, a confusing transition or a manually requested expensive run. State the
known reason or uncertainty and relevant candidate; no per-job register, new form,
blocker or tracking service is needed. A reason does not authorize missing coverage.

Use ordinary necessary work and existing history. Do not create extra sample
tasks, paid demonstrations, automation or a scheduled audit merely to prove a
prose edit. Separately requested audits or CI work proceed within their existing
authorization. Separate first feedback and full-cycle time from summed platform/job
minutes; compare suitable workloads and keep unavailable billing explicit.
Record instructions as ready, not savings as proven.

Sources: [DORA](https://dora.dev/capabilities/test-automation/),
[risk-based testing](https://bmad-code-org.github.io/bmad-method-test-architecture-enterprise/explanation/risk-based-testing/),
[release engineering](https://sre.google/sre-book/release-engineering/).
