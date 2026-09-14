# Project delivery

Status: draft. Configure this runbook from verified project facts; do not mark
adoption ready merely because these files exist. Keep `delivery.json` aligned.

## Tracker and review

Describe the current tracker, real ticket/PR reference convention, existing link
validator, status mapping, automatic/manual transitions and responsible roles.
Keep partial and deployment-pending work out of Done. Add the real convention to
the PR template and the real tracker validation step to CI.

## Checks and environments

Record local/CI checks, stage/pilot and production/distribution targets, access
methods, service/workflow IDs, data separation and safe functional test procedures.
Link existing guides instead of maintaining conflicting copies. Include the
selected profile and any justified exception.

## Candidate and promotion

Describe immutable candidate identity, how main reaches stage, what proves stage
passed, who approves that exact candidate, the maintained promotion entry point,
deployment locking and actual post-delivery verification. Record runtime facts
in deployment receipts; a static target URL is not installation evidence.

## Backup and rollback

Identify protected data and compatible prior artifacts. Describe consistent
backup, off-device recovery, isolated restore verification, data/schema limitations
and bounded retention. An old code directory is not a data backup. State a precise
reason if a data-backup step is not applicable to this project.

## Evidence and completion

Record actual checks and environment setup still outstanding. Define whether Done
requires verified production, a verified stable package or reviewed merge for a
specific non-deployed change. Document current approval/protection limitations.
