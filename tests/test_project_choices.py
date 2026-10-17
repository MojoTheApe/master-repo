"""Pure proposed descriptor3 choices; no simulated execution4 engine/export."""
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import project
import standard
from test_project import INPUTS, OLD, NEW, files as old_files


def choices(**overrides):
    value = dict(INPUTS, role='shared-tooling-library', route='direct',
                 completion='reviewed-merge', implementation_limit=1, review_limit=1,
                 task_context={'schema_version': 2}, completion_policy={'schema_version': 1})
    value.update(overrides)
    return value


def snapshot(root):
    return {p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in root.rglob('*') if p.is_file()}


class ProjectChoices(unittest.TestCase):
    def test_roles_do_not_choose_delivery_route_or_stage(self):
        for role in project.ROLES:
            for stage in (False, True):
                with self.subTest(role=role, stage=stage):
                    data = project.descriptor(choices(role=role, staging=stage), OLD)
                    self.assertEqual(data['schema_version'], 3)
                    self.assertEqual(data['role'], role)
                    self.assertEqual(data['completion'], 'reviewed-merge')
                    self.assertEqual(data['workflow']['staging'], stage)
                    self.assertEqual(data['workflow']['execution'], {
                        'schema_version': 4, 'route': 'direct',
                        'implementation_limit': 1, 'review_limit': 1})
                    self.assertEqual(set(data['environments']), {'stage'} if stage else set())
                    self.assertNotIn('approved', project.phases(stage, data['workflow']['execution']))

    def test_explicit_completion_preserves_every_profile_obligation_and_both_routes(self):
        for profile, completion in project.PROFILES.items():
            for route in ('direct', 'batch'):
                extra = {'batch_limit': 2} if route == 'batch' else {}
                with self.subTest(profile=profile, route=route):
                    data = project.descriptor(choices(profile=profile, completion=completion,
                                                     role='research', route=route, **extra), OLD)
                    self.assertEqual(data['completion'], completion)
                    self.assertEqual('production' in data['environments'], completion != 'reviewed-merge')
                    policy = project.delivery_policy(data)
                    self.assertEqual(policy['completion'], completion)
                    self.assertEqual('approved' in project.phases(True, data['workflow']['execution']),
                                     route == 'batch')

    def test_simple_and_application_presets_fill_omissions_without_role_inference(self):
        for preset, expected in (('simple', ('direct', False, 1, 1)),
                                 ('application', ('batch', True, 2, 1))):
            with self.subTest(preset=preset):
                original = dict(INPUTS, preset=preset, role='knowledge', completion='reviewed-merge')
                original.pop('staging')
                before = copy.deepcopy(original)
                selected = project.project_choices(original)
                self.assertEqual((selected['route'], selected['staging'], selected['implementation_limit'],
                                  selected['review_limit']), expected)
                self.assertEqual(selected['role'], 'knowledge')
                self.assertEqual(selected['task_context'], {'schema_version': 2})
                self.assertEqual(selected['completion_policy'], {'schema_version': 1})
                self.assertEqual(original, before)
                selected['task_context']['schema_version'] = 99
                self.assertEqual(project.project_choices(original)['task_context'], {'schema_version': 2})

    def test_explicit_choices_override_presets_and_do_not_carry_a_batch_limit_into_direct(self):
        selected = project.project_choices(dict(INPUTS, preset='application', role='application',
            completion='reviewed-merge', route='direct', staging=False,
            implementation_limit=3, review_limit=2))
        self.assertNotIn('batch_limit', selected)
        self.assertEqual((selected['route'], selected['staging'], selected['implementation_limit'],
                          selected['review_limit']), ('direct', False, 3, 2))
        with self.assertRaisesRegex(ValueError, 'must not select batch_limit'):
            project.project_choices(dict(selected, batch_limit=2))

    def test_missing_choices_or_unknown_input_cannot_silently_select_a_default(self):
        for key in ('role', 'completion', 'route', 'staging', 'implementation_limit',
                    'review_limit', 'task_context', 'completion_policy'):
            value = choices(); value.pop(key)
            with self.subTest(missing=key), self.assertRaisesRegex(ValueError, 'explicit choices'):
                project.descriptor(value, OLD)
        for key in ('roel', 'integration', 'knowledge_capture', 'unknown'):
            with self.subTest(unknown=key), self.assertRaisesRegex(ValueError, 'Unknown'):
                project.descriptor(choices(**{key: 'unselected'}), OLD)
        with self.assertRaisesRegex(ValueError, 'explicit choices'):
            project.project_choices(dict(INPUTS, preset='simple'))

    def test_types_ranges_guards_and_unsafe_completion_combinations_are_rejected(self):
        invalid = [('role', None), ('role', 'invented'), ('profile', []),
                   ('completion', None), ('route', 'automatic'), ('route', True),
                   ('staging', 0), ('staging', 'false'), ('schema_version', True),
                   ('schema_version', 3.0), ('schema_version', 7),
                   ('preset', None), ('preset', []), ('preset', 'universal')]
        for key, maximum in (('implementation_limit', 16), ('review_limit', 5)):
            invalid.extend((key, value) for value in (True, 1.0, '1', None, 0, maximum + 1))
        invalid += [('task_context', {'schema_version': 1}),
                    ('task_context', {'schema_version': 2.0}),
                    ('task_context', {'schema_version': 2, 'extra': 1}),
                    ('completion_policy', {'schema_version': True}),
                    ('completion_policy', {'schema_version': 1, 'extra': 1})]
        for key, value in invalid:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                project.descriptor(choices(**{key: value}), OLD)
        for profile in ('vps', 'n8n', 'package'):
            with self.subTest(profile=profile), self.assertRaisesRegex(ValueError, 'delivery obligation'):
                project.descriptor(choices(profile=profile, completion='reviewed-merge'), OLD)
        for limit in (None, True, 2.0, 0, 6):
            with self.subTest(batch_limit=limit), self.assertRaisesRegex(ValueError, 'batch_limit'):
                project.descriptor(choices(route='batch', batch_limit=limit), OLD)

    def test_identity_inputs_are_rejected_without_type_coercion_or_crashes(self):
        for key, value in (('name', None), ('name', False), ('repository', []),
                           ('repository', 'https://github.com/owner/example'),
                           ('prefix', True), ('prefix', 'ex'), ('workspace_id', {})):
            for original in (INPUTS, choices()):
                with self.subTest(key=key, value=value, modern='role' in original), \
                        self.assertRaises(ValueError):
                    project.descriptor(dict(original, **{key: value}), OLD)

    def test_old_input_schemas_and_choices_are_unchanged_and_never_pick_a_preset(self):
        old_modes = ({}, {'implementation_limit': 3},
                     {'implementation_limit': 4, 'batch_limit': 3},
                     {'implementation_limit': 5, 'batch_limit': 4, 'review_limit': 3})
        for version, extra in enumerate(old_modes):
            original = dict(INPUTS, **extra)
            before = copy.deepcopy(original)
            data = project.descriptor(original, OLD)
            self.assertEqual(data['schema_version'], 2)
            self.assertNotIn('role', data)
            self.assertEqual(data['completion'], 'reviewed-merge')
            self.assertTrue(data['workflow']['staging'])
            self.assertNotIn('task_context', data['workflow'])
            self.assertNotIn('completion_policy', data['workflow'])
            self.assertEqual(data['workflow'].get('execution', {}).get('schema_version'), version or None)
            self.assertEqual(original, before)
        with self.assertRaisesRegex(ValueError, 'descriptor schema3'):
            project.descriptor(choices(schema_version=2), OLD)

    def test_pure_construction_is_not_canonical_execution4_support(self):
        data = project.descriptor(choices(), OLD)
        with self.assertRaisesRegex(ValueError, 'must be 1, 2 or 3'):
            project.validate_execution_policy(data['workflow']['execution'])
        for apply in (False, True):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory) / 'consumer'
                with mock.patch.object(project, 'tracker_checkout') as checkout, \
                        mock.patch.object(project.subprocess, 'run') as exporter:
                    with self.assertRaisesRegex(ValueError, 'released canonical route companion'):
                        project.init(root, choices(), OLD, 'not-an-engine', apply=apply)
                    checkout.assert_not_called(); exporter.assert_not_called()
                self.assertFalse(root.exists())

    def test_actual_inspection_and_upgrade_refuse_modern_selection_without_any_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'consumer'
            # Reuse only the incumbent schema2 fixture; never create a fake4 export.
            with mock.patch.object(project, 'render', side_effect=old_files):
                project.init(root, INPUTS, OLD, 'unused', apply=True)
            (root / 'delivery.json').write_text(project.dumps(project.descriptor(choices(), OLD)))
            before = snapshot(root)
            self.assertTrue(any('released canonical route companion' in message
                                for kind, message in standard.inspect(root) if kind == 'error'))
            for apply in (False, True):
                with mock.patch.object(project, 'render') as render:
                    result = project.upgrade(root, NEW, 'not-an-engine', apply=apply)
                    render.assert_not_called()
                self.assertFalse(result['applied'])
                self.assertEqual(result['conflicts'], ['configuration validation'])
                self.assertEqual(snapshot(root), before)


