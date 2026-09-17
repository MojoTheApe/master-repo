# This repository's layout

`docs/repository/` governs work on Master Repo itself. `docs/system/` describes its
implemented product and constraints. `docs/runtime/` states its runtime boundary.
`standard.md`, `profiles/`, reference docs and `templates/` are the shared product
that consumers adopt, not additional self-repository instructions. `scripts/`
contains this product's actual implementation; it is not an exported Tracker copy.

Consumers receive the [separated layout contract](../../templates/workflow/LAYOUT.md).
Existing paths remain pointers for earlier agents and links. Historical product
changes stay in system history; new maintenance-only changes go in repository history.
