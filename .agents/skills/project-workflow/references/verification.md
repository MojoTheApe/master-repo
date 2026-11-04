# Efficient verification

Read the project's actual commands and required check names, not a generic test
list. Where present in the pinned Master, `docs/verification.md` supplies the common
policy and `docs/verification-submission.md` describes fast/full plans and CI events.
Older pins without either document keep their local instructions and required
checks; do not update a pin merely to obtain a missing reference. Compatible prose
clarifications may be reviewed locally without pin/helper changes. Keep product
platforms, installers, exact admission rules and runtime acceptance local.

## Choose and reuse checks

- During implementation run the cheapest meaningful checks for the changed
  behavior. Group related fixes into a meaningful ready submission on the existing
  branch; keep useful intermediate feedback and normal review corrections.
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
- Use one supported final admission check where it already includes linkage or
  other checks; keep early feedback and distinct required delivery actions.
- Avoid redundant agent-requested runs. GitHub events still select automatic
  checks and cancellation. Preserve required integration/main/release evidence.
  Use supported cancellation only for superseded work where the project allows it.
  Trigger/concurrency/settings changes need explicit task scope; existing
  authorization is sufficient, without a routine new approval.

Use meaningful tests for actual risks. Do not add a test merely to mirror a
reversible prose edit. Existing required repository checks still apply.

## Submit to review in the supported order

Keep unfinished work in a draft PR. Finish the candidate, its task references and
applicable author checks before requesting review. During returned author fixes,
first use the native return/reclaim procedure; keep the existing PR draft while
implementation is incomplete where the adopted route permits it. Do not steal a
claim, edit another author's work or change task phase merely to make CI green.

Read the exact pinned handoff prerequisites before choosing the order:

- Legacy routes that permit an explicit Review transition: record the actual
  completed implementation and set Review through the supported command, read it
  back, then mark the PR ready.
- Execution-owned routes: use the actual Worker identity/claim and native handoff.
  If it requires an open non-draft PR, prepare the complete handoff first, mark the
  PR ready and invoke handoff immediately. Never substitute a label edit or insist
  on draft handoff when that engine rejects it.
- A project with selected ready-PR synchronization follows that maintained
  reconciler. Observe its result; do not run a competing writer or assume that the
  GitHub event already completed the task transition.

Before dispatching the independent Reviewer, read back the linked task's real
Review state, exact PR head and any required durable handoff/review reservation.
Ready, Review and review ownership are distinct facts. An uncertain handoff needs
inspection and the supported same-owner recovery, not another blind write.

Some existing routes necessarily expose a short ready-before-handoff window.
Their linkage check may fail before the transition completes. A later label
change alone may not retrigger that GitHub job. Diagnose its actual log: if the
only failure was the task phase and the completed native handoff now verifies,
use the adopted retry procedure for the failed linkage job only. Keep the same
source and valid successful source checks; do not create an empty commit, toggle
draft/ready repeatedly or launch a full suite to refresh metadata. A still active,
blocked, mislinked or incompletely handed-off task is not eligible for that retry.
This guidance changes no engine, trigger, retry budget or merge gate and does not
promise to eliminate the inherent event race on older consumers.

## Observe ordinary work

Use ordinary necessary tasks and existing Issue/PR/run links. Briefly note an
unexpected repeat, confusing transition or manual expensive launch with its known
reason or uncertainty; do not create a per-job register, new blocker or form.
Do not create extra sample tasks, paid demonstrations, automation or scheduled
audits merely to prove a prose edit. Separately requested audits or configuration
work follow their existing authorization and retain required checks.

Compare similar workloads only: first feedback, elapsed cycle and platform/job
minutes are different measures; unavailable billing stays unknown. Updated prose
establishes guidance, not savings.

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
