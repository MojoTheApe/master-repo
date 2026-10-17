"""Observe retry selection/export/upgrade trust boundaries, without native reruns."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from test_project import INPUTS, OLD, NEW, REAL_RENDER, files, portable_files
import project
import standard

POLICY = {'schema_version': 1, 'max_executions': 2}


class RetrySelection(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)/'consumer'

    def read(self, name):
        return json.loads((self.root/name).read_bytes())

    def snapshot(self):
        return {p.relative_to(self.root).as_posix():p.read_bytes()
                for p in self.root.rglob('*') if p.is_file()}

    def test_unselected_upgrade_keeps_absence_and_no_retry_navigation(self):
        with mock.patch.object(project, 'render', side_effect=files):
            project.init(self.root, INPUTS, OLD, 'unused', apply=True)
            project.upgrade(self.root, NEW, 'unused', apply=True)
        self.assertNotIn('ci_retry', self.read('delivery.json')['workflow'])
        self.assertNotIn('ci_retry_policy', self.read('tracker/config.json'))
        self.assertNotIn('ci_retry', self.read(project.BASELINE)['inputs'])
        text = (self.root/'docs/repository/VERIFICATION.md').read_text()
        self.assertNotIn('## Adopted CI retry policy', text)
        self.assertNotIn('__CI_RETRY_GUIDANCE__', text)
        self.assertFalse((self.root/'docs/repository/CI_RETRY.md').exists())

    def test_explicit_upgrade_preserves_local_controls_preview_and_ancestry(self):
        with mock.patch.object(project, 'render', side_effect=files):
            project.init(self.root, INPUTS, OLD, 'unused', apply=True)
            local = {'docs/system/PROJECT.md':b'Local product.\r\n',
                     'docs/runtime/DELIVERY.md':b'Keep actual authorization.\r\n',
                     'installer.sh':b'Unique installer\n'}
            for name, content in local.items(): (self.root/name).write_bytes(content)
            descriptor = self.read('delivery.json'); descriptor['checks'] = ['actual local check']
            (self.root/'delivery.json').write_text(project.dumps(descriptor))
            before = self.snapshot()
            preview = project.upgrade(self.root, NEW, 'unused', ci_retry_policy=POLICY)
            self.assertFalse(preview['conflicts']); self.assertFalse(preview['applied'])
            self.assertEqual(before, self.snapshot())
            result = project.upgrade(self.root, NEW, 'unused', apply=True, ci_retry_policy=POLICY)
            self.assertTrue(result['applied'], result)
            self.assertEqual(self.read('delivery.json')['checks'], ['actual local check'])
            self.assertEqual(self.read('delivery.json')['workflow']['ci_retry'], POLICY)
            self.assertEqual(self.read('tracker/config.json')['ci_retry_policy'], POLICY)
            self.assertEqual(self.read(project.BASELINE)['inputs']['ci_retry'], POLICY)
            for name, content in local.items(): self.assertEqual((self.root/name).read_bytes(), content)
            self.assertIn('## Adopted CI retry policy', (self.root/'docs/repository/VERIFICATION.md').read_text())
            self.assertEqual(project.upgrade(self.root, NEW, 'unused', apply=True)['changed'], [])

    def test_mismatched_mirror_blocks_upgrade_without_writes_and_requires_guide(self):
        with mock.patch.object(project, 'render', side_effect=files):
            project.init(self.root, dict(INPUTS, ci_retry=POLICY), OLD, 'unused', apply=True)
            config = self.read('tracker/config.json'); config.pop('ci_retry_policy')
            (self.root/'tracker/config.json').write_text(project.dumps(config))
            self.assertTrue(any('CI retry policy differs' in m for k,m in project.inspect(self.root) if k=='error'))
            before = self.snapshot()
            result = project.upgrade(self.root, NEW, 'unused', apply=True)
            self.assertFalse(result['applied']); self.assertEqual(before, self.snapshot())
            config['ci_retry_policy'] = POLICY
            (self.root/'tracker/config.json').write_text(project.dumps(config))
            (self.root/'docs/repository/CI_RETRY.md').unlink()
            self.assertTrue(any('Missing docs/repository/CI_RETRY.md' in m for k,m in project.inspect(self.root) if k=='error'))

    def test_explicit_selection_cannot_be_silently_ignored_by_retained_local_policy(self):
        original_only = {'schema_version': 1, 'max_executions': 1}
        with mock.patch.object(project, 'render', side_effect=files):
            project.init(self.root, dict(INPUTS, ci_retry=POLICY), OLD, 'unused', apply=True)
            descriptor = self.read('delivery.json'); descriptor['workflow']['ci_retry'] = original_only
            config = self.read('tracker/config.json'); config['ci_retry_policy'] = original_only
            (self.root/'delivery.json').write_text(project.dumps(descriptor))
            (self.root/'tracker/config.json').write_text(project.dumps(config))
            before = self.snapshot()
            selected = project.upgrade(self.root, NEW, 'unused', apply=True, ci_retry_policy=POLICY)
            self.assertFalse(selected['applied']); self.assertIn('explicit CI retry policy selection', selected['conflicts'])
            self.assertEqual(before, self.snapshot())
            ordinary = project.upgrade(self.root, NEW, 'unused', apply=True)
            self.assertTrue(ordinary['applied'], ordinary)
            self.assertEqual(self.read('delivery.json')['workflow']['ci_retry'], original_only)
            self.assertEqual(self.read('tracker/config.json')['ci_retry_policy'], original_only)
            matched = project.upgrade(self.root, NEW, 'unused', apply=True, ci_retry_policy=original_only)
            self.assertTrue(matched['applied'], matched)
            self.assertEqual(self.read(project.BASELINE)['inputs']['ci_retry'], original_only)

    def test_invalid_selection_fails_before_export_or_consumer_write(self):
        for value in (None, {}, {'schema_version': 1, 'max_executions': 3},
                      {'schema_version': True, 'max_executions': 2}):
            with self.subTest(value=value), mock.patch.object(project.subprocess, 'run',
                    side_effect=AssertionError('Invalid policy invoked exporter')):
                with self.assertRaises(ValueError):
                    project.init(self.root, dict(INPUTS, ci_retry=value), OLD, 'unused', apply=True)
                self.assertFalse(self.root.exists())

    def test_malformed_installed_mirror_is_rejected_before_upgrade_can_replace_it(self):
        original_only = {'schema_version': 1, 'max_executions': 1}
        with mock.patch.object(project, 'render', side_effect=files):
            project.init(self.root, dict(INPUTS, ci_retry=original_only), OLD, 'unused', apply=True)
            valid = self.read('tracker/config.json')
            for field, value in (('schema_version', True), ('schema_version', 1.0),
                                 ('max_executions', True), ('max_executions', 1.0)):
                with self.subTest(field=field, value=value):
                    config = dict(valid, ci_retry_policy=dict(original_only, **{field:value}))
                    (self.root/'tracker/config.json').write_text(project.dumps(config))
                    self.assertTrue(any('CI retry policy needs' in m for k,m in project.inspect(self.root) if k=='error'))
                    before = self.snapshot()
                    for selected in (None, original_only):
                        result = project.upgrade(self.root, NEW, 'unused', apply=True, ci_retry_policy=selected)
                        self.assertFalse(result['applied']); self.assertEqual(before, self.snapshot())

    def test_duplicate_local_policy_keys_block_inspection_and_upgrade_without_writes(self):
        with mock.patch.object(project, 'render', side_effect=files):
            project.init(self.root, dict(INPUTS, ci_retry=POLICY), OLD, 'unused', apply=True)
            for name in ('tracker/config.json', 'delivery.json'):
                path = self.root/name; original = path.read_text()
                path.write_text(original.replace('"max_executions": 2', '"max_executions": 1, "max_executions": 2'))
                before = self.snapshot()
                if name == 'delivery.json':
                    with self.assertRaisesRegex(ValueError, 'Duplicate'):
                        project.inspect(self.root)
                else:
                    self.assertTrue(any('Duplicate' in m for k,m in project.inspect(self.root) if k=='error'))
                result = project.upgrade(self.root, NEW, 'unused', apply=True, ci_retry_policy=POLICY)
                self.assertFalse(result['applied']); self.assertEqual(before, self.snapshot())
                path.write_text(original)

    def test_malformed_new_mirror_cannot_pass_explicit_upgrade_postcondition(self):
        original_only = {'schema_version': 1, 'max_executions': 1}
        with mock.patch.object(project, 'render', side_effect=files):
            project.init(self.root, dict(INPUTS, ci_retry=original_only), OLD, 'unused', apply=True)
        def malformed(*args):
            rendered = files(*args)
            rendered['tracker/config.json'] = rendered['tracker/config.json'].replace('"max_executions": 1', '"max_executions": true')
            return rendered
        before = self.snapshot()
        with mock.patch.object(project, 'render', side_effect=malformed):
            result = project.upgrade(self.root, NEW, 'unused', apply=True, ci_retry_policy=original_only)
        self.assertFalse(result['applied']); self.assertIn('explicit CI retry policy selection', result['conflicts'])
        self.assertEqual(before, self.snapshot())

    def test_cli_file_selection_is_explicit_and_bad_json_never_starts_work(self):
        selected = self.root.parent/'retry.json'; selected.write_text(json.dumps(POLICY))
        init = ['init', '--root', str(self.root), '--profile', 'local', '--repository', 'owner/example',
                '--name', 'Example', '--id-prefix', 'EX', '--workspace-id', 'example', '--tracker-root', 'unused']
        upgrade = ['upgrade', '--root', str(self.root), '--tracker-root', 'unused']
        with mock.patch.object(standard, 'source_revision', return_value=OLD):
            with mock.patch.object(project, 'init', return_value={}) as create:
                self.assertEqual(standard.main(init), 0)
                self.assertNotIn('ci_retry', create.call_args.args[1])
                self.assertEqual(standard.main(init+['--ci-retry-policy',str(selected)]), 0)
                self.assertEqual(create.call_args.args[1]['ci_retry'], POLICY)
                for raw in ('null', '{"schema_version":1,"schema_version":1,"max_executions":2}'):
                    selected.write_text(raw); create.reset_mock()
                    self.assertEqual(standard.main(init+['--ci-retry-policy',str(selected)]), 2)
                    create.assert_not_called()
            selected.write_text(json.dumps(POLICY))
            with mock.patch.object(project, 'upgrade', return_value={}) as update:
                self.assertEqual(standard.main(upgrade), 0)
                self.assertIsNone(update.call_args.kwargs['ci_retry_policy'])
                self.assertEqual(standard.main(upgrade+['--ci-retry-policy',str(selected)]), 0)
                self.assertEqual(update.call_args.kwargs['ci_retry_policy'], POLICY)

    def test_real_renderer_refuses_dropped_inherited_or_missing_guide_exports(self):
        engine = self.root.parent/'engine'; engine.mkdir()
        selected = dict(INPUTS, ci_retry={'schema_version':1, 'max_executions':1})
        for failure in ('dropped', 'inherited', 'missing-guide', 'changed-limit', 'boolean', 'float', 'duplicate'):
            def exporter(command, **kwargs):
                target = Path(command[command.index('--output')+1])
                self.assertEqual('--ci-retry-policy' in command, failure!='inherited')
                config = {} if failure=='dropped' else {'ci_retry_policy': dict(selected['ci_retry'])}
                if failure=='changed-limit': config['ci_retry_policy']['max_executions'] = 2
                if failure=='boolean': config['ci_retry_policy']['max_executions'] = True
                if failure=='float': config['ci_retry_policy']['schema_version'] = 1.0
                exported = portable_files()
                exported.update({'tracker/config.json':project.dumps(config),
                    'docs/TRACKER_AGENT_WORKFLOW.md':'Exact guide\n',
                    '.github/pull_request_template.md':'Tracker issues: EX-12\n'})
                if failure=='duplicate':
                    exported['tracker/config.json'] = exported['tracker/config.json'].replace('"max_executions": 1', '"max_executions": 2, "max_executions": 1')
                if failure!='missing-guide': exported['docs/CI_RETRY.md'] = 'Exact retry guide\n'
                for name, text in exported.items():
                    path=target/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(text.encode())
                return mock.Mock(returncode=0,stdout='',stderr='')
            with self.subTest(failure=failure), mock.patch.object(project,'tracker_checkout',return_value=engine), \
                    mock.patch.object(project.subprocess,'run',side_effect=exporter):
                with self.assertRaisesRegex(ValueError,'CI retry policy differs|exact CI retry guide|CI retry policy needs|Duplicate'):
                    project.init(self.root, INPUTS if failure=='inherited' else selected, NEW, engine, apply=True)
                self.assertFalse(self.root.exists())


if __name__ == '__main__': unittest.main()
