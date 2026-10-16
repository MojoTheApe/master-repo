import copy
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import project
import standard
import test_project as fixtures
INPUTS, OLD, NEW = fixtures.INPUTS, fixtures.OLD, fixtures.NEW


class TaskContext(unittest.TestCase):
    setUp = fixtures.Projects.setUp
    create = fixtures.Projects.create
    json = fixtures.Projects.json
    put = fixtures.Projects.put
    errors = fixtures.Projects.errors
    def inputs(self, **changes):
        return dict(INPUTS, implementation_limit=2, batch_limit=2,
                    task_context={'schema_version': 1}, **changes)

    def test_context_is_explicit_and_all_profiles_share_contract(self):
        self.assertNotIn('task_context', project.descriptor(INPUTS, OLD)['workflow'])
        for profile in project.PROFILES:
            for staged in (False, True):
                values = self.inputs(); values.update(profile=profile, staging=staged)
                data = project.descriptor(values, OLD)
                self.assertEqual(data['workflow']['task_context'], {'schema_version': 1})
                self.assertEqual(data['completion'], project.PROFILES[profile])

    def test_invalid_context_or_nonbatch_execution_fails(self):
        for value in (None, {}, {'schema_version': True}, {'schema_version': 2}, {'schema_version': 1, 'skip': True}):
            values = self.inputs(); values['task_context'] = value
            with self.assertRaises(ValueError): project.descriptor(values, OLD)
        with self.assertRaises(ValueError): project.descriptor(dict(INPUTS, task_context={'schema_version': 1}), OLD)

    def test_context_upgrade_preserves_journal_knowledge_and_exact_policy(self):
        self.create(self.inputs())
        self.assertEqual(self.errors(), [])
        path = self.root/'docs/system/PROJECT.md'; path.write_text('Actual project-owned knowledge.\n')
        self.assertTrue(project.upgrade(self.root, NEW, 'unused', apply=True)['applied'])
        self.assertEqual(path.read_text(), 'Actual project-owned knowledge.\n')
        self.assertEqual(self.json('tracker/config.json')['task_context_policy'], {'schema_version': 1})
        self.assertIn('.workflow/tools/tracker_task_context.py', self.json(project.BASELINE)['files'])

    def test_missing_mirror_or_helper_fails_without_upgrade_writes(self):
        self.create(self.inputs())
        config = self.json('tracker/config.json'); config.pop('task_context_policy')
        self.put('tracker/config.json', config)
        before = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertFalse(project.upgrade(self.root, NEW, 'unused', apply=True)['applied'])
        self.assertEqual(before, {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
        config['task_context_policy'] = {'schema_version': 1}; self.put('tracker/config.json', config)
        (self.root/'.workflow/tools/tracker_task_context.py').unlink()
        self.assertTrue(any('tracker_task_context.py' in message for message in self.errors()))

    def test_cli_forwards_only_explicit_context(self):
        with mock.patch.object(project, 'init', return_value={}) as init, mock.patch.object(standard, 'source_revision', return_value=NEW):
            status = standard.main(['init', '--root', str(self.root), '--profile', 'local', '--repository', 'owner/example',
                '--name', 'Example', '--id-prefix', 'EX', '--workspace-id', 'example', '--tracker-root', 'unused',
                '--implementation-limit', '2', '--batch-limit', '2', '--task-context'])
            self.assertEqual(status, 0)
            self.assertEqual(init.call_args.args[1]['task_context'], {'schema_version': 1})

    def test_project_local_opt_in_survives_upgrade_without_changing_pristine_inputs(self):
        self.create(dict(INPUTS, implementation_limit=2, batch_limit=2))
        data = self.json('delivery.json'); data['workflow']['task_context'] = {'schema_version': 1}
        config = self.json('tracker/config.json'); config['task_context_policy'] = {'schema_version': 1}
        self.put('delivery.json', data); self.put('tracker/config.json', config)
        self.assertTrue(project.upgrade(self.root, NEW, 'unused', apply=True)['applied'])
        self.assertEqual(self.json('delivery.json')['workflow']['task_context'], {'schema_version': 1})
        self.assertNotIn('task_context', self.json(project.BASELINE)['inputs'])
