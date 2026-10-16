"""Portable task tracker commands. Run from a repository with Python 3.11+."""
from __future__ import annotations
import argparse
import json
import shutil
import sys
from pathlib import Path
from . import commands, merge, queue, workflow, catalog, identifiers, releases, intake, pr_checks, delivery, execution, batches
from .github import GitHub, install_labels
from .model import DEFAULT_CONFIG, PRIORITIES, TYPES, load_config, names, payload, tasks_from_issues
from .sync import sync


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, default=Path('tracker/config.json') if Path('tracker/config.json').is_file() else DEFAULT_CONFIG)
    p.add_argument("--gh-command-json", default='["gh"]')
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("sync"); s.add_argument("--output", type=Path, required=True); s.add_argument("--allow-empty", action="store_true")
    sub.add_parser("init", help="Create missing labels and the configured empty release milestone")
    sub.add_parser("list", help="Read current tasks, releases and module descriptions")
    sub.add_parser('guide', help='Print the canonical agent workflow from this pinned engine')
    a = sub.add_parser('timing', help='Record actual legacy review/merge duration; grants no ownership or admission')
    a.add_argument('action', choices=('start', 'stop'))
    a.add_argument('--kind', choices=('reviewing', 'merging'), required=True)
    a.add_argument('--issues', nargs='+', default=[])
    a.add_argument('--actor', required=True); a.add_argument('--session', required=True)
    a = sub.add_parser('maintenance', help='Owned CAS admission pause; compatible writers/service must be published first')
    a.add_argument('action', choices=('show', 'reserve', 'resume', 'transfer'))
    worker_arguments(a)
    a.add_argument('--previous-claim'); a.add_argument('--stopped', action='store_true')
    a.add_argument('--report-file', type=Path); a.add_argument('--apply', action='store_true')
    a = sub.add_parser('delivery-policy', help='Inspected idle staging toggle with explicit preserved-evidence reconciliation')
    a.add_argument('action', choices=('migrate',))
    a.add_argument('--previous-config', type=Path, required=True); a.add_argument('--previous-revision', required=True)
    a.add_argument('--report-file', type=Path, required=True); a.add_argument('--apply', action='store_true')
    worker_arguments(a)
    a = sub.add_parser('task-context', help='Explicit task readiness, requirements journal and independent source compatibility')
    a.add_argument('action', choices=('adopt', 'assess', 'review-acquire', 'review-record', 'review-release'))
    a.add_argument('issue', nargs='?')
    worker_arguments(a)
    a.add_argument('--evidence-file', type=Path); a.add_argument('--report-file', type=Path)
    a.add_argument('--apply', action='store_true')
    a = sub.add_parser('ci-evidence', help='Optional trusted job coverage; required checks and runtime gates remain mandatory')
    a.add_argument('action', choices=('collect', 'coverage', 'plan', 'gate'))
    a.add_argument('--profile', required=True); a.add_argument('--run', type=int); a.add_argument('--source-pr', type=int)
    a.add_argument('--pr', type=int); a.add_argument('--head'); a.add_argument('--apply', action='store_true')
    a.add_argument('--context', choices=('auto', 'source', 'integration', 'main', 'manual', 'release', 'promotion', 'runtime'), default='source')
    a.add_argument('--github-output', type=Path, help='Append the recomputed missing-job JSON to this actual Actions output file')
    c = sub.add_parser("create")
    c.add_argument("--title", required=True); c.add_argument("--body-file", type=Path, required=True, help="Markdown with filled Description and Specifications sections; see the agent guide")
    c.add_argument("--status", default="idea", help="Configured planning stage ID or semantic action")
    c.add_argument("--module"); c.add_argument("--priority", choices=PRIORITIES); c.add_argument("--type", dest="kind", choices=TYPES); c.add_argument("--design", action="store_true")
    c.add_argument('--release', dest='included', action='store_true')
    w = sub.add_parser('work', help='Find/create a task and verify In Progress for an immediate development request')
    w.add_argument('issue', nargs='?'); w.add_argument('--title'); w.add_argument('--body-file', type=Path, help='Required for a new task; filled Description and Specifications with the working context')
    w.add_argument('--module'); w.add_argument('--type', dest='kind', choices=TYPES)
    w.add_argument('--priority', choices=PRIORITIES); w.add_argument('--design', action='store_true')
    w.add_argument('--release', dest='included', action='store_true'); w.add_argument('--resume', action='store_true')
    worker_arguments(w)
    s = sub.add_parser("set")
    s.add_argument("issue"); s.add_argument("--status", help="Configured stage ID or semantic action; start/merged remain protected")
    s.add_argument("--module"); s.add_argument("--priority", choices=PRIORITIES); s.add_argument("--type", dest="kind", choices=TYPES)
    for flag in ("design","blocked","required"): s.add_argument("--" + flag, action=argparse.BooleanOptionalAction, default=None, help='Legacy alias for --release in single-release projects' if flag=='required' else None)
    s.add_argument('--release', dest='included', action=argparse.BooleanOptionalAction, default=None)
    s.add_argument("--reason"); s.add_argument("--milestone", type=int, help="Legacy GitHub milestone metadata; 0 clears the milestone, not Release membership")
    s = sub.add_parser("start"); s.add_argument("issue"); s.add_argument("--resume", action="store_true", help="Explicitly take over the existing task after inspecting its work and handoff")
    worker_arguments(s)
    x = sub.add_parser('execution', help='Explicit opt-in claims and the sequential review/integration lane')
    x.add_argument('action', choices=('show', 'migrate', 'handoff', 'stop', 'takeover', 'review-acquire', 'review-return', 'review-takeover'))
    x.add_argument('issue', nargs='?')
    worker_arguments(x)
    x.add_argument('--pr', type=int); x.add_argument('--apply', action='store_true')
    x.add_argument('--report-file', type=Path); x.add_argument('--previous-claim')
    x.add_argument('--stopped', action='store_true'); x.add_argument('--reason')
    x.add_argument('--keep-lane', action='store_true', help='Keep integration ownership while the worker fixes this task')
    x.add_argument('--preserve-review-queue', action='store_true', help='Explicit v1-to-v2 or v2-to-v3 adoption preserving verified queued handoffs while all owners/stage are idle; v2-to-v3 also preserves current Approved proof')
    x.add_argument('--preserve-closed-review-handoffs', action='store_true', help='With --preserve-review-queue, retain verified historical closed unmerged sources as unfinished handoffs')
    b = sub.add_parser('batch', help='Schema-2 independent approval and owned frozen integration batches')
    b.add_argument('action', choices=('approve', 'intake', 'begin', 'review-acquire', 'review-return', 'return', 'refresh', 'cancel', 'intake-cancel', 'takeover', 'close-sources', 'delivery-cancel'))
    b.add_argument('--issue'); b.add_argument('--issues', nargs='+'); b.add_argument('--all-approved', action='store_true')
    worker_arguments(b)
    b.add_argument('--intake'); b.add_argument('--batch-id'); b.add_argument('--pr', type=int); b.add_argument('--report-file', type=Path)
    b.add_argument('--deliver', action='store_true', help='Owner-authorized continuation through exact verified delivery after main; only with begin')
    b.add_argument('--delivery-workflow'); b.add_argument('--delivery-job')
    b.add_argument('--previous-claim'); b.add_argument('--stopped', action='store_true'); b.add_argument('--reason')
    m = sub.add_parser("merged")
    m.add_argument("issues", nargs="+"); m.add_argument("--pr", action="append", type=int, required=True)
    m.add_argument("--apply", action="store_true"); m.add_argument("--reviewed-complete", action="store_true")
    c = sub.add_parser("complete", help="Verified non-code result, with evidence; same final stage")
    c.add_argument("issue"); c.add_argument("--evidence-file", type=Path, required=True); c.add_argument("--verified-non-code", action="store_true", required=True)
    q = sub.add_parser("queue"); q.add_argument("action", choices=("show","begin","next","order","release","cancel")); q.add_argument("issues", nargs="*")
    m = sub.add_parser("migration-plan"); m.add_argument("--mapping", type=Path, required=True); m.add_argument("--output", type=Path, required=True)
    m = sub.add_parser("migrate"); m.add_argument("--plan", type=Path, required=True); m.add_argument("--rollback", action="store_true")
    e = sub.add_parser("export-template"); e.add_argument("--output", type=Path, required=True); e.add_argument("--repository", required=True); e.add_argument("--name", required=True); e.add_argument("--base", default="main"); e.add_argument("--engine-revision", required=True)
    e.add_argument('--id-prefix', required=True)
    e.add_argument('--delivery-policy', type=Path, help='Opt in to the pinned Master Repo delivery contract')
    e.add_argument('--process-instructions', type=Path, help='Explicit instruction-only route policy; never inherited from the engine')
    e.add_argument('--execution-policy', type=Path, help='Explicit parallel execution opt-in; never inherited from the engine')
    e.add_argument('--task-context-policy', type=Path, help='Explicit task context policy; never inherited from the engine')
    e.add_argument('--ci-evidence-policy', type=Path, help='Explicit native CI evidence policy; never inherited from the engine')
    a = sub.add_parser('register-project', help='Prepare an idempotent workspace registry change; never deploy it')
    a.add_argument('--workspace', type=Path, required=True); a.add_argument('--project-config', type=Path, required=True)
    a.add_argument('--id', dest='identifier', required=True); a.add_argument('--apply', action='store_true')
    a = sub.add_parser('archive'); a.add_argument('issue'); a.add_argument('--reason', required=True)
    a = sub.add_parser('restore'); a.add_argument('issue')
    a = sub.add_parser('module'); a.add_argument('action', choices=['add']); a.add_argument('--id', dest='identifier', required=True); a.add_argument('--name', required=True); a.add_argument('--description', required=True); a.add_argument('--example', dest='examples', action='append', required=True); a.add_argument('--reason', required=True)
    a = sub.add_parser('sync-workspace'); a.add_argument('--workspace', type=Path, required=True); a.add_argument('--output', type=Path, required=True)
    a = sub.add_parser('serve-sync', help='Receive signed GitHub events and reconcile cached workspace snapshots')
    a.add_argument('--workspace', type=Path, required=True); a.add_argument('--output', type=Path, required=True)
    a.add_argument('--state-dir', type=Path, required=True); a.add_argument('--secret-file', type=Path, required=True)
    a.add_argument('--host', default='127.0.0.1'); a.add_argument('--port', type=int, default=8787)
    a.add_argument('--interval', type=int, default=900)
    a = sub.add_parser('sync-metrics', help='Read private synchronization request counters and pending projects')
    a.add_argument('--state-dir', type=Path, required=True)
    a = sub.add_parser('release'); a.add_argument('action', choices=['close']); a.add_argument('--name', required=True)
    a.add_argument('--apply', action='store_true'); a.add_argument('--published', action='store_true'); a.add_argument('--resume', action='store_true')
    a = sub.add_parser('check-pr'); a.add_argument('pr', type=int)
    a = sub.add_parser('check-merge'); a.add_argument('pr', type=int)
    for name in ('record-review', 'stage'):
        a = sub.add_parser(name); a.add_argument('--pr', type=int, required=True); a.add_argument('--apply', action='store_true')
        if name == 'record-review': a.add_argument('--evidence-file', type=Path, required=True)
    a = sub.add_parser('record-acceptance', help='Retained integration Reviewer records exact post-main unchecked-criterion evidence')
    a.add_argument('--pr', type=int, required=True); a.add_argument('--evidence-file', type=Path, required=True)
    a.add_argument('--apply', action='store_true'); worker_arguments(a)
    a = sub.add_parser('verify-stage'); a.add_argument('--evidence-file', type=Path, required=True); a.add_argument('--apply', action='store_true')
    a = sub.add_parser('record-delivery'); a.add_argument('issues', nargs='+')
    a.add_argument('--evidence-file', type=Path, required=True); a.add_argument('--apply', action='store_true')
    a = sub.add_parser('legacy-delivery', help='Inspect explicitly authorized audited legacy package receipts; no deployment')
    a.add_argument('--evidence-file', type=Path, required=True); a.add_argument('--apply', action='store_true')
    a = sub.add_parser('audit-history', help='Read-only historical completion proposal; review and commit the manifest separately')
    a.add_argument('--legacy-config', type=Path, required=True)
    a.add_argument('--source-revision', required=True)
    a.add_argument('--approved-by', required=True)
    a.add_argument('--report', required=True)
    return p


