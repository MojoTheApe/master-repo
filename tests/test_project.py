import copy
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import project
import standard
import onboard
REAL_RENDER = project.render

OLD='a'*40
NEW='b'*40
INPUTS={'name':'Example','repository':'owner/example','prefix':'EX','workspace_id':'example','profile':'local','staging':True}


class OptionalProducerExport(unittest.TestCase):
    def exported(self):
        return {'docs/TRACKER_AGENT_WORKFLOW.md': 'Read the pinned guide.\n',
                'scripts/task_tracker.py': 'root = Path(__file__).resolve().parents[1]\n',
                'scripts/tracker_pr_check.py': 'root = Path(__file__).resolve().parents[1]\n',
                'scripts/tracker_delivery_policy.py': '# existing policy\n'}

    def test_separated_producer_retains_exact_code_and_root_relative_configuration(self):
        producer = ('from pathlib import Path\n'
                    'import json\n'
                    'if __name__ == "__main__":\n'
                    '    print(json.loads(Path("tracker/config.json").read_text())["project"]["repository"])\n')
        exported = self.exported()
        exported['scripts/tracker_ci_evidence.py'] = producer
        project.separate_export(exported)
        self.assertEqual(exported['.workflow/tools/tracker_ci_evidence.py'], producer)
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            for name, content in exported.items():
                path = root/name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            (root/'tracker').mkdir()
            (root/'tracker/config.json').write_text('{"project":{"repository":"owner/example"}}')
            for name in ('scripts/tracker_ci_evidence.py', '.workflow/tools/tracker_ci_evidence.py'):
                result = subprocess.run([sys.executable, name], cwd=root, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), 'owner/example')

    def test_older_export_does_not_invent_ci_producer_or_opt_in(self):
        exported = self.exported()
        project.separate_export(exported)
        self.assertFalse(any('ci_evidence' in path for path in exported))

    def test_receipt_recorder_keeps_bytes_portable_import_and_both_entry_points(self):
        producer = ('try:\n    from . import delivery_policy as rules\n'
                    'except ImportError:\n    import tracker_delivery_policy as rules\n'
                    'def github(path):\n    return "github:" + path\n'
                    'def verification_job(*args):\n    return (rules.VALUE, 2)\n'
                    'if __name__ == "__main__":\n    print(rules.VALUE)\n')
        exported = self.exported()
        exported['scripts/tracker_delivery_policy.py'] = 'VALUE = 42\n'
        exported['scripts/tracker_delivery_receipt.py'] = producer
        project.separate_export(exported)
        self.assertEqual(exported['.workflow/tools/tracker_delivery_receipt.py'], producer)
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            for name, content in exported.items():
                path = root/name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(content)
            for name in ('scripts/tracker_delivery_receipt.py', '.workflow/tools/tracker_delivery_receipt.py'):
                result = subprocess.run([sys.executable, name], cwd=root, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), '42')
            imported = subprocess.run([sys.executable, '-c',
                'from scripts.tracker_delivery_receipt import github, verification_job; '
                'assert github("synthetic") == "github:synthetic"; '
                'assert verification_job() == (42, 2)'], cwd=root, capture_output=True, text=True)
            self.assertEqual(imported.returncode, 0, imported.stderr)

    def test_older_export_does_not_require_or_invent_receipt_recorder(self):
        exported = self.exported()
        project.separate_export(exported)
        self.assertFalse(any('delivery_receipt' in path for path in exported))


def files(inputs=INPUTS, revision=OLD, *_args):
    """Minimal exported contract; real pinned exporter is exercised separately."""
    data=project.descriptor(inputs,revision)
    config={'schema_version':3,'project':{'name':inputs['name'],'repository':inputs['repository'],'id_prefix':inputs['prefix'],'base_branch':'main'},
            'workflow':project.phases(inputs['staging'], data['workflow'].get('execution')), 'delivery_policy':project.delivery_policy(data),
            'modules':[{'id':'product','name':'Product','description':'Product functionality'}]}
    if 'execution' in data['workflow']: config['execution_policy']=data['workflow']['execution']
    if 'process_instructions' in data['workflow']:
        config['process_instructions']=data['workflow']['process_instructions']
    out={'delivery.json':project.dumps(data),'tracker/config.json':project.dumps(config),
         'tracker/engine.json':project.dumps({'repository':data['tracker']['repository'],'revision':data['tracker']['revision']}),
         'docs/TRACKER_AGENT_WORKFLOW.md':'Read the pinned guide.\n', 'scripts/task_tracker.py':'root = Path(__file__).resolve().parents[1]\n',
         'scripts/tracker_pr_check.py':'root = Path(__file__).resolve().parents[1]\n','scripts/tracker_delivery_policy.py':'# policy check\n'}
    out['scripts/tracker_process_instructions.py'] = '# instruction route check\n'
    if data['workflow'].get('execution', {}).get('schema_version') in (2, 3):
        out['scripts/tracker_batch_policy.py'] = '# batch policy check\n'
        if data['completion'] != 'reviewed-merge':
            out['scripts/tracker_delivery_receipt.py'] = '# portable receipt recorder\n'
    project.separate_export(out)
    out.update(project.layout_files())
    for source,destination in project.FILES.items():
        out[destination]=(project.SOURCE/'templates/workflow'/source).read_text().replace('__STANDARD_REVISION__',revision)
    return out


