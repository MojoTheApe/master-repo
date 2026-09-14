# The delivery descriptor

`delivery.json` describes how a project fulfills the standard. JSON keeps tooling
dependency-free. Commands are descriptions/entry points: the validator never runs
them. Put passwords, tokens and private keys in appropriate stores, not here.

| Field | Meaning |
| --- | --- |
| `schema_version` | Descriptor format; currently 1 |
| `project` | Human name and canonical repository URL |
| `standard` | Source repository, VERSION label and immutable revision |
| `profile` | `vps`, `n8n`, `local`, or internal `standard` |
| `adoption` | `draft` until configuration and actual procedures are verified |
| `tracker` | Existing system, URL, PR reference convention and validation procedure |
| `checks` | Project verification commands/procedures |
| `environments` | Stage and production targets and verification procedures |
| `delivery` | Candidate identity, approval, staging/promotion, rollback and backup procedures |
| `completion` | Verified production, verified stable package, or reviewed merge |
| `exceptions` | Specific reason, scope and reference for an intentional deviation |

All keys are checked; unknown keys are errors to catch misspellings. Empty fields
and `__CONFIGURE__` markers cannot pass readiness validation. Real values can be
commands or precise runbook section references. A real Git commit is syntactically
required but this offline tool cannot prove that it exists remotely or is released.

VPS and n8n profiles require stage/production descriptions; local uses a pilot/test
target and a stable distribution target under the same keys. All three require
explicit approval. Backup may refer to a justified stateless policy in the runbook;
it must not merely be omitted. The internal standard profile has no environments
or deployment procedures and completes after reviewed merge.

`audit` is read-only and prints findings. `validate` fails for incomplete setup.
`validate --allow-draft` permits draft/placeholder findings while still rejecting
malformed structure, mutable references and broken action pins. It is for authoring
templates, not release admission. Exit 0 means the requested check passed, 1 means
descriptor findings, and 2 means an input/operation error.

The reusable action always runs strict validation and checks its own checkout
matches the consumer's expected revision. It has no production side effects.

Evidence limits: these checks establish configuration consistency, not deployed
state, genuine independent review, backup restoreability, live tests, effective
GitHub permissions, or absence of every possible embedded secret. Verify those
through the project's maintained tools and receipts.
