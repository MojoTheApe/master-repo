# Local projects

The default local profile is a repository the owner pulls manually. It completes
after independent review, required tests, optional stage verification and the
admitted merge into main. Do not wait for the owner's pull, create an installer or
require stable distribution unless the package profile was explicitly selected.

With staging enabled, keep a permanent stage branch and use a real isolated local
checkout/test environment or the project's maintained preview. Describe its
verification target; a branch alone is not a tested environment. The user can
explicitly disable staging. Preserve local data and configuration on every upgrade.

For an application with an installer, use `package`: test the candidate, publish a
verified stable package and perform the agreed installation/update check. Record
that delivery before completion. Keep package signing, data compatibility and
rollback rules local. Do not rewrite an existing updater through standard adoption.

Schema 1 consumers retain their earlier stable-package policy until migrated.
