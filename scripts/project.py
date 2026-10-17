"""Project choices, pinned scaffolding and conservative three-way upgrades."""
import copy
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import standard
import ci_policy
import instruction_render
import export_contract

SOURCE = Path(__file__).resolve().parents[1]
PROFILES = {'vps': 'verified-production', 'n8n': 'verified-production', 'n8n-source': 'reviewed-merge', 'local': 'reviewed-merge',
            'package': 'verified-stable-package', 'tooling': 'reviewed-merge'}
ROLES = ('application', 'shared-tooling-library', 'application-data',
         'release-storage', 'knowledge', 'research')
CHOICE_PRESETS = {
    'simple': {'route': 'direct', 'staging': False, 'implementation_limit': 1, 'review_limit': 1},
    'application': {'route': 'batch', 'staging': True, 'implementation_limit': 2,
                    'review_limit': 1, 'batch_limit': 2},
}
INPUT_FIELDS = {'name', 'repository', 'prefix', 'workspace_id', 'profile', 'staging',
                'implementation_limit', 'review_limit', 'batch_limit', 'task_context',
                'completion_policy', 'process_instructions', 'ci_evidence', 'ci_retry', 'knowledge_capture'}
CHOICE_FIELDS = {'schema_version', 'role', 'route', 'completion', 'preset'}
PHASES = ['idea', 'backlog', 'todo', 'in_progress', 'review', 'stage', 'merged']
BASELINE = '.workflow/template-base.json'
LAYOUT = '.workflow/layout.json'
PROJECT_AREAS = ('docs/system/', 'docs/runtime/')
FILES = {'AGENTS.md': 'AGENTS.md', 'WORKFLOW.md': 'docs/repository/WORKFLOW.md',
         'VERIFICATION.md': 'docs/repository/VERIFICATION.md',
         'DELIVERY_CONTINUATION.md': 'docs/repository/DELIVERY_CONTINUATION.md',
         'LAYOUT.md': 'docs/repository/LAYOUT.md', 'DELIVERY.md': 'docs/repository/DELIVERY.md',
         'REPOSITORY_CHANGELOG.md': 'docs/repository/CHANGELOG.md',
         'PROJECT.md': 'docs/system/PROJECT.md', 'CONTEXT.md': 'docs/system/AGENT_CONTEXT.md',
         'RUNTIME.md': 'docs/runtime/DELIVERY.md', 'CHANGELOG.md': 'docs/system/CHANGELOG.md',
         'SPECS.md': 'docs/system/specs/README.md',
         'delivery-check.yml': '.github/workflows/delivery-check.yml'}
FORWARDS = {'docs/PROJECT.md': 'system/PROJECT.md', 'AGENT_CONTEXT.md': 'docs/system/AGENT_CONTEXT.md',
            'docs/DELIVERY.md': 'repository/DELIVERY.md', 'docs/CHANGELOG.md': 'system/CHANGELOG.md',
            'docs/TRACKER_AGENT_WORKFLOW.md': 'repository/TRACKER.md',
            'docs/specs/README.md': '../system/specs/README.md'}
LAYOUT_DATA = {'schema_version': 1, 'repository': 'docs/repository/',
               'system': 'docs/system/', 'runtime': 'docs/runtime/', 'tools': '.workflow/tools/'}


def separate_export(files):
    """Relocate document navigation; consume Tracker's helper layouts verbatim."""
    guide = files.pop('docs/TRACKER_AGENT_WORKFLOW.md')
    # Move the entire exported reference closure together. Sibling Markdown
    # links remain valid and the pinned reference bodies stay byte-for-byte.
    references = sorted(name for name in files
                        if name.startswith('docs/') and name.count('/') == 1
                        and name.endswith('.md'))
    for old in references:
        name = Path(old).name
        files['docs/repository/' + name] = files.pop(old)
        files[old] = '# Moved\n\nSee [' + name + '](repository/' + name + ').\n'
        # The generated primary guide is navigation, not a contract source.
        guide = guide.replace('../docs/' + name, name)
        guide = guide.replace(old, 'docs/repository/' + name)
    guide = guide.replace('](../tracker/', '](../../tracker/')
    files['docs/repository/TRACKER.md'] = guide
    return files


def layout_files():
    files = {name: '# Moved\n\nSee [' + target + '](' + target + ').\n'
             for name, target in FORWARDS.items()}
    files[LAYOUT] = dumps(LAYOUT_DATA)
    return files



def dumps(value): return json.dumps(value, indent=2, ensure_ascii=False) + '\n'


def compatibility():
    result = json.loads((SOURCE / 'compatibility.json').read_text())
    if (result.get('tracker_repository') != 'MojoTheApe/task-tracker' or result.get('delivery_contract') != 1
            or not standard.SHA.fullmatch(result.get('tracker_revision', '')) or set(result['tracker_revision']) == {'0'}):
        raise ValueError('Standard must pin a concrete compatible Tracker commit')
    return result


def tracker_checkout(path, revision):
    path = Path(path).resolve()
    head = subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git', '-C', str(path), 'status', '--porcelain'], text=True)
    remote = subprocess.check_output(['git', '-C', str(path), 'remote', 'get-url', 'origin'], text=True).strip()
    if head != revision or dirty or remote.removesuffix('.git') not in (
            'https://github.com/MojoTheApe/task-tracker', 'git@github.com:MojoTheApe/task-tracker'):
        raise ValueError('Use a clean official Tracker checkout at the compatible pinned commit')
    return path


def delivery_policy(data):
    stages = data['workflow']; env = data['environments']
    return {'schema_version': 1,
            'staging': {'enabled': stages['staging'], 'branch': stages['stage_branch'],
                        'target': env['stage']['target'] if stages['staging'] else 'disabled'},
            'completion': data['completion'],
            'delivery_target': env['production']['target'] if data['completion'] != 'reviewed-merge' else data['project']['repository'] + ':' + stages['main_branch'],
            'required_checks': stages['required_checks']}