def worker_arguments(parser):
    for key in ('actor', 'session', 'coordinator', 'branch', 'worktree', 'claim'):
        parser.add_argument('--' + key)


def export(config, args):
    """Export project integration files; the engine remains in its own repository."""
    import re
    target = args.output.resolve()
    if target.exists(): raise ValueError("Template output must be a new directory")
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", args.repository): raise ValueError("Invalid repository")
    revision = getattr(args, 'engine_revision', None)
    if not revision or not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('Specify --engine-revision with the verified shared engine commit SHA')
    prefix = getattr(args, 'id_prefix', None) or ''.join(w[0] for w in args.name.split()).upper()
    if len(prefix)<2: prefix = re.sub('[^A-Z]', '', args.name.upper())[:2]
    config = dict(config, schema_version=3, release_mode='single',
                  project={"name":args.name,"repository":args.repository,"base_branch":args.base,'id_prefix':prefix},
                  completion_label="Merged", default_release="", release_view_label="Release",
                  modules=[{"id":"product","name":"Product","description":"Replace with this project\'s functional boundaries before onboarding.","examples":[]}])
    config['workflow'] = workflow.stages(config)
    config.pop('delivery_policy', None)
    config.pop('execution_policy', None)
    config.pop('process_instructions', None)
    config.pop('historical_completion', None)
    config.pop('ci_evidence_policy', None)
    config.pop('task_context_policy', None)
    config['workflow'] = [row for row in config['workflow'] if row['phase'] not in ('approved', 'stage')]
    if getattr(args, 'delivery_policy', None):
        config['delivery_policy'] = json.loads(args.delivery_policy.read_text(encoding='utf-8'))
        from .delivery_policy import policy
        value = policy(config)
        config['workflow'] = list(workflow.PHASES if value['staging']['enabled'] else workflow.BASE_PHASES)
        workflow.validate(config)
    if getattr(args, 'execution_policy', None):
        config['execution_policy'] = json.loads(args.execution_policy.read_text(encoding='utf-8'))
        from .delivery_policy import execution_policy
        value = execution_policy(config)
        if value['schema_version'] in (2, 3):
            config['workflow'] = [phase for phase in workflow.BATCH_PHASES
                                  if phase != 'stage' or config['delivery_policy']['staging']['enabled']]
        workflow.validate(config)
    if getattr(args, 'process_instructions', None):
        config['process_instructions'] = json.loads(args.process_instructions.read_text(encoding='utf-8'))
        from .process_instructions import policy as process_policy
        process_policy(config)
    if getattr(args, 'task_context_policy', None):
        config['task_context_policy'] = json.loads(args.task_context_policy.read_text(encoding='utf-8'))
        from .task_context import policy as context_policy
        context_policy(config)
    if getattr(args, 'ci_evidence_policy', None):
        config['ci_evidence_policy'] = json.loads(args.ci_evidence_policy.read_text(encoding='utf-8'))
        from .ci_evidence import policy as evidence_policy
        if evidence_policy(config) is None: raise ValueError('Explicit CI evidence policy cannot be null')
    config.pop('module_history', None)
    source = Path(__file__).parent
    (target / 'tracker').mkdir(parents=True)
    (target / 'scripts').mkdir()
    (target / 'docs').mkdir()
    (target / '.github/ISSUE_TEMPLATE').mkdir(parents=True)
    (target / '.github/workflows').mkdir()
    (target / 'tracker/config.json').write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')
    (target / 'tracker/engine.json').write_text(json.dumps({'repository':'MojoTheApe/task-tracker','revision':revision},indent=2)+'\n',encoding='utf-8')
    shutil.copy(source/'templates/task_tracker.py',target/'scripts/task_tracker.py')
    shutil.copy(source/'pr_checks.py',target/'scripts/tracker_pr_check.py')
    shutil.copy(source/'delivery_policy.py',target/'scripts/tracker_delivery_policy.py')
    shutil.copy(source/'batch_policy.py',target/'scripts/tracker_batch_policy.py')
    shutil.copy(source/'process_instructions.py',target/'scripts/tracker_process_instructions.py')
    shutil.copy(source/'ci_evidence.py',target/'scripts/tracker_ci_evidence.py')
    shutil.copy(source/'delivery_receipt.py',target/'scripts/tracker_delivery_receipt.py')
    shutil.copy(source/'task_context.py',target/'scripts/tracker_task_context.py')
    shutil.copy(source.parent/'docs/TASK_CONTEXT.md', target/'docs/TASK_CONTEXT.md')
    shutil.copy(source.parent/'docs/CI_REUSE.md', target/'docs/CI_REUSE.md')
    shutil.copy(source/'templates/tracker-link.yml',target/'.github/workflows/tracker-link.yml')
    guide = "# Tracker workflow\n\nRun `python scripts/task_tracker.py guide` to read the pinned shared workflow. Read `tracker/config.json` for project IDs and module boundaries. Every implementation, including immediate fixes, needs an Issue before code. Use `python scripts/task_tracker.py work ID` or `work --title ... --body-file task.md --module ... --type ...` and verify In Progress. Every new task starts with a plain-English Description written by the agent from the request and verified context, followed by Specifications with verified context, behavior, scope, criteria, checks and current handoff. Read the complete Issue body; only the UI collapses Specifications. Use tracker/task-template.md; empty or placeholder Description/Specifications sections are rejected. Preserve existing task scope and history; review a sample before any bulk retrospective rewrite. Planning only creates tasks. Release uses one --release flag. Use check-pr for early linkage feedback, check-merge once for final admission and the verified merged transition after complete review. Follow existing repository review and release rules.\n"
    (target/'docs/TRACKER_AGENT_WORKFLOW.md').write_text(guide,encoding='utf-8')
    if config.get('delivery_policy'):
        with (target/'docs/TRACKER_AGENT_WORKFLOW.md').open('a') as output:
            output.write('\nThis project adopts the shared delivery policy. Read the pinned guide and `docs/DELIVERY.md`. Use `check-merge` immediately before merge, record independent review, and use `stage` / `verify-stage` when staging is enabled. A Merged label alone is not completion; record verified delivery when required. Preserve the working branch through stage fixes.\n')
    if config.get('execution_policy'):
        with (target/'docs/TRACKER_AGENT_WORKFLOW.md').open('a') as output:
            output.write('\nThis project opts into bounded parallel implementation and one review/integration lane. `guide` includes the exact execution contract. Before work, complete idle `execution migrate` adoption and use neutral actor/session claims, dedicated worktrees and durable handoffs. Existing review and delivery gates remain mandatory.\n')
    if config.get('task_context_policy'):
        with (target/'docs/TRACKER_AGENT_WORKFLOW.md').open('a') as output:
            output.write('\nTask context is explicitly selected. Read docs/TASK_CONTEXT.md. Assess current scope/main before implementation; use the strict terminal journal and owned independent compatibility review. Initial state is fenced by execution migrate; existing state requires inspected owned task-context adopt.\n')
    if config.get('ci_evidence_policy'):
        with (target/'docs/TRACKER_AGENT_WORKFLOW.md').open('a') as output:
            output.write('\nNative CI evidence is explicitly selected. Read docs/CI_REUSE.md for planning, running every missing job, final native gating, retained main proof and exact required aggregate adoption. Existing review/admission/delivery gates remain.\n')
    if config.get('process_instructions'):
        shutil.copy(source.parent/'docs/PROCESS_INSTRUCTIONS.md', target/'docs/PROCESS_INSTRUCTIONS.md')
        with (target/'docs/TRACKER_AGENT_WORKFLOW.md').open('a') as output:
            output.write('\nThis project explicitly adopts the instruction-only process route. Read `docs/PROCESS_INSTRUCTIONS.md`. Eligible one-task PRs target main and retain independent current review and the configured process checks. Existing legacy task-slot or adopted execution ownership continues to apply. Mixed and unsafe changes retain the ordinary delivery route.\n')
    for filename in ('AGENTS.md','CLAUDE.md'):
        (target/filename).write_text('Before task work, read docs/TRACKER_AGENT_WORKFLOW.md and tracker/config.json. Use the pinned client `python scripts/task_tracker.py`; do not copy the engine into this project. Preserve existing project instructions.\n',encoding='utf-8')
    shutil.copy(source/'templates/ISSUE_TEMPLATE/task.yml',target/'.github/ISSUE_TEMPLATE/task.yml')
    shutil.copy(source/'templates/task.md',target/'tracker/task-template.md')
    shutil.copy(source/'templates/pull_request_template.md',target/'.github/pull_request_template.md')
    (target/'.gitignore').write_text('.tracker-runtime/\n',encoding='utf-8')
    return {'template':str(target),'next':'Merge these files with existing instructions, adapt modules, then run python scripts/task_tracker.py init.'}


