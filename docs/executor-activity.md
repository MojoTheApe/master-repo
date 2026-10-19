# Truthful executor activity

Task status, a reservation, current activity and useful progress are different
facts. An agent reports only its own actual run using the compatible project's
selected Tracker guide. New shared support is implemented in
[TT-174](https://github.com/MojoTheApe/task-tracker/issues/174); instructions alone
do not install a reporter or update a consumer pin.

- Report running when actually executing, waiting before waiting for checks or
  input, and stopped when the executor finishes. While running, confirm once a
  minute through the maintained shared command and actual owner/session/claim.
- Five minutes without a running/waiting report means Activity unconfirmed. Freeze at the last
  confirmed work total; silence never proves a stop and never releases ownership.
  A confirmed stopped fact remains while its original owner is still assigned.
- Waiting and missing-reporting gaps do not count as work. Repeated review,
  takeover and batch attempts retain distinct runs; missing historical runtime
  remains explicitly incomplete rather than estimated from Issue timestamps.
- The common foreground `activity run --exec` wrapper may cover the actual agent
  child process. Preserve its failure code and lifetime. Never wrap a perpetual
  sleeper or launch a detached heartbeat that survives the executor.
  Periodic wrapper renewals preserve the actual run's latest explicit mode,
  including waiting/stopped; they never resume work by themselves. Explicit owner
  reports or a real new launch control resumption, including concurrent reports.
  A coordinator must not renew another executor's report. A test process being
  alive does not prove a separate reviewer is active or useful progress.
- Interactive agents report at actual tool boundaries. A long period without a
  tool call can become unconfirmed; do not conceal that by keeping a fake reporter
  alive. Current compatible ownership commands remain the only stop/transfer path.
- Publish compatible readers before adopting the new writer pin. Existing runs
  remain unknown until their real owners report or their next actual launch uses
  the common wrapper. Do not restart or transfer another owner's work implicitly.

Tracker owns commands, lightweight observations, bounded retries, public projection,
clock expiry and history. Master owns these common rules and generated guidance.
ACL adopts the same reviewed mechanism; no campaign-specific activity controller
or change in delivery/execution policy is implied. Other consumers stay pinned.

Public presentation retains safe mode/kind, confirmation time and confirmed totals.
Do not expose claim/session IDs, process arguments, reports or credentials. History
names the actual GitHub actor; shared credentials do not identify a particular
human or independently prove an agent's identity. Native status transitions may
stay within one UI category, such as Review to Approved. Retain coverage limits
and source links; missing history is not proof that nothing happened.