def validate_execution_policy(value):
    """An explicit opt-in; absence must retain the pinned legacy workflow."""
    if isinstance(value, dict) and type(value.get('schema_version')) is int and value['schema_version'] == 4:
        return export_contract.structural_execution_policy({'execution_policy': value})
    if not isinstance(value, dict) or type(value.get('schema_version')) is not int or value['schema_version'] not in (1, 2, 3):
        raise ValueError('Execution policy schema_version must be 1, 2 or 3')
    keys = {'schema_version', 'implementation_limit', 'review_limit'}
    if value['schema_version'] in (2, 3): keys.add('batch_limit')
    if set(value) != keys:
        raise ValueError('Execution policy has missing or unsupported fields')
    if type(value['implementation_limit']) is not int or not 1 <= value['implementation_limit'] <= 16:
        raise ValueError('Execution policy implementation_limit must be an integer from 1 to 16')
    review_max = 5 if value['schema_version'] == 3 else 1
    if type(value['review_limit']) is not int or not 1 <= value['review_limit'] <= review_max:
        raise ValueError('Execution policy review_limit must be an integer from 1 to ' + str(review_max))
    batch_max = 5 if value['schema_version'] == 3 else 16
    if value['schema_version'] in (2, 3) and (type(value['batch_limit']) is not int or not 1 <= value['batch_limit'] <= batch_max):
        raise ValueError('Execution policy batch_limit must be an integer from 1 to ' + str(batch_max))


def validate_process_instructions(value):
    """A separate explicit route; never weaken the application's delivery policy."""
    if (not isinstance(value, dict) or set(value) != {'schema_version', 'required_checks'}
            or type(value.get('schema_version')) is not int or value['schema_version'] != 1):
        raise ValueError('Process instructions need schema_version 1 and required_checks')
    checks = value['required_checks']
    if (not isinstance(checks, list) or not checks or any(not isinstance(x, str) or not x.strip() or x != x.strip() for x in checks)
            or len(set(checks)) != len(checks) or not {'descriptor', 'tracker-link'} <= set(checks)):
        raise ValueError('Process instructions require unique check names including descriptor and tracker-link')


def phases(staging, execution=None):
    result = [p for p in PHASES if p != 'stage' or staging]
    if execution and (execution['schema_version'] in (2, 3)
                      or execution['schema_version'] == 4 and execution.get('route') == 'batch'):
        result.insert(result.index('stage' if staging else 'merged'), 'approved')
    return result


def validate_task_context(value, execution):
    if (not isinstance(value, dict) or set(value) != {'schema_version'}
            or type(value.get('schema_version')) is not int or value['schema_version'] != 1
            or not isinstance(execution, dict) or execution.get('schema_version') not in (2, 3)):
        raise ValueError('Task context schema 1 requires explicit execution schema 2 or 3')


def validate_completion_policy(value):
    """Select accepted-scope checking without changing the completion target."""
    if (not isinstance(value, dict) or set(value) != {'schema_version'}
            or type(value.get('schema_version')) is not int or value['schema_version'] != 1):
        raise ValueError('Completion policy requires exactly schema_version 1')


def modern_inputs(inputs):
    """New choice fields select descriptor3; old recorded inputs remain schema2."""
    if not isinstance(inputs, dict):
        raise ValueError('Project inputs must be an object')
    if 'schema_version' in inputs:
        version = inputs['schema_version']
        if type(version) is not int or version not in (2, 3):
            raise ValueError('Project input schema_version must be 2 or 3')
        if version == 2 and (CHOICE_FIELDS - {'schema_version'}) & inputs.keys():
            raise ValueError('Explicit project choices require descriptor schema3')
    return inputs.get('schema_version') == 3 or bool((CHOICE_FIELDS - {'schema_version'}) & inputs.keys())


def project_choices(inputs):
    """Construct proposed Master choices, not a canonical engine policy validator.

    Presets fill only omitted choices. Role/profile/completion stay explicit, and
    this pure construction cannot grant export, admission or state activation.
    """
    if not isinstance(inputs, dict) or set(inputs) - (INPUT_FIELDS | CHOICE_FIELDS):
        raise ValueError('Unknown or invalid project choice inputs')
    if not modern_inputs(inputs):
        raise ValueError('Explicit project choices require descriptor schema3')
    selected = {}
    if 'preset' in inputs:
        if not isinstance(inputs['preset'], str) or inputs['preset'] not in CHOICE_PRESETS:
            raise ValueError('Use the simple or application project preset')
        selected.update(copy.deepcopy(CHOICE_PRESETS[inputs['preset']]))
        selected.update(task_context={'schema_version': 2}, completion_policy={'schema_version': 1})
        if inputs.get('route') == 'direct':
            selected.pop('batch_limit', None)
    selected.update(copy.deepcopy(inputs))
    required = {'role', 'profile', 'completion', 'route', 'staging',
                'implementation_limit', 'review_limit', 'task_context', 'completion_policy'}
    missing = required - selected.keys()
    if missing:
        raise ValueError('Descriptor3 needs explicit choices: ' + ', '.join(sorted(missing)))
    if not isinstance(selected['role'], str) or selected['role'] not in ROLES:
        raise ValueError('Unknown project role')
    profile, completion = selected['profile'], selected['completion']
    if not isinstance(profile, str) or profile not in PROFILES:
        raise ValueError('Unknown delivery profile')
    if not isinstance(completion, str) or completion != PROFILES[profile]:
        raise ValueError('Unsupported profile/completion combination; preserve the profile delivery obligation')
    if type(selected['staging']) is not bool:
        raise ValueError('Stage must be an explicit boolean choice')
    if not isinstance(selected['route'], str) or selected['route'] not in ('direct', 'batch'):
        raise ValueError('Integration route must be direct or batch')
    for key, maximum in (('implementation_limit', 16), ('review_limit', 5)):
        if type(selected[key]) is not int or not 1 <= selected[key] <= maximum:
            raise ValueError(key + ' must be a true integer from 1 to ' + str(maximum))
    if selected['route'] == 'direct' and 'batch_limit' in selected:
        raise ValueError('Direct integration must not select batch_limit')
    if selected['route'] == 'batch' and (type(selected.get('batch_limit')) is not int
                                      or not 1 <= selected['batch_limit'] <= 5):
        raise ValueError('Batch integration needs a true integer batch_limit from 1 to 5')
    context = selected['task_context']
    if (not isinstance(context, dict) or set(context) != {'schema_version'}
            or type(context['schema_version']) is not int or context['schema_version'] != 2):
        raise ValueError('Modern choices require explicit task_context schema2')
    validate_completion_policy(selected['completion_policy'])
    selected['schema_version'] = 3
    return selected


