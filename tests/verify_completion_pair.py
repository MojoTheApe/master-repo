"""Exercise actual exported consumers; no live state or consumer is changed."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
from urllib.parse import unquote
import subprocess
import sys
import tempfile
from unittest import mock


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


def source_inputs(args):
    """Bind every current/old input before any export or upgrade is attempted."""
    sources = {}
    for name, repository in (('master', 'master-repo'), ('tracker', 'task-tracker'),
                             ('old_master', 'master-repo'), ('old_tracker', 'task-tracker')):
        root = getattr(args, name)
        origin = git(root, 'remote', 'get-url', 'origin')
        official = origin.removesuffix('.git') in ('https://github.com/MojoTheApe/'+repository,
                                                  'git@github.com:MojoTheApe/'+repository)
        row = dict(head=git(root, 'rev-parse', 'HEAD'), tree=git(root, 'rev-parse', 'HEAD^{tree}'),
                   dirty=bool(git(root, 'status', '--porcelain')), origin=origin, official_origin=official)
        sources[name] = row
        if args.require_pinned and (row['dirty'] or not official):
            raise ValueError('Final pair requires a clean official '+name+' input')
    old = json.loads((args.old_master/'compatibility.json').read_bytes())
    matched = old.get('tracker_repository') == 'MojoTheApe/task-tracker' and old.get('tracker_revision') == sources['old_tracker']['head']
    if args.require_pinned and not matched:
        raise ValueError('Old Master compatibility pin differs from the actual old Tracker input')
    sources['old_compatibility_pin_matches'] = matched
    return sources


def changed_engine_contract(args, scratch, *, retry=False, direct=False):
    """Actual committed rule drift must fail even with freshly matching pin metadata."""
    label = 'route' if direct else 'retry' if retry else 'ci'
    engine = scratch/('changed-'+label+'-engine')
    subprocess.run(['git', 'clone', '--quiet', '--no-hardlinks', str(args.tracker), str(engine)], check=True)
    subprocess.run(['git', '-C', str(engine), 'remote', 'set-url', 'origin',
                    'https://github.com/MojoTheApe/task-tracker.git'], check=True)
    source_name = 'tracker/direct_policy.py' if direct else 'tracker/ci_retry.py' if retry else 'tracker/ci_evidence.py'
    source = engine/source_name
    before = source.read_bytes()
    old, new = ((b"integer(value.get('review_limit'), 1, 5)", b"integer(value.get('review_limit'), 1, 6)") if direct else
                (b"value['max_executions'] not in (1, 2)", b"value['max_executions'] not in (1, 2, 3)") if retry else
                (b"p['max_age_seconds'] <= 30 * 86400", b"p['max_age_seconds'] <= 31 * 86400"))
    assert before.count(old) == 1, 'Update the real contract-drift mutation for this engine'
    source.write_bytes(before.replace(old, new))
    subprocess.run(['git', '-C', str(engine), 'add', source_name], check=True)
    subprocess.run(['git', '-C', str(engine), '-c', 'user.name=Isolated contract fixture',
                    '-c', 'user.email=fixture@example.invalid', 'commit', '--quiet',
                    '-m', 'Fixture only: change the actual canonical contract rule'], check=True)
    revision = git(engine, 'rev-parse', 'HEAD')
    master = scratch/('stale-master-'+label+'-contract')
    shutil.copytree(args.master, master, ignore=shutil.ignore_patterns('.git', '__pycache__', '.venv', '.pytest_cache'))
    # Refresh identity alone, deliberately retaining the old technical rules and
    # hashes. A manually wrong SHA or a dirty checkout is not this negative case.
    record_path = master/'scripts/vendor/tracker-export-contract.json'
    record = json.loads(record_path.read_bytes()); record['engine']['revision'] = revision
    raw = (json.dumps(record, indent=2, sort_keys=True)+'\n').encode()
    record_path.write_bytes(raw)
    compat_path = master/'compatibility.json'; compat = json.loads(compat_path.read_bytes())
    compat.update(tracker_revision=revision, export_contract_sha256=hashlib.sha256(raw).hexdigest())
    compat_path.write_text(json.dumps(compat))
    inputs = dict(name='Isolated changed contract', repository='example/portable', prefix='EX',
                  workspace_id='portable', profile='tooling', staging=False)
    probe = '''import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1]); import project
try: project.render(json.loads(sys.argv[2]),sys.argv[3],Path(sys.argv[4]),sys.executable)
except ValueError as error:
 assert 'export manifest differs from the trusted compatible source record' in str(error),str(error)
 print('actual changed canonical rule refused with matching metadata and stale contract')
else: raise AssertionError('Changed engine rules passed a stale trusted contract')
'''
    checked = subprocess.run([sys.executable, '-I', '-c', probe, str(master/'scripts'),
                              json.dumps(inputs), git(args.master, 'rev-parse', 'HEAD'), str(engine)],
                             cwd=scratch, capture_output=True, text=True)
    assert checked.returncode == 0, (checked.stdout, checked.stderr)
    return dict(actual_canonical_rule_changed=True, local_committed_engine=revision,
                official_origin_preserved=True, clean_engine=True, matching_pin_metadata=True,
                canonical_source=source_name,
                stale_trusted_rule_and_helper_record_rejected=True, live_mutations=0)


def selected_instructions(root, exported, config, inputs, tracker):
    """Compare real final consumer prose with its engine-owned source and links."""
    sys.path.insert(0, str(tracker))
    from tracker import instructions
    guide = exported['docs/repository/TRACKER.md']
    expected = instructions.render_guide(config).replace('](../tracker/', '](../../tracker/')
    assert guide == expected, 'Master changed selected Tracker rules beyond layout navigation'
    pr = exported['.github/pull_request_template.md']
    assert pr.startswith(instructions.render_pr_template(config))
    assert len(re.findall(r'^Tracker issues:', pr, re.M)) == 1
    for name in instructions.SHARED_DOCS:
        assert exported['docs/repository/' + name] == (tracker/'docs'/name).read_text()
        assert '(repository/' + name + ')' in exported['docs/' + name]
    assert exported['docs/repository/WORKFLOW_REFERENCE.md'] == instructions.render_reference()
    version = config.get('execution_policy', {}).get('schema_version')
    for other in (1, 2, 3, 4):
        heading = 'execution schema4' if other == 4 else f'execution schema {other}'
        assert (heading in guide) == (version == other)
    assert ('Selected route: legacy ownership' in guide) == (version is None)
    for key, heading in (('task_context_policy', 'Selected task context'),
                         ('completion_policy', 'Selected accepted-scope completion'),
                         ('process_instructions', 'Selected instruction-only exception'),
                         ('ci_evidence_policy', 'Selected native CI evidence'),
                         ('ci_retry_policy', 'Selected CI retry policy')):
        assert (heading in guide) == (key in config), (key, heading)
    common = exported['docs/repository/WORKFLOW.md']
    assert ('Stage is enabled' in common) == inputs['staging']
    assert ('Stage is disabled' in common) != inputs['staging']
    links = 0
    for name, text in exported.items():
        if not name.endswith('.md'):
            continue
        for raw in re.findall(r'(?<!!)\[[^\]]*\]\(([^)]+)\)', text):
            target = raw.split('#', 1)[0].split('?', 1)[0]
            if not target or re.match(r'^[a-zA-Z]+:', target):
                continue
            resolved = (root/name).parent/unquote(target)
            assert root.resolve() in resolved.resolve().parents, (name, raw, 'escaped export')
            assert resolved.is_file(), (name, raw, 'broken consumer navigation')
            links += 1
    return {'selected_guide_exact_except_navigation': True,
            'tracker_pr_verbatim': True, 'shared_reference_bytes_exact': True,
            'relative_markdown_links_checked': links}


def modern_outputs(args, scratch, project, revision):
    """Actual Master outputs; canonical saved lifecycle replay is separate."""
    from portable_contract_fixture import isolated_consumer
    rows = []
    cases = [('tooling', 'shared-tooling-library', 'direct', False, False),
             ('tooling', 'research', 'direct', True, False),
             ('n8n-source', 'research', 'direct', True, False),
             ('package', 'shared-tooling-library', 'direct', True, False),
             ('vps', 'application', 'direct', False, False),
             ('local', 'application', 'batch', False, False),
             ('local', 'application', 'batch', True, False),
             ('tooling', 'knowledge', 'direct', False, True),
             ('tooling', 'knowledge', 'direct', True, True)]
    for index, (profile, role, route, staged, capture) in enumerate(cases):
        inputs = dict(name='Modern synthetic consumer', repository='owner/example', prefix='EX', workspace_id='example',
            profile=profile, role=role, route=route, completion=project.PROFILES[profile], staging=staged,
            implementation_limit=2, review_limit=2, task_context={'schema_version': 2}, completion_policy={'schema_version': 1})
        if route == 'batch': inputs['batch_limit'] = 2
        if capture:
            inputs['knowledge_capture'] = dict(schema_version=1, roots=['notes/'], scope='Ordinary project-approved observations; no governance or automation.')
        files = project.render(inputs, revision, args.tracker, sys.executable)
        root = scratch/('modern-'+str(index)); root.mkdir()
        for name, content in files.items():
            path = root/name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(content)
        errors = [message for kind, message in project.inspect(root) if kind == 'error']
        assert not errors, (inputs, errors)
        config = json.loads(files['tracker/config.json']); descriptor = json.loads(files['delivery.json'])
        assert descriptor['schema_version'] == 3 and descriptor['role'] == role
        assert descriptor['completion'] == project.PROFILES[profile]
        assert config['execution_policy'] == descriptor['workflow']['execution']
        assert config['task_context_policy'] == {'schema_version': 2} and config['completion_policy'] == {'schema_version': 1}
        assert ('approved' in config['workflow']) == (route == 'batch')
        assert config.get('knowledge_capture_policy') == inputs.get('knowledge_capture')
        rows.append(dict(profile=profile, role=role, route=route, stage=staged, capture=capture,
            generated_config_sha256=hashlib.sha256(files['tracker/config.json'].encode()).hexdigest(),
            portable_runtime=isolated_consumer(root, args.python39),
            instructions=selected_instructions(root, files, config, inputs, args.tracker),
            saved_canonical_lifecycle_replay_is_separate=True))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--master', type=Path, required=True)
    parser.add_argument('--tracker', type=Path, required=True)
    parser.add_argument('--old-master', type=Path, required=True)
    parser.add_argument('--old-tracker', type=Path, required=True)
    parser.add_argument('--python39', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--upgrades-only', action='store_true')
    parser.add_argument('--selected-instructions', action='store_true', help='Check the complete final selected guide/reference/PR closure; synthetic explicit CI policy tests navigation only')
    parser.add_argument('--bounded', action='store_true', help='Six representative actual outputs plus four genuine old-source upgrades')
    parser.add_argument('--portable-contract', action='store_true', help='Require exact trusted artifacts, engine-free native fixtures and real contract-drift refusal')
    parser.add_argument('--retry-contract', action='store_true', help='Exercise explicit retry selection/preservation, actual accounting CLI and retry-rule drift')
    parser.add_argument('--direct-contract', action='store_true', help='Exercise actual modern Master outputs and canonical direct admission/receipt fixtures')
    parser.add_argument('--selection-delivery-contract', action='store_true', help='Require canonical one-policy package delivery before owned activation')
    parser.add_argument('--require-pinned', action='store_true', help='Reject a dirty Master or an engine override')
    args = parser.parse_args()
    if args.retry_contract and not args.portable_contract:
        parser.error('--retry-contract requires --portable-contract')
    if args.direct_contract and not args.portable_contract:
        parser.error('--direct-contract requires --portable-contract')
    if args.selection_delivery_contract and not args.portable_contract:
        parser.error('--selection-delivery-contract requires --portable-contract')
    if args.selection_delivery_contract and args.upgrades_only:
        parser.error('--selection-delivery-contract requires actual portable replay; omit --upgrades-only')
    for name in ('master', 'tracker', 'old_master', 'old_tracker', 'output'):
        setattr(args, name, getattr(args, name).resolve())
    sources = source_inputs(args)
    sys.path.insert(0, str(args.master / 'scripts'))
    import project
    tracker_revision = git(args.tracker, 'rev-parse', 'HEAD')
    master_revision = git(args.master, 'rev-parse', 'HEAD')
    original_compatibility = project.compatibility()
    candidate = dict(original_compatibility, tracker_revision=tracker_revision)
    result = {'master_head': master_revision, 'master_dirty': bool(git(args.master, 'status', '--porcelain')),
              'tracker_head': tracker_revision, 'tracker_dirty': bool(git(args.tracker, 'status', '--porcelain')),
              'compatibility_pin_in_source': original_compatibility['tracker_revision'],
              'candidate_pair_override': original_compatibility != candidate,
              'matrix': [], 'upgrades': [], 'python39': args.python39,
              'consumer_activation': False, 'selected_instructions': args.selected_instructions}
    result.update(bounded=args.bounded, portable_contract=args.portable_contract,
                  retry_contract=args.retry_contract,
                  direct_contract=args.direct_contract,
                  selection_delivery_contract=args.selection_delivery_contract,
                  upgrades_only=args.upgrades_only,
                  publication_verified_by_this_command=False, source_inputs=sources)
    if result['tracker_dirty']:
        raise ValueError('The actual Tracker candidate must be clean and immutable')
    if args.require_pinned and (result['master_dirty'] or result['candidate_pair_override']):
        raise ValueError('Final pair verification requires the clean exact Master and its actual compatible engine pin')
    modes = {'legacy': {}, 'v1': {'implementation_limit': 3},
             'v2': {'implementation_limit': 5, 'batch_limit': 5},
             'v3': {'implementation_limit': 5, 'batch_limit': 5, 'review_limit': 5}}
    smoke = '''import copy, json, sys
from pathlib import Path
import re
from urllib.parse import unquote
root = Path(sys.argv[1])
sys.path.insert(0, str(root / '.workflow/tools'))
import tracker_delivery_policy as rules
import tracker_delivery_receipt
config = json.loads((root / 'tracker/config.json').read_text())
issue = {'number': 12, 'title': 'Original task', 'body': '## Description\\nExpected outcome.\\n\\n## Specifications\\nAccepted requirements.\\n', 'labels': ['status:merged', 'type:feature']}
scope = rules.task_scope(issue, config)
receipt = {'policy': rules.fingerprint(config), 'state': 'verified', 'admitted': True, 'verified': True, 'scope': scope, 'scope_provenance': 'a' * 64}
assert rules.completion_assessment(issue, config, receipt, activated=True)['complete']
changed = copy.deepcopy(issue); changed['body'] += 'New requirement.\\n'
assessment = rules.completion_assessment(changed, config, receipt, activated=True)
assert not assessment['complete'] and assessment['delivery_state'] == 'requirements-changed', assessment
unknown = dict(receipt); unknown.pop('scope'); unknown.pop('scope_provenance')
assessment = rules.completion_assessment(issue, config, unknown, activated=True)
assert not assessment['complete'] and assessment['delivery_state'] == 'unverified', assessment
assessment = rules.completion_assessment(issue, config, {}, activated=True)
assert not assessment['complete'] and assessment['delivery_state'] == 'unverified', assessment
unmerged = copy.deepcopy(issue); unmerged['labels'] = ['status:backlog', 'type:feature']
assert rules.completion_assessment(unmerged, config, {}, activated=True)['delivery_state'] == 'pending'
assert not rules.completion_assessment(issue, config, receipt, activated=False)['complete']
assert not any(name == 'tracker' or name.startswith('tracker.') for name in sys.modules)
print('isolated portable assessment/import passed')
'''
    with mock.patch.object(project, 'compatibility', return_value=candidate), tempfile.TemporaryDirectory(prefix='completion-pair-') as scratch:
        scratch = Path(scratch)
        for profile in (() if args.upgrades_only else project.PROFILES):
            for staging in (False, True):
                for mode, choices in modes.items():
                    contexts = (False, True) if mode in ('v2', 'v3') else (False,)
                    for context in contexts:
                        inputs = dict(name='Synthetic consumer', repository='owner/example', prefix='EX',
                                      workspace_id='example', profile=profile, staging=staging, **choices)
                        if context:
                            inputs['task_context'] = {'schema_version': 1}
                        for selected in (False, True):
                            if args.bounded and (profile, staging, mode, context, selected) not in {
                                    ('tooling', False, 'legacy', False, False), ('vps', True, 'v1', False, True),
                                    ('package', True, 'v2', True, True), ('vps', False, 'v3', True, True),
                                    ('n8n-source', True, 'v2', False, False), ('local', False, 'legacy', False, True)}:
                                continue
                            actual = dict(inputs)
                            if selected:
                                actual['completion_policy'] = {'schema_version': 1}
                                if args.retry_contract:
                                    actual['ci_retry'] = {'schema_version': 1,
                                        'max_executions': 1 if (profile, mode)==('local','legacy') else 2}
                                if args.selected_instructions:
                                    actual['process_instructions'] = {'schema_version': 1, 'required_checks': ['descriptor', 'tracker-link']}
                                    actual['ci_evidence'] = {'schema_version': 2, 'profiles': {'checks': {
                                        'workflow_path': '.github/workflows/product.yml', 'workflow_blob_sha': 'a'*40,
                                        'producer_files': {'.workflow/tools/tracker_ci_evidence.py': 'b'*40},
                                        'metadata_mode': 'commit', 'max_age_seconds': 3600,
                                        'jobs': {'Product checks': {'mode': 'fresh'}}}}}
                            root = scratch / 'consumer'
                            exported = project.render(actual, master_revision, args.tracker, sys.executable)
                            for name, content in exported.items():
                                path = root / name
                                path.parent.mkdir(parents=True, exist_ok=True)
                                path.write_bytes(content.encode('utf-8'))
                            errors = [message for kind, message in project.inspect(root) if kind == 'error']
                            assert not errors, (actual, errors)
                            config = json.loads(exported['tracker/config.json'])
                            descriptor = json.loads(exported['delivery.json'])
                            assert ('completion_policy' in config) == selected
                            assert ('completion_policy' in descriptor['workflow']) == selected
                            if args.retry_contract:
                                assert config.get('ci_retry_policy') == actual.get('ci_retry')
                                assert descriptor['workflow'].get('ci_retry') == actual.get('ci_retry')
                            assert descriptor['completion'] == project.PROFILES[profile]
                            assert descriptor['workflow']['staging'] == staging
                            row = dict(profile=profile, stage=staging, execution=mode, task_context=context,
                                       selected=selected, ci_retry=actual.get('ci_retry'))
                            if args.portable_contract:
                                from portable_contract_fixture import isolated_consumer
                                row['portable_runtime'] = isolated_consumer(root, args.python39)
                            if args.selected_instructions:
                                row['instructions'] = selected_instructions(root, exported, config, actual, args.tracker)
                            if selected:
                                guide = exported['docs/repository/COMPLETION_POLICY.md']
                                assert guide == (args.tracker / 'docs/COMPLETION_POLICY.md').read_text()
                                row['guide_sha256'] = hashlib.sha256(guide.encode()).hexdigest()
                                for name, source in (('tracker_delivery_policy.py', 'delivery_policy.py'),
                                                     ('tracker_task_context.py', 'task_context.py'),
                                                     ('tracker_delivery_receipt.py', 'delivery_receipt.py')):
                                    assert exported['.workflow/tools/' + name] == (args.tracker / 'tracker' / source).read_text()
                                checked = subprocess.run([args.python39, '-I', '-c', smoke, str(root)],
                                                         cwd=scratch, capture_output=True, text=True)
                                assert checked.returncode == 0, (row, checked.stdout, checked.stderr)
                                row['isolated_python39_portable_assessment'] = True
                            result['matrix'].append(row)
                            shutil.rmtree(root)
        if not args.upgrades_only:
            result['exports_passed'] = True
            args.output.write_text(json.dumps(result, indent=2) + '\n')
            print('All actual exports and isolated portable checks passed', flush=True)
        old_revision = git(args.old_master, 'rev-parse', 'HEAD')
        for mode, choices in modes.items():
            root = scratch / ('upgrade-' + mode)
            inputs = dict(name='Synthetic consumer', repository='owner/example', prefix='EX',
                          workspace_id='example', profile='local', staging=False, **choices)
            old_code = ('import json,sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); '
                        'import project; project.init(Path(sys.argv[2]),json.loads(sys.argv[3]),'
                        'sys.argv[4],Path(sys.argv[5]),sys.executable,apply=True)')
            created = subprocess.run([sys.executable, '-I', '-c', old_code, str(args.old_master / 'scripts'),
                                      str(root), json.dumps(inputs), old_revision, str(args.old_tracker)],
                                     cwd=scratch, capture_output=True, text=True)
            assert created.returncode == 0, (created.stdout, created.stderr)
            base = json.loads((root / project.BASELINE).read_text())
            assert 'completion_policy' not in base['inputs']
            custom = {'docs/system/PROJECT.md': 'Project-owned original knowledge.\n',
                      'docs/runtime/DELIVERY.md': 'Actual local authorization and recovery.\n',
                      'installer.sh': 'Unique local installer.\n'}
            for name, content in custom.items():
                (root / name).write_text(content)
            modern_root = None
            if args.direct_contract:
                modern_root = scratch/('upgrade-modern-'+mode)
                shutil.copytree(root, modern_root)
                (modern_root/'installer.sh').chmod(0o750)
            before = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            retry_options = ({'ci_retry_policy': {'schema_version': 1, 'max_executions': 1 if mode=='legacy' else 2}}
                             if args.retry_contract and mode!='v1' else {})
            preview = project.upgrade(root, master_revision, args.tracker, sys.executable,
                                      completion_policy={'schema_version': 1}, **retry_options)
            assert not preview['applied'] and not preview['conflicts'], preview
            assert before == {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            applied = project.upgrade(root, master_revision, args.tracker, sys.executable, apply=True,
                                      completion_policy={'schema_version': 1}, **retry_options)
            assert applied['applied'] and not applied['conflicts'], applied
            for name, content in custom.items():
                assert (root / name).read_text() == content
            assert json.loads((root / 'tracker/config.json').read_text())['completion_policy'] == {'schema_version': 1}
            if args.retry_contract:
                assert json.loads((root/'tracker/config.json').read_bytes()).get('ci_retry_policy') == retry_options.get('ci_retry_policy')
                assert json.loads((root/'delivery.json').read_bytes())['workflow'].get('ci_retry') == retry_options.get('ci_retry_policy')
            assert project.upgrade(root, master_revision, args.tracker, sys.executable, apply=True)['changed'] == []
            result['upgrades'].append({'execution': mode, 'genuine_old_master': old_revision,
                                       'old_tracker': git(args.old_tracker, 'rev-parse', 'HEAD'),
                                       'preview_no_writes': True, 'local_knowledge_preserved': True,
                                       'ci_retry': retry_options.get('ci_retry_policy'),
                                       'idempotent': True})
            if modern_root is not None:
                explicit = dict(schema_version=3, role='research', route='batch' if mode in ('v2','v3') else 'direct',
                    completion='reviewed-merge', staging=inputs['staging'],
                    implementation_limit=choices.get('implementation_limit', 1),
                    review_limit=choices.get('review_limit', 1),
                    task_context={'schema_version': 2}, completion_policy={'schema_version': 1})
                if explicit['route'] == 'batch': explicit['batch_limit'] = choices['batch_limit']
                def snapshot():
                    return {p.relative_to(modern_root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns, p.stat().st_mode)
                            for p in modern_root.rglob('*') if p.is_file()}
                original = snapshot()
                preview = project.upgrade(modern_root, master_revision, args.tracker, sys.executable,
                                          choices=explicit, **retry_options)
                assert not preview['applied'] and not preview['conflicts'], preview
                assert snapshot() == original
                applied = project.upgrade(modern_root, master_revision, args.tracker, sys.executable,
                                          apply=True, choices=explicit, **retry_options)
                assert applied['applied'] and not applied['conflicts'], applied
                assert not [message for kind, message in project.inspect(modern_root) if kind == 'error']
                for name, content in custom.items(): assert (modern_root/name).read_text() == content
                assert (modern_root/'installer.sh').stat().st_mode & 0o777 == 0o750
                descriptor = json.loads((modern_root/'delivery.json').read_bytes())
                assert descriptor['schema_version'] == 3 and descriptor['workflow']['execution']['schema_version'] == 4
                assert descriptor['workflow']['execution']['route'] == explicit['route']
                assert 'knowledge_capture' not in descriptor['workflow']
                once = snapshot()
                assert project.upgrade(modern_root, master_revision, args.tracker, sys.executable, apply=True)['changed'] == []
                assert snapshot() == once
                result.setdefault('direct_upgrades', []).append(dict(old_execution=mode, route=explicit['route'],
                    genuine_old_master=old_revision, old_tracker=git(args.old_tracker,'rev-parse','HEAD'),
                    preview_no_writes=True, local_bytes_modes_preserved=True, optional_capture_absent=True,
                    idempotent_bytes_mtimes_modes=True))
        if args.portable_contract and not args.upgrades_only:
            assert result['matrix'] and all(row.get('portable_runtime') for row in result['matrix']), \
                'Missing engine-free runtime fixture proof; finish the portable gate before acceptance'
            from portable_contract_fixture import exercise_all
            result['native_portable_contexts'] = exercise_all(args.python39, args.tracker)
            if args.selection_delivery_contract:
                selected = result['native_portable_contexts']['selection_delivery']
                assert len(selected) == 8, 'Missing canonical selection package runtime cases'
                assert all(row['phases'] == ['pending-package', 'recorded-package', 'owned-adopted']
                           and not row['engine_imported'] and not row['consumer_writes']
                           for row in selected), 'Incomplete engine-free selection package replay'
            if args.direct_contract:
                assert len(result['native_portable_contexts']['direct']) == 8, 'Missing actual canonical direct runtime cases'
                result['direct_matrix'] = modern_outputs(args, scratch, project, master_revision)
                result['changed_route_contract'] = changed_engine_contract(args, scratch, direct=True)
            result['changed_engine_contract'] = changed_engine_contract(args, scratch)
            if args.retry_contract:
                result['changed_retry_contract'] = changed_engine_contract(args, scratch, retry=True)
    result['passed'] = True
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': True, 'exports': len(result['matrix']), 'real_upgrades': len(result['upgrades']),
                      'portable_python39': sum(x.get('isolated_python39_portable_assessment', False) for x in result['matrix'])}))


if __name__ == '__main__':
    main()
