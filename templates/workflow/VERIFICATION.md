# Verification policy

Verify process changes separately from product delivery for every profile.
Instructions and isolated task/workflow tooling need relevant checks and
independent review. Assess complete immutable inputs, including indirect product,
build, install and update effects; a directory or label alone is insufficient.
Testing a build or installer does not authorize publishing an unchanged product.
Split mixed changes and use only the pinned supported completion proof.

__CI_RETRY_GUIDANCE__

For explicitly adopted `workflow.ci_evidence`, read the exact engine's
docs/repository/CI_REUSE.md and the [shared recipe](https://github.com/MojoTheApe/master-repo/blob/__STANDARD_REVISION__/docs/ci-reuse.md).
Plan missing jobs, run them and retain the final native-evidence gate. Collect
successful actual source/integration producers before merge for supported reuse.
One supported `check-merge` includes linkage; use `check-pr` for early feedback,
not an immediately repeated final admission check. Absent-policy/old pins keep
their actual commands and checks.

Follow the [shared verification policy](https://github.com/MojoTheApe/master-repo/blob/__STANDARD_REVISION__/docs/verification.md)
at this project's exact standard pin. `delivery.json` defines actual product
commands/required CI names; retain matching Tracker settings, runtime checks and
local exceptions. Separate fast source feedback, combined-candidate integration
and actual delivery acceptance. Select by changed risk, not a desired green result.

Keep a project-owned fast/full plan with actual commands, platforms and distinct
truthful result names. Fast feedback is intermediate; ready handoff and final
admission require all applicable full coverage. Unknown/mixed changes keep full
checks. Group related corrections on the owned task branch, preserving useful
early feedback and checkpoints without a fixed waiting interval. Record the real
reason for new heavy work and its candidate/run; inferred history stays inferred.
Follow the exact pinned [submission rules](https://github.com/MojoTheApe/master-repo/blob/__STANDARD_REVISION__/docs/verification-submission.md).

Preserve the adopted collector's existing bounded reuse rules. Expand context
proof only through reviewed compatible support/adoption; the common policy alone
cannot add an unsupported environment signature. Run missing jobs/platforms.
Preserve independent combined review, exact stage target and package/production
proof. Inspect passing unchanged evidence before rerunning; add checks for changed
inputs, findings, missing scope or unresolved concerns. Cancel obsolete PR runs,
preserve admitted integration push evidence and measure costs before pruning tests.
Keep metadata/linkage concurrency separate from code suites; cancel only
superseded work for that same PR. A fast success or instruction-only skip cannot
replace a full result. Partial retry needs the adopted collector's actual original
job/dependent proof; otherwise use a supported bounded fresh attempt or stop.

For an authorized standard upgrade, use the
[coordinated procedure](https://github.com/MojoTheApe/master-repo/blob/__STANDARD_REVISION__/docs/workflow-upgrades.md).
Only the exact compatible Tracker guide supplies commands. A newer standard/skill
cannot activate an unimplemented maintenance or evidence collector.

For explicit native CI policy, use generated `scripts/tracker_ci_gate.py plan|gate`
on CI with its same-repository read token. This portable route needs no private
engine checkout. Full task_tracker.py commands and pre-merge CAS collection belong
to author environments with authenticated access to the exact pinned engine.
