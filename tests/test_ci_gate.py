import base64
import importlib.util
import json
from pathlib import Path
import re
from types import SimpleNamespace
import tempfile
import unittest
from unittest import mock

SOURCE = Path(__file__).resolve().parents[1]


class PortableGate(unittest.TestCase):
    def setUp(self):
        self.ci = SimpleNamespace(SHA=re.compile(r'[a-f0-9]{40}\Z'), unique_object=self.unique,
                                  plan=mock.Mock(return_value={'missing':['Product']}), gate=mock.Mock(return_value={'missing':[]}))
        self.rules = SimpleNamespace(state_schema=mock.Mock(return_value=1),
            file_bytes=lambda request,root,row:base64.b64decode(row['content']),
            route=mock.Mock(return_value='source'), batch_mode=mock.Mock(return_value=False))
        modules={'tracker_ci_evidence':self.ci,'tracker_delivery_policy':self.rules,
                 'tracker_delivery_receipt':SimpleNamespace(github=mock.Mock())}
        with mock.patch.dict('sys.modules',modules):
            spec=importlib.util.spec_from_file_location('portable',SOURCE/'templates/workflow/ci_gate.py')
            self.tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.tool)
        self.root='repos/owner/project';self.sha='a'*40
        self.ref={'ref':'refs/heads/tracker-state','object':{'type':'commit','sha':self.sha}}
        self.state={'schema_version':1,'todo_order':[], 'private_claim':'NEVER_PRINT_THIS'}

    @staticmethod
    def unique(pairs):
        result={}
        for k,v in pairs:
            if k in result:raise ValueError('duplicate key')
            result[k]=v
        return result

    def request(self,refs=None,state=None):
        refs=[self.ref] if refs is None else refs
        raw=json.dumps(self.state if state is None else state).encode()
        def request(path):
            if path==self.root+'/git/matching-refs/heads/tracker-state':return refs
            self.assertEqual(path,self.root+'/contents/.tracker-state.json?ref='+self.sha)
            return {'content':base64.b64encode(raw).decode()}
        return request

    def test_exact_ref_immutable_read_and_private_state_is_not_projected(self):
        rows=[{'ref':'refs/heads/tracker-state-backup'},self.ref]
        self.assertEqual(self.tool.read_state(self.request(rows),'owner/project'),self.state)
        self.rules.state_schema.assert_called_once_with(self.state)
        empty=self.tool.read_state(self.request(rows[:1]),'owner/project')
        self.assertNotIn('private_claim',empty)
        self.assertEqual(empty['todo_order'],[])

    def test_bad_ref_targets_and_stored_state_fail_closed(self):
        refs=[[self.ref,self.ref],[dict(self.ref,object={'type':'tree','sha':self.sha})],
              [dict(self.ref,object={'type':'commit','sha':'wrong'})],{},[None]]
        for rows in refs:
            with self.assertRaises(ValueError):self.tool.read_state(self.request(rows),'owner/project')
        for state in ({'schema_version':1}, {'schema_version':1,'todo_order':{}}):
            with self.assertRaises(ValueError):self.tool.read_state(self.request(state=state),'owner/project')
        self.rules.state_schema.side_effect=ValueError('unsupported fence')
        with self.assertRaisesRegex(ValueError,'unsupported fence'):
            self.tool.read_state(self.request(),'owner/project')
        with self.assertRaises(OSError):self.tool.read_state(mock.Mock(side_effect=OSError('network')),'owner/project')

    def test_duplicate_json_keys_are_rejected(self):
        def request(path):
            if 'matching-refs' in path:return [self.ref]
            return {'content':base64.b64encode(b'{"schema_version":1,"schema_version":2,"todo_order":[]}').decode()}
        with self.assertRaises(ValueError):self.tool.read_state(request,'owner/project')

    def test_same_repository_token_route_uses_exported_core_without_engine(self):
        with tempfile.TemporaryDirectory() as tmp:
            config=Path(tmp)/'config.json';config.write_text(json.dumps({'project':{'repository':'owner/project'}}))
            output=Path(tmp)/'github-output'
            args=SimpleNamespace(config=config,context='auto',pr=0,head='b'*40,action='plan',run=None,profile='checks',github_output=output)
            transport=mock.Mock(return_value=[])
            result=self.tool.run(args,transport,{'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':'owner/project'})
            self.assertEqual(result,{'missing':['Product']})
            self.assertEqual(output.read_text(),'missing=["Product"]\n')
            call=self.ci.plan.call_args.args
            self.assertEqual(call[-1],'main');self.assertEqual(call[3]['todo_order'],[])
            with self.assertRaises(ValueError):call[0]('repos/other/private/contents/key')
            with self.assertRaises(ValueError):self.tool.run(args,transport,{'GITHUB_ACTIONS':'true','GITHUB_REPOSITORY':'other/project'})
            args.action='gate'
            with self.assertRaises(ValueError):self.tool.run(args,transport,{})
            args.run=71;self.tool.run(args,transport,{})
            self.assertEqual(self.ci.gate.call_args.args[-2:],(71,'main'))
            args.pr=10;self.rules.route.return_value='batch';self.rules.batch_mode.return_value=True
            self.tool.run(args,transport,{})
            self.assertEqual(self.ci.gate.call_args.args[-1],'integration')

    def test_native_profile_requires_portable_helper_after_init(self):
        import test_ci_policy as fixtures
        case=fixtures.EvidencePolicy();case.setUp()
        self.addCleanup(case.doCleanups)
        case.create(dict(__import__('test_project').INPUTS,ci_evidence=fixtures.policy()))
        # Fake exporter does not run an engine; this asserts the Master-owned
        # portable frontend and compatibility wrapper are actually rendered.
        for relative in ('.workflow/tools/tracker_ci_gate.py','scripts/tracker_ci_gate.py'):
            self.assertTrue((case.root/relative).is_file())
        (case.root/'.workflow/tools/tracker_ci_gate.py').unlink()
        self.assertTrue(any('tracker_ci_gate.py' in x for x in case.errors()))


if __name__=='__main__':unittest.main()