class ChoicesCLI(unittest.TestCase):
    def arguments(self, root):
        return ['init', '--root', str(root), '--profile', 'tooling', '--repository', 'owner/example',
                '--name', 'Example', '--id-prefix', 'EX', '--workspace-id', 'example',
                '--tracker-root', 'not-an-engine']

    def test_cli_passes_explicit_preset_choices_without_the_old_five_slot_defaults(self):
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(standard, 'source_revision', return_value=OLD), \
                mock.patch.object(project, 'init', return_value={}) as initialize, \
                contextlib.redirect_stdout(io.StringIO()):
            args = self.arguments(Path(directory) / 'consumer')
            self.assertEqual(standard.main(args + ['--preset', 'simple', '--role', 'research',
                                                  '--completion', 'reviewed-merge']), 0)
            selected = initialize.call_args.args[1]
            self.assertFalse(selected['staging']); self.assertEqual(selected['implementation_limit'], 1)
            self.assertNotIn('batch_limit', selected)
            self.assertEqual(selected['task_context'], {'schema_version': 2})
            self.assertEqual(standard.main(args + ['--preset', 'simple', '--role', 'research',
                '--completion', 'reviewed-merge', '--staging', '--implementation-limit', '3']), 0)
            self.assertTrue(initialize.call_args.args[1]['staging'])
            self.assertEqual(initialize.call_args.args[1]['implementation_limit'], 3)

    def test_explicit_cli_route_requires_its_choices_and_keeps_context2_without_batch_defaults(self):
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(standard, 'source_revision', return_value=OLD), \
                mock.patch.object(project, 'init', return_value={}) as initialize, \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            args = self.arguments(Path(directory) / 'consumer') + [
                '--role', 'application', '--route', 'direct', '--completion', 'reviewed-merge',
                '--implementation-limit', '4', '--review-limit', '2',
                '--task-context', '--completion-policy']
            self.assertEqual(standard.main(args), 2)
            initialize.assert_not_called()
            self.assertEqual(standard.main(args + ['--no-staging']), 0)
            selected = initialize.call_args.args[1]
            self.assertEqual(selected['task_context'], {'schema_version': 2})
            self.assertEqual(selected['completion_policy'], {'schema_version': 1})
            self.assertEqual((selected['implementation_limit'], selected['review_limit']), (4, 2))
            self.assertNotIn('batch_limit', selected)

    def test_actual_cli_preview_and_apply_fail_before_export_or_target_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'consumer'
            args = self.arguments(root) + ['--preset', 'simple', '--role', 'research',
                                          '--completion', 'reviewed-merge']
            for suffix in ([], ['--apply'], ['--legacy-execution']):
                with mock.patch.object(standard, 'source_revision', return_value=OLD), \
                        mock.patch.object(project, 'tracker_checkout') as checkout, \
                        contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(standard.main(args + suffix), 2)
                    checkout.assert_not_called()
                self.assertFalse(root.exists())

    def test_duplicate_descriptor_choices_are_not_collapsed_before_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = project.dumps(project.descriptor(choices(), OLD))
            data = data.replace('"role": "shared-tooling-library"',
                                '"role": "research", "role": "shared-tooling-library"')
            (root / 'delivery.json').write_text(data)
            before = snapshot(root)
            with self.assertRaisesRegex(ValueError, 'Duplicate'):
                standard.inspect(root)
            self.assertEqual(snapshot(root), before)


if __name__ == '__main__':
    unittest.main()
