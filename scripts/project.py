"""Version 2 project scaffolding and conservative three-way template upgrades."""
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import standard

SOURCE = Path(__file__).resolve().parents[1]
PROFILES = {'vps': 'verified-production', 'n8n': 'verified-production', 'n8n-source': 'reviewed-merge', 'local': 'reviewed-merge',
            'package': 'verified-stable-package', 'tooling': 'reviewed-merge'}
PHASES = ['idea', 'backlog', 'todo', 'in_progress', 'review', 'stage', 'merged']
BASELINE = '.workflow/template-base.json'
FILES = {'AGENTS.md': 'AGENTS.md', 'DELIVERY.md': 'docs/DELIVERY.md', 'PROJECT.md': 'docs/PROJECT.md',
         'CHANGELOG.md': 'docs/CHANGELOG.md', 'SPECS.md': 'docs/specs/README.md',
         'PULL_REQUEST_TEMPLATE.md': '.github/pull_request_template.md',
         'delivery-check.yml': '.github/workflows/delivery-check.yml'}


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


def descriptor(inputs, revision):
    c = compatibility(); profile = inputs['profile']; repo = inputs['repository']
    if (profile not in PROFILES or not re.fullmatch(r'[\w.-]+/[\w.-]+', repo)
            or not re.fullmatch(r'[A-Z][A-Z0-9]+', inputs['prefix'])
            or not re.fullmatch(r'[a-z][a-z0-9-]*', inputs['workspace_id'])
            or type(inputs['staging']) is not bool or not inputs['name'].strip()):
        raise ValueError('Invalid project identity, profile, prefix or stage choice')
    env = {}
    if inputs['staging']: env['stage'] = {'target': '__STAGE_TARGET__', 'verify': '__STAGE_CHECKS__'}
    if PROFILES[profile] != 'reviewed-merge': env['production'] = {'target': '__PRODUCTION_TARGET__', 'verify': '__PRODUCTION_CHECKS__'}
    return {'schema_version': 2, 'project': {'name': inputs['name'], 'repository': 'https://github.com/' + repo},
            'standard': {'repository': standard.REPOSITORY, 'revision': revision, 'version': (SOURCE/'VERSION').read_text().strip()},
            'profile': profile, 'adoption': 'draft',
            'workflow': {'staging': inputs['staging'], 'main_branch': 'main', 'stage_branch': 'stage', 'required_checks': ['descriptor', 'tracker-link']},
            'tracker': {'repository': c['tracker_repository'], 'revision': c['tracker_revision'], 'workspace_id': inputs['workspace_id'],
                        'registration': 'pending', 'verification': '__ONBOARDING_PROOF__'},
            'checks': ['__PROJECT_CHECK_COMMANDS__'], 'environments': env,
            'delivery': {'procedure': '__PROJECT_RELEASE_PROCEDURE__' if env else 'Reviewed main merge; owner pulls manually.',
                         'authorization': '__EXISTING_AUTHORIZATION__' if env else 'Within the authorized implementation request.',
                         'rollback': '__RECOVERY_PROCEDURE__' if env else 'Review and revert through a linked PR.',
                         'backup': '__DATA_PROTECTION__' if env else 'No runtime data managed by this workflow.'},
            'completion': PROFILES[profile], 'exceptions': []}


def render(inputs, revision, tracker_root, python=sys.executable):
    if not standard.SHA.fullmatch(revision): raise ValueError('Use an immutable standard revision')
    data = descriptor(inputs, revision); engine = tracker_checkout(tracker_root, data['tracker']['revision'])
    with tempfile.TemporaryDirectory(prefix='master-template-') as scratch:
        scratch = Path(scratch); policy = scratch/'policy.json'; policy.write_text(dumps(delivery_policy(data)))
        target = scratch/'project'
        code = 'import sys; sys.path.insert(0,sys.argv.pop(1)); from tracker.cli import main; raise SystemExit(main())'
        command = [python, '-c', code, str(engine), '--config', str(engine/'tracker/config.json'), 'export-template', '--output', str(target), '--repository', inputs['repository'],
                   '--name', inputs['name'], '--base', 'main', '--id-prefix', inputs['prefix'], '--engine-revision', data['tracker']['revision'],
                   '--delivery-policy', str(policy)]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode: raise ValueError('Tracker export failed (requires Python 3.11+): ' + result.stderr + result.stdout)
        files = {p.relative_to(target).as_posix(): p.read_text() for p in target.rglob('*') if p.is_file()}
    files['delivery.json'] = dumps(data)
    for name, dest in FILES.items():
        files[dest] = (SOURCE/'templates/workflow'/name).read_text().replace('__STANDARD_REVISION__', revision).replace('EX-12', inputs['prefix']+'-12')
    files['CLAUDE.md'] = 'Read AGENTS.md and the project instructions it links before work.\n'
    return files


def baseline(inputs, revision, files):
    return dumps({'schema_version': 1, 'standard_revision': revision, 'inputs': inputs, 'files': files})


def write_plan(root, planned, before):
    # Preflight every path before writing anything. Never traverse project symlinks.
    for name in planned:
        path = standard.safe_path(root, name)
        current = path.read_text() if path.is_file() else None
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
            else: path.write_text(text, encoding='utf-8')
    except OSError:
        for name in reversed(written):
            path = standard.safe_path(root, name)
            if before[name] is None: path.unlink(missing_ok=True)
            else: path.write_text(before[name], encoding='utf-8')
        raise


