# System context

Record project-specific business rules, invariants, ownership boundaries and dated
technical evidence here. Link the current [system description](PROJECT.md) and
source entry points. Operational access and deployment rules belong in
[the runtime guide](../runtime/DELIVERY.md); Git rules belong in
[the repository workflow](../repository/WORKFLOW.md).

Fill the following from actual project facts; an unfilled outline is not completed
setup. Refer to the adopted Master's engineering rules rather than copying them.

- Languages, supported versions, local conventions and execution environments.
- Component responsibilities, extension points and where typical changes belong.
- Authoritative sources, generators, generated outputs, vendor copies and history.
- Existing error/state/external-call handling and dependency constraints.
- Two useful existing-code examples, with when and why to follow them.
- Real check commands, supported coverage, prerequisites and explicit limitations;
  link the local verification plan instead of maintaining another command list.

Keep language-specific tool choices and operating safeguards local. Similar file
names across projects do not establish common ownership. Preserve this completed
context on upgrade; shared template changes alone must not replace local knowledge.
