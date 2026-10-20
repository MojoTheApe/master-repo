# Deliver the process separately from the product

This rule applies to every repository, role and delivery profile. Installation
type does not change it. A process update changes how agents develop, review,
track or verify work. A product update changes what users run, install or use.
Keep their accepted scope, verification, versions and completion evidence separate.

| Accepted outcome | Required result |
| --- | --- |
| Repository instructions | Independently reviewed, checked instructions included in main |
| Isolated task/workflow tooling or compatible shared support | Independently reviewed source, relevant process checks, admitted main integration and any actual delivery of that tooling |
| Product, installation, update or production behavior | The product's maintained checks and actual delivery for its configured target |
| Mixed work | Separate process and product changes; keep each outcome unfinished until its own evidence exists |

A process-only change does not publish a new consumer installer, deploy its
application, restart its service or publish its n8n workflow. Tooling can have its
own releases, skill distribution or service deployment: delivering that process
does not mean delivering the consuming product. An explicitly requested product
publication remains required even if the underlying application bytes are unchanged.

## Establish the boundary

Classify the complete accepted scope and actual immutable diff, including
dependencies and indirect inputs. A filename, directory, task label or author
statement alone cannot establish that executable tooling is isolated from the
product. Preserve independent review and checks that test the changed process.
Build/install/update inputs and code that can change product publication retain
their applicable product checks. Running those checks is separate from publishing
an otherwise unchanged product.

Split mixed changes before approval where possible. A process PR never completes
a broader parent with missing product or business acceptance. Unknown effects
need investigation and relevant checks; they do not authorize process completion
or automatically authorize a product release.

## Supported execution and compatibility

The existing [instruction-only contract](process-instructions.md) remains its
bounded schema1 route. Do not expand it to arbitrary scripts, CI or configuration.
The companion Tracker contract adds complete canonical shared-support proof for
published standard/engine upgrades, while preserving ordinary integration gates.
Its supported proof, exact source capability and actual adoption must be verified
before using process completion beyond the existing instruction route.

For a proven shared-support update, keep the current source approval, real
ownership, batch/Stage/main admission and applicable checks. Select process delivery
without a consumer product-release request; record the exact admitted process
outcome. Never silently cancel or repurpose an already authorized delivery request,
reinterpret old receipts, fabricate deployment proof or add a generic completion
waiver. Unsupported executable changes require a maintained verified process
boundary before they can obtain automated process-only completion.

Master owns this global rule, templates and canonical skill. Tracker owns proof,
commands and completion projection. Projects own their product/runtime boundary
and relevant local process checks. New source and distributed instructions do not
silently upgrade pinned clients or activate consumer state. Follow the
[coordinated upgrade procedure](workflow-upgrades.md), preserving local controls,
original task scopes, history, actual owners and unfinished product delivery.
