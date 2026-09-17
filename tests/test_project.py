import copy
import json
from pathlib import Path
import sys
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


def files(inputs=INPUTS, revision=OLD, *_args):
    """Minimal exported contract; real pinned exporter is exercised separately."""
    data=project.descriptor(inputs,revision)
    config={'schema_version':3,'project':{'name':inputs['name'],'repository':inputs['repository'],'id_prefix':inputs['prefix'],'base_branch':'main'},
            'workflow':[x for x in project.PHASES if x!='stage' or inputs['staging']], 'delivery_policy':project.delivery_policy(data),
            'modules':[{'id':'product','name':'Product','description':'Product functionality'}]}
    out={'delivery.json':project.dumps(data),'tracker/config.json':project.dumps(config),
         'tracker/engine.json':project.dumps({'repository':data['tracker']['repository'],'revision':data['tracker']['revision']}),
         'docs/TRACKER_AGENT_WORKFLOW.md':'Read the pinned guide.\n', 'scripts/task_tracker.py':'root = Path(__file__).resolve().parents[1]\n',
         'scripts/tracker_pr_check.py':'root = Path(__file__).resolve().parents[1]\n','scripts/tracker_delivery_policy.py':'# policy check\n'}
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