def require_engine_choices(data):
    """Validate modern choices through the exact canonical provider, never a fallback."""
    if data.get('schema_version') == 3:
        _, record, _ = export_contract.trusted()
        try:
            export_contract.selected(record, data)
        except ValueError as error:
            raise ValueError('Descriptor3 requires a released canonical route companion: ' + str(error)) from None
        return export_contract.structural_route_policy(route_config(data))


def route_config(data):
    workflow = data['workflow']
    config = {'delivery_policy': delivery_policy(data)}
    for name, field in (('execution', 'execution_policy'), ('task_context', 'task_context_policy'),
                        ('completion_policy', 'completion_policy'), ('knowledge_capture', 'knowledge_capture_policy')):
        if name in workflow:
            config[field] = workflow[name]
    return config


def descriptor(inputs, revision):
    modern = modern_inputs(inputs)
    if modern:
        inputs = project_choices(inputs)
    c = compatibility(); profile = inputs.get('profile'); repo = inputs.get('repository')
    if (not isinstance(profile, str) or profile not in PROFILES
            or not isinstance(repo, str) or not re.fullmatch(r'[\w.-]+/[\w.-]+', repo)
            or not isinstance(inputs.get('prefix'), str) or not re.fullmatch(r'[A-Z][A-Z0-9]+', inputs['prefix'])
            or not isinstance(inputs.get('workspace_id'), str) or not re.fullmatch(r'[a-z][a-z0-9-]*', inputs['workspace_id'])
            or type(inputs.get('staging')) is not bool
            or not isinstance(inputs.get('name'), str) or not inputs['name'].strip()):
        raise ValueError('Invalid project identity, profile, prefix or stage choice')
    env = {}
    if inputs['staging']: env['stage'] = {'target': '__STAGE_TARGET__', 'verify': '__STAGE_CHECKS__'}
    completion = inputs['completion'] if modern else PROFILES[profile]
    if completion != 'reviewed-merge': env['production'] = {'target': '__PRODUCTION_TARGET__', 'verify': '__PRODUCTION_CHECKS__'}
    workflow = {'staging': inputs['staging'], 'main_branch': 'main', 'stage_branch': 'stage',
                'required_checks': ['descriptor', 'tracker-link']}
    if 'process_instructions' in inputs:
        validate_process_instructions(inputs['process_instructions'])
        workflow['process_instructions'] = inputs['process_instructions']
    if modern:
        workflow['execution'] = {'schema_version': 4, 'route': inputs['route'],
                                 'implementation_limit': inputs['implementation_limit'],
                                 'review_limit': inputs['review_limit']}
        if inputs['route'] == 'batch':
            workflow['execution']['batch_limit'] = inputs['batch_limit']
    elif 'implementation_limit' in inputs:
        execution = {'schema_version': 1, 'implementation_limit': inputs['implementation_limit'], 'review_limit': 1}
        if 'batch_limit' in inputs:
            execution.update(schema_version=2, batch_limit=inputs['batch_limit'])
        if 'review_limit' in inputs:
            if 'batch_limit' not in inputs:
                raise ValueError('Parallel source reviews require an explicit batch limit')
            execution.update(schema_version=3, review_limit=inputs['review_limit'])
        validate_execution_policy(execution)
        phases(inputs['staging'], execution)
        workflow['execution'] = execution
    elif 'batch_limit' in inputs or 'review_limit' in inputs:
        raise ValueError('Batch integration and parallel reviews require an explicit implementation limit')
    if 'task_context' in inputs:
        if not modern:
            validate_task_context(inputs['task_context'], workflow.get('execution'))
        workflow['task_context'] = copy.deepcopy(inputs['task_context'])
    if 'completion_policy' in inputs:
        validate_completion_policy(inputs['completion_policy'])
        workflow['completion_policy'] = inputs['completion_policy']
    if 'knowledge_capture' in inputs:
        if not modern:
            raise ValueError('Knowledge capture requires explicit descriptor3 modern choices')
        workflow['knowledge_capture'] = copy.deepcopy(inputs['knowledge_capture'])
    if 'ci_evidence' in inputs:
        if inputs['ci_evidence'] is None:
            raise ValueError('CI evidence policy must be explicit and non-null')
        ci_policy.policy({'ci_evidence_policy': inputs['ci_evidence']})
        workflow['ci_evidence'] = inputs['ci_evidence']
    if 'ci_retry' in inputs:
        if inputs['ci_retry'] is None:
            raise ValueError('CI retry policy must be explicit and non-null')
        export_contract.structural_retry_policy({'ci_retry_policy': inputs['ci_retry']})
        workflow['ci_retry'] = inputs['ci_retry']
    result = {'schema_version': 3 if modern else 2, 'project': {'name': inputs['name'], 'repository': 'https://github.com/' + repo},
            'standard': {'repository': standard.REPOSITORY, 'revision': revision, 'version': (SOURCE/'VERSION').read_text().strip()},
            'profile': profile, 'adoption': 'draft',
            'workflow': workflow,
            'tracker': {'repository': c['tracker_repository'], 'revision': c['tracker_revision'], 'workspace_id': inputs['workspace_id'],
                        'registration': 'pending', 'verification': '__ONBOARDING_PROOF__'},
            'checks': ['__PROJECT_CHECK_COMMANDS__'], 'environments': env,
            'delivery': {'procedure': '__PROJECT_RELEASE_PROCEDURE__' if env else 'Reviewed main merge; owner pulls manually.',
                         'authorization': '__EXISTING_AUTHORIZATION__' if env else 'Within the authorized implementation request.',
                         'rollback': '__RECOVERY_PROCEDURE__' if env else 'Review and revert through a linked PR.',
                         'backup': '__DATA_PROTECTION__' if env else 'No runtime data managed by this workflow.'},
            'completion': completion, 'exceptions': []}
    if modern:
        result['role'] = inputs['role']
    return result


