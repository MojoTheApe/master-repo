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
