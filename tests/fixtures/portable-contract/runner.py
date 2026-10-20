"""Offline native proof data and real portable CLI execution; never live GitHub."""
import base64
import copy
import datetime
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def native_fixture(layout='raw', context='source'):
    # Author-side fixture generation only. The Python 3.9 client receives JSON,
    # never this module's engine/tests import paths.
    from tracker import ci_evidence as ci
    from test_ci_reuse import modern
    from test_delivery import sha
    from unittest import mock
    clock='2026-10-14T10:10:00+00:00'
    if context not in ('source','integration','main','promotion'):
        raise ValueError('Unknown native fixture context')
    if context=='integration':
        from test_batches import Project
        from test_ci_evidence import Native
        with tempfile.TemporaryDirectory(prefix='tracker-native-integration-') as directory:
            project=Project(Path(directory),count=1,staged=False,completion='verified-production')
            project.config['modules']=[{'id':'product','name':'Product','description':'Synthetic product module'}]
            for row in project.api.rows.values():
                row['labels']=[{'name':'module:product'} if label['name'].startswith('module:') else label for label in row['labels']]
            project.approve_task(1);coordinator=project.begin();project.candidate(coordinator)
            n=Native(project.api,project.config,200)
            n.config['ci_evidence_policy']['schema_version']=2
            n.context['native_ref']='refs/pull/200/merge';n.set_log()
    else:n = modern()
    if context=='promotion':
        from tracker import workflow
        n.config['delivery_policy']['staging']['enabled']=True
        n.config['workflow']=list(workflow.PHASES)
        n.api.prs[n.number]['head']['ref']='stage'
    head=n.head
    if context=='main':
        head=sha(700);n.api.merge(n.number,head)
        n.context.update(workflow_sha=head,checkout_sha=head,native_ref='refs/heads/main')
    if layout == 'separated':
        old = 'scripts/tracker_ci_evidence.py'; new = '.workflow/tools/tracker_ci_evidence.py'
        n.files[new] = n.files.pop(old)
        n.p['producer_files'] = {new: n.p['producer_files'][old]}
        n.p['jobs']['Linux unit']['producer_path'] = new
        n.workflow['jobs']['linux']['steps'][1]['run'] = ci.command('unit', 'Linux unit', n.p['jobs']['Linux unit'])
        n.set_workflow()
    n.main_config = copy.deepcopy(n.config)
    n.job['completed_at']='2026-10-14T10:01:00+00:00'
    run = dict(copy.deepcopy(n.run), id=72, status='in_progress', conclusion=None,head_sha=head)
    if context=='main':run.update(event='push',head_branch='main',pull_requests=[])
    linux = dict(copy.deepcopy(n.job), id=83, run_id=72, conclusion='success',head_sha=head,
                 html_url='https://github.com/owner/repo/actions/runs/72/job/83',
                 check_run_url='https://api.github.com/repos/owner/repo/check-runs/93')
    windows = dict(copy.deepcopy(linux), id=82, name='Windows installer', conclusion='success', steps=[],
                   html_url='https://github.com/owner/repo/actions/runs/72/job/82',
                   check_run_url='https://api.github.com/repos/owner/repo/check-runs/92')
    rows = [linux, windows]; recorded = {}
    def request(path):
        if path == n.api.root+'/actions/runs/72': value=copy.deepcopy(run)
        elif path.startswith(n.api.root+'/actions/runs/72/attempts/'): value={'jobs':copy.deepcopy(rows)}
        elif path in [job['check_run_url'].replace('https://api.github.com/', '') for job in rows]:
            job=next(job for job in rows if path==job['check_run_url'].replace('https://api.github.com/', ''))
            value={'name':job['name'],'head_sha':head,'app':{'slug':'github-actions'},
                   'status':job['status'],'conclusion':job['conclusion'],'details_url':job['html_url']}
        else: value=n.request(path)
        recorded[path]=copy.deepcopy(value)
        return value
    def log(number):
        value=('2026-10-14T10:00:03.100Z '+ci.MARKER+json.dumps(dict(n.context,run_id=72))+'\n'
               if number==83 else n.read_log(number))
        recorded[n.api.root+'/actions/jobs/'+str(number)+'/logs']=value
        return value
    with mock.patch.object(ci,'utc_now',lambda:datetime.datetime.fromisoformat(clock)):
        expected_plan=ci.plan(request,log,n.config,n.api.state,'unit',n.number,head,context)
        expected_gate=ci.gate(request,log,n.config,n.api.state,'unit',n.number,head,72,context)
    state=copy.deepcopy(n.api.state);state['private_claim']='NEVER_PRINT_PRIVATE_STATE'
    state_sha='7'*40
    recorded[n.api.root+'/git/matching-refs/heads/tracker-state']=[{
        'ref':'refs/heads/tracker-state','object':{'type':'commit','sha':state_sha}}]
    recorded[n.api.root+'/contents/.tracker-state.json?ref='+state_sha]={
        'content':base64.b64encode(json.dumps(state).encode()).decode()}
    return {'config':n.config,'head':head,'pr':n.number,'context':context,'clock':clock,
            'requests':recorded,'plan':expected_plan,'gate':expected_gate}


