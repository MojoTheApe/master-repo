# VPS applications

When project staging is enabled (the default), use one logical stage environment
and one production environment. If explicitly disabled, retain independent review,
CI and verified production delivery without inventing a stage receipt. Each
environment may contain multiple services. Keep configuration, credentials and writable data
separate. Same-host staging needs demonstrated isolation and resource limits;
otherwise report the capacity/isolation blocker before provisioning anything paid.

Build a pinned artifact once, verify it in stage and promote those bytes with
production configuration. Preserve existing native admission and environment-bound
proof. Reuse compatible pinned components without duplicating mutable state.

Prefer the application's maintained controller: inspect active work, lock/drain
as appropriate, take consistent backups, prepare a candidate, switch safely,
verify and retain a compatible rollback set. Do not edit running files one by one.

Document stage/prod service identities, ports, data roots, secret references,
release selectors, test commands, authorized approval and post-release behavior.
Stage must not send real customer messages or publish to production destinations.

Local retention protects current environments, an in-flight release, selected
rollback artifacts and every live/evidence/preview dependency. Archive/delete only
under the project's scoped policy after recovery and references are verified.
Generated customer builds are not application installations and need their own
retention rules. Git history does not replace consistent off-device data backups.

For ReactForge, retain orchestrator authority, renderer/consumer separation,
existing maintenance locking and independent qualifications. Its legacy path
names do not justify cosmetic live renaming. Hotfix/update redesign stays deferred.
