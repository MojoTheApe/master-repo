# Locally installed applications

The staging equivalent is a test package on supported operating systems and
agreed pilot machines. Production is the stable distribution channel. Do not add
a VPS or permanent server environments when the application does not need them.

Build and identify the release package once. Verify installation, upgrade and
required behavior on the supported OS/architecture matrix. After approval,
publish that candidate to the stable channel with its version, hash and applicable
signing/notarization evidence. Publish per-platform artifacts as one release set.

Users install it, or an already-authorized updater offers/installs it according
to project policy. A Git push does not authorize modifying everybody's computer.

Record distribution location, pilot target, install/update checks, approval role,
OS support, prior compatible package and local data/schema migration policy.
Keep user data and credentials separate from application binaries. An old
installer is not a backup of the user's data.

Done normally means a verified stable package is available and the agreed pilot
install/upgrade check passed. Do not wait for every user's laptop to update unless
that rollout coverage is explicitly part of the ticket's acceptance criteria.