GH_STUB = '''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
args=sys.argv[1:]
if len(args)!=4 or args[:3]!=['api','--method','GET']:
    raise SystemExit('Only same-repository fixture GETs are supported')
fixture=json.loads(Path(os.environ['TRACKER_TEST_HTTP_FIXTURE']).read_text())
path=args[3]
if not path.startswith('repos/owner/repo/') or path not in fixture['requests']:
    raise SystemExit('Unrecorded or foreign fixture request')
with open(os.environ['TRACKER_TEST_REQUEST_LOG'],'a') as output:
    output.write(json.dumps(['GET',path])+'\\n')
value=fixture['requests'][path]
print(value if isinstance(value,str) else json.dumps(value))
'''

BOOTSTRAP = '''import datetime,json,runpy,sys
from pathlib import Path
entry=Path(sys.argv[1]);fixture=json.loads(Path(sys.argv[2]).read_text())
root=Path.cwd()
tools=root/'.workflow/tools'
sys.path.insert(0,str(tools if tools.is_dir() else root/'scripts'))
import tracker_ci_evidence as ci
ci.utc_now=lambda:datetime.datetime.fromisoformat(fixture['clock'])
sys.argv=[str(entry),*sys.argv[3:]]
runpy.run_path(str(entry),run_name='__main__')
'''


