import copy
import sys
from pathlib import Path
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import project
import standard
import test_project as fixtures


def policy():
    return {'schema_version': 1, 'profiles': {'checks': {
        'workflow_path': '.github/workflows/product.yml', 'workflow_blob_sha': 'a'*40,
        'producer_files': {'.workflow/tools/tracker_ci_evidence.py': 'b'*40},
        'metadata_mode': 'commit', 'max_age_seconds': 3600,
        'jobs': {'Product checks': {'mode': 'fresh'}}}}}


class EvidencePolicy(unittest.TestCase):
    setUp = fixtures.Projects.setUp
    create = fixtures.Projects.create
    json = fixtures.Projects.json
    put = fixtures.Projects.put
    errors = fixtures.Projects.errors

    def test_all_profiles_preserve_explicit_policy_and_optional_stage(self):
        self.assertNotIn('ci_evidence', project.descriptor(fixtures.INPUTS, fixtures.OLD)['workflow'])
        for profile in project.PROFILES:
            for staging in (False, True):
                data = project.descriptor(dict(fixtures.INPUTS, profile=profile, staging=staging, ci_evidence=policy()), fixtures.OLD)
                self.assertEqual(data['workflow']['ci_evidence'], policy())
                self.assertEqual(data['completion'], project.PROFILES[profile])
        value = policy(); value['schema_version'] = 2
        self.assertEqual(project.descriptor(dict(fixtures.INPUTS, ci_evidence=value), fixtures.OLD)['workflow']['ci_evidence'], value)

    def test_unsafe_policy_rejected_before_files_written(self):
        values = [None, {}, {'schema_version': True, 'profiles': {}}, policy()]
        values[-1]['profiles']['checks']['metadata_mode'] = 'anything'
        for value in values:
            with self.assertRaises(ValueError): self.create(dict(fixtures.INPUTS, ci_evidence=value))
        self.assertFalse(self.root.exists())

    def test_mirror_drift_aborts_upgrade_without_writes(self):
        self.create(dict(fixtures.INPUTS, ci_evidence=policy()))
        config = self.json('tracker/config.json'); config.pop('ci_evidence_policy')
        self.put('tracker/config.json', config)
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertFalse(project.upgrade(self.root, fixtures.NEW, 'unused', apply=True)['applied'])
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_local_adoption_survives_without_rewriting_pristine_inputs(self):
        self.create()
        data = self.json('delivery.json'); data['workflow']['ci_evidence'] = policy()
        config = self.json('tracker/config.json'); config['ci_evidence_policy'] = policy()
        self.put('delivery.json', data); self.put('tracker/config.json', config)
        (self.root/'docs/system/PROJECT.md').write_text('Actual project knowledge.\n')
        self.assertTrue(project.upgrade(self.root, fixtures.NEW, 'unused', apply=True)['applied'])
        self.assertEqual(self.json('delivery.json')['workflow']['ci_evidence'], policy())
        self.assertNotIn('ci_evidence', self.json(project.BASELINE)['inputs'])
        self.assertEqual((self.root/'docs/system/PROJECT.md').read_text(), 'Actual project knowledge.\n')
        (self.root/'.workflow/tools/tracker_ci_evidence.py').unlink()
        self.assertTrue(any('tracker_ci_evidence.py' in x for x in self.errors()))

    def test_cli_requires_a_real_explicit_policy_document(self):
        path = self.root.parent/'policy.json'; path.write_text(project.dumps(policy()))
        with mock.patch.object(project, 'init', return_value={}) as init, mock.patch.object(standard, 'source_revision', return_value=fixtures.NEW):
            status = standard.main(['init', '--root', str(self.root), '--profile', 'local', '--repository', 'owner/example',
                '--name', 'Example', '--id-prefix', 'EX', '--workspace-id', 'example', '--tracker-root', 'unused',
                '--ci-evidence-policy', str(path)])
            self.assertEqual(status, 0)
            self.assertEqual(init.call_args.args[1]['ci_evidence'], policy())
