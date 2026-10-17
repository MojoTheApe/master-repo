"""Selected normative guidance; exact commands/templates remain Tracker-owned."""


def selected(data):
    workflow = data['workflow']
    execution = workflow.get('execution')
    stage = workflow['staging']
    version = execution['schema_version'] if execution else None
    if version not in (None, 1, 2, 3, 4):
        raise ValueError('Unsupported selected instruction route')
    direct = version == 4 and execution.get('route') == 'direct'
    batch = version in (2, 3) or version == 4 and execution.get('route') == 'batch'
    if version == 4 and not (direct or batch):
        raise ValueError('Modern instructions require an explicit supported route')

    if version is None:
        route = ('This project retains the legacy single implementation slot and its '
                 'independent review attestation. Use the adopted legacy handoff and '
                 'slot recovery commands. Related tasks may share a source only under '
                 'that legacy contract; do not use execution-lane commands.')
    elif version == 1:
        route = ('This project selects execution schema 1 with '
                 f"{execution['implementation_limit']} implementation slots and one "
                 'review/integration lane. Each source PR contains exactly one task. '
                 'After author handoff, acquire the genuine review lane before '
                 'starting independent review and retain it through the selected '
                 'integration and admitted main merge. Further tasks wait for its explicit release.')
    elif direct:
        route = (f"This project selects execution schema 4, direct integration, "
                 f"{execution['implementation_limit']} implementation slots and "
                 f"{execution['review_limit']} independently owned source-review slots. "
                 'Each engineering source has one genuine task. It does not enter '
                 'Approved or a synthetic batch. The actual independent source '
                 'Reviewer retains its source lane and the linked single integration '
                 'reservation through admitted main merge, exact durable accepted-scope '
                 'receipt, task-status reconciliation and archive/release. Return, '
                 'stop, takeover and crash recovery retain the exact source binding; '
                 'a public subject or digest never replaces a secret ownership claim. '
                 'Wait for current integration, intake, Stage and maintenance owners.')
    else:
        topology = ('one shared source/combined-review lane and a separate Coordinator '
                    'batch reservation' if version == 2 else
                    f"{execution['review_limit']} separately owned source-review slots "
                    'and one separate integration Reviewer, plus a Coordinator batch reservation')
        route = (f"This project selects execution schema {version} with "
                 f"{execution['implementation_limit']} implementation slots, {topology}. "
                 'Each ordinary source PR contains exactly one task. Independent '
                 'source review and checks move it from Review to Approved and release '
                 'its source-review ownership. Development alone ends at Approved. '
                 'An integration request selects one frozen batch of 1..'
                 f"{execution['batch_limit']} tasks; no minimum batch size is required. "
                 'Its separate Coordinator claim preserves every source, author, '
                 'accepted scope and current approval. Independently review and check '
                 'the combined candidate; integration/promotion preserves the complete '
                 'frozen member set and batch identity. Ship-all snapshots current '
                 'Approved intake, leaving later arrivals for another intake.')
    if stage:
        if batch:
            route += (' Stage is enabled: the reserved batch goes to permanent stage, '
                      'its exact configured target/tree is verified, then the unchanged '
                      'batch is promoted to permanent main. Ordinary sources are approval-only.')
        else:
            route += (' Stage is enabled: working branch -> permanent stage -> permanent '
                      'main. Verify the exact Stage target/tree before promoting unchanged '
                      'content. Keep one current candidate; preserve the task branch for fixes.')
    else:
        route += (' Stage is disabled: the reserved independently reviewed batch is '
                  'admitted to main using the pinned batch direction; ordinary sources '
                  'remain approval-only.' if batch else
                  ' Stage is disabled: reviewed working branch -> main. There is no Stage column.')

    context = ''
    if 'task_context' in workflow:
        current_source = 'reviewed source' if version == 4 else 'Approved source'
        context = ('## Adopted task context\n\n'
                   'Use the exact [local task-context guide](TASK_CONTEXT.md) before '
                   'start/resume and for the strict terminal journal. Assess current '
                   'requirements, main and semantic readiness. An unchanged ' + current_source +
                   ' may retain approval after main advances only through the '
                   'adopted owned independent compatibility review. New scope or actual '
                   'conflicts return to a claimed author; disjoint paths alone prove '
                   'no semantic compatibility.')
    process = ''
    if 'process_instructions' in workflow:
        process = ('## Adopted instruction-only exception\n\n'
                   'Use the exact [local process guide](PROCESS_INSTRUCTIONS.md) and '
                   'its complete immutable-diff classifier. Only proven eligible '
                   'regular instructions retain genuine author/review ownership and '
                   'instruction checks through Review -> main -> Merged. Do not move '
                   'that source to Approved, batch or Stage or manufacture installation '
                   'proof. Wait for reserved integration/unpromoted Stage ownership. '
                   'Mixed, unsafe, unknown or incomplete proof follows the selected '
                   'ordinary route and actual target obligations.')

    completion = data['completion']
    if completion == 'reviewed-merge':
        target = ('This project completes fully implemented scope after independent '
                  'review, successful checks and an admitted main merge. Its '
                  'repository-only/manual-pull target creates no installer or '
                  'application deployment obligation.')
    elif completion == 'verified-stable-package':
        target = ('This package project remains unfinished after main until the '
                  'maintained producer publishes the stable release and verifies '
                  'installation for the exact accepted source/task/target. Record the '
                  'genuine delivery receipt; merge or a tag alone is insufficient.')
    elif completion == 'verified-production':
        target = ('This project remains unfinished after main until its maintained '
                  'producer verifies production delivery for the exact accepted '
                  'source/task/target. Record the genuine delivery receipt; source '
                  'storage or Stage evidence alone is insufficient.')
    else:
        raise ValueError('Unsupported selected completion rule')
    if data['profile'] == 'n8n-source':
        target += (' The selected n8n-source profile covers Git source only. Workflow '
                   'publication and verified business behavior require their own '
                   'actual authorization/proof and cannot be claimed from this merge.')
    elif data['profile'] == 'n8n':
        target += (' Preserve LIVE_FIRST controls. Workflow publication is distinct '
                   'from upgrading the n8n server or proving a business outcome.')
    if stage:
        target += (' Stage is enabled; verify its configured target before unchanged '
                   'main promotion through the selected route. Git-only Stage checks '
                   'must be labelled as such rather than runtime acceptance.')
    else:
        target += ' Stage is explicitly disabled and does not require a Stage receipt.'
    if batch and completion != 'reviewed-merge':
        target += (' An authorized eligible runtime/package integration uses the '
                   'pinned batch delivery continuation by default, unless explicitly '
                   'deferred. Source approval alone authorizes no delivery.')
    if version in (2, 3) and not stage and completion == 'verified-stable-package':
        target += (' When adding a new optional policy to an existing project, first '
                   'verify the exact pinned engine supports its bounded one-member '
                   'selection package. Finish and reconcile that fully verified package '
                   'before reserving maintenance for owned idle activation. Do not '
                   'co-select policies or deliver through a held maintenance gate; '
                   'other pending delivery and unresolved owners still block adoption.')

    scoped = ''
    if 'completion_policy' in workflow:
        scoped = ('## Adopted accepted-scope completion\n\n'
                  'Read the exact [local completion guide](COMPLETION_POLICY.md). '
                  'The explicitly selected descriptor/config policy requires compatible '
                  'published readers/writers and separate owned idle durable activation. '
                  'Original review/batch scope is preserved; changed requirements are '
                  'unfinished, unknown old scope stays unverified, and explicit historical '
                  'acceptance never invents current delivery. Follow the exact separate '
                  'selection/activation order when task context is also new.')
        if version == 4:
            scoped += (' Modern execution/context selection requires owned idle '
                       'outer7 adoption over the actual known completion5 or retry6 '
                       'base. Preserve retry anchors, budgets and unresolved intents; '
                       'never strip a state fence or clear another owner for an upgrade.')
    retry = ''
    if 'ci_retry' in workflow:
        retry = ('## Adopted CI retry policy\n\n'
                 'Read the exact [local retry guide](CI_RETRY.md). The explicitly '
                 'mirrored policy needs published compatible readers/writers and '
                 'owned durable activation. Use only the maintained command and '
                 'persisted operator-attested diagnosis for a still-relevant '
                 'verification-only run. Original executions, outside reruns and '
                 'uncertain dispatches consume the durable episode budget. New '
                 'chats, empty commits, run IDs or cause/plan renaming do not reset '
                 'it. An uncertain POST remains held until supported reconciliation; '
                 'elapsed time never authorizes another request. Read-only CI '
                 'gates gain no write permission or release authority.')
    source = ('Create a real Issue before implementation. Ideas remain Idea; requested tasks\n'
              'start Backlog. Planning does not claim code capacity. When development is\n'
              'requested, read the entire Description and Specifications and use the pinned\n'
              "Tracker's `work` command to claim the actual available slot and verify In Progress.\n"
              'Follow its supported branch/actor/session rules and any host-required prefix.\n'
              'An older task needs current readiness assessment, not routine owner reapproval.')
    pr_reference = ('Prepare a linked PR after implementation and self-checks. Preserve the exact\n'
                    'machine-readable `Tracker issues:` field and source-versus-integration identity\n'
                    "from this project's PR template. No automatic Issue-closing keywords.")
    if 'knowledge_capture' in workflow:
        source += ('\n\nOnly ordinary capture under the identical already adopted explicit '
                   'knowledge policy and real approved mandate uses a genuine capture '
                   'operation instead of an Issue. It consumes normal Worker/review/integration '
                   'capacity, complete immutable-diff classification and independent semantic '
                   'attestation. Eligible regular UTF-8 .md/.txt notes cannot alter governance, '
                   'structure, rules, configuration or automation. Mixed, unsafe, unknown or '
                   'outside-mandate changes use a real engineering task. Notes cannot introduce '
                   'or broaden their own mandate. Keep the exact operation, owner and recovery '
                   'history; never create a fake task, dependency or release member.')
        pr_reference = ('Prepare the actual source PR after self-checks. Preserve the exact '
                        'task, capture or frozen-batch identity from the pinned selected PR '
                        'template. Capture uses its genuine operation field without an Issue '
                        'alias; ordinary engineering keeps its real task. No automatic '
                        'Issue-closing keywords. A capture receipt grants no package, runtime '
                        'or publication proof. The selected Stage choice and full checks remain.')
    return {'__SELECTED_WORKFLOW__': route, '__TASK_CONTEXT_GUIDANCE__': context,
            '__PROCESS_GUIDANCE__': process, '__SELECTED_DELIVERY__': target,
            '__COMPLETION_GUIDANCE__': scoped, '__CI_RETRY_GUIDANCE__': retry,
            '__SOURCE_GUIDANCE__': source, '__PR_REFERENCE_GUIDANCE__': pr_reference}


def render(text, data):
    for token, value in selected(data).items():
        text = text.replace(token, value)
    return text
