# Adopt the standard

## New projects

Use a reviewed immutable master-repo revision. Run `standard.py init` in preview
mode, choose `vps`, `n8n` or `local`, and apply to the intended project. A preview
does not create the destination. The resulting setup is explicitly draft.

Fill `delivery.json` with actual project details and edit `docs/DELIVERY.md`.
Retain the existing tracker, or configure the selected tracker for a new project.
Add the existing application checks and real tracker validation to CI. Verify
environment separation, backup/rollback and the applicable delivery process before
setting `adoption` to `ready`. Do not invent target URLs or executable commands.

## Existing projects

Audit first. Read their AGENTS.md, tracker guide, CI and actual deployment
configuration. Inspect current branches, work and live references read-only when
authorized. Preserve useful integrations and any stronger local safeguards.

The initializer refuses to overwrite **any** destination file and rejects symlink
targets/parents. If it reports a conflict, manually integrate the proposed changes
in a normal project PR. Do not remove existing files to make scaffolding succeed.
AGENTS.md and PR templates often need small additions rather than replacement.

Run the descriptor audit and the project's real checks. Record what is verified,
what remains draft, and any documented exception. Migrating the description alone
does not mean staging, deployment or automatic ticket transitions exist.

## How agents find it

Every adopted repository has a small AGENTS.md pointer to its own descriptor and
runbook. These files travel with the repository and work without chat history.
The project-workflow skill is available automatically while working in master-repo.

For discovery across other repositories, install that skill once in each Codex
environment using the supported skill installer, from
`MojoTheApe/master-repo/.agents/skills/project-workflow` at a reviewed commit.
Alternatively invoke it explicitly while providing the source repository.
Installation and access must also be set up on other machines/cloud environments;
merely storing a skill in GitHub does not install it everywhere.

The skill is deliberately self-contained: it locates the pinned standard from
the consumer descriptor. It does not rely on relative links outside the installed
skill directory. If the skill is unavailable, the checked-in AGENTS.md/runbook
still explains the process and the exact standard reference.

Do not add broad instructions that activate repository migration for unrelated
tasks. Normal feature work follows the consumer's adopted version; standard
upgrades are separate tasks. A plugin can package distribution later if needed.

## GitHub access

This master-repo is private. To use its action from another repository, an owner
must grant the intended repositories access in the master's Actions settings,
within the options supported by the current GitHub account/plan. The consumer
must also allow the pinned action. Test cross-repository access before claiming
adoption is ready. Do not make the repository public as a workaround.

The scaffolded CI uses a GitHub-hosted runner with `contents: read`. It does not
receive deployment secrets. The shared action only validates the descriptor; it
does not execute commands found in that descriptor.

References: [Codex customization](https://learn.chatgpt.com/docs/customization/overview),
[sharing private Actions](https://docs.github.com/en/actions/how-tos/reuse-automations/share-with-your-private-repository).
