# Engineering standards

Use these rules with the accepted task and the project's local engineering
context. Master owns these common principles; the project owns its language,
component boundaries, source files, check commands and delivery. Follow the
adopted revision, not an unreviewed candidate or the latest installed skill.

## R1 — Smallest complete solution

Implement the agreed behavior, necessary failure handling, compatibility and
verification. Do not add settings, extension points or future capabilities without
a current requirement. Simplicity does not justify omitting required behavior.

## R2 — Inspect and reuse

Read the affected code and look for an existing implementation before adding one.
Prefer established helpers, libraries and patterns when their semantics fit.
Similar-looking code with different responsibilities or owners need not be merged.

## R3 — Justify substantial additions

A new dependency, architectural layer or substantial component must solve a
concrete problem in the task. Briefly explain that need in the existing Issue or
PR, including why the existing mechanism is insufficient. Small local helpers
need no separate justification or approval ritual.

## R4 — Stay within the task

Keep unrelated features, broad refactors and speculative platforms out of the
change. Small local cleanup is appropriate when needed for the result and easy
to review without changing neighboring behavior. Record other useful work
separately; discovering it does not authorize implementing it.

## R5 — Surface material changes

Use ordinary implementation judgment within the agreed boundaries. If the result
requires expanded requirements, changed architectural boundaries or new operating
obligations, explain the need and update the agreed task before expanding work
through the existing owner decision process. Do not silently reduce the result
or request permission for every routine implementation choice.

## R6 — Make code understandable

Use clear names, readable control flow and coherent responsibilities. Explain
non-obvious decisions. Neither compressed one-line functions nor many trivial
layers improve maintainability merely by satisfying a size or design slogan.
Follow the local conventions and useful examples; extract a responsibility when
the current change demonstrates a real need, not to satisfy a universal line cap.

## R7 — Verify behavior

Test observable outcomes and important failures with the project's applicable
checks. Do not weaken expectations to obtain success or replace behavioral tests
with assertions about implementation text. Add tests for changed risk and missing
coverage; retain still-valid evidence and the existing final verification plan.

## R8 — Change the authoritative source

Identify authored sources, generators, generated outputs, vendor copies and
historical snapshots before editing. Regenerate outputs through their maintained
producer and preserve ownership across repositories. A large generated diff is
not evidence of unnecessary authored code; a tiny diff is not proof of simplicity.

## Apply the rules in the existing task and review

The task states the result, boundaries, behavior to preserve and observable
acceptance. Its short plan identifies affected parts and any substantial new
elements. The PR explains the result, meaningful deviations and actual checks.
Use the existing fields; no extra report, role, approval stage or size score is
required. Formatting, lint and type checks belong to the project's supported tools,
with explicit coverage and legacy exceptions, not to a second rules engine.

The separate non-implementing reviewer reads the original task, actual full diff,
applicable local rules and verification evidence. Briefly assess:

- Does each substantial change serve the agreed result without missing behavior?
- Were suitable existing mechanisms reused and substantial additions justified?
- Is there unnecessary generality, hidden scope expansion or avoidable complexity?
- Do the checks support the result, compatibility and actual delivery obligations?

A blocking finding identifies the concrete problem and violated requirement or
R1–R8 rule. A preferred alternative without that basis is advice, not a blocker.
Review suggestions do not expand the task automatically. A reviewer who implements
the correction cannot supply its final independent approval. Keep the project's
existing handoff, checks and completion; these rules select no new workflow policy.