class Projects(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'project'
        patch=mock.patch.object(project,'render',side_effect=files);patch.start();self.addCleanup(patch.stop)
    def create(self,inputs=INPUTS):
        project.init(self.root,inputs,OLD,'unused',apply=True)
    def json(self,name):return json.loads((self.root/name).read_text())
    def put(self,name,value):(self.root/name).write_text(project.dumps(value))
    def errors(self):return [m for kind,m in standard.inspect(self.root) if kind=='error']
    def test_preview_does_not_write_and_init_cannot_overwrite(self):
        result=project.init(self.root,INPUTS,OLD,'unused')
        self.assertFalse(result['applied']);self.assertFalse(self.root.exists())
        self.create();before=(self.root/'AGENTS.md').read_text()
        with self.assertRaisesRegex(ValueError,'Existing files'):self.create()
        self.assertEqual(before,(self.root/'AGENTS.md').read_text())
    def test_default_stage_and_local_completion_with_ready_validation(self):
        self.create();self.assertEqual(self.errors(),[])
        data=self.json('delivery.json');self.assertTrue(data['workflow']['staging']);self.assertEqual(data['completion'],'reviewed-merge')
        self.assertTrue(any(k=='setup' for k,_ in standard.inspect(self.root)))
        def fill(value):
            if isinstance(value,dict):return {k:fill(v) for k,v in value.items()}
            if isinstance(value,list):return [fill(v) for v in value]
            return 'Verified test procedure' if isinstance(value,str) and value.startswith('__') else value
        data=fill(data);data['adoption']='ready';data['tracker']['registration']='verified';self.put('delivery.json',data)
        config=self.json('tracker/config.json');config['delivery_policy']=project.delivery_policy(data);self.put('tracker/config.json',config)
        self.assertEqual(standard.inspect(self.root),[])
    def test_stage_disabled_has_no_column_or_stage_environment(self):
        self.create(dict(INPUTS,staging=False));self.assertEqual(self.errors(),[])
        self.assertNotIn('stage',self.json('tracker/config.json')['workflow'])
        self.assertEqual(self.json('delivery.json')['environments'],{})
    def test_execution_is_explicit_and_capacity_is_configurable(self):
        self.create()
        self.assertNotIn('execution',self.json('delivery.json')['workflow'])
        self.assertNotIn('execution_policy',self.json('tracker/config.json'))
        for limit in (1,2,4,16):
            with self.subTest(limit=limit):
                data=project.descriptor(dict(INPUTS,implementation_limit=limit),OLD)
                self.assertEqual(data['workflow']['execution'],
                                 {'schema_version':1,'implementation_limit':limit,'review_limit':1})
        for limit in (0,17,True,2.0,'2',None):
            with self.subTest(limit=limit),self.assertRaises(ValueError):
                project.descriptor(dict(INPUTS,implementation_limit=limit),OLD)
    def test_execution_policy_validation_rejects_malformed_or_drifted_values(self):
        self.create(dict(INPUTS,implementation_limit=2))
        self.assertEqual(self.errors(),[])
        original=self.json('delivery.json');config=self.json('tracker/config.json')
        policy=original['workflow']['execution']
        invalid=[None,[],{},dict(policy,schema_version=True),dict(policy,schema_version=2),
                 dict(policy,implementation_limit=False),dict(policy,implementation_limit=17),
                 dict(policy,review_limit=2),dict(policy,review_limit=True),dict(policy,unknown=1)]
        for value in invalid:
            with self.subTest(value=value):
                data=copy.deepcopy(original);data['workflow']['execution']=value
                self.put('delivery.json',data)
                self.assertTrue(self.errors())
        self.put('delivery.json',original)
        config['execution_policy']['implementation_limit']=3;self.put('tracker/config.json',config)
        self.assertTrue(any('execution policy differs' in e for e in self.errors()))
        config.pop('execution_policy');self.put('tracker/config.json',config)
        self.assertTrue(any('execution policy differs' in e for e in self.errors()))
        original['workflow'].pop('execution');self.put('delivery.json',original)
        config['execution_policy']=None;self.put('tracker/config.json',config)
        self.assertTrue(self.errors())
        config['execution_policy']=policy;self.put('tracker/config.json',config)
        self.assertTrue(any('execution policy differs' in e for e in self.errors()))
    def test_batch_opt_in_adds_approved_and_preserves_local_limit_on_upgrade(self):
        self.create(dict(INPUTS, implementation_limit=5, batch_limit=5))
        self.assertEqual(self.errors(), [])
        config = self.json('tracker/config.json')
        self.assertEqual(config['workflow'], project.phases(True, config['execution_policy']))
        self.assertEqual(config['execution_policy'], {'schema_version':2, 'implementation_limit':5, 'review_limit':1, 'batch_limit':5})
        data = self.json('delivery.json')
        data['workflow']['execution']['batch_limit'] = 3
        config['execution_policy']['batch_limit'] = 3
        self.put('delivery.json', data); self.put('tracker/config.json', config)
        self.assertTrue(project.upgrade(self.root, NEW, 'unused', apply=True)['applied'])
        self.assertEqual(self.json('delivery.json')['workflow']['execution']['batch_limit'], 3)
        self.assertEqual(self.json('tracker/config.json')['execution_policy']['batch_limit'], 3)
        self.assertEqual(json.loads(self.json(project.BASELINE)['files']['tracker/config.json'])['execution_policy']['batch_limit'], 5)
    def test_batch_opt_in_requires_capacity_and_valid_limit(self):
        for inputs in (dict(INPUTS,batch_limit=5),):
            with self.subTest(inputs=inputs), self.assertRaises(ValueError): project.descriptor(inputs, OLD)
        for limit in (0,17,True,None,5.0,'5'):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                project.descriptor(dict(INPUTS,implementation_limit=5,batch_limit=limit), OLD)
    def test_parallel_review_opt_in_and_mirrored_bounds(self):
        for limit in range(1, 6):
            with self.subTest(limit=limit):
                data = project.descriptor(dict(INPUTS, implementation_limit=5, batch_limit=5, review_limit=limit), OLD)
                self.assertEqual(data['workflow']['execution'],
                    {'schema_version':3, 'implementation_limit':5, 'review_limit':limit, 'batch_limit':5})
                self.assertIn('approved', project.phases(True, data['workflow']['execution']))
        self.create(dict(INPUTS, implementation_limit=5, batch_limit=5, review_limit=5))
        self.assertEqual(self.errors(), [])
        original = self.json('delivery.json')
        policy = original['workflow']['execution']
        for value in (dict(policy, review_limit=0), dict(policy, review_limit=6),
                      dict(policy, review_limit=True), dict(policy, review_limit=5.0),
                      dict(policy, batch_limit=6), dict(policy, batch_limit=True)):
            with self.subTest(value=value):
                data = copy.deepcopy(original); data['workflow']['execution'] = value
                self.put('delivery.json', data); self.assertTrue(self.errors())
        self.put('delivery.json', original)
        config = self.json('tracker/config.json'); config['execution_policy']['review_limit'] = 4
        self.put('tracker/config.json', config)
        self.assertTrue(any('execution policy differs' in e for e in self.errors()))
    def test_parallel_review_selection_requires_explicit_batch_and_capacity(self):
        for inputs in (dict(INPUTS, review_limit=5),
                       dict(INPUTS, implementation_limit=5, review_limit=5),
                       dict(INPUTS, implementation_limit=5, batch_limit=6, review_limit=5)):
            with self.subTest(inputs=inputs), self.assertRaises(ValueError):
                project.descriptor(inputs, OLD)
        # The earlier v2 contract deliberately retains its wider batch ceiling.
        self.assertEqual(project.descriptor(dict(INPUTS, implementation_limit=5, batch_limit=16), OLD)
                         ['workflow']['execution']['schema_version'], 2)
    def test_no_stage_batches_keep_approved_and_production_completion(self):
        for extra in ({'implementation_limit':5, 'batch_limit':5},
                      {'implementation_limit':5, 'batch_limit':5, 'review_limit':5}):
            for profile, completion in project.PROFILES.items():
                with self.subTest(extra=extra, profile=profile), tempfile.TemporaryDirectory() as scratch:
                    root = Path(scratch)/'project'
                    project.init(root, dict(INPUTS, staging=False, profile=profile, **extra), OLD, 'unused', apply=True)
                    self.assertEqual([m for k,m in standard.inspect(root) if k=='error'], [])
                    data = json.loads((root/'delivery.json').read_text())
                    config = json.loads((root/'tracker/config.json').read_text())
                    self.assertEqual(config['workflow'][-3:], ['review', 'approved', 'merged'])
                    self.assertEqual(set(data['environments']),
                                     set() if completion=='reviewed-merge' else {'production'})
                    self.assertEqual(data['completion'], completion)
                    self.assertEqual(config['delivery_policy']['staging'],
                                     {'enabled':False, 'branch':'stage', 'target':'disabled'})
                    self.assertEqual(config['delivery_policy']['completion'], completion)
    def test_no_stage_batch_validator_rejects_stale_column_or_delivery_mirror(self):
        self.create(dict(INPUTS, staging=False, implementation_limit=5, batch_limit=5, review_limit=5))
        config = self.json('tracker/config.json')
        stale = copy.deepcopy(config); stale['workflow'].insert(-1, 'stage')
        self.put('tracker/config.json', stale)
        self.assertTrue(any('stages differ' in e for e in self.errors()))
        stale = copy.deepcopy(config); stale['delivery_policy']['staging']['enabled'] = True
        self.put('tracker/config.json', stale)
        self.assertTrue(any('policy differs' in e for e in self.errors()))
    def test_delivery_batch_requires_both_receipt_paths_and_upgrade_cannot_hide_deletion(self):
        for staging in (True, False):
            for extra in ({'implementation_limit':5, 'batch_limit':5},
                          {'implementation_limit':5, 'batch_limit':5, 'review_limit':5}):
                for name in ('.workflow/tools/tracker_delivery_receipt.py', 'scripts/tracker_delivery_receipt.py'):
                    with self.subTest(staging=staging, extra=extra, name=name), tempfile.TemporaryDirectory() as scratch:
                        self.root = Path(scratch)/'project'
                        self.create(dict(INPUTS, profile='package', staging=staging, **extra))
                        (self.root/name).unlink()
                        self.assertTrue(any(name in error for error in self.errors()))
                        before = {p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
                        result = project.upgrade(self.root, NEW, 'unused', apply=True)
                        self.assertFalse(result['applied'])
                        self.assertEqual(before, {p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
    def test_upgrade_retains_explicit_no_stage_batch_and_pristine_stage_baseline(self):
        self.create(dict(INPUTS, implementation_limit=5, batch_limit=5, review_limit=5))
        data = self.json('delivery.json'); data['workflow']['staging'] = False
        data['environments'].pop('stage')
        config = self.json('tracker/config.json')
        config['delivery_policy'] = project.delivery_policy(data)
        config['workflow'] = project.phases(False, config['execution_policy'])
        self.put('delivery.json', data); self.put('tracker/config.json', config)
        self.assertTrue(project.upgrade(self.root, NEW, 'unused', apply=True)['applied'])
        self.assertEqual(self.errors(), [])
        self.assertFalse(self.json('delivery.json')['workflow']['staging'])
        self.assertNotIn('stage', self.json('tracker/config.json')['workflow'])
        base = self.json(project.BASELINE)
        self.assertTrue(base['inputs']['staging'])
        self.assertTrue(json.loads(base['files']['delivery.json'])['workflow']['staging'])
        self.assertEqual(project.upgrade(self.root, NEW, 'unused', apply=True)['changed'], [])
    def test_parallel_review_upgrade_preserves_local_limits_and_rejects_drift_without_writes(self):
        self.create(dict(INPUTS, implementation_limit=5, batch_limit=5, review_limit=5))
        data = self.json('delivery.json'); config = self.json('tracker/config.json')
        for policy in (data['workflow']['execution'], config['execution_policy']):
            policy.update(review_limit=4, batch_limit=2)
        self.put('delivery.json', data); self.put('tracker/config.json', config)
        self.assertTrue(project.upgrade(self.root, NEW, 'unused', apply=True)['applied'])
        self.assertEqual(self.errors(), [])
        self.assertEqual(self.json('tracker/config.json')['execution_policy'], config['execution_policy'])
        base = self.json(project.BASELINE)
        self.assertEqual(base['inputs']['review_limit'], 5)
        self.assertEqual(json.loads(base['files']['tracker/config.json'])['execution_policy']['review_limit'], 5)
        data = self.json('delivery.json'); data['workflow']['execution']['review_limit'] = 3
        self.put('delivery.json', data)
        before = {p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result = project.upgrade(self.root, OLD, 'unused', apply=True)
        self.assertFalse(result['applied']); self.assertTrue(result['errors'])
        self.assertEqual(before, {p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
    def test_existing_project_v3_opt_in_survives_upgrade_without_changing_pristine_base(self):
        self.create(dict(INPUTS, implementation_limit=5, batch_limit=5))
        policy = {'schema_version':3, 'implementation_limit':5, 'review_limit':5, 'batch_limit':5}
        data = self.json('delivery.json'); data['workflow']['execution'] = policy
        config = self.json('tracker/config.json'); config['execution_policy'] = policy
        self.put('delivery.json', data); self.put('tracker/config.json', config)
        self.assertTrue(project.upgrade(self.root, NEW, 'unused', apply=True)['applied'])
        self.assertEqual(self.errors(), [])
        self.assertEqual(self.json('tracker/config.json')['execution_policy'], policy)
        self.assertEqual(json.loads(self.json(project.BASELINE)['files']['tracker/config.json'])
                         ['execution_policy']['schema_version'], 2)
    def test_upgrade_preserves_opt_in_and_local_capacity_with_pristine_baseline(self):
        self.create(dict(INPUTS,implementation_limit=2))
        data=self.json('delivery.json');data['workflow']['execution']['implementation_limit']=4
        config=self.json('tracker/config.json');config['execution_policy']['implementation_limit']=4
        config['refresh_seconds']=120
        self.put('delivery.json',data);self.put('tracker/config.json',config)
        result=project.upgrade(self.root,NEW,'unused',apply=True)
        self.assertTrue(result['applied']);self.assertEqual(self.errors(),[])
        self.assertEqual(self.json('delivery.json')['workflow']['execution']['implementation_limit'],4)
        self.assertEqual(self.json('tracker/config.json')['execution_policy']['implementation_limit'],4)
        self.assertEqual(self.json('tracker/config.json')['refresh_seconds'],120)
        base=self.json(project.BASELINE)
        self.assertEqual(base['inputs']['implementation_limit'],2)
        self.assertEqual(json.loads(base['files']['tracker/config.json'])['execution_policy']['implementation_limit'],2)
        self.assertEqual(project.upgrade(self.root,NEW,'unused',apply=True)['changed'],[])
    def test_upgrade_does_not_enable_execution_for_legacy_consumer(self):
        self.create();result=project.upgrade(self.root,NEW,'unused',apply=True)
        self.assertTrue(result['applied']);self.assertEqual(self.errors(),[])
        self.assertNotIn('execution',self.json('delivery.json')['workflow'])
        self.assertNotIn('execution_policy',self.json('tracker/config.json'))
        self.assertNotIn('implementation_limit',self.json(project.BASELINE)['inputs'])
    def test_upgrade_preserves_project_opt_in_added_after_initialization(self):
        self.create()
        policy={'schema_version':1,'implementation_limit':2,'review_limit':1}
        data=self.json('delivery.json');data['workflow']['execution']=policy
        config=self.json('tracker/config.json');config['execution_policy']=policy
        self.put('delivery.json',data);self.put('tracker/config.json',config)
        self.assertTrue(project.upgrade(self.root,NEW,'unused',apply=True)['applied'])
        self.assertEqual(self.errors(),[])
        self.assertEqual(self.json('tracker/config.json')['execution_policy'],policy)
        self.assertNotIn('execution_policy',json.loads(self.json(project.BASELINE)['files']['tracker/config.json']))
    def test_inconsistent_execution_upgrade_writes_nothing(self):
        self.create(dict(INPUTS,implementation_limit=2))
        data=self.json('delivery.json');data['workflow']['execution']['implementation_limit']=3
        self.put('delivery.json',data)
        before={p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result=project.upgrade(self.root,NEW,'unused',apply=True)
        self.assertFalse(result['applied'])
        self.assertTrue(any('execution policy differs' in e for e in result['errors']))
        self.assertEqual(before,{p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
    def test_n8n_source_is_explicit_and_does_not_claim_runtime_delivery(self):
        self.create(dict(INPUTS,profile='n8n-source'))
        data=self.json('delivery.json')
        self.assertEqual(self.errors(),[])
        self.assertEqual(data['completion'],'reviewed-merge')
        self.assertEqual(set(data['environments']),{'stage'})
        self.assertTrue(data['workflow']['staging'])
        self.assertEqual(self.json('tracker/config.json')['delivery_policy']['delivery_target'],
                         'https://github.com/owner/example:main')
        self.assertEqual(project.descriptor(dict(INPUTS,profile='n8n'),OLD)['completion'],
                         'verified-production')
        data['profile']='n8n';self.put('delivery.json',data)
        self.assertTrue(any('Profile/completion mismatch' in error for error in self.errors()))
    def test_n8n_source_upgrade_preserves_staging_and_local_handoff(self):
        self.create(dict(INPUTS,profile='n8n-source'))
        data=self.json('delivery.json')
        data['delivery']['procedure']='Agent transfers an exact accepted revision in a separate runtime task.'
        self.put('delivery.json',data)
        result=project.upgrade(self.root,NEW,'unused',apply=True)
        self.assertTrue(result['applied'])
        self.assertEqual(self.json('delivery.json')['delivery']['procedure'],data['delivery']['procedure'])
        self.assertEqual(self.errors(),[])
    def test_drift_and_wrong_pins_fail(self):
        self.create();cfg=self.json('tracker/config.json');cfg['delivery_policy']['staging']['enabled']=False;self.put('tracker/config.json',cfg)
        self.assertTrue(any('policy differs' in x for x in self.errors()))
        cfg['delivery_policy']['staging']['enabled']=True;self.put('tracker/config.json',cfg)
        (self.root/'.github/workflows/delivery-check.yml').write_text('uses: MojoTheApe/master-repo@main\n')
        self.assertTrue(any('CI action pin' in x for x in self.errors()))
    def test_upgrade_adds_pinned_verification_guidance_and_preserves_product_checks(self):
        self.create(dict(INPUTS, implementation_limit=5, batch_limit=5, review_limit=5))
        name = 'docs/repository/VERIFICATION.md'
        base = self.json(project.BASELINE)
        base['files'].pop(name)
        self.put(project.BASELINE, base)
        (self.root/name).unlink()
        data = self.json('delivery.json')
        data['checks'] = ['python -m pytest product_tests/ -q']
        self.put('delivery.json', data)
        policy = copy.deepcopy(data['workflow']['execution'])
        result = project.upgrade(self.root, NEW, 'unused', apply=True)
        self.assertTrue(result['applied'])
        self.assertIn('/blob/'+NEW+'/docs/verification.md', (self.root/name).read_text())
        self.assertEqual(self.json('delivery.json')['checks'], data['checks'])
        self.assertEqual(self.json('delivery.json')['workflow']['execution'], policy)
        self.assertEqual(self.errors(), [])
    def test_upgrade_preserves_conflicting_local_verification_file_without_any_write(self):
        self.create()
        name = 'docs/repository/VERIFICATION.md'
        base = self.json(project.BASELINE)
        base['files'].pop(name)
        self.put(project.BASELINE, base)
        (self.root/name).write_text('Local verification procedure, not an upstream copy.\n')
        before = {p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result = project.upgrade(self.root, NEW, 'unused', apply=True)
        self.assertFalse(result['applied'])
        self.assertEqual(result['conflicts'], [name])
        self.assertEqual(before, {p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
    def test_upgrade_preserves_unique_installer_local_json_and_docs(self):
        self.create();(self.root/'installer.sh').write_text('unique installer\n')
        agents=self.root/'AGENTS.md';agents.write_text(agents.read_text()+'\nLocal safety rule.\n')
        data=self.json('delivery.json');data['exceptions']=[{'scope':'installer','reason':'preserve local behavior','reference':'issue-12'}];self.put('delivery.json',data)
        preview=project.upgrade(self.root,NEW,'unused');self.assertFalse(preview['conflicts']);self.assertEqual(self.json('delivery.json')['standard']['revision'],OLD)
        result=project.upgrade(self.root,NEW,'unused',apply=True)
        self.assertTrue(result['applied']);self.assertEqual(self.errors(),[])
        self.assertEqual(self.json('delivery.json')['standard']['revision'],NEW)
        self.assertEqual(self.json('delivery.json')['exceptions'],data['exceptions'])
        self.assertIn('Local safety rule',agents.read_text());self.assertEqual((self.root/'installer.sh').read_text(),'unique installer\n')
        self.assertEqual(project.upgrade(self.root,NEW,'unused',apply=True)['changed'],[])
    def test_conflicting_change_reports_and_writes_nothing(self):
        self.create();p=self.root/'AGENTS.md';original=p.read_text();p.write_text(original.replace('# Project instructions','# Local process'))
        incoming=files(INPUTS,NEW);incoming['AGENTS.md']=original.replace('# Project instructions','# Revised upstream process')
        before={p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        with mock.patch.object(project,'render',return_value=incoming):result=project.upgrade(self.root,NEW,'unused',apply=True)
        self.assertEqual(result['conflicts'],['AGENTS.md']);self.assertFalse(result['applied'])
        self.assertEqual(before,{p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
    def test_inconsistent_combined_config_is_not_applied(self):
        self.create();data=self.json('delivery.json');data['workflow']['staging']=False;self.put('delivery.json',data)
        result=project.upgrade(self.root,NEW,'unused',apply=True)
        self.assertFalse(result['applied']);self.assertTrue(result['errors'])
        self.assertEqual(self.json('delivery.json')['standard']['revision'],OLD)
    def test_unknown_baseline_and_symlinks_are_preserved(self):
        with self.assertRaisesRegex(ValueError,'No recorded'):project.upgrade(self.root,NEW,'unused',apply=True)
        self.root.mkdir();outside=Path(self.tmp.name)/'outside';outside.mkdir();(self.root/'docs').symlink_to(outside,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'symlink'):self.create()
        self.assertEqual(list(outside.iterdir()),[])
    def test_stale_plan_cannot_overwrite_current_file(self):
        self.root.mkdir();(self.root/'x').write_text('new local')
        with self.assertRaisesRegex(ValueError,'changed while planning'):project.write_plan(self.root,{'x':'replacement'},{'x':'old'})
        self.assertEqual((self.root/'x').read_text(),'new local')
    def test_json_three_way_disjoint_changes_and_conflict(self):
        self.assertEqual(project.merge_json({'a':1,'b':1},{'a':2,'b':1},{'a':1,'b':2}),{'a':2,'b':2})
        with self.assertRaises(ValueError):project.merge_json({'a':1},{'a':2},{'a':3})
    def test_malformed_descriptor_and_nested_config_return_findings(self):
        self.create();original=self.json('delivery.json')
        for value in ([],None,'invalid',17):
            self.put('delivery.json',value)
            self.assertTrue(self.errors())
        self.put('delivery.json',original)
        config=self.json('tracker/config.json');config['project']=[];self.put('tracker/config.json',config)
        self.assertTrue(self.errors())
    def test_renderer_uses_pinned_config_independently_of_calling_project(self):
        engine=Path(self.tmp.name)/'engine';(engine/'tracker').mkdir(parents=True)
        (engine/'tracker/config.json').write_text('{"refresh_seconds":60}')
        def exporter(command,**kwargs):
            source=Path(command[command.index('--config')+1]) if '--config' in command else self.root/'tracker/config.json'
            target=Path(command[command.index('--output')+1]);(target/'tracker').mkdir(parents=True)
            (target/'tracker/config.json').write_text(source.read_text())
            (target/'docs').mkdir();(target/'docs/TRACKER_AGENT_WORKFLOW.md').write_text('Pinned guide')
            (target/'scripts').mkdir()
            for name in project.HELPERS:
                (target/'scripts'/name).write_text('root = Path(__file__).resolve().parents[1]\n')
            return mock.Mock(returncode=0,stderr='',stdout='')
        self.create();config=self.json('tracker/config.json');config['refresh_seconds']=120;self.put('tracker/config.json',config)
        with mock.patch.object(project,'tracker_checkout',return_value=engine),mock.patch.object(project.subprocess,'run',side_effect=exporter):
            result=REAL_RENDER(INPUTS,NEW,engine)
        self.assertEqual(json.loads(result['tracker/config.json'])['refresh_seconds'],60)
        self.assertEqual(self.json('tracker/config.json')['refresh_seconds'],120)
    def test_renderer_sends_only_explicit_execution_policy_and_rejects_inheritance(self):
        engine=Path(self.tmp.name)/'engine';(engine/'tracker').mkdir(parents=True)
        observed=[]
        inherited={'schema_version':1,'implementation_limit':8,'review_limit':1}
        def exporter(command,**kwargs):
            target=Path(command[command.index('--output')+1]);(target/'tracker').mkdir(parents=True)
            config={}
            if '--execution-policy' in command:
                config['execution_policy']=json.loads(Path(command[command.index('--execution-policy')+1]).read_text())
            observed.append(config.copy())
            (target/'tracker/config.json').write_text(project.dumps(config))
            (target/'docs').mkdir();(target/'docs/TRACKER_AGENT_WORKFLOW.md').write_text('Pinned guide')
            (target/'scripts').mkdir()
            for name in project.HELPERS:
                (target/'scripts'/name).write_text('root = Path(__file__).resolve().parents[1]\n')
            return mock.Mock(returncode=0,stderr='',stdout='')
        with mock.patch.object(project,'tracker_checkout',return_value=engine),mock.patch.object(project.subprocess,'run',side_effect=exporter):
            result=REAL_RENDER(dict(INPUTS,implementation_limit=2),NEW,engine)
            self.assertEqual(json.loads(result['tracker/config.json'])['execution_policy'],
                             {'schema_version':1,'implementation_limit':2,'review_limit':1})
            REAL_RENDER(INPUTS,NEW,engine)
        self.assertNotIn('execution_policy',observed[-1])
        def leaking_exporter(command,**kwargs):
            result=exporter(command,**kwargs)
            target=Path(command[command.index('--output')+1])
            (target/'tracker/config.json').write_text(project.dumps({'execution_policy':inherited}))
            return result
        with mock.patch.object(project,'tracker_checkout',return_value=engine),mock.patch.object(project.subprocess,'run',side_effect=leaking_exporter):
            with self.assertRaisesRegex(ValueError,'explicit project choice'):REAL_RENDER(INPUTS,NEW,engine)
    def test_init_cli_omits_policy_unless_requested(self):
        args=['init','--root',str(self.root),'--profile','local','--repository','owner/example',
              '--name','Example','--id-prefix','EX','--workspace-id','example','--tracker-root','unused']
        with mock.patch.object(standard,'source_revision',return_value=OLD),mock.patch.object(project,'init',return_value={}) as initialize:
            self.assertEqual(standard.main(args),0)
            self.assertNotIn('implementation_limit',initialize.call_args.args[1])
            self.assertEqual(standard.main(args+['--implementation-limit','2']),0)
            self.assertEqual(initialize.call_args.args[1]['implementation_limit'],2)
            self.assertNotIn('batch_limit', initialize.call_args.args[1])
            self.assertEqual(standard.main(args+['--implementation-limit','5','--batch-limit']),0)
            self.assertEqual(initialize.call_args.args[1]['batch_limit'],5)
            self.assertEqual(standard.main(args+['--implementation-limit','2','--batch-limit','3']),0)
            self.assertEqual(initialize.call_args.args[1]['batch_limit'],3)
            self.assertNotIn('review_limit', initialize.call_args.args[1])
            self.assertEqual(standard.main(args+['--implementation-limit','5','--batch-limit','--review-limit','5']),0)
            self.assertEqual(initialize.call_args.args[1]['review_limit'],5)
            self.assertEqual(standard.main(args+['--no-staging','--implementation-limit','5','--batch-limit','5','--review-limit','5']),0)
            self.assertFalse(initialize.call_args.args[1]['staging'])
    def test_renderer_keeps_no_stage_batch_policy_and_rejects_stale_export(self):
        engine = Path(self.tmp.name)/'engine'; (engine/'tracker').mkdir(parents=True)
        observed = []
        def exporter(command, **kwargs):
            target = Path(command[command.index('--output')+1]); (target/'tracker').mkdir(parents=True)
            policy = json.loads(Path(command[command.index('--delivery-policy')+1]).read_text())
            execution = json.loads(Path(command[command.index('--execution-policy')+1]).read_text())
            config = {'execution_policy':execution, 'delivery_policy':policy,
                      'workflow':project.phases(policy['staging']['enabled'], execution)}
            observed.append(config)
            (target/'tracker/config.json').write_text(project.dumps(config))
            (target/'docs').mkdir(); (target/'docs/TRACKER_AGENT_WORKFLOW.md').write_text('Pinned guide')
            (target/'scripts').mkdir()
            for name in (*project.HELPERS, 'tracker_batch_policy.py', 'tracker_delivery_receipt.py'):
                (target/'scripts'/name).write_text('root = Path(__file__).resolve().parents[1]\n')
            return mock.Mock(returncode=0, stderr='', stdout='')
        inputs = dict(INPUTS, staging=False, profile='package', implementation_limit=5, batch_limit=5, review_limit=5)
        with mock.patch.object(project, 'tracker_checkout', return_value=engine), mock.patch.object(project.subprocess, 'run', side_effect=exporter):
            result = REAL_RENDER(inputs, NEW, engine)
        config = json.loads(result['tracker/config.json'])
        self.assertEqual(config['workflow'][-3:], ['review', 'approved', 'merged'])
        self.assertEqual(config['delivery_policy']['completion'], 'verified-stable-package')
        self.assertIn('.workflow/tools/tracker_batch_policy.py', result)
        self.assertIn('.workflow/tools/tracker_delivery_receipt.py', result)
        def incomplete(command, **kwargs):
            result = exporter(command, **kwargs)
            target = Path(command[command.index('--output')+1])
            (target/'scripts/tracker_delivery_receipt.py').unlink()
            return result
        with mock.patch.object(project, 'tracker_checkout', return_value=engine), mock.patch.object(project.subprocess, 'run', side_effect=incomplete):
            with self.assertRaisesRegex(ValueError, 'lacks the delivery receipt helper'):
                REAL_RENDER(inputs, NEW, engine)
        for drift in ('workflow', 'delivery_policy'):
            def stale_export(command, **kwargs):
                result = exporter(command, **kwargs)
                config = copy.deepcopy(observed[-1])
                if drift == 'workflow': config['workflow'].insert(-1, 'stage')
                else: config['delivery_policy']['staging']['enabled'] = True
                target = Path(command[command.index('--output')+1])
                (target/'tracker/config.json').write_text(project.dumps(config))
                return result
            with self.subTest(drift=drift), mock.patch.object(project, 'tracker_checkout', return_value=engine), mock.patch.object(project.subprocess, 'run', side_effect=stale_export):
                with self.assertRaisesRegex(ValueError, 'batch route differs'):
                    REAL_RENDER(inputs, NEW, engine)
    def test_process_route_is_explicit_and_preserves_delivery_and_execution(self):
        process={'schema_version':1,'required_checks':['descriptor','tracker-link','Process verification']}
        for extra in ({}, {'implementation_limit':2}, {'implementation_limit':5,'batch_limit':5}):
            with self.subTest(extra=extra):
                plain=project.descriptor(dict(INPUTS,profile='package',**extra),OLD)
                opted=project.descriptor(dict(INPUTS,profile='package',process_instructions=process,**extra),OLD)
                self.assertNotIn('process_instructions',plain['workflow'])
                self.assertEqual(opted['workflow']['process_instructions'],process)
                self.assertEqual(project.delivery_policy(plain),project.delivery_policy(opted))
                self.assertEqual(plain['workflow'].get('execution'),opted['workflow'].get('execution'))
    def test_process_policy_validation_and_mirrored_presence(self):
        process={'schema_version':1,'required_checks':['descriptor','tracker-link']}
        self.create(dict(INPUTS,process_instructions=process));self.assertEqual(self.errors(),[])
        original=self.json('delivery.json');config=self.json('tracker/config.json')
        invalid=[None,[],{},dict(process,schema_version=True),dict(process,schema_version=2),
                 dict(process,paths=['src/']),dict(process,required_checks=[]),
                 dict(process,required_checks=['descriptor']),dict(process,required_checks=['descriptor','tracker-link','']),
                 dict(process,required_checks=['descriptor','tracker-link','tracker-link']),
                 dict(process,required_checks=['descriptor','tracker-link',' Check']),
                 dict(process,required_checks=['descriptor','tracker-link',False])]
        for value in invalid:
            with self.subTest(value=value):
                data=copy.deepcopy(original);data['workflow']['process_instructions']=value
                self.put('delivery.json',data);self.assertTrue(self.errors())
        self.put('delivery.json',original)
        config.pop('process_instructions');self.put('tracker/config.json',config)
        self.assertTrue(any('process instructions differ' in e for e in self.errors()))
        config['process_instructions']=process;self.put('tracker/config.json',config)
        original['workflow'].pop('process_instructions');self.put('delivery.json',original)
        self.assertTrue(any('process instructions differ' in e for e in self.errors()))
    def test_missing_process_helper_aborts_upgrade_without_writes(self):
        process={'schema_version':1,'required_checks':['descriptor','tracker-link']}
        for name in ('.workflow/tools/tracker_process_instructions.py','scripts/tracker_process_instructions.py'):
            with self.subTest(name=name),tempfile.TemporaryDirectory() as scratch:
                self.root=Path(scratch)/'project';self.create(dict(INPUTS,process_instructions=process))
                (self.root/name).unlink()
                before={p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
                result=project.upgrade(self.root,NEW,'unused',apply=True)
                self.assertFalse(result['applied']);self.assertTrue(any(name in e for e in result['errors']))
                self.assertEqual(before,{p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
    def test_upgrade_retains_project_process_checks_and_knowledge(self):
        process={'schema_version':1,'required_checks':['descriptor','tracker-link','Local instruction checks']}
        self.create();data=self.json('delivery.json');config=self.json('tracker/config.json')
        data['workflow']['process_instructions']=process;config['process_instructions']=process
        self.put('delivery.json',data);self.put('tracker/config.json',config)
        owned=self.root/'docs/system/PROJECT.md';owned.write_text('Project-specific knowledge.\n')
        self.assertTrue(project.upgrade(self.root,NEW,'unused',apply=True)['applied'])
        self.assertEqual(self.json('delivery.json')['workflow']['process_instructions'],process)
        self.assertEqual(self.json('tracker/config.json')['process_instructions'],process)
        self.assertEqual(owned.read_text(),'Project-specific knowledge.\n');self.assertEqual(self.errors(),[])
    def test_process_cli_requires_explicit_opt_in_and_passes_actual_checks(self):
        args=['init','--root',str(self.root),'--profile','local','--repository','owner/example',
              '--name','Example','--id-prefix','EX','--workspace-id','example','--tracker-root','unused']
        with mock.patch.object(standard,'source_revision',return_value=OLD),mock.patch.object(project,'init',return_value={}) as initialize:
            self.assertEqual(standard.main(args),0);self.assertNotIn('process_instructions',initialize.call_args.args[1])
            self.assertEqual(standard.main(args+['--process-check','Actual check']),2)
            self.assertEqual(standard.main(args+['--process-instructions','--process-check','Actual check']),0)
            self.assertEqual(initialize.call_args.args[1]['process_instructions'],
                             {'schema_version':1,'required_checks':['descriptor','tracker-link','Actual check']})
    def test_renderer_process_policy_is_explicit_and_helper_is_required(self):
        process={'schema_version':1,'required_checks':['descriptor','tracker-link']}
        engine=Path(self.tmp.name)/'engine';(engine/'tracker').mkdir(parents=True)
        observed=[]
        def exporter(command,**kwargs):
            target=Path(command[command.index('--output')+1]);(target/'tracker').mkdir(parents=True)
            config={}
            if '--process-instructions' in command:
                config['process_instructions']=json.loads(Path(command[command.index('--process-instructions')+1]).read_text())
            observed.append(config.copy());(target/'tracker/config.json').write_text(project.dumps(config))
            (target/'docs').mkdir();(target/'docs/TRACKER_AGENT_WORKFLOW.md').write_text('Pinned guide')
            if 'process_instructions' in config:
                (target/'docs/PROCESS_INSTRUCTIONS.md').write_text('Actual instruction route guide.\n')
                (target/'docs/TRACKER_AGENT_WORKFLOW.md').write_text(
                    '[Process instructions](../docs/PROCESS_INSTRUCTIONS.md). Read `docs/PROCESS_INSTRUCTIONS.md`.\n')
            (target/'scripts').mkdir()
            for name in project.HELPERS:
                (target/'scripts'/name).write_text('root = Path(__file__).resolve().parents[1]\n')
            (target/'scripts/tracker_process_instructions.py').write_text('VALUE = 42\n')
            return mock.Mock(returncode=0,stderr='',stdout='')
        with mock.patch.object(project,'tracker_checkout',return_value=engine),mock.patch.object(project.subprocess,'run',side_effect=exporter):
            result=REAL_RENDER(dict(INPUTS,process_instructions=process),NEW,engine)
            self.assertEqual(json.loads(result['tracker/config.json'])['process_instructions'],process)
            self.assertIn('.workflow/tools/tracker_process_instructions.py',result)
            self.assertEqual(result['docs/repository/PROCESS_INSTRUCTIONS.md'],'Actual instruction route guide.\n')
            self.assertIn('(repository/PROCESS_INSTRUCTIONS.md)',result['docs/PROCESS_INSTRUCTIONS.md'])
            self.assertIn('(PROCESS_INSTRUCTIONS.md)',result['docs/repository/TRACKER.md'])
            self.assertIn('`docs/repository/PROCESS_INSTRUCTIONS.md`',result['docs/repository/TRACKER.md'])
            REAL_RENDER(INPUTS,NEW,engine);self.assertNotIn('process_instructions',observed[-1])
            self.assertNotIn('docs/repository/PROCESS_INSTRUCTIONS.md',REAL_RENDER(INPUTS,NEW,engine))
        def leaking(command,**kwargs):
            result=exporter(command,**kwargs);target=Path(command[command.index('--output')+1])
            (target/'tracker/config.json').write_text(project.dumps({'process_instructions':process}));return result
        with mock.patch.object(project,'tracker_checkout',return_value=engine),mock.patch.object(project.subprocess,'run',side_effect=leaking):
            with self.assertRaisesRegex(ValueError,'explicit project choice'):REAL_RENDER(INPUTS,NEW,engine)
        def incomplete(command,**kwargs):
            result=exporter(command,**kwargs);target=Path(command[command.index('--output')+1])
            (target/'scripts/tracker_process_instructions.py').unlink();return result
        with mock.patch.object(project,'tracker_checkout',return_value=engine),mock.patch.object(project.subprocess,'run',side_effect=incomplete):
            with self.assertRaisesRegex(ValueError,'lacks the process'):REAL_RENDER(dict(INPUTS,process_instructions=process),NEW,engine)
    def test_project_knowledge_is_never_refreshed_even_if_untouched(self):
        self.create()
        incoming=files(INPUTS,NEW)
        owned=[name for name in incoming if name.startswith(project.PROJECT_AREAS)]
        before={name:(self.root/name).read_text() for name in owned}
        for name in owned:incoming[name]='Upstream replacement would lose project knowledge.\n'
        with mock.patch.object(project,'render',return_value=incoming):
            result=project.upgrade(self.root,NEW,'unused',apply=True)
        self.assertTrue(result['applied'])
        self.assertEqual(before,{name:(self.root/name).read_text() for name in owned})
        self.assertEqual(self.json(project.BASELINE)['files'],incoming)
    def test_missing_project_knowledge_needs_manual_repair(self):
        self.create();(self.root/'docs/runtime/DELIVERY.md').unlink()
        result=project.upgrade(self.root,NEW,'unused',apply=True)
        self.assertFalse(result['applied'])
        self.assertTrue(any('docs/runtime/DELIVERY.md' in e for e in result['errors']))
        self.assertFalse((self.root/'docs/runtime/DELIVERY.md').exists())
        self.assertEqual(self.json('delivery.json')['standard']['revision'],OLD)
    def test_missing_v2_batch_helper_aborts_upgrade_without_writes(self):
        for name in ('.workflow/tools/tracker_batch_policy.py', 'scripts/tracker_batch_policy.py'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as scratch:
                self.root = Path(scratch)/'project'
                self.create(dict(INPUTS, implementation_limit=5, batch_limit=5))
                (self.root/name).unlink()
                self.assertTrue(any(name in e for e in self.errors()))
                before = {p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
                result = project.upgrade(self.root,NEW,'unused',apply=True)
                self.assertFalse(result['applied'])
                self.assertTrue(any(name in e for e in result['errors']))
                self.assertEqual(before, {p.relative_to(self.root):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
    def test_legacy_layout_stops_without_writes(self):
        self.create();base=self.json(project.BASELINE);base['files'].pop(project.LAYOUT);self.put(project.BASELINE,base)
        before={p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result=project.upgrade(self.root,NEW,'unused',apply=True)
        self.assertEqual(result['conflicts'],['legacy mixed layout'])
        self.assertEqual(before,{p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
    def test_layout_and_canonical_files_are_required(self):
        self.create();self.put(project.LAYOUT,dict(project.LAYOUT_DATA,system='docs/'))
        self.assertTrue(any('separated' in e for e in self.errors()))
        self.put(project.LAYOUT,project.LAYOUT_DATA)
        (self.root/'docs/repository/WORKFLOW.md').unlink()
        self.assertTrue(any('WORKFLOW.md' in e for e in self.errors()))
    def test_wrappers_preserve_cli_imports_and_project_root(self):
        import subprocess
        import runpy
        source={'docs/TRACKER_AGENT_WORKFLOW.md':'Guide'}
        for name in project.HELPERS:
            source['scripts/'+name]=("from pathlib import Path\nROOT = Path(__file__).resolve().parents[1]\n"
                "VALUE = 42\nif __name__ == '__main__': print(ROOT)\n") if name != 'tracker_delivery_policy.py' else 'VALUE = 42\n'
        project.separate_export(source)
        for name,content in source.items():
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content)
        for name in project.HELPERS:
            self.assertEqual(runpy.run_path(str(self.root/'scripts'/name))['VALUE'],42)
            if name != 'tracker_delivery_policy.py':
                result=subprocess.check_output([sys.executable,str(self.root/'scripts'/name)],cwd=self.tmp.name,text=True)
                self.assertEqual(result.strip(),str(self.root.resolve()))
        source={'docs/TRACKER_AGENT_WORKFLOW.md':'Guide','scripts/task_tracker.py':'unexpected export'}
        with self.assertRaisesRegex(ValueError,'layout changed'):project.separate_export(source)
    def test_onboarding_preview_and_apply_do_not_claim_publication(self):
        self.create();calls=[]
        def request(path,payload=None,optional=False):
            calls.append((path,payload))
            if path=='repos/owner/example':return {'full_name':'owner/example'}
            if path.endswith('/heads/main'):return {'object':{'sha':OLD}}
            if path.endswith('/heads/stage'):return None
            if payload:return {}
            raise AssertionError(path)
        run=mock.Mock(return_value=mock.Mock(returncode=0,stdout='{"changed":true,"published":false}',stderr=''))
        with mock.patch.object(onboard,'request',side_effect=request),mock.patch.object(project,'tracker_checkout',return_value=Path('engine')),mock.patch.object(onboard.subprocess,'run',run):
            result=onboard.connect(self.root,'engine',Path(self.tmp.name)/'workspace.json')
            self.assertFalse(result['connected']);self.assertFalse(any(p for _,p in calls));self.assertEqual(run.call_count,1)
            result=onboard.connect(self.root,'engine',Path(self.tmp.name)/'workspace.json',apply=True)
            self.assertTrue(result['create_stage']);self.assertFalse(result['connected'])
            self.assertEqual([p for _,p in calls if p],[{'ref':'refs/heads/stage','sha':OLD}])


if __name__=='__main__':unittest.main()
