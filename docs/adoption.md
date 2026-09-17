# Creating, connecting and adopting projects

## New project procedure

The running agent performs the whole onboarding within the new-project request.
Use a reviewed published standard revision. If only a selected candidate exists,
state that fact and keep the result draft. Never invent a tag or deployment target.

1. Create/inspect the authorized project repository; choose its profile, prefix,
   shared workspace ID and real environment/check procedures. Staging defaults on.
2. Obtain clean official checkouts at the selected standard commit and the exact
   Tracker commit in `compatibility.json`. The scaffold refuses a dirty or different
   engine. Python 3.11+ runs the Tracker exporter; Master validation supports 3.9+.
3. Preview, then apply the scaffold from the standard checkout:

   ```sh
   python3 scripts/standard.py init --root /path/to/new-project --profile local \
     --repository owner/new-project --name "New Project" --id-prefix NP \
     --workspace-id new-project --tracker-root /path/to/pinned-tracker
   ```

   Add `--apply` to create files; add `--no-staging` for an explicitly disabled stage.
   `--python /path/to/python3.12` selects the export runtime if necessary. Profiles:
   `vps`, `n8n`, `n8n-source` (explicit Git-only scope), `local` (manual pull),
   `package`, `tooling`.
4. Preserve the supplied specs, describe the actual system, adapt modules, check
   commands, required CI jobs and environment procedures. Synchronize the
   descriptor's policy and Tracker config; validation rejects disagreement. Draft
   validation: `python3 scripts/standard.py validate --root PROJECT --allow-draft`.
   Fill every setup marker; never claim draft placeholders represent real setup.
5. Publish the initial repository/main using its authorized bootstrap procedure.
   Use `scripts/onboard.py --root PROJECT --tracker-root PINNED_ENGINE --workspace
   TRACKER_REGISTRY/workspace.json` to preview branch/label/registration setup.
   Add `--apply` to create a missing stage from main, initialize project labels and
   prepare an idempotent registry entry with a fallback config. It preserves
   differing existing branches and registrations for audit. The engine checkout
   and the registry editing checkout may be separate.
6. Create/link the necessary Tracker registry issue/PR and complete its maintained
   review/publication process. Verify the project's fresh live board: right repo,
   IDs, modules, exactly the selected columns, successful empty/project sync and
   effective permissions. Verify private Action access, required check names and
   branch controls. Local registration alone does not make the project visible.
7. Record the durable onboarding proof in `tracker.verification`, set registration
   to `verified`, finish environment verification, then set adoption to `ready`.
   Run strict validation and actual project tests before claiming full readiness.

The generated `.workflow/template-base.json` stores the unmodified generated base
for future three-way comparisons. Commit it; do not rewrite it to disguise local
changes. The small Tracker client/config live in the project; the entire Tracker
app does not. A failure in registration/publication leaves the project visibly
pending and resumable, with no fabricated completion.

## Existing project adoption

Audit AGENTS, Tracker config/history, open PRs/branches, CI, release state, actual
deployment and unique fixes first. Existing Issue IDs, custom labels/modules,
installers, environment settings, backup/rollback and authorization survive.
Finish existing open PRs under their original rules before activating the new
contract; report these blockers rather than renaming history. Reconcile evidence
for already completed tasks before switching completion rules.

Preview in an isolated new directory. The initializer refuses all file collisions
and symlinks; integrate intentionally in a project issue/PR. Never delete local
files to satisfy the template. Without a trusted earlier template baseline, the
upgrader stops for this audited adoption; it does not guess or overwrite files.
After reviewing the imported base and the merged result, retain the original
rendered template as baseline, with actual deviations in the project files and
`delivery.json` exceptions. Test both local behavior and shared checks.

An owner-authorized Git-only n8n adoption may use `n8n-source`; see the
[profile](../profiles/n8n.md). Keep an unreleased selected revision visibly draft.
To obtain hosted feedback during audited adoption, the pinned shared Action may
explicitly use `allow-draft: 'true'`. This permits incomplete setup findings only;
it does not authorize runtime work or pretend a standard release exists. Remove
that option when strict readiness is verified. Record any one-time bootstrap
merge exception in the project issue/runbook before applying the new contract.

Audit already-completed issues and their original merged PR evidence before
activating the new policy; retain their accepted history through an explicit,
reviewed reconciliation record, without inventing old stage or runtime tests.
Unfinished tasks keep their original acceptance criteria and remain unfinished.

## Skill distribution

Canonical source: `.agents/skills/project-workflow/SKILL.md` in Master Repo. Install
that directory once per agent environment from a reviewed immutable revision using
its supported skill installation mechanism. Another machine/cloud environment
needs its own installation. This task changes the source; it does not globally
install it as a test. Projects keep their short AGENTS and local descriptor/docs,
not another full copy of the global skill. Their instructions also work without it.

The skill finds the project's pinned standard/Tracker and follows that version.
Installing a newer skill does not migrate a project. No instruction relies on
files next to a globally installed skill; it fetches/locates explicit pinned repos.

## Private Action access

Grant intended consumers access to the private Master Repo Action through the
actual GitHub account's supported controls and verify it on a real consumer PR.
Do not make the repository public or expose credentials as a workaround. The
shared Action only validates data and pins; it does not execute descriptor commands.

## Knowledge ownership

Use the [layout contract](../templates/workflow/LAYOUT.md). New repositories get
separate `docs/repository/`, `docs/system/` and `docs/runtime/` areas. System/runtime
outlines become project-owned at creation; upgrades never overwrite or merge them.
An earlier mixed baseline stops without writes: audit and split local documents,
keep safeguards and forwarding paths, record the move map and validate the final
candidate. Retain the pristine newly rendered template as the new baseline.
Shared helper implementations live in `.workflow/tools/`; old `scripts/` paths
remain compatible. No layout change implies new deployment or task semantics.
