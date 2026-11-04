# ACL alignment with Master 1.9.0

Read-only assessment for [MR-85](https://github.com/MojoTheApe/master-repo/issues/85),
2026-11-04. Observed ACL main:
[`035f75a4b484fea999db6679ac4d96fe43bd1f6a`](https://github.com/MojoTheApe/adopy-campaing-launcher/commit/035f75a4b484fea999db6679ac4d96fe43bd1f6a).
This checks repository configuration and instructions, not running executors or
application/package acceptance. No ACL files, tasks, state or releases were changed.

## Conclusion

No mandatory workflow rebuild is needed. Master 1.9.0 standardizes document
responsibilities and the starting choices for new projects. Existing projects
retain their adopted choices. ACL already follows the common document layout and
has an established application-specific process. Keeping its existing standard
reference is valid; publication alone does not require immediate adoption.

## Observed alignment

| Area | Current ACL evidence | Decision |
| --- | --- | --- |
| Reading entry | README links the current workflow, AGENTS reading map, system overview and stable Windows release | Keep these entry points; no replacement README |
| Documents and history | `docs/repository/LAYOUT.md` separates repository, system and runtime ownership; `docs/system/specs/README.md` preserves original specs/plans and distinguishes plans from implemented behavior | Keep existing paths and history; no file migration or new parallel logs |
| Standard versus engine | `delivery.json` selects Master 1.8.0 (`fddcdd0`), while its standalone workflow provider and Tracker engine select 3.24.1 (`9dc08c3`) | Treat the Master documentation reference and operational provider separately |
| Work and integration | `tracker/config.json` retains execution schema 3, implementation/review/batch limits 5/5/5 and Stage disabled | Preserve the chosen parallel/batch route; new-project simple/direct defaults do not apply |
| Completion | Package profile with `verified-stable-package`; current WORKFLOW retains manual-merge/recovery guidance | Keep actual product acceptance and supported reuse of already accepted release evidence |
| Verification | VERIFICATION retains relevant checks, existing reuse and distinct tooling/product coverage; delivery-check uses the pinned official provider | Keep check names, provider and existing reuse; no new package run for this assessment |
| Optional policies | Task-context and completion-policy opt-ins are absent from current Tracker configuration; instruction-only routing is separately selected | Do not activate optional policies to resemble a new scaffold |

Primary evidence at the observed immutable revision:
[descriptor](https://github.com/MojoTheApe/adopy-campaing-launcher/blob/035f75a4b484fea999db6679ac4d96fe43bd1f6a/delivery.json),
[Tracker configuration](https://github.com/MojoTheApe/adopy-campaing-launcher/blob/035f75a4b484fea999db6679ac4d96fe43bd1f6a/tracker/config.json),
[workflow](https://github.com/MojoTheApe/adopy-campaing-launcher/blob/035f75a4b484fea999db6679ac4d96fe43bd1f6a/docs/repository/WORKFLOW.md),
[verification](https://github.com/MojoTheApe/adopy-campaing-launcher/blob/035f75a4b484fea999db6679ac4d96fe43bd1f6a/docs/repository/VERIFICATION.md),
[reading map](https://github.com/MojoTheApe/adopy-campaing-launcher/blob/035f75a4b484fea999db6679ac4d96fe43bd1f6a/AGENTS.md),
[ownership](https://github.com/MojoTheApe/adopy-campaing-launcher/blob/035f75a4b484fea999db6679ac4d96fe43bd1f6a/docs/repository/LAYOUT.md),
[spec index](https://github.com/MojoTheApe/adopy-campaing-launcher/blob/035f75a4b484fea999db6679ac4d96fe43bd1f6a/docs/system/specs/README.md),
[README](https://github.com/MojoTheApe/adopy-campaing-launcher/blob/035f75a4b484fea999db6679ac4d96fe43bd1f6a/README.md),
[provider validation](https://github.com/MojoTheApe/adopy-campaing-launcher/blob/035f75a4b484fea999db6679ac4d96fe43bd1f6a/.github/workflows/delivery-check.yml).

## Smallest useful future change

When ACL elects to adopt 1.9.0, make one bounded project task to align its selected
Master reference and active documentation links with the verified release commit,
and link the new document map/evolution guide from existing navigation. Record why
the update changes no operational policy in the existing repository changelog.
Keep historical pins and original decisions intact; do not globally replace old
version strings or rewrite the pristine provider/template baseline by hand.

Use ACL's adopted standalone-provider procedure, inspect its supported preview
and actual diff, and preserve Tracker/provider 3.24.1 and all current settings.
Do not run Master's generic scaffold/upgrade over ACL: Master's paired 3.10.0
engine is not ACL's current provider. A descriptor/configuration change must take
ACL's normal applicable review/integration route; it is not automatically eligible
for the instruction-only shortcut. Reuse valid unchanged evidence under the
existing rules. This assessment does not assert that a provider preview or future
adoption check has already passed.

There is no reason here to replace working batch integration with direct delivery,
enable Stage, alter capacities, introduce extra documents/approvals, broaden the
meaning of Done, relaunch package checks or publish another ACL installer. Keep
`adoption: draft` and any deferred-readiness history until their real outstanding
conditions are resolved; a new standard number is not proof of readiness.
