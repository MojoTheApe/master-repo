# Project capacity

Capacity describes durable reservations across the whole project. Task activity
describes what is currently happening. Neither is permission to start work. Read
the project's selected Tracker guide before acquiring, returning or releasing a
claim; its compatible engine owns the executable projection and admission rules.

## Count the selected topology

| Adopted mode | Work | Review | Integration |
| --- | --- | --- | --- |
| Legacy | One shared slot reserved by the current legacy owner. | No additional pool. | No additional pool. |
| Execution v1 | Actual Worker claims against the configured work limit. | One shared source-review/integration lane. | Included in that shared lane. |
| Execution v2 | Actual Worker claims against the configured work limit. | One shared lane, occupied by either a source Reviewer or the current batch Reviewer. | One separate frozen-batch reservation. |
| Execution v3 | Actual Worker claims against the configured work limit. | Source-review claims against the configured source-review limit. | One separate frozen-batch reservation; its integration Reviewer is a subrole, not an extra source-review slot. |

Show occupied/limit and arithmetic free capacity visibly for each actual pool.
A review queue is waiting work, with a separate count and no invented capacity
denominator. A four-task batch occupies one integration slot and has four members.
Approved tasks and intake selection do not each reserve another integration slot.
Host agent availability is separate from every project's adopted limits.

A held record counts throughout its supported lifetime, including a pending
handoff, return, fix or uncertain write. A returning Reviewer can retain a lane
while an author holds a genuine implementation claim for the same task: those
are two different pools, each occupied once. Do not count historical batch
Reviewers, completed claims, activity aliases, labels or elapsed timers as extra
reservations. Only the supported owned transition releases actual capacity;
apparent inactivity does not establish abandonment.

## Separate free capacity from admission

For a consistent known pool, free is its limit minus occupied. A value such as
work2/5, free3 describes observed reservations; it does not establish task
freshness, dependencies, compatible policy, review authority or a successful CAS.
The real command checks those conditions again when the operation starts.

Admission barriers apply to their actual operations. Maintenance can pause new
admission while existing owners drain. Pending authorized delivery can block the
next batch even after its integration reservation is legitimately released;
this does not imply that every Worker is paused. A held process review, intake
or Stage candidate likewise retains its adopted scope of restriction. Display
the supported pause reason separately from the numeric occupancy; do not turn
an empty pool into an automatic permission or a scoped barrier into a global ban.

Absent, incomplete or unsupported authority means unknown, not zero. A saved
snapshot may show its last observed counts, but stale data cannot promise current
free capacity. Retain the normal last-good snapshot, repository identity and
freshness checks. An unavailable projection must not silently reinterpret a
parallel project as an empty legacy slot.
An explicitly malformed state fence still fails through its adopted reader;
an unknown display is not a way to publish invalid state as a healthy snapshot.

## Keep the display project-wide and safe

The compatible Tracker projection supplies the counts before private ownership
fields are discarded. The UI consumes that projection once; it does not count
filtered task cards or infer reservations from animations. Search, module and
status filters change the displayed tasks, not total reserved capacity. Project
switching and snapshot replacement use that project's own current observation.

Safe task/PR and batch display references may explain which reservations are
held. Missing or filtered task details must not erase a held reservation. Private
claim/session identifiers, actor registries, paths and reports do not belong in
the public snapshot. Capacity navigation and activity animation have different
meanings: a held fixing lane must not falsely appear actively reviewing.

## Compatible publication

This is the existing-topology part of Task09 / TT-144. The modern direct-route
extension belongs to the actual Task07 contract when released; a proposal is not
an enabled topology. Preserve every old descriptor, chosen limit, Stage setting,
delivery target and state protocol during this presentation change.

Verify projection fixtures, normal browser regressions, numeric/mobile/keyboard
behavior and a read-only comparison with actual held reservations after the
compatible service is deployed. Source publication, the installed reader and
that observed comparison are separate evidence. Updating the standard pin or
navigation skill never changes a consumer's capacity or grants a new claim.