def exercise(root, python, layout, fixture):
    """Execute actual plan/gate CLI paths with only fixture GET responses."""
    root=Path(root).resolve()
    before={p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
    with tempfile.TemporaryDirectory(prefix='tracker-portable-http-') as scratch:
        scratch=Path(scratch);binary=scratch/'gh';binary.write_text(GH_STUB);binary.chmod(0o755)
        data=scratch/'http.json';data.write_text(json.dumps(fixture))
        log=scratch/'get.jsonl'
        env=dict(os.environ, PATH=str(scratch)+os.pathsep+os.environ.get('PATH',''),
                 TRACKER_TEST_HTTP_FIXTURE=str(data),TRACKER_TEST_REQUEST_LOG=str(log),
                 GITHUB_ACTIONS='true',GITHUB_REPOSITORY='owner/repo',GH_TOKEN='synthetic-offline-read-token',
                 PYTHONDONTWRITEBYTECODE='1')
        for key in ('PYTHONPATH','TASK_TRACKER_HOME'):env.pop(key,None)
        entries=['scripts/tracker_ci_gate.py']
        if layout=='separated':entries.append('.workflow/tools/tracker_ci_gate.py')
        for entry in entries:
            result=subprocess.run([python,'-B',str(root/entry),'--help'],cwd=root,env=env,capture_output=True,text=True)
            assert result.returncode==0 and '{plan,gate}' in result.stdout,result.stderr
            base=[python,'-B','-I','-c',BOOTSTRAP,str(root/entry),str(data)]
            for action in ('plan','gate'):
                argv=base+[action,'--profile','unit','--pr',str(fixture['pr']),'--head',fixture['head'],'--context',fixture['context']]
                if action=='gate':argv+=['--run','72']
                result=subprocess.run(argv,cwd=root,env=env,capture_output=True,text=True)
                assert result.returncode==0,(entry,action,result.stderr)
                assert json.loads(result.stdout)==fixture[action],(entry,action,result.stdout)
                assert 'NEVER_PRINT_PRIVATE_STATE' not in result.stdout+result.stderr
            bad=subprocess.run(base+['plan','--profile','unit','--pr',str(fixture['pr']),'--head','f'*40,'--context',fixture['context']],
                               cwd=root,env=env,capture_output=True,text=True)
            assert bad.returncode!=0 and 'NEVER_PRINT_PRIVATE_STATE' not in bad.stdout+bad.stderr
            if fixture['context']=='source':
                good=base+['plan','--profile','unit','--pr',str(fixture['pr']),'--head',fixture['head'],'--context','source']
                foreign=subprocess.run(good,cwd=root,env=dict(env,GITHUB_REPOSITORY='other/project'),capture_output=True,text=True)
                assert foreign.returncode!=0 and 'actual Actions repository' in foreign.stderr
                malformed=copy.deepcopy(fixture)
                state_path='repos/owner/repo/contents/.tracker-state.json?ref='+'7'*40
                state=json.loads(base64.b64decode(malformed['requests'][state_path]['content']))
                state['schema_version']=5;state.pop('completion',None)
                malformed['requests'][state_path]['content']=base64.b64encode(json.dumps(state).encode()).decode()
                data.write_text(json.dumps(malformed))
                fenced=subprocess.run(good,cwd=root,env=env,capture_output=True,text=True)
                assert fenced.returncode!=0 and 'scoped completion state protocol' in fenced.stderr
                assert 'NEVER_PRINT_PRIVATE_STATE' not in fenced.stdout+fenced.stderr
                data.write_text(json.dumps(fixture))
        code="import sys; sys.path.insert(0,sys.argv[1]); import tracker_ci_gate, tracker_ci_evidence, tracker_batch_policy, tracker_pr_check, tracker_task_context, tracker_delivery_receipt; assert not any(n=='tracker' or n.startswith('tracker.') for n in sys.modules); print('isolated import passed')"
        for directory in ['scripts']+(['.workflow/tools'] if layout=='separated' else []):
            result=subprocess.run([python,'-B','-I','-c',code,str(root/directory)],cwd=scratch,env=env,capture_output=True,text=True)
            assert result.returncode==0,result.stderr
        calls=[json.loads(line) for line in log.read_text().splitlines()]
        assert calls and all(method=='GET' and path.startswith('repos/owner/repo/') for method,path in calls)
    after={p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
    assert before==after,'Portable planning/gating changed consumer files'
    assert not (root/'.tracker-runtime').exists()
    return {'layout':layout,'context':fixture['context'],'entrypoints':entries,'native_fixture_gets':len(calls),'engine_imported':False,'consumer_writes':False}


def exercise_accounting(root, python, layout, row):
    """Run the real generic report CLI using only wholly synthetic saved GETs."""
    root=Path(root).resolve()
    assert row.get('synthetic') is True and row.get('schema_version')==1
    jobs=next(item['value']['jobs'] for item in row['responses'].values() if 'jobs' in item['value'])
    naive=sum(math.ceil((datetime.datetime.fromisoformat(job['completed_at'].replace('Z','+00:00'))
                         - datetime.datetime.fromisoformat(job['started_at'].replace('Z','+00:00'))).total_seconds()/60)
              for job in jobs)
    assert naive==row['expected']['naive_rounded_row_estimate']
    before={p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
    entries=['scripts/tracker_ci_accounting.py']
    if layout=='separated':entries.append('.workflow/tools/tracker_ci_accounting.py')
    bootstrap="""import runpy,sys
from pathlib import Path
entry=Path(sys.argv[1]);sys.path.insert(0,str(entry.parent))
sys.argv=[str(entry),*sys.argv[2:]]
try:runpy.run_path(str(entry),run_name='__main__')
except SystemExit as result:status=result.code
else:status=0
assert not any(n=='tracker' or n.startswith('tracker.') for n in sys.modules)
raise SystemExit(status)
"""
    with tempfile.TemporaryDirectory(prefix='tracker-accounting-offline-') as directory:
        scratch=Path(directory);data=scratch/'synthetic.json';data.write_text(json.dumps(row))
        env=dict(os.environ,PATH=str(scratch),PYTHONDONTWRITEBYTECODE='1')
        for key in ('PYTHONPATH','TASK_TRACKER_HOME','GH_TOKEN','GITHUB_TOKEN'):env.pop(key,None)
        for entry in entries:
            result=subprocess.run([python,'-B','-I','-c',bootstrap,str(root/entry),'--snapshot',str(data),'--json'],
                                  cwd=scratch,env=env,capture_output=True,text=True)
            assert result.returncode==0,(entry,result.stderr)
            report=json.loads(result.stdout)
            for key,value in row['expected'].items():
                if key!='naive_rounded_row_estimate':assert report['totals'][key]==value,(entry,key)
            assert report['coverage']['complete'] and report['billing']['status']=='unknown'
            assert report['billing']['net_charge'] is None and report['billing']['rates'] is None
            assert report['schema_version']==2 and report['required_coverage']['status']=='unknown'
    after={p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
    assert before==after,'Portable accounting changed consumer files'
    assert not (root/'.tracker-runtime').exists()
    return dict(layout=layout,entrypoints=entries,engine_imported=False,consumer_writes=False,
                naive_rounded_row_estimate=naive,
                counted_rounded_interval_estimate=row['expected']['rounded_interval_minutes_estimate'])


def direct_fixture(case):
    """Author-only real lifecycle generation; exported clients consume saved GETs.

    No live repository/state/logs are used. The fixed clock, UUID sequence and
    synthetic worktree make the committed fixture mechanically reproducible.
    """
    import itertools
    from types import SimpleNamespace
    from unittest import mock
    import uuid
    from tracker import delivery,direct_actions,execution,pr_checks,queue,sync
    from test_capture_workflow import Capture
    from test_direct_workflow import Project
    from test_delivery import sha
    if case not in ('task-main','task-stage','capture-main','capture-stage'):
        raise ValueError('Unknown modern direct fixture')
    capture=case.startswith('capture-');staged=case.endswith('-stage')
    sequence=itertools.count(1);clock=lambda:'2026-10-17T12:00:00Z'
    with tempfile.TemporaryDirectory(prefix='tracker-direct-author-') as directory, \
            mock.patch.object(uuid,'uuid4',lambda:SimpleNamespace(hex=f'{next(sequence):032x}')), \
            mock.patch.object(sync,'now',clock),mock.patch.object(queue,'now',clock), \
            mock.patch.object(direct_actions,'now',clock),mock.patch.object(execution,'now',clock), \
            mock.patch.object(delivery,'now',clock):
        p=Capture(Path(directory),staged) if capture else Project(Path(directory),staged)
        # Match actual standalone export defaults before any governed source.
        p.config['schema_version']=3
        p.config['modules']=[dict(id='product',name='Product',description="Replace with this project's functional boundaries before onboarding.",examples=[])]
        for item in p.api.rows.values():
            item['labels']=[{'name':'module:product'} if label['name'].startswith('module:') else label for label in item['labels']]
        if capture:
            p.worker.worktree='/synthetic/direct/'+case
            review=p.reviewed();source=review.pr
        else:
            p.handoff(worktree='/synthetic/direct/'+case);review=p.review();p.approve()
            direct_actions.reserve(p.api,p.config,p.store,review);source=review.pr
        main=source
        if staged:
            p.api.merge(source,sha(3));delivery.stage(p.api,p.config,p.store,source,True)
            delivery.verify_stage(p.api,p.config,p.store,dict(tree_sha=sha(102),source_sha=sha(3),result='passed',
                target='example/stage',checks=['Synthetic Stage verification'],report='Actual synthetic Stage result'),True)
            p.api.refs['stage']=sha(3)
            if capture:
                args=SimpleNamespace(**dict(vars(review),purpose='promotion',title='[Capture '+p.id+'] Promote note',
                    body_file=p.body,journal_file=Path(directory)/'promotion.json'))
                main=direct_actions.capture_pr(p.api,p.config,p.store,args)['pr']
            else:
                main=11;p.api.prs[main]=dict(copy.deepcopy(p.api.prs[source]),number=main,state='open',merged=False,
                    head=dict(ref='stage',sha=sha(3),repo={'full_name':'owner/repo'}),base=dict(ref='main',sha=sha(1)))
        phases=[]
        def snapshot(name):
            original=p.api.request;recorded={}
            def request(path,method='GET',payload=None,**kwargs):
                assert method=='GET','The portable fixture author records only GETs'
                if path==p.api.root+'/contents/.tracker-state.json?ref=tracker-state':
                    shared=copy.deepcopy(p.api.state);shared['fixture_secret']='NEVER_PRINT_PRIVATE_DIRECT_STATE'
                    value=dict(content=base64.b64encode(json.dumps(shared).encode()).decode())
                else:value=original(path,method,payload,**kwargs)
                recorded[path]=copy.deepcopy(value);return value
            expected=pr_checks.check(request,p.config,main,admission=True)
            assert expected['subject']==({'kind':'capture','id':p.id} if capture else {'kind':'task','id':1})
            phases.append(dict(name=name,requests=recorded,expected=expected))
        snapshot('held-admission')
        p.api.merge(main,sha(4));review.pr=main
        if capture:direct_actions.capture_finish(p.api,p.config,p.store,review)
        else:
            delivery.record_merge(p.api,p.config,p.store,[dict(number=1,prs=[main])],[main])
            p.api.labels(1,{'status:merged'},{'status:review','status:stage'})
            execution.finish(p.config,p.store,[1],[main])
        snapshot('released-receipt')
        assert not p.section['integration'] and not p.section['source_reviews']
        if capture:assert not p.issue_calls and p.operation['receipt']['result']=='accepted'
        return dict(schema_version=1,synthetic=True,case=case,config=p.config,pr=main,phases=phases)


DIRECT_BOOTSTRAP = '''import json,runpy,sys
from pathlib import Path
entry=Path(sys.argv[1]);sys.path.insert(0,str(entry.parent))
sys.argv=[str(entry),*sys.argv[2:]]
try:runpy.run_path(str(entry),run_name='__main__')
except SystemExit as result:status=result.code
else:status=0
assert not any(n=='tracker' or n.startswith('tracker.') for n in sys.modules)
raise SystemExit(status)
'''


def exercise_direct(root,python,layout,row):
    """Real exported PR admission, complete receipt replay and writer fences.

    The actual engine-free stdlib3.9 client may read only recorded same-repo
    endpoints. Both separated entrypoints execute their real shipped modules.
    """
    root=Path(root).resolve()
    assert row['schema_version']==1 and row['synthetic'] is True
    before={p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
    assert json.loads((root/'tracker/config.json').read_text())==row['config']
    entries=['scripts/tracker_pr_check.py']
    if layout=='separated':entries.append('.workflow/tools/tracker_pr_check.py')
    stub=GH_STUB.replace("if len(args)!=4 or args[:3]!=['api','--method','GET']:",
                        "if len(args)!=2 or args[0]!='api':").replace('path=args[3]','path=args[1]')
    with tempfile.TemporaryDirectory(prefix='tracker-direct-offline-') as directory:
        scratch=Path(directory);binary=scratch/'gh';binary.write_text(stub);binary.chmod(0o755)
        data=scratch/'http.json';log=scratch/'get.jsonl'
        env=dict(os.environ,PATH=str(scratch)+os.pathsep+os.environ.get('PATH',''),PYTHONDONTWRITEBYTECODE='1',
            TRACKER_TEST_HTTP_FIXTURE=str(data),TRACKER_TEST_REQUEST_LOG=str(log))
        for key in ('PYTHONPATH','TASK_TRACKER_HOME','GH_TOKEN','GITHUB_TOKEN'):env.pop(key,None)
        negative_cases=0
        for entry in entries:
            base=[python,'-B','-I','-c',DIRECT_BOOTSTRAP,str(root/entry),'--pr',str(row['pr']),'--admission']
            for phase in row['phases']:
                data.write_text(json.dumps(phase))
                result=subprocess.run(base,cwd=root,env=env,capture_output=True,text=True)
                assert result.returncode==0,(row['case'],entry,phase['name'],result.stdout,result.stderr)
                assert json.loads(result.stdout)==phase['expected'],result.stdout
                assert 'NEVER_PRINT_PRIVATE_DIRECT_STATE' not in result.stdout+result.stderr
            phase=row['phases'][0]
            path='repos/owner/repo/contents/.tracker-state.json?ref=tracker-state'
            shared=json.loads(base64.b64decode(phase['requests'][path]['content']))
            for mutation in ('old-outer','null-contract','missing-completion','legacy-owner','wrong-review','unknown-pr-intent'):
                bad=copy.deepcopy(phase);state=copy.deepcopy(shared)
                if mutation=='old-outer':state['schema_version']=2
                elif mutation=='null-contract':state['execution_contract']=None
                elif mutation=='missing-completion':state.pop('completion')
                elif mutation=='legacy-owner':state['active']={'issue':2,'started_at':'2026-10-17T12:00:00Z'}
                elif mutation=='wrong-review':state['execution']['source_reviews']={}
                else:
                    if not row['case'].startswith('capture'):continue
                    next(iter(state['execution']['captures']['operations'].values()))['pr_intent']['state']='unknown'
                bad['requests'][path]['content']=base64.b64encode(json.dumps(state).encode()).decode()
                data.write_text(json.dumps(bad))
                result=subprocess.run(base,cwd=root,env=env,capture_output=True,text=True)
                assert result.returncode!=0,(row['case'],entry,mutation,'incorrectly admitted')
                assert 'NEVER_PRINT_PRIVATE_DIRECT_STATE' not in result.stdout+result.stderr
                negative_cases+=1
            if row['case'].startswith('capture'):
                assert not any('/issues' in key for phase in row['phases'] for key in phase['requests'])
        calls=[json.loads(line) for line in log.read_text().splitlines()]
        assert calls and all(method=='GET' and path.startswith('repos/owner/repo/') for method,path in calls)
    after={p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
    assert before==after and not (root/'.tracker-runtime').exists()
    return dict(case=row['case'],layout=layout,entrypoints=entries,phases=[p['name'] for p in row['phases']],
        negative_cases=negative_cases,native_fixture_gets=len(calls),engine_imported=False,consumer_writes=False)


SELECTION_CASES = {
    'context-v2': ('task_context_policy', (), 2),
    'completion-v3': ('completion_policy', ('task_context_policy',), 3),
    'retry-v3': ('ci_retry_policy', ('task_context_policy', 'completion_policy'), 3),
    'completion-retry-v2': ('completion_policy', ('task_context_policy', 'ci_retry_policy'), 2),
}


def selection_fixture(case):
    """Generate saved native data with actual batch, receipt and owned adoption.

    Only this author-side function imports the engine/test fixtures. The public
    replay below consumes ordinary synthetic JSON and the real exported CLI.
    """
    from contextlib import ExitStack, redirect_stdout
    import io
    import itertools
    from types import SimpleNamespace
    from unittest import mock
    import uuid
    from tracker import batches, ci_retry_actions, completion, delivery, delivery_receipt, execution, maintenance, queue, sync, task_context, timing
    from selection_fixture import SelectionRepository
    if case not in SELECTION_CASES:
        raise ValueError('Unknown selection package fixture')
    selection, prior, version = SELECTION_CASES[case]
    clock = '2026-10-17T12:00:00Z'
    class Clock(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return cls.fromisoformat(clock.replace('Z', '+00:00'))
    with tempfile.TemporaryDirectory(prefix='tracker-selection-author-') as directory, ExitStack() as patches, redirect_stdout(io.StringIO()):
        sequence = itertools.count(1)
        patches.enter_context(mock.patch.object(uuid, 'uuid4', lambda: SimpleNamespace(hex=f'{next(sequence):032x}')))
        for module in (batches, ci_retry_actions, completion, delivery, execution, maintenance, queue, sync, task_context, timing):
            if hasattr(module, 'now'):
                patches.enter_context(mock.patch.object(module, 'now', lambda: clock))
        patches.enter_context(mock.patch.object(delivery_receipt, 'datetime', Clock))
        fixture = SelectionRepository(Path(directory), selection=selection, prior=prior, version=version, standalone=True)
        project = fixture.project
        project.api.state['fixture_secret'] = 'NEVER_PRINT_PRIVATE_SELECTION_STATE'
        phases = []
        for phase in ('pending-package', 'recorded-package', 'owned-adopted'):
            if phase == 'owned-adopted':
                project.config = fixture.selected
                owner = fixture.maintainer()
                owner.claim = maintenance.reserve(project.store, owner)['maintenance']['id']
                {'task_context_policy': task_context, 'completion_policy': completion,
                 'ci_retry_policy': ci_retry_actions}[selection].adopt(project.api, project.config, project.store, owner)
                maintenance.resume(project.store, owner)
            original = project.api.request
            recorded, writes = {}, []
            def request(path, method='GET', payload=None, **kwargs):
                value = original(path, method, payload, **kwargs)
                if method == 'GET':
                    if path in recorded:
                        assert recorded[path] == value, 'Native fixture changed during one recorded phase'
                    recorded[path] = copy.deepcopy(value)
                else:
                    assert method == 'PUT' and path == 'repos/owner/repo/contents/.tracker-state.json'
                    writes.append(dict(path=path, payload=copy.deepcopy(payload), response=copy.deepcopy(value)))
                return value
            document = delivery_receipt.resolve('owner/repo', fixture.main_sha, 100,
                request=request, include_delivered=True)
            expected = delivery_receipt.record(document, fixture.native.receipt, 200, 300, apply=True, request=request)
            assert len(writes) == (1 if phase == 'pending-package' else 0)
            phases.append(dict(name=phase, requests=recorded, writes=writes, document=document, record=expected))
        return dict(schema_version=1, synthetic=True, case=case, clock=clock, config=fixture.selected,
            receipt=fixture.native.receipt, run=200, job=300, phases=phases)


SELECTION_BOOTSTRAP = '''import copy,datetime,json,os,sys
from pathlib import Path
entry=Path(sys.argv[1]);sys.path.insert(0,str(entry.parent))
import tracker_delivery_receipt as receipt
fixture=json.loads(Path(os.environ['TRACKER_TEST_HTTP_FIXTURE']).read_text())
def request(path,method='GET',payload=None):
    if not path.startswith('repos/owner/repo/'):
        raise ValueError('Foreign fixture request')
    with open(os.environ['TRACKER_TEST_REQUEST_LOG'],'a') as output:
        output.write(json.dumps([method,path])+'\\n')
    if method=='GET':
        if path not in fixture['requests']:raise ValueError('Unrecorded fixture GET')
        value=fixture['requests'][path]
    elif method=='PUT':
        if len(fixture['writes'])!=1:raise ValueError('Unapproved fixture write')
        expected=fixture['writes'][0]
        if path!=expected['path'] or payload!=expected['payload']:
            raise ValueError('Receipt CAS payload differs from the actual canonical fixture')
        value=expected['response']
    else:raise ValueError('Unsupported fixture method')
    return copy.deepcopy(value)
class Clock(datetime.datetime):
    @classmethod
    def now(cls,tz=None):return cls.fromisoformat('2026-10-17T12:00:00+00:00')
receipt.datetime=Clock
receipt.main.__globals__['datetime']=Clock
# Replace only the stdlib transport at the two real CLI entry functions. The
# exported resolver/recorder, validators and CAS payload builder execute intact;
# no gh binary, engine import or authenticated fallback exists in this process.
for name in ('resolve','record'):
    receipt.main.__globals__[name].__kwdefaults__['request']=request
sys.argv=[str(entry),*sys.argv[2:]]
try:status=receipt.main()
except (ValueError,KeyError,OSError) as error:
    print(str(error),file=sys.stderr);status=1
assert not any(n=='tracker' or n.startswith('tracker.') for n in sys.modules)
raise SystemExit(status)
'''


def exercise_selection(root, python, layout, row):
    """Real receipt resolve/one exact CAS/idempotence before and after adoption.

    All target/native data are synthetic; no authenticated transport, engine
    checkout, consumer mutation or workflow dispatch is available to the client.
    """
    root = Path(root).resolve()
    assert row['schema_version'] == 1 and row['synthetic'] is True
    before = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}
    assert json.loads((root/'tracker/config.json').read_text()) == row['config']
    entries = ['scripts/tracker_delivery_receipt.py']
    if layout == 'separated':
        entries.append('.workflow/tools/tracker_delivery_receipt.py')
    with tempfile.TemporaryDirectory(prefix='tracker-selection-offline-') as directory:
        scratch = Path(directory)
        data = scratch/'http.json'; log = scratch/'requests.jsonl'
        request_file = scratch/'request.json'; evidence = scratch/'receipt.json'
        evidence.write_text(json.dumps(row['receipt']))
        env = dict(os.environ, PATH=str(scratch),
            PYTHONDONTWRITEBYTECODE='1', TRACKER_TEST_HTTP_FIXTURE=str(data), TRACKER_TEST_REQUEST_LOG=str(log))
        for key in ('PYTHONPATH','TASK_TRACKER_HOME','GH_TOKEN','GITHUB_TOKEN'):
            env.pop(key, None)
        negative_cases = 0
        for entry in entries:
            base = [python, '-B', '-I', '-c', SELECTION_BOOTSTRAP, str(root/entry)]
            for phase in row['phases']:
                data.write_text(json.dumps(phase))
                document = phase['document']
                if phase['name'] == 'pending-package':
                    result = subprocess.run(base+['resolve','--repository','owner/repo',
                        '--merge-sha',document['merge_sha'],'--ci-run',str(document['ci_run']),
                        '--output',str(request_file)], cwd=root, env=env, capture_output=True, text=True)
                    assert result.returncode == 0, (row['case'],entry,result.stdout,result.stderr)
                    assert json.loads(request_file.read_text()) == document
                    assert json.loads(result.stdout) == document
                request_file.write_text(json.dumps(document))
                argv = base+['record','--request',str(request_file),'--evidence',str(evidence),
                    '--verification-run',str(row['run']),'--verification-job',str(row['job']),'--apply']
                result = subprocess.run(argv, cwd=root, env=env, capture_output=True, text=True)
                assert result.returncode == 0, (row['case'],entry,phase['name'],result.stdout,result.stderr)
                assert json.loads(result.stdout) == phase['record']
                assert 'NEVER_PRINT_PRIVATE_SELECTION_STATE' not in result.stdout+result.stderr
            pending = row['phases'][0]
            path = 'repos/owner/repo/contents/.tracker-state.json?ref=tracker-state'
            original = json.loads(base64.b64decode(pending['requests'][path]['content']))
            for change in ('missing-freeze', 'changed-scope', 'old-outer', 'unknown-maintenance'):
                bad = copy.deepcopy(pending)
                shared = copy.deepcopy(original)
                if change == 'missing-freeze':
                    shared['execution']['history'] = [r for r in shared['execution']['history'] if r['event'] != 'batch-frozen']
                elif change == 'changed-scope':
                    issue_path = 'repos/owner/repo/issues/1'
                    bad['requests'][issue_path]['body'] += '\nA new actual requirement'
                elif change == 'old-outer':
                    shared['schema_version'] = 1
                else:
                    shared['schema_version'] = 3
                    shared['maintenance'] = {'schema_version': 99}
                bad['requests'][path]['content'] = base64.b64encode(json.dumps(shared).encode()).decode()
                data.write_text(json.dumps(bad))
                request_file.write_text(json.dumps(pending['document']))
                result = subprocess.run(argv, cwd=root, env=env, capture_output=True, text=True)
                assert result.returncode != 0, (row['case'],entry,change,'incorrectly recorded')
                assert 'NEVER_PRINT_PRIVATE_SELECTION_STATE' not in result.stdout+result.stderr
                negative_cases += 1
        calls = [json.loads(line) for line in log.read_text().splitlines()]
        assert calls and all(method in ('GET','PUT') and path.startswith('repos/owner/repo/') for method,path in calls)
        assert sum(method == 'PUT' for method,_ in calls) == len(entries)
    after = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}
    assert before == after and not (root/'.tracker-runtime').exists()
    return dict(case=row['case'], layout=layout, entrypoints=entries, phases=[p['name'] for p in row['phases']],
        negative_cases=negative_cases, native_fixture_gets=sum(method=='GET' for method,_ in calls),
        fixture_receipt_cas=len(entries), engine_imported=False, consumer_writes=False)


def support_fixture():
    """Save actual ordinary admission/completion with wholly synthetic GETs."""
    from unittest import mock
    from tracker import delivery
    from test_process_support import SupportProject
    with mock.patch.object(delivery, 'now', lambda: '2026-10-20T00:00:00+00:00'):
        project = SupportProject()
        source = copy.deepcopy(project.api.prs[10])
        project.review()
        receipt = project.merge()
        return dict(schema_version=1, synthetic=True, case='canonical-support-main',
            config=project.config, source_pr=source, main_pr=project.api.prs[10],
            state=project.api.state, admission=receipt['verification']['admission'],
            requests=project.observed, expected_proof_sha256=receipt['verification']['proof_sha256'])


SUPPORT_BOOTSTRAP = r'''
import copy,json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import tracker_process_support as support, tracker_delivery_policy as rules
row=json.loads(Path(sys.argv[2]).read_text())
assert row['schema_version']==1 and row['synthetic'] is True and row['case']=='canonical-support-main'
calls=[]
def request(path):
 calls.append(path)
 if path not in row['requests']:raise AssertionError('Undeclared synthetic GET: '+path)
 return copy.deepcopy(row['requests'][path])
proof=support.classify(request,row['config'],row['source_pr'])
assert proof['proof_sha256']==row['expected_proof_sha256']
result=support.completion(request,row['config'],row['state'],row['main_pr'],row['admission'],[1])
assert result['route']=='process-support' and result['admission']['route']=='main'
receipt=row['state']['delivery_workflow']['tasks']['1']
assert rules.summary(receipt)['process_support'] and rules.summary(receipt)['verified']
negative=0
original=copy.deepcopy(row)
root='repos/'+support.MASTER
for change in ('unpublished','wrong-tag','changed-scope','mixed-product','requested-delivery','unknown-isolation'):
 row=copy.deepcopy(original)
 if change=='unpublished':row['requests'][root+'/releases/tags/v1.6.0']['draft']=True
 elif change=='wrong-tag':row['requests'][root+'/git/ref/tags/v1.6.0']['object']['sha']='f'*40
 elif change=='changed-scope':row['requests']['repos/owner/repo/issues/1']['body']+='\nNew publication criterion.'
 elif change=='mixed-product':
  tree='repos/owner/repo/git/trees/'+('0000000000000000000000000000000000000066')+'?recursive=1'
  entry=next(x for x in row['requests'][tree]['tree'] if x['path']=='app.py')
  entry['mode']='100755'
 elif change=='requested-delivery':row['state']['execution']={'integration':{'issues':[1],'delivery_request':{'state':'requested','issues':[1]}}}
 else:row['state']['delivery_workflow']['reviews']['10']['process_support']['product_isolation']['result']='unknown'
 try:
  invalid=support.completion(request,row['config'],row['state'],row['main_pr'],row['admission'],[1])
 except ValueError:pass
 else:assert invalid is None,(change,'invalid support accepted')
 negative+=1
assert not any(n=='tracker' or n.startswith('tracker.') for n in sys.modules)
print(json.dumps(dict(case=original['case'],negative_cases=negative,engine_imported=False,consumer_writes=False,native_fixture_gets=len(calls))))
'''


def exercise_support(root, python, layout, row):
    """Real exported proof/reader on the portable floor, with GET-only fixtures."""
    root = Path(root)
    before = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}
    locations = ['scripts'] + (['.workflow/tools'] if layout == 'separated' else [])
    results = []
    with tempfile.TemporaryDirectory(prefix='tracker-support-portable-') as directory:
        data = Path(directory)/'synthetic.json'; data.write_text(json.dumps(row))
        for location in locations:
            completed = subprocess.run([python, '-B', '-I', '-c', SUPPORT_BOOTSTRAP, str(root/location), str(data)],
                cwd=directory, capture_output=True, text=True)
            assert completed.returncode == 0, completed.stderr + completed.stdout
            results.append(dict(location=location, **json.loads(completed.stdout)))
    after = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}
    assert before == after and not (root/'.tracker-runtime').exists()
    return dict(case=row['case'], layout=layout, entries=results, engine_imported=False, consumer_writes=False)
