# Current baseline

Read-only observations: 17 October 2026, repository refs/protections from approximately 07:56 UTC (09:56 Europe/Madrid); service and ownership were reread separately. Per-row timestamps and Git object references are authoritative. All fifteen main revisions still match the supplied audit; open work and reservations have changed.

| Repository | Current main | Route / Stage | Proposed disposition | Open PRs |
| --- | --- | --- | --- | --- |
| master-repo | [9257f7be9f89](https://github.com/MojoTheApe/master-repo/commit/9257f7be9f89e10eeb7b169247db368932662d6e) | not onboarded / self exception; Stage unknown/local exception | onboard engineering workflow and live board; preserve self-pin exception until Task 08 | 0 |
| task-tracker | [2c01481a86ee](https://github.com/MojoTheApe/task-tracker/commit/2c01481a86ee8e8af31736378574a91505c7f94f) | legacy single slot; Stage unknown/local exception | upgrade self-project separately from service; retain TT identities | 1 |
| ai-skills | [4a9ed1619002](https://github.com/MojoTheApe/ai-skills/commit/4a9ed1619002737fc8fa0ef627e2dbe1e922e8f9) | not onboarded / self exception; Stage unknown/local exception | onboard authored engineering and verified catalog publication | 0 |
| adopy-campaing-launcher | [af0ade29b106](https://github.com/MojoTheApe/adopy-campaing-launcher/commit/af0ade29b106129089dbabd3f208b548efa246d9) | execution-v3 batch; Stage off | bounded early pilot, then remaining Task 13 delta after owned drain | 67 |
| react-forge | [96c5dd8dd0b5](https://github.com/MojoTheApe/react-forge/commit/96c5dd8dd0b55626512773484b11d59e69612e87) | legacy single slot; Stage unknown/local exception | upgrade with existing status aliases, local updater and admission retained | 13 |
| tg-bot | [1d03d83c7fcd](https://github.com/MojoTheApe/tg-bot/commit/1d03d83c7fcd6d0f9c25213aa959cbc2c0957dd2) | legacy single slot; Stage off | upgrade workflow; preserve production delivery | 0 |
| facebook-lead-automation | [a24a6c3c1dff](https://github.com/MojoTheApe/facebook-lead-automation/commit/a24a6c3c1dff5f36bee088f2913fe7bf728327b3) | legacy single slot; Stage off | upgrade and reconcile existing registration work | 1 |
| n8n-jira-tgbot | [2e90da1c523d](https://github.com/MojoTheApe/n8n-jira-tgbot/commit/2e90da1c523db3b2094cabc9811a5ab5b6efea79) | legacy single slot; Stage on | upgrade source workflow with existing Git Stage | 0 |
| n8n-jcloud-automation | [49f343d688fc](https://github.com/MojoTheApe/n8n-jcloud-automation/commit/49f343d688fcc58f52914bcf39d216ba47b4974c) | legacy single slot; Stage on | upgrade source workflow with existing Git Stage | 0 |
| n8n-namari-automation | [ff4d06f20029](https://github.com/MojoTheApe/n8n-namari-automation/commit/ff4d06f2002941e7a29b8793f043fc863970f5f5) | legacy single slot; Stage on | upgrade source workflow with existing Git Stage | 0 |
| n8n-keitaro-ftd-notifications | [9b24fd1b899f](https://github.com/MojoTheApe/n8n-keitaro-ftd-notifications/commit/9b24fd1b899f2d8314d3fe0d7eed20f8e8ba3f28) | legacy single slot; Stage off | upgrade after current owner completes or explicitly revalidates work | 1 |
| make-facebook-rpc-poc | [1506e4f7cc49](https://github.com/MojoTheApe/make-facebook-rpc-poc/commit/1506e4f7cc49078594349f207287fde435c2d0a9) | legacy single slot; Stage off | adopt modern simple reviewed route when released | 0 |
| the-source | [346003637f06](https://github.com/MojoTheApe/the-source/commit/346003637f066b1da9198d044406723065949fd1) | not onboarded / self exception; Stage unknown/local exception | onboard governance engineering and live board | 0 |
| acl-lib | [f02d642c96ed](https://github.com/MojoTheApe/acl-lib/commit/f02d642c96ed2e7ff1428a5111e90c579b7a7d65) | not onboarded / self exception; Stage unknown/local exception | resource-only; link to ACL in Task 11 | 0 |
| acl-releases | [c9c4351bfe94](https://github.com/MojoTheApe/acl-releases/commit/c9c4351bfe946c0e40ac65a3fde94a7b5a5f12df) | not onboarded / self exception; Stage unknown/local exception | resource-only; link to ACL in Task 11 | 0 |

## Service and completion defect

The running service is `4ac9b3fa3ea7559f43eb849778f99e347f2eb67b`, while published Tracker v3.2.0 is `2c01481a86ee8e8af31736378574a91505c7f94f`. Direct service imports accept CI policy 1 and reject policy 2; ci-plan/ci-gate are absent. The event service is active and the retired minute timer inactive. Ten scoped snapshots are OK. Successful snapshots do not prove new writer compatibility. See [service readback](service-observation.json) and [current source capability fixture](source-capabilities.json).

The [fresh synthetic reproduction](completion-reproduction.json) uses actual current-main command/state/projection code. After a requirements edit, frozen scope no longer matches, but current completion and dependent admission still succeed. Explicit reopen invalidates current task completion. Task 02 is therefore still required; the old historical-label presentation task TT-138 is not the requested scope-bound repair.

## Ownership and existing work

ACL has 67 open PRs, two work claims, five source-review lanes, a four-member assembling integration reservation and a running intake; its review queue contains 33 items. Configured limits remain 5/5/batch 5, Stage off. Keitaro retains legacy Issue #40 ownership. FLA no longer has the historical legacy claim. Do not release any claim by elapsed time, replace active interpretation, or require all open PRs to disappear. Refresh exact state blobs before any cutover.

Tracker PR #110 / TT-109 is unfinished registration work. TT-75 and Master MR-13 also remain open and are preserved; no duplicate registration or historical task closure is scheduled. Main source does not contain Task 02; the complete new scope is TT-142. Planning Issues used the maintained Tracker create command and an explicitly journaled coordinator registry; embedded markers and exact Issue readback reconciled a delayed create without repeating POST. All-state Issues were inspected before creation. Read-only fixture checks did not claim implementation or mutate real task outcomes.

Historical `retained_legacy_pending` entries are migration history, not current pending operations. The inventory uses the pinned engine maintenance predicate and current ownership records; intake history length is not occupied capacity. Current pending delivery remains a separate obligation.

## Native enforcement and D01

Master main requires strict current-base `validate`, `tracker-link` and `skill-impact`, enforces administrators and requires zero native approval votes. Independent agent review is an additional cooperative rule. Private-repository protection/ruleset APIs return account-plan HTTP 403; branch metadata reports unprotected. Admin permission does not establish bypass-protected review. No enforcement, plan, visibility or accepted limitation is invented. D01 remains open for the concrete later choice; independent source work can continue.

## Ownership of content and proposed projection

Master owns normative policy and the canonical workflow directory. Tracker owns executable semantics and exports. Consumers own product/runtime knowledge and local producers. AI Skills authors library skills and mirrors the registered Master directory; [all ten Git entries, modes and paths match exactly](skill-mirror-proof.json). Catalog/plugin installation is separate from consumer adoption.

Proposed engineering homes total thirteen; acl-lib and acl-releases are ACL resources, with no duplicate board. The future categories are All / Backlog / In Progress / Review / Delivery / Done / Archive; they remain a Task 10 proposal. Task 02 preserves current Archive semantics. No role/category declaration grants a route or delivery bypass.

ReactForge’s exact baseline release guide records dispatch disabled on 8 October for its build-only transition. Its maintained controller path exists; historical onboarding does not prove current automatic VPS activation. Preserve its explicit runtime authorization boundary.

## CI support and attributed baseline

Current shared source supports explicit immutable fixed-container job evidence and fresh fallback. Consumer task-context and shared CI-evidence policies are absent; changing a pin would not activate them. ACL retains its local exact-tree/native collector and Windows/Python matrix, installer and delivery checks. Mutable-host, matrix, build and installer jobs have no blanket shared reuse claim. Task 12 must establish its bounded original-attempt support separately. Exact old-engine protocol, CI and client-cache guard source is recorded in [pinned engine capability evidence](pinned-engine-capabilities.json). Every repository row records actual portable/CI blobs, current producer paths and its operational authorization boundary. Cache observations cover this workspace only; unobserved employee overrides are an activation blocker, not assumed installed support.

A current read-only Actions sample reports 5,791 retained run records and retains twenty latest rows locally. Native run [38707841668](https://github.com/MojoTheApe/adopy-campaing-launcher/actions/runs/38707841668) remains the carried-forward-attempt fixture. These are inventory observations, not a complete period report. Historical 212 versus 112 rounded interval estimates remain attributed to the earlier audit until Task 05 independently reconciles original job execution. The billing endpoint returned HTTP 404; actual charges, credits and per-job net costs are unknown. No savings percentage or paid measurement run is asserted. The sanitized [CI baseline record](ci-baseline.json) retains run IDs, sample limits, fixture identity and the billing failure; private operational logs remain local.

## Acceptance boundary

All 29 goals and all 202 original criterion IDs/texts are preserved and mapped to real Issues. WFO-09 evidence is collected for independent source review; final criterion acceptance remains pending. Source review/merge, immutable publication, service activation, consumer adoption and actual outcome stay separate. This slice changes documentation and planning only.
