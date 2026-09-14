# Project delivery guidance

Before engineering/release work, read `delivery.json`, `docs/DELIVERY.md` and the
existing tracker instructions. Keep this pointer when adding project-specific
guidance. Existing safety, quality and deployment boundaries remain in force.

This project follows MojoTheApe/master-repo at the exact commit recorded in
`delivery.json`. Use the project-workflow skill if available; otherwise read
`standard.md` and the selected profile from that pinned repository revision.
Do not substitute its latest branch or upgrade the standard during feature work.

Use the project's existing ticket tracker. Link tickets and PRs both ways. Merge
does not complete deployment-dependent work: apply this project's completion
policy and record actual verification.

Use configured application checks and the existing maintained delivery path.
Stage and promote the exact approved candidate. Configuration placeholders or
a passing descriptor check do not prove an environment works.
