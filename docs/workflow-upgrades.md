# Coordinated workflow upgrades

Upstream source, installed skill, shared service publication and consumer state
activation are separate results. Ordinary feature work follows the current pin.
This procedure applies to an authorized upgrade; it supplies no consumer rollout
or deployment permission.

## Plan dependencies once

Record current/target standard and engine, affected clients/writers, local policies,
exceptions and completion criteria in the upgrade task. Reuse unchanged facts;
refresh a dependent input when it changes and before admission/mutation, rather
than repeating broad inventories after every unrelated action.

1. Independently review and integrate compatible Tracker support.
2. Pin it in Master; review/integrate the standard and canonical skill.
3. Prepare each authorized consumer under its actual old route, retaining genuine
   old-policy ownership/handoffs. New settings in a source head are not activation.
4. Publish compatible writers/service through their maintained procedure before
   live state activation. A source pin or registry edit is not publication.
5. Establish the cutover window, reconcile owners/stage and preserve private
   before-state evidence. Preview/apply only the supported migration.
6. Verify retained queue/history/delivery and the actual fresh projection; resume
   authorized admissions. Record each source/publication/activation result once.

Explicit bounded-retry selection follows the same order. Read the exact engine's
CI_RETRY.md: all actual readers/writers must support its fenced durable state
before owned activation. Preserve episode consumption, unresolved causes and
uncertain intents across policy edits; absence and export are not activation.
Independent reporting has no retry/state dependency and can remain an on-demand
operation while a busy consumer's workflow adoption waits for its real owners.

For selected native CI evidence, compare the actual producer copies and reviewed
workflow/profile pins with the new engine's exact artifacts. A helper-byte change
needs an explicit reviewed producer/blob update even when its emission command is
unchanged; an ordinary upgrade preserves policy choices and cannot invent those
new attestations. Follow the [portable artifact boundary](portable-contract.md)
and obtain the actual missing native proof before admission.

## Prevent new starts during cutover

Use a durable maintenance admission gate only when all actual clients/writers
support the same reviewed protocol. Its CAS owner/recovery and allowed drain paths
belong to Tracker; see the [supported companion](tracker-companion.md) and its
exact pinned command guide.

The compatible engine supplies this optional gate; a source upgrade does not
publish its writers or reserve an interval. Until every actual writer supports
the protocol, coordinate one explicit no-new-start
interval and use existing owner stop/handoff procedures. Retain confirmed pause
authorization while unchanged; ask again only for a genuine new launch, changed
coordination or unresolved owner. Continue preparation while work drains. The
actual migration still requires a current-state/CAS check: a human confirmation
cannot reserve shared state or prove present idleness.

Do not invent commands, add a flag old clients ignore, edit claims or reset stage
to appear idle. If new work starts, continue independent preparation and report
the concrete blocking owner rather than discarding the queue or claiming activation.

## Verify platform controls separately

Required names in a descriptor and an agent's `check-merge` are not native branch
protection. Audit main and enabled stage during onboarding/upgrades or after a
relevant settings change, not on every ordinary feature check.

From the selected standard checkout:

```sh
python3 scripts/check_branch_controls.py --root /path/to/project
```

This read-only helper checks classic PR/status requirements, up-to-date checks,
admin enforcement and force-push/deletion restrictions. Exit 0 verifies only its
stated coverage. Independently verify effective rulesets, check producer bindings
and genuine agent review. Unsupported/denied/hidden/ruleset-only/incomplete replies
remain unverified, not green or proof that protection is absent. Legacy consumers
provide actual `--repository owner/repo --branch BRANCH --check NAME` selections.

Preserve stronger local controls. A native PR setting with zero account approvals
can require the PR path, but cannot attest independent-agent review. One shared
GitHub account cannot manufacture distinct approving users. Report plan limitations
and actual alternative enforcement. [GitHub's contract](https://docs.github.com/en/rest/branches/branch-protection)
defines platform settings; a file or a green descriptor check does not.

An unreleased selected standard stays visibly draft for adoption. Actual workflow
activation is recorded separately; neither means a published stable standard.
Publication remains the [explicit release procedure](versioning.md).
