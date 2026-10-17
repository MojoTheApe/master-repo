# On-demand CI accounting

Use the pinned report implementation with an explicit repository, UTC interval
and grouping. Capture a baseline from ordinary authorized work before relevant
adoption and run the same method on comparable later work. Reporting is read-only;
it neither launches jobs nor changes artifact/cache retention. No hosted analytics
service or recurring collection is required.

The canonical exported report runs with Python3.9+ and an authorized own
environment's `gh` GET access. Both supported paths use the same implementation:

```sh
python3 scripts/tracker_ci_accounting.py --repo owner/repo \
  --from 2026-10-15 --to 2026-10-15 --group-by created --json
python3 .workflow/tools/tracker_ci_accounting.py \
  --snapshot /private/path/actions-snapshot.json --json
```

Without `--json` it prints the human report. Capture uses explicit
`--project-root /path/to/project --save-snapshot /private/path/new-snapshot.json`;
the destination must be outside that project and must not exist. A thin project
adapter can supply its real default repository, privacy root and exact overhead
job names. It supplies no interval matching or money rules. This report does not
read workflow state or require retry-policy activation.

A raw versioned GET snapshot makes the report reproducible without querying
latest state during replay. Keep private snapshots outside source worktrees with
restricted permissions. Publish only an allowlisted human/JSON summary; native
logs, account details and private task bodies do not belong in public fixtures.
A sequence of API observations is not an atomic historical snapshot.

## Counting execution

A native job ID or attempt number identifies an observation, not necessarily a
new execution. Count original intervals once when unchanged native execution
identity proves later rows were carried forward. Preserve same-attempt
multiplicity; changed or ambiguous runner, timing, step or identity data stays
unresolved. Instruction-only/not-applicable skips do not prove reused coverage.
A pending retry reservation consumes retry budget, not observed execution minutes.

Creation cohorts group runs by their original creation time and include observed
attempts. Execution-period reports clip actual observed intervals to their UTC
window. An older run can be rerun during a later period; bounded creation lookback
cannot prove the absence of still older reruns. Partition capped run-history
queries, deduplicate IDs and state any incomplete access, pagination, saturated
second or missing job/attempt data. An observed subtotal is not a complete total
when contributions remain unknown; show unresolved bounds and unbounded gaps.

Retain repository, workflow/event, actual candidate/PR/batch links where observed,
job name, platform/matrix identity, run/attempt observations, execution intervals
and rounded job-minute estimates. Report first useful feedback and full-cycle
latency separately from summed parallel execution. Label orchestration overhead,
retry reasons and coverage as observed, inferred, missing or unknown according to
the actual evidence; run count or merge-message classification alone proves none
of these. Preserve supported project-local proof adapters.

## Billing and storage

Rounded interval minutes are estimates, not invoices. Use actual historical SKU,
runner class, rounding, rates, included usage and discounts only when a supplied
authorized billing source supports them. Keep gross attribution estimates separate
from actual net charges. Unavailable rates or billing access mean unknown, never
zero. A fixed Windows multiplier does not establish a money charge.

Billing summaries and detailed exports have their own aggregation. A daily
repository/workflow/SKU amount cannot be reported as exact native job/PR/attempt
net charges. Retain the source interval, currency, aggregation and limitations
when an authorized export is available. The ordinary detailed workflow report
and summarized REST data are distinct sources; see the primary
[billing report reference](https://docs.github.com/en/billing/reference/billing-reports)
and [REST billing usage](https://docs.github.com/en/rest/billing/usage).

Report artifact and cache bytes, known creation/expiry/access times and actual
storage billing separately. A current listing is not historical GB-hours or an
invoice; missing lifetime/retention information remains unknown. Preserve evidence,
release artifacts and required retention. Reporting grants no deletion permission.

Before/after comparisons retain workload, runner/environment, plan/rate, missing
coverage and fresh package/runtime acceptance differences. Report available
observations and pending measurement gaps without inventing a savings percentage
or extrapolating a short isolated test to the fleet.
