# Efficient verification

Read the project's actual commands and required check names, not a generic test
list. The pinned Master's `docs/verification.md` supplies the common policy;
`docs/verification-submission.md` describes fast/full plans and existing CI events.
Keep product platforms, installers and runtime acceptance local.

## Choose and reuse checks

- During implementation run the cheapest meaningful checks for the changed
  behavior. Group related fixes before another expensive run.
- At ready handoff and integration, cover the full applicable project plan.
  Fast feedback is intermediate; unknown or mixed scope keeps full coverage.
- Reviewers inspect existing evidence first. Add checks for a finding, missing
  scope, changed input or unresolved concern; do not rerun every passing test
  merely because a different agent performs the review.
- Reuse successful results only for the content, workflow, dependencies, platform
  and context their existing evidence actually covers. Dependency caches speed
  preparation but are not test results. Source checks do not prove a new combined
  result or delivery.
- Use supported native failed-job reruns when the project's final check can
  account for the original successful jobs and dependencies. Otherwise use the
  existing complete check and explain the missing coverage; do not build a
  collector to avoid one run.
- Diagnose a failure before repeating it. For a confirmed temporary problem,
  make one justified repeat of the needed part; if it fails again, investigate.
  Preserve any stricter already adopted retry rules. An uncertain dispatch needs
  observation before another request; a new session or empty commit is no cure.
- Cancel only your own superseded run where supported, preserving required
  integration/main/release evidence. Separate metadata-only edits from heavy
  source suites using existing settings when that change is in scope.

Use meaningful tests for actual risks. Do not add a test merely to mirror a
reversible prose edit. Existing required repository checks still apply.

## Demonstrate the benefit

Use ordinary necessary work and existing history. Compare similar changes:
first useful feedback, total wait, run count and runner minutes, keeping platforms
separate. Parallel job minutes are not elapsed time. Estimates are not invoices;
unavailable billing stays unknown. Do not schedule paid demonstration runs.

Record each concrete waste, its cause, the available correction and how to check
it. Examples include duplicate PR/push tests, unchanged reviewer reruns, heavy
setup before cheap failures and unnecessary rebuilds. Preserve useful checks.
A documentation update establishes the instruction, not measured savings.

## Existing selected support

Read these references from the project's exact pinned Master/Tracker checkout
only for an operation or mechanism the project actually uses. Do not guess
commands from a different version or activate a policy by editing a flag.

| Selected mechanism | Applicable instructions |
| --- | --- |
| Bounded CI retry | Master's `docs/ci-retry.md`, generated `CI_RETRY.md` and the local Tracker guide |
| Native CI result reuse | Master's `docs/ci-reuse.md` and generated `CI_REUSE.md` |
| Maintenance and CI evidence | Master's `docs/tracker-companion.md`, `docs/workflow-upgrades.md` and Tracker's `docs/MAINTENANCE_AND_CI_EVIDENCE.md` |
| Exported helper or compatibility changes | Master's `docs/portable-contract.md` and its exact paired-source procedure |
| Package policy selection before activation | [Delivery continuation](delivery-continuation.md) and the local selected guide |

Keep original evidence and any held budget/unknown dispatch until the selected
procedure reconciles it. General permission to continue does not supply an
explicit cause-specific grant required by an already adopted retry policy.
Keep private claims and raw sensitive evidence outside public state.

Existing bounded collectors retain their actual supported coverage; this skill
does not expand it or invalidate valid old-pin results by imposing an unsupported
signature. Run missing coverage. Keep separate review of combined changes and
actual target verification.

Instruction-only edits do not change exported helper bytes, provider snapshots
or descriptors. Do not trigger a technical source-pair migration merely to update
prose. A real export/compatibility change still needs its declared verification
and independent review before publication.