def execute(args, config, api):
    store = queue.StateStore(api, config["project"]["base_branch"])
    if args.command == 'task-context':
        from . import task_context
        if args.action == 'adopt': return task_context.adopt(api, config, store, args)
        if not args.issue: raise ValueError('Supply the actual task ID')
        number = identifiers.resolve(api, config, args.issue)
        return getattr(task_context, args.action.replace('-', '_'))(api, config, store, number, args)
    if args.command == 'delivery-policy':
        from .policy_migration import migrate
        return migrate(api, config, store, args)
    if args.command == 'maintenance':
        from . import maintenance
        if args.action == 'show': return maintenance.show(store)
        return getattr(maintenance, args.action)(store, args)
    if args.command == 'ci-evidence':
        from . import ci_evidence
        if args.action == 'collect':
            if not args.run: raise ValueError('Supply --run with the actual successful Actions run')
            return ci_evidence.save(api, config, store, args)
        if args.context == 'auto':
            if args.pr:
                from . import delivery_policy as rules
                pr = api.request(api.root + f'/pulls/{args.pr}')
                direction = rules.route(config, pr, api.request)
                args.context = ('integration' if rules.batch_mode(config) and direction in ('stage', 'batch')
                                else 'promotion' if direction == 'promotion' else 'source')
            else: args.context = 'main'
        if not args.head or not args.pr and (args.context != 'main' or args.action == 'coverage'):
            raise ValueError('Coverage needs the actual --pr and expected --head; plan/gate main can resolve its merged PR')
        if args.apply: raise ValueError('Coverage is read-only')
        state = store.read(optional=True)[0]
        if args.action == 'gate':
            if not args.run: raise ValueError('CI gate requires its actual --run')
            result = ci_evidence.gate(api.request, api.action_job_log, config, state, args.profile,
                                      args.pr, args.head, args.run, args.context)
        else:
            result = getattr(ci_evidence, args.action)(api.request, api.action_job_log, config, state, args.profile,
                                                       args.pr, args.head, args.context)
        if args.github_output:
            with args.github_output.open('a', encoding='utf-8') as output:
                output.write('missing='+json.dumps(result['missing'], separators=(',', ':'))+'\n')
        return result
    # Legacy pins reject schema 2. Updated clients also fail closed when their
    # project config is stale; read-only snapshots remain available during rollout.
    readonly = {'list', 'sync', 'guide', 'check-pr', 'check-merge', 'export-template', 'audit-history',
                'migration-plan', 'register-project', 'init', 'execution'}
    if args.command not in readonly:
        from .delivery_policy import execution_state
        execution_state(store.read(optional=True)[0], config)
    if args.command == 'timing':
        from .timing import legacy_timer
        return legacy_timer(api, config, store, args)
    if args.command == 'execution':
        if args.action == 'migrate': return execution.migrate(api, config, store, args.apply, args.preserve_review_queue, args.preserve_closed_review_handoffs, args)
        if args.action == 'show':
            return {'execution': execution.read(store, config)[2], 'private': True}
        if args.action in ('handoff', 'stop', 'takeover'):
            if not args.issue: raise ValueError('Specify the task ID')
            number = identifiers.resolve(api, config, args.issue)
            if args.action in ('handoff', 'stop') and not args.report_file: raise ValueError('Supply --report-file')
            if args.action == 'handoff' and not args.pr: raise ValueError('Supply --pr')
            return getattr(execution, args.action)(api, config, store, number, args)
        if args.action == 'review-acquire':
            if not args.pr: raise ValueError('Supply --pr')
            return execution.acquire_review(api, config, store, args)
        if args.action == 'review-return':
            if not args.report_file: raise ValueError('Supply --report-file')
            return execution.return_review(api, config, store, args)
        if args.action == 'review-takeover': return execution.takeover_review(api, config, store, args)
    if args.command == 'batch':
        if args.deliver and args.action != 'begin':
            raise ValueError('--deliver is an explicit authorization on batch begin only')
        if (args.delivery_workflow or args.delivery_job) and not args.deliver:
            raise ValueError('--delivery-workflow and --delivery-job require --deliver')
        if args.issues:
            args.issues = [identifiers.resolve(api, config, n) for n in args.issues]
        if args.action == 'return':
            if not args.issue or not args.report_file: raise ValueError('Supply --issue and --report-file')
            return batches.return_task(api, config, store, identifiers.resolve(api, config, args.issue), args)
        if args.action == 'review-acquire':
            if not args.pr: raise ValueError('Supply --pr')
            return batches.acquire_review(api, config, store, args)
        if args.action in ('cancel', 'review-return', 'intake-cancel') and not args.report_file: raise ValueError('Supply --report-file')
        if args.action == 'review-return': return batches.return_candidate(api, config, store, args)
        if args.action == 'intake-cancel': return batches.cancel_intake(api, config, store, args)
        if args.action == 'close-sources':
            if not args.batch_id: raise ValueError('Supply --batch-id')
            return batches.close_sources(api, config, store, args)
        if args.action == 'delivery-cancel':
            if not args.batch_id or not args.report_file:
                raise ValueError('Supply --batch-id and --report-file for the explicit cancellation decision')
            return batches.cancel_delivery(api, config, store, args)
        if args.action == 'takeover' and args.issue:
            args.issue = identifiers.resolve(api, config, args.issue)
        return getattr(batches, args.action)(api, config, store, args)
    if args.command == 'audit-history':
        from .historical_completion import audit
        return {'historical_completion': audit(api.issues(), load_config(args.legacy_config), config,
                source_revision=args.source_revision, approved_by=args.approved_by, report=args.report),
                'applied': False, 'next': 'Review the explicit task allowlist and commit it in the project config adoption PR. No receipts or live state were written.'}
    if args.command == 'work': return intake.work(api,config,store,args)
    if args.command == 'check-pr': return pr_checks.check(api.request,config,args.pr)
    if args.command == 'check-merge': return pr_checks.check(api.request,config,args.pr,admission=True)
    if hasattr(args, 'issue'): args.issue = identifiers.resolve(api, config, args.issue)
    if hasattr(args, 'issues'): args.issues = [identifiers.resolve(api, config, n) for n in args.issues]
    if args.command == 'record-review':
        return delivery.record_review(api,config,store,args.pr,delivery.evidence(args.evidence_file,'independent-review'),args.apply)
    if args.command == 'record-acceptance':
        from . import acceptance
        return acceptance.record(api, config, store, args, delivery.evidence(args.evidence_file, 'post-main-acceptance'))
    if args.command == 'stage': return delivery.stage(api,config,store,args.pr,args.apply)
    if args.command == 'verify-stage':
        return delivery.verify_stage(api,config,store,delivery.evidence(args.evidence_file,'stage-verification'),args.apply)
    if args.command == 'legacy-delivery':
        from . import legacy_delivery
        return legacy_delivery.record(api, config, store, delivery.evidence(args.evidence_file, 'legacy-delivery-reconciliation'), args.apply)
    if args.command == 'record-delivery':
        return delivery.record_delivery(api,config,store,args.issues,delivery.evidence(args.evidence_file,'delivery-verification'),args.apply)
    if args.command == 'register-project':
        from .onboarding import register
        return register(args.workspace,args.project_config,args.identifier,args.apply)
    if getattr(args,"module",None) and args.module not in [m["id"] for m in config["modules"]]:
        raise ValueError("Choose a module from tracker/config.json")
    if args.command == "sync": return sync(api,config,args.output,allow_empty=args.allow_empty)
    if args.command == 'guide':
        result = {'workflow': Path(__file__).with_name('AGENT_WORKFLOW.md').read_text(encoding='utf-8'), 'project': config['project'], 'modules': config['modules']}
        if config.get('execution_policy'):
            contract = 'BATCH_INTEGRATION.md' if config['execution_policy']['schema_version'] in (2, 3) else 'PARALLEL_EXECUTION.md'
            result['execution_workflow'] = (Path(__file__).resolve().parents[1]/'docs'/contract).read_text(encoding='utf-8')
        return result
    if args.command == 'module': return catalog.add_module(api, config, args.config, **{k:getattr(args,k) for k in ('identifier','name','description','examples','reason')})
    if args.command == 'archive':
        if config.get('execution_policy'):
            return execution.archive(api,config,store,args.issue,args.reason)
        return catalog.archive(api,store,args.issue,args.reason)
    if args.command == 'restore': return catalog.restore(api,args.issue)
    if args.command == 'release': return releases.close(api,config,store,args.name,apply=args.apply,published=args.published,resume=args.resume)
    if args.command == "export-template": return export(config,args)
    if args.command == "init":
        install_labels(api,config)
        milestones = api.request(api.root + "/milestones?state=all&per_page=100",paginate=True)
        title = config.get("default_release")
        if config.get('release_mode') != 'single' and title and not any(m["title"]==title for m in milestones):
            api.request(api.root+"/milestones","POST",{"title":title,"description":"Scope is assigned explicitly by the project owner. An empty milestone is not release-ready."})
        return {"initialized":api.repository}
    if args.command == "list":
        return payload(api.issues(),config,api.request(api.root+"/milestones?state=all&per_page=100",paginate=True),queue.public_state(store.read(optional=True)[0]))
    if args.command == "create":
        if args.included and store.read(optional=True)[0].get('release_rollover'):
            raise ValueError('Finish release rollover before adding Release tasks')
        result = commands.create(api,config,args)
        if workflow.phase(config, workflow.target(config, args.status)) == "todo":
            state,sha=store.read(optional=True);state.setdefault("todo_added",{})[str(result["number"])]=queue.now();store.write(state,sha)
        return {"number":result["number"],"id":identifiers.task_id(result,config),"url":result.get("html_url"),"labels":sorted(names(result))}
    if args.command == "set":
        result=commands.change(api,config,store,args.issue,**{k:getattr(args,k) for k in ("status","module","priority","kind","design","blocked","reason","milestone","required","included")})
        return {"number":result["number"],"labels":sorted(names(result))}
    if args.command == "start": return queue.start(api,config,store,args.issue,args.resume,execution_args=args)
    if args.command == "merged":
        if args.apply and not args.reviewed_complete: raise ValueError("Apply requires --reviewed-complete after reviewing ALL task work")
        from . import acceptance
        verifier = (lambda issue: acceptance.verify(api, config, store, issue, args.pr)) if config.get('execution_policy', {}).get('schema_version') in (2, 3) else None
        plan=merge.prepare(api,api.repository,args.issues,args.pr,config["project"]["base_branch"], config=config, acceptance=verifier)
        if args.apply:
            delivery.record_merge(api,config,store,plan,args.pr)
            merge.apply(api,api.repository,plan,config=config, acceptance=verifier)
            execution.finish(config,store,args.issues,args.pr)
            if not config.get('execution_policy'):
                from .timing import end_observations
                state, sha = store.read(optional=True)
                changed = False
                for number in args.issues:
                    changed = end_observations(state, number) or changed
                if changed:
                    store.write(state, sha)
            state,_=store.read(optional=True)
            if state.get("active") and state["active"]["issue"] in args.issues: queue.release(store,state["active"]["issue"])
        return {"applied":args.apply,"plan":plan}
    if args.command == "complete":
        if config.get('execution_policy'):
            raise ValueError('Execution-enabled tasks use an independently reviewed PR, including report-only work; complete cannot bypass the review lane')
        issue=api.issue(args.issue);labels=names(issue);evidence=args.evidence_file.read_text(encoding="utf-8").strip()
        merge.validate_issue(issue,config)
        if not evidence or not ({"type:research","type:operations"}&labels):
            raise ValueError("Non-code completion requires Research/Operations and verified evidence")
        if "resolution:non_code" not in labels:
            api.request(api.root+f"/issues/{args.issue}","PATCH",{"body":(issue.get("body") or "")+"\n\n## Verified non-code result\n"+evidence})
        delivery.non_code(config,store,args.issue,evidence)
        api.labels(args.issue,{"status:"+workflow.target(config,'merged'),"resolution:non_code"},{n for n in labels if n.startswith('status:')})
        from .timing import end_observations
        state, sha = store.read(optional=True)
        if end_observations(state, args.issue):
            store.write(state, sha)
        state,_=store.read(optional=True)
        if state.get("active") and state["active"]["issue"]==args.issue: queue.release(store,args.issue)
        return {"number":args.issue,"status":workflow.target(config,'merged'),"display":"Complete"}
    if args.command == "queue":
        state,sha=store.read(optional=True)
        if args.action != 'show': queue.legacy(state)
        if args.action=="show": return state
        if args.action=="begin": return queue.begin(store,tasks_from_issues(api.issues(),config,state.get('delivery_workflow',{}).get('tasks',{})))
        if args.action=="next": return queue.next_task(api,config,store)
        if args.action=="order":
            if len(set(args.issues))!=len(args.issues): raise ValueError("Duplicate issue in order")
            for n in args.issues:
                if not any(workflow.phase(config, s[7:]) == 'todo' for s in names(api.issue(n)) if s.startswith('status:')): raise ValueError(f"#{n} is not Todo")
            state["todo_order"]=args.issues;store.write(state,sha);return state
        if args.action=="cancel":
            if state.get("active"): raise ValueError("Release the active task with a handoff first")
            if state.get("run"):state["run"]["state"]="cancelled";store.write(state,sha)
            return state
        if len(args.issues)!=1: raise ValueError("queue release requires one issue number")
        issue=api.issue(args.issues[0]);labels=names(issue)
        if not ('flag:blocked' in labels or any(workflow.phase(config, s[7:]) in ('review','stage','merged') for s in labels if s.startswith('status:'))): raise ValueError("Record a blocker or a review handoff before releasing execution")
        queue.release(store,args.issues[0]);return {"released":args.issues[0]}
    if args.command=="migration-plan":
        plan=commands.migration_plan(api,config,json.loads(args.mapping.read_text(encoding="utf-8")))
        args.output.write_text(json.dumps(plan,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        return {"plan":str(args.output),"issues":len(plan["issues"]),"writes":False}
    if args.command=="migrate":
        if config.get('execution_policy'): raise ValueError('Legacy label migration is unavailable after execution adoption')
        return commands.migrate(api,json.loads(args.plan.read_text(encoding="utf-8")),args.rollback)
    raise ValueError("Unknown command")


def main(argv=None):
    p=parser();args=p.parse_args(argv)
    try:
        command=json.loads(args.gh_command_json)
        if not isinstance(command,list) or not command or any(not isinstance(x,str) or not x for x in command): raise ValueError("Expected a nonempty array of command strings")
        if args.command == 'serve-sync':
            from .events import serve
            serve(args.workspace, args.output, args.state_dir, args.secret_file, command=command,
                  host=args.host, port=args.port, interval=args.interval)
            return 0
        if args.command == 'sync-metrics':
            from .sync_state import SyncState
            print(json.dumps(SyncState(args.state_dir).metrics(), indent=2))
            return 0
        if args.command == 'sync-workspace':
            from .workspace import sync_workspace
            result=sync_workspace(args.workspace,args.output,command=command)
            print(json.dumps(result,indent=2))
            return 0 if result['ok'] else 1
        config=load_config(args.config)
        result=execute(args,config,GitHub(config["project"]["repository"],command))
        print(json.dumps(result,indent=2,ensure_ascii=True))
        return 0
    except (OSError,ValueError,RuntimeError,KeyError) as error:
        print(str(error),file=sys.stderr);return 1
