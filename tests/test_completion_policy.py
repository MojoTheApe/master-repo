"""Consumer completion opt-in, conservative upgrades and exact export checks."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from test_project import INPUTS, OLD, NEW, REAL_RENDER, files
import project
import standard


class CompletionPolicy(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / 'consumer'
        patch = mock.patch.object(project, 'render', side_effect=files)
        patch.start()
        self.addCleanup(patch.stop)

    def read(self, name):
        return json.loads((self.root / name).read_text())

    def put(self, name, value):
        (self.root / name).write_text(project.dumps(value))

    def create(self, **inputs):
        project.init(self.root, dict(INPUTS, **inputs), OLD, 'unused', apply=True)

    def errors(self):
        return [message for kind, message in project.inspect(self.root) if kind == 'error']

    def test_opt_in_preserves_profile_target_stage_and_execution_choices(self):
        for profile in project.PROFILES:
            for staging in (False, True):
                with self.subTest(profile=profile, staging=staging):
                    initial = dict(INPUTS, profile=profile, staging=staging)
                    old = project.descriptor(initial, OLD)
                    selected = project.descriptor(dict(initial, completion_policy={'schema_version': 1}), OLD)
                    self.assertNotIn('completion_policy', old['workflow'])
                    self.assertEqual(selected['workflow']['completion_policy'], {'schema_version': 1})
                    self.assertEqual(selected['completion'], old['completion'])
                    self.assertEqual(selected['environments'], old['environments'])
                    self.assertEqual(project.delivery_policy(selected), project.delivery_policy(old))
                    self.assertNotIn('execution', selected['workflow'])
        for value in (None, [], {}, {'schema_version': True}, {'schema_version': 2},
                      {'schema_version': 1, 'unknown': True}):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'Completion policy'):
                project.descriptor(dict(INPUTS, completion_policy=value), OLD)

    def test_cli_selection_is_explicit_for_init_and_upgrade(self):
        args = ['init', '--root', str(self.root), '--profile', 'local', '--repository', 'owner/example',
                '--name', 'Example', '--id-prefix', 'EX', '--workspace-id', 'example', '--tracker-root', 'unused']
        with mock.patch.object(standard, 'source_revision', return_value=OLD):
            with mock.patch.object(project, 'init', return_value={}) as initialize:
                self.assertEqual(standard.main(args), 0)
                self.assertNotIn('completion_policy', initialize.call_args.args[1])
                self.assertEqual(standard.main(args + ['--completion-policy']), 0)
                self.assertEqual(initialize.call_args.args[1]['completion_policy'], {'schema_version': 1})
            with mock.patch.object(project, 'upgrade', return_value={}) as upgrade:
                args = ['upgrade', '--root', str(self.root), '--tracker-root', 'unused']
                self.assertEqual(standard.main(args), 0)
                self.assertIsNone(upgrade.call_args.kwargs['completion_policy'])
                self.assertEqual(standard.main(args + ['--completion-policy']), 0)
                self.assertEqual(upgrade.call_args.kwargs['completion_policy'], {'schema_version': 1})

    def test_unselected_upgrade_does_not_enable_or_install_completion_contract(self):
        self.create()
        self.assertTrue(project.upgrade(self.root, NEW, 'unused', apply=True)['applied'])
        self.assertNotIn('completion_policy', self.read('delivery.json')['workflow'])
        self.assertNotIn('completion_policy', self.read('tracker/config.json'))
        self.assertNotIn('completion_policy', self.read(project.BASELINE)['inputs'])
        self.assertFalse((self.root / 'docs/repository/COMPLETION_POLICY.md').exists())

    def test_explicit_three_way_upgrade_preserves_local_controls_and_real_old_base(self):
        self.create()
        before_base = self.read(project.BASELINE)
        self.assertNotIn('completion_policy', before_base['inputs'])
        custom = {'docs/system/PROJECT.md': 'Local product truth.\n',
                  'docs/runtime/DELIVERY.md': 'Actual target acceptance and authorization.\n',
                  'installer.sh': 'Unique installer.\n'}
        for name, content in custom.items():
            (self.root / name).write_text(content)
        descriptor = self.read('delivery.json')
        descriptor['checks'] = ['python -m unittest product_checks']
        self.put('delivery.json', descriptor)
        before = {p.relative_to(self.root).as_posix(): p.read_bytes()
                  for p in self.root.rglob('*') if p.is_file()}
        preview = project.upgrade(self.root, NEW, 'unused', completion_policy={'schema_version': 1})
        self.assertFalse(preview['applied'])
        self.assertFalse(preview['conflicts'])
        self.assertEqual(before, {p.relative_to(self.root).as_posix(): p.read_bytes()
                                  for p in self.root.rglob('*') if p.is_file()})
        result = project.upgrade(self.root, NEW, 'unused', apply=True, completion_policy={'schema_version': 1})
        self.assertTrue(result['applied'], result)
        self.assertEqual(self.errors(), [])
        self.assertEqual(self.read('tracker/config.json')['completion_policy'], {'schema_version': 1})
        self.assertEqual(self.read('delivery.json')['checks'], descriptor['checks'])
        self.assertEqual(self.read('delivery.json')['completion'], descriptor['completion'])
        self.assertEqual(self.read(project.BASELINE)['inputs']['completion_policy'], {'schema_version': 1})
        for name, content in custom.items():
            self.assertEqual((self.root / name).read_text(), content)
        self.assertEqual(project.upgrade(self.root, NEW, 'unused', apply=True)['changed'], [])

    def test_mismatch_or_missing_exact_guide_blocks_validation_and_upgrade_without_writes(self):
        self.create(completion_policy={'schema_version': 1})
        config = self.read('tracker/config.json')
        config.pop('completion_policy')
        self.put('tracker/config.json', config)
        self.assertTrue(any('completion policy differs' in error for error in self.errors()))
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result = project.upgrade(self.root, NEW, 'unused', apply=True)
        self.assertFalse(result['applied'])
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
        config['completion_policy'] = {'schema_version': 1}
        self.put('tracker/config.json', config)
        (self.root / 'docs/repository/COMPLETION_POLICY.md').unlink()
        self.assertTrue(any('Missing docs/repository/COMPLETION_POLICY.md' in error for error in self.errors()))

    def test_separator_preserves_exact_completion_guide_and_rewrites_only_navigation(self):
        exported = {'docs/TRACKER_AGENT_WORKFLOW.md': 'Read `docs/COMPLETION_POLICY.md`.\n',
                    'docs/COMPLETION_POLICY.md': '# Frozen accepted scope\n\nOriginal engine-owned commands.\n',
                    'scripts/task_tracker.py': 'root = Path(__file__).resolve().parents[1]\n',
                    'scripts/tracker_pr_check.py': 'root = Path(__file__).resolve().parents[1]\n',
                    'scripts/tracker_delivery_policy.py': '# unchanged portable assessment\n'}
        exact = exported['docs/COMPLETION_POLICY.md']
        project.separate_export(exported)
        self.assertEqual(exported['docs/repository/COMPLETION_POLICY.md'], exact)
        self.assertIn('docs/repository/COMPLETION_POLICY.md', exported['docs/repository/TRACKER.md'])
        self.assertIn('(repository/COMPLETION_POLICY.md)', exported['docs/COMPLETION_POLICY.md'])
        self.assertEqual(exported['.workflow/tools/tracker_delivery_policy.py'], '# unchanged portable assessment\n')

    def test_missing_transitive_portable_helper_blocks_upgrade_without_writes(self):
        self.create(completion_policy={'schema_version': 1})
        for name in ('scripts/tracker_task_context.py', '.workflow/tools/tracker_task_context.py'):
            (self.root / name).unlink()
        self.assertTrue(any('tracker_task_context.py' in error for error in self.errors()))
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result = project.upgrade(self.root, NEW, 'unused', apply=True)
        self.assertFalse(result['applied'])
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_renderer_rejects_inherited_dropped_and_incomplete_engine_exports(self):
        engine = self.root.parent / 'engine'
        (engine / 'tracker').mkdir(parents=True)
        observed = []

        def exporter(command, **_kwargs):
            target = Path(command[command.index('--output') + 1])
            (target / 'tracker').mkdir(parents=True)
            selected = (json.loads(Path(command[command.index('--completion-policy') + 1]).read_text())
                        if '--completion-policy' in command else None)
            observed.append(selected)
            config = {'completion_policy': selected} if selected is not None else {}
            (target / 'tracker/config.json').write_text(project.dumps(config))
            (target / 'docs').mkdir()
            (target / 'docs/TRACKER_AGENT_WORKFLOW.md').write_text('Pinned guide\n')
            if selected:
                (target / 'docs/COMPLETION_POLICY.md').write_text('Exact guide\n')
            (target / 'scripts').mkdir()
            for name in set(project.HELPERS + project.COMPLETION_HELPERS):
                (target / 'scripts' / name).write_text('root = Path(__file__).resolve().parents[1]\n')
            return mock.Mock(returncode=0, stdout='', stderr='')

        with mock.patch.object(project, 'tracker_checkout', return_value=engine):
            with mock.patch.object(project.subprocess, 'run', side_effect=exporter):
                REAL_RENDER(INPUTS, NEW, engine)
                result = REAL_RENDER(dict(INPUTS, completion_policy={'schema_version': 1}), NEW, engine)
                self.assertEqual(observed, [None, {'schema_version': 1}])
                self.assertIn('docs/repository/COMPLETION_POLICY.md', result)
            for failure in ('inherited', 'dropped', 'missing-guide', 'missing-transitive-helper'):
                def bad_export(command, **kwargs):
                    result = exporter(command, **kwargs)
                    target = Path(command[command.index('--output') + 1])
                    config = {} if failure == 'dropped' else {'completion_policy': {'schema_version': 1}}
                    (target / 'tracker/config.json').write_text(project.dumps(config))
                    if failure == 'missing-guide':
                        (target / 'docs/COMPLETION_POLICY.md').unlink()
                    elif failure == 'missing-transitive-helper':
                        (target / 'scripts/tracker_task_context.py').unlink()
                    return result
                inputs = INPUTS if failure == 'inherited' else dict(INPUTS, completion_policy={'schema_version': 1})
                with self.subTest(failure=failure), mock.patch.object(project.subprocess, 'run', side_effect=bad_export):
                    with self.assertRaisesRegex(ValueError, 'completion policy differs|exact guide'):
                        REAL_RENDER(inputs, NEW, engine)
