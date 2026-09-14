# Shared delivery standard

## What is shared

Each project retains its existing tracker, test suite, authorization rules and
deployment implementation. This standard supplies common release guarantees and
a description of how the project meets them. It is not a universal installer.

Ordinary software defaults to one `main` integration branch and short-lived
ticket branches. A platform-specific branch mapping, including native n8n source
control, can differ when documented. Preserve the same review and approval gates.

## Ticket and PR lifecycle

| Event | Logical status and evidence |
| --- | --- |
| Accepted task | TODO; real ticket with behavior and acceptance criteria |
| Work starts | IN PROGRESS; ticket-linked branch, subject to the existing tracker |
| PR ready for review | REVIEW; PR links to the ticket, ticket links to the PR |
| Changes requested | IN PROGRESS while editing; return to REVIEW when ready |
| CI or deployment fails | Unfinished; record the failed step, never claim success |
| PR closed without merge | TODO or cancelled per tracker; never automatically DONE |
| Merge | Record included commit/PR; deployment-dependent work remains REVIEW |
| Required delivery verified | DONE for the included, completed tickets |

Map these logical statuses onto the project's current tracker; do not rename its
states or add another tracker unnecessarily. Its existing automation remains the
authority. Repeated or out-of-order events must not regress completed work or
close tickets for a different release. Parent tickets stay open for partial work.

For deployment-dependent work, avoid GitHub auto-close keywords at merge. Use an
explicit ticket reference. This repository uses `Tracker issues: #1`; consumers
retain their own validated convention (for example ReactForge's `RF-N` IDs).
CI should validate real ticket linkage through the existing tracker integration.
Where a transition is manual, document the responsible role and command instead
of claiming it is automated.

Completion depends on delivery type: a server release is verified on production;
a local app has a published stable package and the agreed installation check;
docs/tooling without deployment may complete after review, checks and merge.

## Candidate, approval and release

1. Verify the actual merged source revision, then build/assemble one candidate.
2. Identify source commit and immutable artifact hashes/image digests. Include
   independently versioned components, dependencies and schema compatibility.
3. Deploy the candidate to staging or the applicable test/pilot environment.
4. Record test results against that candidate and environment.
5. Obtain authorized approval of that exact candidate before production delivery.
6. Deliver the same approved content with destination-specific configuration.
   Main advancing must not silently change the approved candidate.
7. Verify installed/published identity and the required functional behavior.
8. Record the release and its included PRs/tickets; complete only verified work.

Serialize deliveries to each target. An old job must not replace a newer version;
do not cancel a live deployment transaction merely because another commit arrived.
Approval identifies a candidate and target, not an arbitrary future branch head.
Use existing authorization when it covers the action; finish independent
preparation before requesting any missing production approval.

Use GitHub environment approvals where supported by the actual plan. Otherwise
use the project's explicit authorized promotion mechanism and retain its receipt.
A manual button alone is not proof of restricted approval. Document enforcement
gaps; never claim branch protection or reviewer approval that is not configured.

## State, rollback and retention

Code/artifact history, operational data, secrets and deployment receipts have
different homes and retention needs. Git is not a database or credential backup.
Backups need a verified recovery process and appropriate off-device protection.

Keep current stage/prod, in-flight candidates and compatible selected rollback
releases. Also protect anything referenced by services, previews, mounts or
required evidence. A fixed folder count is not a safe deletion criterion.
Default cleanup is an exact dry-run inventory. Destructive cleanup follows the
project's authorized policy and rechecks references before removal.

Code rollback must respect current data/schema compatibility. It must not silently
overwrite new business data or pretend to reverse external side effects.

## Boundaries and measurements

PR checks must not run arbitrary PR code on production-connected runners or expose
production credentials. A deployment runner executes trusted, approved delivery
jobs with scoped access. Hosting-specific safeguards belong to the profile.

Keep necessary native admission and independent verification. Staging evidence
cannot simply be relabelled as production proof. In ReactForge, preserve existing
hotfix/update semantics and qualifications; redesign is a deferred task.

Measure build, transfer, preparation, backup, tests, activation, verification and
recovery separately. Report total elapsed time and gaps without calling every gap
human wait. A descriptor and a successful merge are not runtime evidence.
