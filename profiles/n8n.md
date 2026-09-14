# n8n workflows

Inspect the installed n8n version, license and current development integration.
Reuse existing working delivery. A workflow change and an upgrade of the n8n
server/node packages are different releases; use the VPS profile for the latter.

Native Git environments require n8n Business/Enterprise according to current
documentation. A self-hosted Community installation can use supported API or
export/import tooling instead; validate the actual endpoints and capabilities.
Do not buy a plan or implement a competing integration without a concrete need.

Record whether stage/prod are **separate instances** or **separate workflows on
one instance**. The latter is weaker isolation, not two independent servers.
It needs stable workflow-ID mapping, separate test destinations/webhooks/schedules,
scoped credentials and controls against test side effects reaching production.

## Promotion contract

1. Reconcile the repository with the authoritative current workflow before edits.
   Preserve existing LIVE_FIRST/provenance rules; never overwrite newer live work
   merely because a local JSON file exists.
2. Export/version selected definitions and all required dependent subworkflows.
   Associate them with the ticket/PR and an exact content digest.
3. Import/pull the reviewed candidate into stage; bind test connections/settings.
4. Verify the actual loaded version and behavior with safe test inputs.
5. After approval, promote that same content to the recorded production IDs.
   Rebind production connections and publish/activate under the agreed policy.
6. Verify actual publication and operation. A Git push, import, successful API
   response and successful business outcome are separate facts.

Do not pull a moving branch and assume it is the approved candidate. Native Git
mapping may use controlled promotion branches; an API path can use a hashed export.
Prevent concurrent edits and stale promotion. Preserve production credentials and
intended activation state; do not blindly copy the entire staging workflow object.

Native Git carries definitions and credential/variable stubs, not secret values
or a full instance backup. Inspect exports for hardcoded secrets. Back up relevant
database state, encryption-key recovery material and required files securely.
Handle ownership, deletion and data-table/schema changes explicitly. Reverting a
workflow cannot undo messages, payments or other external actions already executed.

## VPS with an IP whitelist

A self-hosted GitHub Actions runner initiates outbound HTTPS to GitHub. GitHub
does not require unsolicited inbound access to n8n. If runner and n8n share a VPS,
configure a local/internal API route; otherwise allow the runner's controlled
egress IP or private network route. Check outbound restrictions with IT too.

Keep deployment credentials on restricted trusted jobs. Run PR code checks on
ordinary isolated runners, not on the production-connected runner. Installing a
runner alone does not implement workflow promotion or approval. Its host and
trust boundary require explicit setup; this repository does not register it.

Sources checked 2026-09-14: [n8n source control](https://docs.n8n.io/administer/use-source-control-and-environments),
[API](https://docs.n8n.io/connect/n8n-api),
[push/pull behavior](https://docs.n8n.io/administer/use-source-control-and-environments/push-and-pull-changes),
[runner communication](https://docs.github.com/en/actions/reference/runners/self-hosted-runners#communication).