def init(root, inputs, revision, tracker_root, python=sys.executable, apply=False):
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
    if name.endswith('.json'): return dumps(merge_json(json.loads(old), json.loads(new), json.loads(local)))
    with tempfile.TemporaryDirectory(prefix='master-merge-') as scratch:
        paths = [Path(scratch)/x for x in ('local', 'old', 'new')]
        for p, content in zip(paths, (local, old, new)): p.write_text(content)
        result = subprocess.run(['git', 'merge-file', '-p', *map(str, paths)], capture_output=True, text=True)
        if result.returncode: raise ValueError('Overlapping text edits')
        return result.stdout


def upgrade(root, revision, tracker_root, python=sys.executable, apply=False):
    path = standard.safe_path(root, BASELINE)
    if not path.is_file(): raise ValueError('No recorded template base; audit and adopt manually without inventing a baseline')
    raw = path.read_text(); base = json.loads(raw)
    if base.get('schema_version') != 1 or not isinstance(base.get('files'), dict): raise ValueError('Invalid template baseline')
    old = base['files']; new = render(base['inputs'], revision, tracker_root, python)
    planned, before, conflicts = {}, {}, []
    for name in sorted(old.keys() | new.keys()):
        path = standard.safe_path(root, name)
        before[name] = path.read_text() if path.is_file() else None
        try: planned[name] = merge_file(name, old.get(name), new.get(name), before[name])
        except ValueError: conflicts.append(name)
    if conflicts: return {'applied': False, 'conflicts': conflicts, 'changed': [], 'next': 'Resolve explicitly in a project PR; nothing was overwritten.'}
    planned = {n: value for n, value in planned.items() if value != before[n]}
    planned[BASELINE] = baseline(base['inputs'], revision, new)
    before[BASELINE] = raw
    if planned[BASELINE] == raw: planned.pop(BASELINE)
    with tempfile.TemporaryDirectory(prefix='master-validate-') as scratch:
        candidate = dict(before, **planned)
        for name, text in candidate.items():
            if text is not None:
                path = standard.safe_path(scratch, name); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text)
        errors = [message for kind, message in inspect(scratch) if kind == 'error']
        if errors:
            return {'applied': False, 'conflicts': ['configuration validation'], 'changed': [], 'errors': errors}
    if apply: write_plan(root, planned, before)
    return {'applied': apply, 'conflicts': [], 'changed': sorted(planned), 'next': 'Validate, review project exceptions and test in the project PR.'}


def inspect(root, expected_revision=None):
    findings = []; data = standard.read_descriptor(root)
    keys = standard.TOP | {'workflow'}
    if not standard.object_keys(data, keys, 'delivery', findings): return findings
    try:
        if type(data['schema_version']) is not int or data['schema_version'] != 2: raise ValueError('Expected schema 2')
        if data['profile'] not in PROFILES or data['completion'] != PROFILES[data['profile']]: raise ValueError('Profile/completion mismatch')
        for name, fields in (('project', {'name','repository'}), ('standard', {'repository','revision','version'}),
                             ('tracker', {'repository','revision','workspace_id','registration','verification'}),
                             ('delivery', {'procedure','authorization','rollback','backup'})):
            if not standard.text_fields(data[name], fields, name, findings): return findings
        wf = data['workflow']
        if not standard.object_keys(wf, {'staging','main_branch','stage_branch','required_checks'}, 'workflow', findings): return findings
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
        config = json.loads(standard.safe_path(root, 'tracker/config.json').read_text())
        lock = json.loads(standard.safe_path(root, 'tracker/engine.json').read_text())
        if lock != {'repository': compat['tracker_repository'], 'revision': compat['tracker_revision']}: raise ValueError('Tracker client pin differs from descriptor')
        if not re.fullmatch(r'[A-Z][A-Z0-9]+', config['project'].get('id_prefix', '')): raise ValueError('Tracker prefix is invalid')
        if not re.fullmatch(r'[a-z][a-z0-9-]*', data['tracker']['workspace_id']): raise ValueError('Workspace ID is invalid')
        if config['project']['repository'] != data['project']['repository'].split('github.com/')[1] or config['project']['base_branch'] != wf['main_branch']: raise ValueError('Tracker project identity differs')
        if config.get('delivery_policy') != delivery_policy(data): raise ValueError('Tracker policy differs from delivery.json; synchronize both in this PR')
        phases = [v if isinstance(v,str) else v['phase'] for v in config['workflow']]
        if phases != [p for p in PHASES if p != 'stage' or wf['staging']]: raise ValueError('Tracker stages differ from the adopted workflow')
        checks = wf['required_checks']
        if not isinstance(checks,list) or not checks or any(not isinstance(x,str) or not x.strip() for x in checks) or len(set(checks))!=len(checks): raise ValueError('List unique required GitHub check names')
        if not {'descriptor','tracker-link'} <= set(checks): raise ValueError('Descriptor and tracker-link checks are required')
        for name in ('AGENTS.md','docs/DELIVERY.md','docs/PROJECT.md','docs/CHANGELOG.md','docs/TRACKER_AGENT_WORKFLOW.md','scripts/task_tracker.py','scripts/tracker_pr_check.py','scripts/tracker_delivery_policy.py'):
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
