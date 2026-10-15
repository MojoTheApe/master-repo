# One authorized integration through verified completion

This is the shared contract; each project owns its actual delivery mechanism.
Adopt through an exact reviewed standard/Tracker pin and project runbook. It does
not migrate consumers, publish services, grant credentials or execute deployment.

## Authorization and responsibility

An explicit owner request to integrate and deliver a defined task set includes
independent combined review, required checks, its admitted main merge, maintained
project delivery, verification and completion receipt. Continue without asking for
another routine approval after main. Preserve any explicitly separate local
approval boundary or concrete missing access. A development request alone ends at
Approved in execution v2/v3; source approval does not authorize integration.

This is the same authorization whether stage is enabled or disabled. With stage,
verify the exact configured stage candidate before unchanged main promotion. With
stage disabled, a reserved independently reviewed frozen batch enters main directly;
ordinary sources remain approval-only and all source/combined CI gates stay required.
Use the exact pinned Tracker guide for commands and current admission. For a
compatible batch that needs runtime/package delivery, freeze the existing owner
authorization with `batch begin --deliver --delivery-workflow PATH --delivery-job
EXACT_NAME`, selecting the actual maintained trusted project workflow/job. These
values describe the real adapter; they do not create one. Omitting `--deliver`
retains ordinary integration behavior; a later main push cannot add permission.

The running Coordinator follows through until success or a concrete blocker.
For tooling/local and explicitly source-only profiles, the existing admitted
reviewed-merge completion rule is the final result. For package, VPS and ordinary
n8n projects, merge hands off unfinished delivery to the project mechanism.

## Project-owned adapter

Use `delivery.procedure`, `authorization`, `rollback` and `backup` to reference the
maintained runtime procedure. It must specify these actual executable steps:

1. Persist the approved task set, source PRs, actual main merge revision/tree,
   configured target, completion rule and durable run identifier before delivery. The supported batch request retains the real requester and
   native verification producer as well as exact batch/policy/target membership.
   Bind a package to its immutable artifact/release identity; VPS to deployed
   revision; n8n to published workflow revision and intended activation state.
2. Trigger the existing project release/deploy mechanism after successful main
   checks, carrying that exact identity. A branch label or floating main lookup
   must not silently replace the selected candidate with newer content. Never
   execute unreviewed PR code with production credentials.
3. Serialize mutations per target and make repeated requests idempotent. Inspect
   persisted state before retry. A stale run cannot overwrite a newer admitted
   release. Do not blindly cancel an in-flight install/deploy; use supported drain,
   rollback or safe supersession with recorded consequences.
4. Verify the configured target and the task's actual acceptance criteria. Package
   publication alone is insufficient when installation/update checks are required;
   a healthy VPS endpoint alone does not prove required behavior; n8n import alone
   does not prove publication or the intended workflow result. Preserve stronger
   local test, data-protection and recovery controls.
5. Record successful delivery using the compatible Tracker's `record-delivery`
   against the actual merged tasks/revision, current policy and configured target,
   with durable report/run/artifact references. Read back completion. Close only
   fully satisfied tasks; partial scope and failed/missing verification remain open.

Prefer durable CI for release/deploy work so a chat ending does not abandon the
handoff. Its least-privilege trusted workflow must consume the exact admitted merge
and task set, retain attempt logs, surface failures and record completion only after
verification. A project's intentional external/manual runtime handoff must remain
explicit. The shared scaffold supplies instructions and settings; it creates no
universal deployer, executable workflow or background agent. Test the real adapter
in the consumer repository before claiming automatic delivery is active.

## Portable native receipt adapter

The compatible Tracker exports `scripts/tracker_delivery_receipt.py`, backed by
`.workflow/tools/tracker_delivery_receipt.py` in a separated project. It needs the
same repository token with the exact Actions/Issues read and contents-write rights
documented by the pinned engine, plus portable policy helpers; no private engine
read token or clone is required. Projects needing batch delivery retain both
recorder paths. The actual project producer uses these supported operations:

```sh
python scripts/tracker_delivery_receipt.py resolve --repository OWNER/REPO \
  --merge-sha MAIN_MERGE_SHA --ci-run SUCCESSFUL_MAIN_CI_RUN --output request.json
python scripts/tracker_delivery_receipt.py record --request request.json \
  --evidence delivery.json --verification-run RUN_ID --verification-job JOB_ID --apply
```

Replace the example identities with the actual run and project. Resolve verifies
successful official main CI, archived authorized batch, exact task set and real
per-task Merged handoff. Exit 75 means a retained handoff/maintenance is temporarily
pending; use bounded retry or explicit resumption, not fabricated merge proof.
After actual target acceptance, the exact configured trusted native workflow/job
emits one `TRACKER_DELIVERY_RECEIPT <compact JSON>` in its real job log matching
the passed delivery-verification evidence. The recorder checks official producer,
revision, target, current policy/request and exact log evidence before CAS writes.
An uploaded manifest, green build, arbitrary workflow or main push cannot create
authorization or acceptance. The project owns release/deploy and real checks.

## Failure and resumption

Persist pending/running/succeeded/failed state with exact task set, candidate,
target, attempt/run identity, evidence and next action using the project's maintained
storage. Distinguish a failed deploy, failed verification and failed receipt write.
Do not create a new release/version or repeat installation just because a receipt
write failed. Revalidate the original evidence and retry only the missing step;
reuse a valid successful receipt idempotently. A change to task set, content, target
or policy requires the supported reconciliation and fresh relevant proof.

Report a concrete blocker and durable recovery pointer once when action is needed.
Missing credentials, an explicit external approval, failed acceptance or incompatible
runtime state is a blocker; a planned extra owner confirmation after main is not.
A green build, closed PR/Issue or recurring sync cannot substitute for delivery.
No pending/failed delivery may count as complete in dependencies or release readiness.
A maintainer can resume from the report without reconstructing state from chat.
A pending authorized delivery serializes later batches to the same target; source
implementation/review can continue. If the owner explicitly abandons a failed
request, use the pinned `batch delivery-cancel` procedure with its real retained
Coordinator/claim and decision report. Cancellation retains unfinished task/receipt
state and history, allowing a later reviewed fix batch; it never declares delivery.

## Ownership and rollout

Master owns this policy, initializer, templates and navigation skill. Tracker owns
admission, durable task state and delivery receipt semantics. The project owns
installers, VPS/n8n commands, trusted CI, secrets, verification and rollback. Shared
instructions cannot claim that these mechanisms exist. Master's own tooling tasks
use its [agent completion procedure](repository/DELIVERY.md); source-only semantics
remain source-only. Existing consumers adopt separately through reviewed pins,
compatible published writers and any required idle state/policy migration.

First consumer: [ACL parent task 1923](https://github.com/MojoTheApe/adopy-campaing-launcher/issues/923)
coordinates the separate [source task 1924](https://github.com/MojoTheApe/adopy-campaing-launcher/issues/924)
through its existing Stage route before authorized live activation. Other consumers
remain pinned and keep their adopted route.