def render(inputs, revision, tracker_root, python=sys.executable):
    if not standard.SHA.fullmatch(revision): raise ValueError('Use an immutable standard revision')
    data = descriptor(inputs, revision)
    require_engine_choices(data)
    engine = tracker_checkout(tracker_root, data['tracker']['revision'])
    with tempfile.TemporaryDirectory(prefix='master-template-') as scratch:
        scratch = Path(scratch); policy = scratch/'policy.json'; policy.write_text(dumps(delivery_policy(data)))
        target = scratch/'project'
        code = 'import sys; sys.path.insert(0,sys.argv.pop(1)); from tracker.cli import main; raise SystemExit(main())'
        command = [python, '-c', code, str(engine), '--config', str(engine/'tracker/config.json'), 'export-template', '--output', str(target), '--repository', inputs['repository'],
                   '--name', inputs['name'], '--base', 'main', '--id-prefix', inputs['prefix'], '--engine-revision', data['tracker']['revision'],
                   '--delivery-policy', str(policy), '--helper-layout', 'separated']
        if 'execution' in data['workflow']:
            execution = scratch/'execution.json'; execution.write_text(dumps(data['workflow']['execution']))
            command.extend(['--execution-policy', str(execution)])
        if 'process_instructions' in data['workflow']:
            instructions = scratch/'process-instructions.json'
            instructions.write_text(dumps(data['workflow']['process_instructions']))
            command.extend(['--process-instructions', str(instructions)])
        if 'task_context' in data['workflow']:
            context = scratch/'task-context.json'; context.write_text(dumps(data['workflow']['task_context']))
            command.extend(['--task-context-policy', str(context)])
        if 'completion_policy' in data['workflow']:
            completion = scratch/'completion-policy.json'; completion.write_text(dumps(data['workflow']['completion_policy']))
            command.extend(['--completion-policy', str(completion)])
        if 'ci_evidence' in data['workflow']:
            evidence = scratch/'ci-evidence.json'; evidence.write_text(dumps(data['workflow']['ci_evidence']))
            command.extend(['--ci-evidence-policy', str(evidence)])
        if 'ci_retry' in data['workflow']:
            retry = scratch/'ci-retry.json'; retry.write_text(dumps(data['workflow']['ci_retry']))
            command.extend(['--ci-retry-policy', str(retry)])
        if 'knowledge_capture' in data['workflow']:
            capture = scratch/'knowledge-capture.json'; capture.write_text(dumps(data['workflow']['knowledge_capture']))
            command.extend(['--knowledge-capture-policy', str(capture)])
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode: raise ValueError('Tracker export failed (requires Python 3.11+): ' + result.stderr + result.stdout)
        files = {p.relative_to(target).as_posix(): p.read_bytes().decode('utf-8') for p in target.rglob('*') if p.is_file()}
        try:
            exported_lock = json.loads(files['tracker/engine.json'], object_pairs_hook=export_contract.unique)
        except (KeyError, ValueError) as error:
            raise ValueError('Tracker export needs a valid immutable engine lock') from error
        if exported_lock != {'repository': data['tracker']['repository'], 'revision': data['tracker']['revision']}:
            raise ValueError('Tracker export engine lock differs from the trusted compatible pin')
        exported_config = json.loads(files['tracker/config.json'], object_pairs_hook=export_contract.unique)
        export_contract.structural_retry_policy(exported_config)
        if data['schema_version'] == 3:
            export_contract.structural_route_policy(exported_config)
        if 'execution_policy' in exported_config: validate_execution_policy(exported_config['execution_policy'])
        if ('execution_policy' in exported_config) != ('execution' in data['workflow']) or exported_config.get('execution_policy') != data['workflow'].get('execution'):
            raise ValueError('Tracker export execution policy differs from the explicit project choice')
        if data['workflow'].get('execution', {}).get('schema_version') in (2, 3, 4):
            exported_phases = [v if isinstance(v, str) else v['phase'] for v in exported_config.get('workflow', [])]
            if (exported_config.get('delivery_policy') != delivery_policy(data)
                    or exported_phases != phases(inputs['staging'], data['workflow']['execution'])):
                route = data['workflow']['execution'].get('route', 'batch')
                raise ValueError('Tracker export ' + route + ' route differs from the explicit staging/delivery choice')
        if (('process_instructions' in exported_config) != ('process_instructions' in data['workflow'])
                or exported_config.get('process_instructions') != data['workflow'].get('process_instructions')):
            raise ValueError('Tracker export process instructions differ from the explicit project choice')
        if (('task_context_policy' in exported_config) != ('task_context' in data['workflow'])
                or exported_config.get('task_context_policy') != data['workflow'].get('task_context')):
            raise ValueError('Tracker export task context differs from the explicit project choice')
        if 'task_context' in data['workflow'] and 'docs/TASK_CONTEXT.md' not in files:
            raise ValueError('Pinned Tracker export lacks the exact task context guide')
        if (('completion_policy' in exported_config) != ('completion_policy' in data['workflow'])
                or exported_config.get('completion_policy') != data['workflow'].get('completion_policy')):
            raise ValueError('Tracker export completion policy differs from the explicit project choice')
        if 'completion_policy' in data['workflow'] and 'docs/COMPLETION_POLICY.md' not in files:
            raise ValueError('Pinned Tracker export lacks the exact completion policy guide')
        if (('ci_evidence_policy' in exported_config) != ('ci_evidence' in data['workflow'])
                or exported_config.get('ci_evidence_policy') != data['workflow'].get('ci_evidence')):
            raise ValueError('Tracker export CI evidence differs from the explicit project choice')
        if 'ci_evidence' in data['workflow'] and 'docs/CI_REUSE.md' not in files:
            raise ValueError('Pinned Tracker export lacks the exact CI evidence guide')
        if (('ci_retry_policy' in exported_config) != ('ci_retry' in data['workflow'])
                or exported_config.get('ci_retry_policy') != data['workflow'].get('ci_retry')):
            raise ValueError('Tracker export CI retry policy differs from the explicit project choice')
        if 'ci_retry' in data['workflow'] and 'docs/CI_RETRY.md' not in files:
            raise ValueError('Pinned Tracker export lacks the exact CI retry guide')
        if (('knowledge_capture_policy' in exported_config) != ('knowledge_capture' in data['workflow'])
                or exported_config.get('knowledge_capture_policy') != data['workflow'].get('knowledge_capture')):
            raise ValueError('Tracker export knowledge capture differs from the explicit project choice')
    files = separate_export(files)
    export_contract.validate_rendered(files, data)
    files.update(layout_files())
    files['delivery.json'] = dumps(data)
    pr_template = '.github/pull_request_template.md'
    if pr_template not in files:
        raise ValueError('Pinned Tracker export lacks the selected PR template')
    files[pr_template] += '\n\n' + (SOURCE/'templates/workflow/PULL_REQUEST_TEMPLATE.md').read_text()
    for name, dest in FILES.items():
        text = (SOURCE/'templates/workflow'/name).read_text().replace('__STANDARD_REVISION__', revision).replace('EX-12', inputs['prefix']+'-12')
        files[dest] = instruction_render.render(text, data)
    files['CLAUDE.md'] = 'Read AGENTS.md and the project instructions it links before work.\n'
    return files


