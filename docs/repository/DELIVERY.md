# Delivery of the standard itself

This repository publishes reusable policy, templates, validation and a skill.
It has no application stage/prod service or database. A ready descriptor means
these maintenance procedures are defined; it does not claim a published version.

- Tracker: GitHub Issues in this repository. Each implementation PR has one
  `Tracker issues: #NUMBER` line. CI verifies those numbers identify real issues.
- Owner/maintainer starts work and records In Progress on the issue. A ready PR
  moves work to Review. Status labels are maintained explicitly for now; this
  repository does not install a second tracker or claim automatic transitions.
- CI runs unit tests, descriptor validation and local link checks on PRs and main.
- Review and merge complete this non-deployed implementation task. Keep its issue
  open until reviewed, checked and merged; release publication is separate.
- Publish the standard only through [versioning](../versioning.md), with an exact
  immutable tag, release notes and verified merged-commit checks.
- Consumers remain pinned. Recovery from a bad standard release is a reviewed
  consumer PR restoring its prior compatible pin/configuration, not moving a tag.
- Source history is retained in Git. No customer data or credentials belong here.

Actual GitHub access/protection depends on repository settings and plan. Record
their observed state in the implementation PR. Do not infer protection from this
document or a green CI check. No auto-merge, tag or production job is configured.
