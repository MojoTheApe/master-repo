# Versioning and upgrades

`VERSION` identifies the proposed standard version. A file saying `0.1.0` does
not establish that a GitHub release exists. The initial implementation must pass
review and merge before an authorized release can publish `v0.1.0`.

For this standard: patch changes clarify/fix compatible behavior; minor changes
add compatible capabilities; major changes require incompatible consumer changes.
Record migration notes for any new readiness requirement. Consumer application
versions are independent from these standard versions.

## Publish a standard

1. Review the exact candidate; run unit tests, self-validation and link checks.
2. Merge according to repository policy and verify the resulting commit's CI.
3. Inspect the final tree, VERSION and migration notes; obtain any missing release
   authorization for that candidate.
4. Publish an immutable version tag and release linked to that commit and checks.
5. Demonstrate onboarding using a clean checkout of the published commit.

Do not move published tags. No workflow in this repository automatically tags,
merges or publishes a standard. The production approval concept maps here to
authorization of a reviewed standard release, not a server deployment.

## Consumers pin an exact revision

The consumer descriptor records a 40-character commit SHA. Its action reference
must use the same SHA. Tags are useful labels; a moving branch or mutable tag must
not silently change release behavior.

The master repository itself uses `revision: self` to validate its current source
tree. Only the validator's own source root may use this value. Consumer projects
must use an immutable SHA.

## Upgrade an existing project

Prepare a separate issue/PR that changes the standard revision and action pin
together. Compare old and new rules, retain project-specific details and explain
migrations or exceptions. Run the project's required checks and isolated delivery
checks where relevant. Apply only after review.

The initializer never overwrites existing files and is not an upgrade engine.
Neither ordinary feature work nor a new commit in master-repo automatically
upgrades consumers. A GitHub template creates starting files, not a continuous
inheritance connection.

Current migration notes: initial version; no existing consumers are claimed to
have adopted it. ReactForge's migration is independent work in progress.