def baseline(inputs, revision, files):
    return dumps({'schema_version': 1, 'standard_revision': revision, 'inputs': inputs, 'files': files})


def write_plan(root, planned, before):
    # Preflight every path before writing anything. Never traverse project symlinks.
    for name in planned:
        path = standard.safe_path(root, name)
        current = path.read_bytes().decode('utf-8') if path.is_file() else None
        if current != before[name]: raise ValueError('Project changed while planning: ' + name)
        if path.exists() and not path.is_file(): raise ValueError('Expected a regular file: ' + name)
        for parent in path.parents:
            if parent == Path(root).absolute().parent: break
            if parent.exists() and not parent.is_dir(): raise ValueError('Invalid parent directory: ' + str(parent))
    written = []
    try:
        for name, text in planned.items():
            path = standard.safe_path(root, name); path.parent.mkdir(parents=True, exist_ok=True)
            written.append(name)
            if text is None: path.unlink()
            else: path.write_bytes(text.encode('utf-8'))
    except OSError:
        for name in reversed(written):
            path = standard.safe_path(root, name)
            if before[name] is None: path.unlink(missing_ok=True)
            else: path.write_bytes(before[name].encode('utf-8'))
        raise


def init(root, inputs, revision, tracker_root, python=sys.executable, apply=False):
    if isinstance(inputs, dict) and inputs.get('role') in ('application-data', 'release-storage'):
        raise ValueError('Independent resource-board initialization needs its actual producer/registration contract; the descriptive role grants no engineering board')
    files = render(inputs, revision, tracker_root, python)
    files[BASELINE] = baseline(inputs, revision, files.copy())
    collisions = [n for n in files if standard.safe_path(root, n).exists()]
    if collisions: raise ValueError('Existing files preserved; use audited adoption: ' + ', '.join(collisions))
    if apply: write_plan(root, files, dict.fromkeys(files))
    return {'applied': apply, 'files': sorted(files), 'adoption': 'draft', 'connected': False}


MISSING = object()


def merge_json(old, new, local):
    if local == old: return new
    if new == old or local == new: return local
    if all(isinstance(v, dict) for v in (old, new, local)):
        out = {}
        for key in old.keys() | new.keys() | local.keys():
            value = merge_json(old.get(key, MISSING), new.get(key, MISSING), local.get(key, MISSING))
            if value is not MISSING: out[key] = value
        return out
    raise ValueError('Overlapping JSON edits')


def merge_file(name, old, new, local):
    if local == old: return new
    if new == old or local == new: return local
    if None in (old, new, local): raise ValueError('Concurrent file addition/removal')
    if name.endswith('.json'):
        values = [json.loads(value, object_pairs_hook=export_contract.unique) for value in (old, new, local)]
        return dumps(merge_json(*values))
    with tempfile.TemporaryDirectory(prefix='master-merge-') as scratch:
        paths = [Path(scratch)/x for x in ('local', 'old', 'new')]
        for p, content in zip(paths, (local, old, new)): p.write_text(content)
        result = subprocess.run(['git', 'merge-file', '-p', *map(str, paths)], capture_output=True, text=True)
        if result.returncode: raise ValueError('Overlapping text edits')
        return result.stdout


def upgrade_inputs(recorded, local, selection=None):
    """Select an explicitly requested modern template without resetting local choices.

    The recorded old template remains the merge ancestor. These are new-template
    inputs only; genuine old/new/local merging still resolves project exceptions.
    """
    if selection is None:
        return copy.deepcopy(recorded)
    allowed = {'schema_version', 'role', 'route', 'completion', 'preset', 'staging',
               'implementation_limit', 'review_limit', 'batch_limit', 'task_context',
               'completion_policy', 'knowledge_capture'}
    if not isinstance(selection, dict) or set(selection) - allowed:
        raise ValueError('Project choices must contain only explicit role/route/Stage/capacity/guard choices; identity and profile are preserved')
    if 'schema_version' in selection and (type(selection['schema_version']) is not int or selection['schema_version'] != 3):
        raise ValueError('Explicit upgrade choices require schema_version3')
    if not isinstance(local, dict) or type(local.get('schema_version')) is not int or local['schema_version'] not in (2, 3):
        raise ValueError('Audit legacy delivery adoption before selecting modern choices')
    workflow = local.get('workflow')
    if not isinstance(workflow, dict) or type(workflow.get('staging')) is not bool:
        raise ValueError('Preserve an explicit actual local Stage choice')
    value = copy.deepcopy(recorded)
    value.update(schema_version=3, profile=local['profile'], completion=local['completion'], staging=workflow['staging'])
    value.pop('preset', None)
    execution = workflow.get('execution')
    if execution is not None:
        validate_execution_policy(execution)
        value.update(implementation_limit=execution['implementation_limit'], review_limit=execution['review_limit'])
        value['route'] = execution['route'] if execution['schema_version'] == 4 else ('direct' if execution['schema_version'] == 1 else 'batch')
        if 'batch_limit' in execution:
            value['batch_limit'] = execution['batch_limit']
    if 'role' in local:
        value['role'] = local['role']
    # Preserve actual adopted optional selections, including genuine absence.
    for field in ('process_instructions', 'ci_evidence', 'ci_retry', 'knowledge_capture', 'completion_policy'):
        value.pop(field, None)
        if field in workflow:
            value[field] = copy.deepcopy(workflow[field])
    value.pop('task_context', None)
    if isinstance(workflow.get('task_context'), dict) and workflow['task_context'].get('schema_version') == 2:
        value['task_context'] = copy.deepcopy(workflow['task_context'])
    value.update(copy.deepcopy(selection))
    if value.get('route') == 'direct' and 'batch_limit' not in selection:
        value.pop('batch_limit', None)
    return project_choices(value)


