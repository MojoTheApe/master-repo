# Agreed shared workflow specification

Owner-approved scope, implemented by Master Repo MR-3 and Task Tracker TT-59.
The original discussion was in Russian; this English requirements record preserves
its decisions. Current implementation is described in `docs/PROJECT.md` and the
standard; this specification is not rewritten as a running changelog.

1. Master Repo is the canonical reusable process/template. Task Tracker owns its
   app and commands; project tickets live in project repositories.
2. Idea intake starts Idea, task intake Backlog. The owner directs prioritization;
   explicit development starts In Progress, a claimed execution slot and branch.
3. Use public prefix/Issue IDs, stable branch naming and linked PR titles/body.
   Preserve historical IDs. One PR can cover a related set of tickets.
4. Implement and self-check, create PR, set Review, automatically spawn a separate
   independent reviewer. Fixes stay in the original branch; review current content.
5. Staging defaults on but is optional by project. Keep permanent stage/main,
   feature -> stage -> main, same tasks and unchanged verified content. One stage
   task set at a time; changed content/main requires fresh verification.
6. Merge requires independent approval and checks, without a routine extra owner
   permission step. Project production authorization and controls remain intact.
7. Merged means main integration. VPS/n8n require verified delivery; local manual
   pull completes after merge. A package is a separate choice. No mandatory Done
   column. Pending/failed delivery must not count as completion.
8. Create and maintain a current system description, meaningful what/why history
   and preserved original specs. Update in the implementation PR; review it.
9. New project onboarding includes the Tracker client/config, labels, registry,
   publication and actual visible board verification. Stage column follows choice.
10. Process changes in either shared repo assess the other and propose a concrete
    linked fix if needed. Avoid silent unrelated cross-repository modifications.
11. Keep the skill's canonical source in Master Repo and install once per agent
    environment. Projects carry short local instructions and pinned settings.
12. Explicit upgrades preserve unique fixes via old/new/local comparison, document
    exceptions and report conflicts. Bulk migration uses separate project PRs.
13. ReactForge installer/deployment redesign, unrelated consumer migration and
    global skill installation are not implicit parts of this implementation.
