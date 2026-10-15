# Runtime procedures

This project-owned document describes actual environments and operational rules.
Fill it from verified facts. If there is no runtime, state that explicitly.

## Environments and access

Document the actual targets, their purpose, credential boundaries and permitted
access. A branch name alone does not establish a connection to an environment.

## Delivery and verification

Describe the actual maintained transfer/publication commands or trusted CI,
existing authorization and acceptable verification. Follow the shared
[continuation contract](../repository/DELIVERY_CONTINUATION.md): bind exact merged
revision/tasks/target/run/artifact; serialize target mutations; prevent stale
replacement; persist attempts and resume retries idempotently. Distinguish deploy,
verification and receipt failures. Record final Tracker delivery only after actual
acceptance, and retry a missing receipt without repeating a completed deployment.
Test failure/retry and duplicate requests before claiming automatic delivery.
An authorized integration/delivery request covers this chain after main without
another routine owner approval; retain any explicit separate local boundary. Keep Git review and task rules in
[repository delivery](../repository/DELIVERY.md).

## Recovery and data

Document rollback, backup and side-effect safeguards. Do not store credentials.
