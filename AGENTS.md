# Master Repo engineering guidance

This repository maintains a shared delivery standard, templates and validation
tools. Read `standard.md` and `delivery.json` before implementation. Keep each
consumer's existing tracker and operational safeguards.

- Track implementation in a real local GitHub issue and use an issue branch.
- Include exactly one `Tracker issues: #NUMBER` line in the PR body; list multiple
  local issues with commas. Link the PR back from the issue.
- Treat merge, publication, installation and verified business behavior as
  separate facts. This tooling repository completes work after review, passing
  checks and merge; it has no application staging or production service.
- Run `python3 -m unittest discover -s tests -v`, then
  `python3 scripts/standard.py validate --root .` and
  `python3 scripts/check_links.py` for the completed candidate.
- Keep Python tools dependency-free and compatible with Python 3.9+.
- Scaffold into isolated temporary directories when testing. Never deploy to a
  consumer, install global skills, or rewrite consumer files as a test.
- Existing hotfix/update behavior, production admission and project-worker
  boundaries belong to the consumer. This standard does not override them.
- Keep source, docs, issue specifications and reusable skill instructions in
  English. Explain outcomes to the owner in their preferred language, briefly.

The project-workflow skill lives in `.agents/skills/project-workflow/SKILL.md`.
It supports adoption and ordinary work under a pinned standard. It must not turn
a small feature request into a repository-wide migration.

For MR-3 and subsequent process work, read `docs/PROJECT.md` and keep it plus
`docs/CHANGELOG.md` current. Assess Task Tracker impact on every process/contract
change; record no impact with reason or link/propose a concrete companion fix.
The owner has authorized MR-3 together with Task Tracker TT-59. Arrange final
review through a separate non-implementing subagent. This self repository keeps its
existing local Issue reference and tooling completion exception during the change.