def upgrade(root, revision, tracker_root, python=sys.executable, apply=False, *, completion_policy=None, ci_retry_policy=None, choices=None):
    path = standard.safe_path(root, BASELINE)
    if not path.is_file(): raise ValueError('No recorded template base; audit and adopt manually without inventing a baseline')
    raw = path.read_text(); base = json.loads(raw, object_pairs_hook=export_contract.unique)
    if base.get('schema_version') != 1 or not isinstance(base.get('files'), dict): raise ValueError('Invalid template baseline')
    old = base['files']
    if LAYOUT not in old:
        return {'applied': False, 'conflicts': ['legacy mixed layout'], 'changed': [],
                'next': 'Audit and separate repository/system/runtime documents in a project PR; nothing was overwritten.'}
    # Validate local selection before three-way equality can mistake booleans for
    # integers and silently replace an invalid policy. Old pins remain valid;
    # this checks only the optional retry structure, not today's whole standard.
    try:
        local_descriptor = standard.read_descriptor(root)
        if not isinstance(local_descriptor, dict):
            raise ValueError('Local delivery.json must be an object')
        require_engine_choices(local_descriptor)
        local_workflow = local_descriptor.get('workflow', {})
        if not isinstance(local_workflow, dict):
            raise ValueError('Local workflow must be an object')
        if 'execution' in local_workflow:
            validate_execution_policy(local_workflow['execution'])
        if 'task_context' in local_workflow and local_descriptor.get('schema_version') != 3:
            validate_task_context(local_workflow['task_context'], local_workflow.get('execution'))
        if 'completion_policy' in local_workflow:
            validate_completion_policy(local_workflow['completion_policy'])
        if 'ci_retry' in local_workflow:
            export_contract.structural_retry_policy({'ci_retry_policy': local_workflow['ci_retry']})
        local_config = json.loads(standard.safe_path(root, 'tracker/config.json').read_text(),
                                  object_pairs_hook=export_contract.unique)
        if not isinstance(local_config, dict):
            raise ValueError('Local Tracker config must be an object')
        if 'execution_policy' in local_config:
            validate_execution_policy(local_config['execution_policy'])
        if 'task_context_policy' in local_config and local_descriptor.get('schema_version') != 3:
            validate_task_context(local_config['task_context_policy'], local_config.get('execution_policy'))
        if 'completion_policy' in local_config:
            validate_completion_policy(local_config['completion_policy'])
        export_contract.structural_retry_policy(local_config)
    except (KeyError, OSError, TypeError, ValueError) as error:
        return {'applied': False, 'conflicts': ['configuration validation'], 'changed': [], 'errors': [str(error)]}
    selection = copy.deepcopy(choices)
    if isinstance(selection, dict) and completion_policy is not None:
        if 'completion_policy' in selection and dumps(selection['completion_policy']) != dumps(completion_policy):
            raise ValueError('Conflicting explicit completion selections')
        selection['completion_policy'] = completion_policy
    try:
        new_inputs = upgrade_inputs(base['inputs'], local_descriptor, selection)
    except (KeyError, TypeError, ValueError) as error:
        if choices is None:
            raise
        return {'applied': False, 'conflicts': ['explicit project choices'], 'changed': [], 'errors': [str(error)]}
    if completion_policy is not None:
        validate_completion_policy(completion_policy)
        new_inputs['completion_policy'] = completion_policy
    if ci_retry_policy is not None:
        export_contract.structural_retry_policy({'ci_retry_policy': ci_retry_policy})
        new_inputs['ci_retry'] = ci_retry_policy
    try:
        new = render(new_inputs, revision, tracker_root, python)
    except (KeyError, TypeError, ValueError) as error:
        if choices is None:
            raise
        return {'applied': False, 'conflicts': ['explicit project choices'], 'changed': [], 'errors': [str(error)]}
    planned, before, conflicts = {}, {}, []
    for name in sorted(old.keys() | new.keys()):
        path = standard.safe_path(root, name)
        before[name] = path.read_bytes().decode('utf-8') if path.is_file() else None
        if name.startswith(PROJECT_AREAS):
            # Project ownership begins at creation, not at the first local edit.
            planned[name] = before[name]
            continue
        try: planned[name] = merge_file(name, old.get(name), new.get(name), before[name])
        except ValueError: conflicts.append(name)
    if conflicts: return {'applied': False, 'conflicts': conflicts, 'changed': [], 'next': 'Resolve explicitly in a project PR; nothing was overwritten.'}
    planned = {n: value for n, value in planned.items() if value != before[n]}
    planned[BASELINE] = baseline(new_inputs, revision, new)
    before[BASELINE] = raw
    if planned[BASELINE] == raw: planned.pop(BASELINE)
    with tempfile.TemporaryDirectory(prefix='master-validate-') as scratch:
        candidate = dict(before, **planned)
        if choices is not None:
            try:
                selected = json.loads(candidate['delivery.json'], object_pairs_hook=export_contract.unique)
                intended = json.loads(new['delivery.json'], object_pairs_hook=export_contract.unique)
                # JSON bytes distinguish booleans from integers. Local target/check
                # exceptions still merge normally; selected choices must stay exact.
                selected_choices = {key: selected[key] for key in ('schema_version', 'role', 'profile', 'completion')}
                intended_choices = {key: intended[key] for key in selected_choices}
                fields = ('staging', 'execution', 'task_context', 'completion_policy', 'knowledge_capture')
                selected_choices['workflow'] = {key: selected['workflow'][key] for key in fields if key in selected['workflow']}
                intended_choices['workflow'] = {key: intended['workflow'][key] for key in fields if key in intended['workflow']}
                if dumps(selected_choices) != dumps(intended_choices):
                    raise ValueError('Local selections differ from the explicit requested modern choices')
            except (KeyError, TypeError, ValueError) as error:
                return {'applied': False, 'conflicts': ['explicit project choices'], 'changed': [], 'errors': [str(error)],
                        'next': 'Reconcile actual choices in both project files explicitly; nothing was overwritten.'}
        if ci_retry_policy is not None:
            try:
                selected_descriptor = json.loads(candidate['delivery.json'], object_pairs_hook=export_contract.unique)['workflow']['ci_retry']
                selected_config = json.loads(candidate['tracker/config.json'], object_pairs_hook=export_contract.unique)['ci_retry_policy']
                export_contract.structural_retry_policy({'ci_retry_policy': selected_descriptor})
                export_contract.structural_retry_policy({'ci_retry_policy': selected_config})
                selection_matches = selected_descriptor == selected_config == ci_retry_policy
            except (KeyError, TypeError, ValueError):
                selection_matches = False
            if not selection_matches:
                return {'applied': False, 'conflicts': ['explicit CI retry policy selection'], 'changed': [],
                        'next': 'Requested retry policy differs from retained local settings; reconcile both files explicitly in this project PR. Nothing was overwritten.'}
        for name, text in candidate.items():
            if text is not None:
                path = standard.safe_path(scratch, name); path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(text.encode('utf-8'))
        errors = [message for kind, message in inspect(scratch) if kind == 'error']
        if errors:
            return {'applied': False, 'conflicts': ['configuration validation'], 'changed': [], 'errors': errors}
    if apply: write_plan(root, planned, before)
    return {'applied': apply, 'conflicts': [], 'changed': sorted(planned), 'next': 'Validate, review project exceptions and test in the project PR.'}


