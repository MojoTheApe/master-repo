# Instruction-only integration

The separated repository/system/runtime layout defines file ownership. It does
not itself select a different integration route. A project explicitly adopts
`workflow.process_instructions` in `delivery.json`, mirrored exactly as top-level
`process_instructions` in `tracker/config.json`:

```json
{"schema_version": 1, "required_checks": ["descriptor", "tracker-link"]}
```

Add the project's actual instruction checks by name. The compatible Tracker must
support the option and portable classifier; changing a skill alone cannot enable it.
The optional object is separate from delivery policy and execution capacity, so
opting in preserves existing package/production receipts and accepted history.

| Actual change | Integration route after implementation |
| --- | --- |
| Only eligible process instructions | Review, independent approval and instruction checks -> main -> Merged |
| Application, build, delivery automation, configuration, or mixed/unknown changes | Existing project route; execution v2 uses Approved -> frozen batch of at most the configured limit -> stage -> main |

Eligible changes are confined to regular `AGENTS.md`, `CLAUDE.md` and Markdown
under `docs/repository/`. The complete immutable diff must establish eligibility.
Renames must keep both paths eligible. Missing/truncated comparison data, symlinks,
unknown paths and extra merge content cannot authorize the shorter route. Product
knowledge under `docs/system/`, operations under `docs/runtime/`, executable
helpers, CI, configuration and templates are outside the exception. Task type,
title, labels or an author's declaration never replace the actual diff.

Keep one real task per instruction source PR, its author claim/handoff, the genuine
independent review and current head/base/tree/scope evidence. Adopted execution
policies use their genuine review lane; legacy projects keep their existing slot
and independent attestation without unsupported execution commands. The source PR
targets main. Use the pinned Tracker's review evidence, `check-pr`, `check-merge`
immediately before integration and normal reviewed-complete `merged` transition.
Execution v2 does not move this source to Approved or put it in a batch; its
independent review lane remains owned through the durable main handoff. A label
change or report-only completion cannot replace admitted integration.

Only this proven route completes after the admitted main merge, including in a
package project. It supplies no stage, installer, deployment or employee-update
receipt. Review the full scope before completion; an instruction-only PR cannot
finish a parent whose application or runtime outcome remains outstanding.

Main may not change underneath a reserved integration batch or an unpromoted stage
candidate. Finish/reconcile that ownership before admitting the direct source.
Before later staged work, freshly validate source approvals against current main.
The compatible Tracker can admit a stage baseline behind main only when its
complete instruction-only delta and first-parent chain are covered by retained
verified process merge receipts with current scope/policy/tree proof. The new
source/batch starts from current main and preserves that baseline in its reviewed
composition. Missing receipts or any other main/stage difference require the
existing claimed reconciliation procedure. No stage reset or force update is used.

The adoption PR changes configuration/helpers/checks, so it follows the project's
existing route. Finish pending work under its old policy before activation; verify
the compatible engine, mirrored config, real checks and maintained board. Other
consumers stay pinned until separately upgraded.
