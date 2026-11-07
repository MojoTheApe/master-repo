# Engineering context

The product is shared delivery tooling, templates, validation and the canonical
navigation skill. Python tools must remain dependency-free and support Python
3.9+. Tracker export/client uses the compatible pinned engine and Python 3.11+.
Keep schema-1 compatibility and each consumer's local safeguards. The self
repository retains its schema-1 descriptor; consumers retain their actual schema2
or explicitly selected compatible schema3. Modern policy validation belongs to
the fixed canonical Tracker snapshot, not a second Master state implementation.

Read [current implementation](PROJECT.md), [the standard](../../standard.md) and
the canonical [engineering rules](../engineering-standards.md). Use those rules
for scope/design review instead of maintaining a second local checklist.

## Source boundaries and local conventions

`standard.md`, `docs/`, `profiles/` and `templates/` define the shared product.
`scripts/` implements descriptor checks, generation and upgrades. The canonical
Project Workflow is `.agents/skills/project-workflow/`; AI Skills is its verified
distribution mirror. Do not edit mirrors or generated Tracker snapshots manually.

Use the existing standard-library Python style and preserve Python3.9 syntax.
Keep runtime tools dependency-free. This repository has no JavaScript application,
database or runtime service to standardize. Generated project context is a seed;
real system/runtime knowledge becomes project-owned and must survive upgrades.

## Examples to follow

- [Link validation](../../scripts/check_links.py) checks local Markdown targets
  through the existing generator's file map, including generated destinations.
  When adding documentation navigation, add the right source link and run this
  checker rather than introducing another link scanner or network service.
- [Project generation and upgrades](../../scripts/project.py) reuse the selected
  Tracker export, append common PR notes and render the existing templates.
  Upgrade handling preserves project-owned knowledge and detects conflicts.
  Change the relevant template for shared prose; do not copy Tracker's command
  implementation or overwrite a consumer's system context. The existing
  [project tests](../../tests/test_project.py) exercise those boundaries.

These are examples of ownership and reuse, not instructions to copy every coding
detail. No broad refactor or formatter migration is needed for an instruction edit.

## Actual verification

Run `python3 -m unittest discover -s tests -v`,
`python3 scripts/standard.py validate --root .` and
`python3 scripts/check_links.py` as required by `delivery.json`.
`python3 tests/portable_contract_fixture.py` exercises the existing canonical
portable fixtures; CI also runs it on Python3.9. The unit suite covers isolated
generation and upgrades. New or changed executable/export contracts retain their
declared additional compatibility checks.

For this prose/template update the existing checks cover the changed artifacts.
No new formatter, linter, type migration, dependency or CI setting is needed.
The link checker verifies local files, not external URL availability or anchors.