def inspect(root, expected_revision=None):
    findings = []; data = standard.read_descriptor(root)
    if isinstance(data, dict) and data.get('schema_version') == 3:
        try:
            require_engine_choices(data)
        except (KeyError, TypeError, ValueError, OSError) as error:
            return [('error', str(error))]
    modern = isinstance(data, dict) and type(data.get('schema_version')) is int and data['schema_version'] == 3
    keys = standard.TOP | {'workflow'} | ({'role'} if modern else set())
    if not standard.object_keys(data, keys, 'delivery', findings): return findings
    try:
        if type(data['schema_version']) is not int or data['schema_version'] not in (2, 3): raise ValueError('Expected schema 2 or 3')
        if modern and (not isinstance(data['role'], str) or data['role'] not in ROLES): raise ValueError('Unknown project role')
        if data['profile'] not in PROFILES or data['completion'] != PROFILES[data['profile']]: raise ValueError('Profile/completion mismatch')
        for name, fields in (('project', {'name','repository'}), ('standard', {'repository','revision','version'}),
                             ('tracker', {'repository','revision','workspace_id','registration','verification'}),
                             ('delivery', {'procedure','authorization','rollback','backup'})):
            if not standard.text_fields(data[name], fields, name, findings): return findings
        wf = data['workflow']
        workflow_keys = {'staging','main_branch','stage_branch','required_checks'}
        if isinstance(wf, dict) and 'execution' in wf: workflow_keys.add('execution')
        if isinstance(wf, dict) and 'process_instructions' in wf: workflow_keys.add('process_instructions')
        if isinstance(wf, dict) and 'task_context' in wf: workflow_keys.add('task_context')
        if isinstance(wf, dict) and 'completion_policy' in wf: workflow_keys.add('completion_policy')
        if isinstance(wf, dict) and 'ci_evidence' in wf: workflow_keys.add('ci_evidence')
        if isinstance(wf, dict) and 'ci_retry' in wf: workflow_keys.add('ci_retry')
        if modern and isinstance(wf, dict) and 'knowledge_capture' in wf: workflow_keys.add('knowledge_capture')
        if not standard.object_keys(wf, workflow_keys, 'workflow', findings): return findings
        if modern:
            if not isinstance(wf.get('execution'), dict) or type(wf['execution'].get('schema_version')) is not int or wf['execution']['schema_version'] != 4:
                raise ValueError('Descriptor3 requires explicit execution4')
        elif isinstance(wf.get('execution'), dict) and wf['execution'].get('schema_version') == 4:
            raise ValueError('Execution4 requires descriptor3 with an explicit role')
        if 'execution' in wf: validate_execution_policy(wf['execution'])
        if 'process_instructions' in wf: validate_process_instructions(wf['process_instructions'])
        if 'task_context' in wf and not modern: validate_task_context(wf['task_context'], wf.get('execution'))
        if 'completion_policy' in wf: validate_completion_policy(wf['completion_policy'])
        if 'ci_evidence' in wf:
            if wf['ci_evidence'] is None: raise ValueError('CI evidence policy must be explicit and non-null')
            ci_policy.policy({'ci_evidence_policy': wf['ci_evidence']})
        if 'ci_retry' in wf:
            if wf['ci_retry'] is None: raise ValueError('CI retry policy must be explicit and non-null')
            export_contract.structural_retry_policy({'ci_retry_policy': wf['ci_retry']})
        if type(wf['staging']) is not bool or wf['main_branch'] != 'main' or wf['stage_branch'] != 'stage': raise ValueError('Version 2 uses main and stage with an explicit boolean stage option')
        expected_env = ({'stage'} if wf['staging'] else set()) | ({'production'} if data['completion'] != 'reviewed-merge' else set())
        if not standard.object_keys(data['environments'], expected_env, 'environments', findings): return findings
        for key in expected_env:
            if not standard.text_fields(data['environments'][key], {'target','verify'}, key, findings): return findings
        if not re.fullmatch(r'https://github.com/[\w.-]+/[\w.-]+', data['project']['repository']): raise ValueError('Expected a GitHub project URL')
        revision = data['standard']['revision']; compat = compatibility()
        if (data['standard']['repository'] != standard.REPOSITORY or not standard.SHA.fullmatch(revision)
                or not re.fullmatch(r'\d+\.\d+\.\d+', data['standard']['version'])): raise ValueError('Invalid standard pin')
        if expected_revision and (expected_revision != revision or data['standard']['version'] != (SOURCE/'VERSION').read_text().strip()): raise ValueError('Running standard differs from descriptor pin/version')
        if data['tracker']['repository'] != compat['tracker_repository'] or data['tracker']['revision'] != compat['tracker_revision']: raise ValueError('Tracker pin is incompatible with this standard')
        config = json.loads(standard.safe_path(root, 'tracker/config.json').read_text(), object_pairs_hook=export_contract.unique)
        export_contract.structural_retry_policy(config)
        if modern:
            export_contract.structural_route_policy(config)
        lock = json.loads(standard.safe_path(root, 'tracker/engine.json').read_text(), object_pairs_hook=export_contract.unique)
        if lock != {'repository': compat['tracker_repository'], 'revision': compat['tracker_revision']}: raise ValueError('Tracker client pin differs from descriptor')
        export_contract.validate_root(root, data)
        if not re.fullmatch(r'[A-Z][A-Z0-9]+', config['project'].get('id_prefix', '')): raise ValueError('Tracker prefix is invalid')
        if not re.fullmatch(r'[a-z][a-z0-9-]*', data['tracker']['workspace_id']): raise ValueError('Workspace ID is invalid')
        if config['project']['repository'] != data['project']['repository'].split('github.com/')[1] or config['project']['base_branch'] != wf['main_branch']: raise ValueError('Tracker project identity differs')
        if config.get('delivery_policy') != delivery_policy(data): raise ValueError('Tracker policy differs from delivery.json; synchronize both in this PR')
        if 'execution_policy' in config: validate_execution_policy(config['execution_policy'])
        if ('execution_policy' in config) != ('execution' in wf) or config.get('execution_policy') != wf.get('execution'):
            raise ValueError('Tracker execution policy differs from delivery.json; synchronize both in this PR')
        if (('process_instructions' in config) != ('process_instructions' in wf)
                or config.get('process_instructions') != wf.get('process_instructions')):
            raise ValueError('Tracker process instructions differ from delivery.json; synchronize both in this PR')
        if (('task_context_policy' in config) != ('task_context' in wf)
                or config.get('task_context_policy') != wf.get('task_context')):
            raise ValueError('Tracker task context differs from delivery.json; synchronize both in this PR')
        if (('completion_policy' in config) != ('completion_policy' in wf)
                or config.get('completion_policy') != wf.get('completion_policy')):
            raise ValueError('Tracker completion policy differs from delivery.json; synchronize both in this PR')
        if (('ci_evidence_policy' in config) != ('ci_evidence' in wf)
                or config.get('ci_evidence_policy') != wf.get('ci_evidence')):
            raise ValueError('Tracker CI evidence differs from delivery.json; synchronize both in this PR')
        if (('ci_retry_policy' in config) != ('ci_retry' in wf)
                or config.get('ci_retry_policy') != wf.get('ci_retry')):
            raise ValueError('Tracker CI retry policy differs from delivery.json; synchronize both in this PR')
        if (('knowledge_capture_policy' in config) != ('knowledge_capture' in wf)
                or config.get('knowledge_capture_policy') != wf.get('knowledge_capture')):
            raise ValueError('Tracker knowledge capture differs from delivery.json; synchronize both in this PR')
        actual_phases = [v if isinstance(v,str) else v['phase'] for v in config['workflow']]
        if actual_phases != phases(wf['staging'], wf.get('execution')): raise ValueError('Tracker stages differ from the adopted workflow')
        checks = wf['required_checks']
        if not isinstance(checks,list) or not checks or any(not isinstance(x,str) or not x.strip() for x in checks) or len(set(checks))!=len(checks): raise ValueError('List unique required GitHub check names')
        if not {'descriptor','tracker-link'} <= set(checks): raise ValueError('Descriptor and tracker-link checks are required')
        layout = json.loads(standard.safe_path(root, LAYOUT).read_text())
        if layout != LAYOUT_DATA: raise ValueError('Use the separated repository/system/runtime layout')
        required = set(FILES.values()) | set(FORWARDS) | {'docs/repository/TRACKER.md', '.github/pull_request_template.md'}
        if 'task_context' in wf:
            required.add('docs/repository/TASK_CONTEXT.md')
        if 'completion_policy' in wf:
            required.add('docs/repository/COMPLETION_POLICY.md')
        if 'ci_evidence' in wf:
            required.add('docs/repository/CI_REUSE.md')
        if 'ci_retry' in wf:
            required.add('docs/repository/CI_RETRY.md')
        for name in sorted(required):
            path = standard.safe_path(root,name)
            if not path.is_file() or not path.read_text().strip(): raise ValueError('Missing '+name)
        ci=standard.safe_path(root,'.github/workflows/delivery-check.yml').read_text()
        uses=re.findall(r'uses:\s*MojoTheApe/master-repo@([^\s#]+)',ci)
        if uses != [revision]: raise ValueError('CI action pin differs from descriptor')
        if not isinstance(data['checks'],list) or not data['checks'] or any(not isinstance(x,str) for x in data['checks']): raise ValueError('List project verification procedures')
        if not isinstance(data['exceptions'],list): raise ValueError('Exceptions must be a list')
        for row in data['exceptions']: standard.text_fields(row,{'scope','reason','reference'},'exception',findings)
        if data['adoption'] not in ('draft','ready'): raise ValueError('Adoption must be draft or ready')
        if data['tracker']['registration'] not in ('pending','verified'): raise ValueError('Registration must be pending or verified')
        if data['adoption']=='draft': findings.append(('setup','Adoption is draft'))
        if data['tracker']['registration']!='verified': findings.append(('setup','Tracker registration/publication is not verified'))
        standard.placeholders(data,'delivery',findings)
    except (KeyError,TypeError,ValueError,OSError,AttributeError) as error: findings.append(('error',str(error)))
    return findings
