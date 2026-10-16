"""Isolated real-Actions experiment frontend; never uses live Tracker state."""
import argparse, base64, json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'engine'))
from tracker import ci_evidence as ci
from tracker.github import GitHub, APIError
p=argparse.ArgumentParser();p.add_argument('action',choices=['plan','gate','collect'])
p.add_argument('--pr',type=int,default=0);p.add_argument('--head');p.add_argument('--run',type=int);p.add_argument('--output',type=Path);p.add_argument('--github-output',type=Path)
a=p.parse_args();config=json.loads(Path('tracker/config.json').read_text());api=GitHub(config['project']['repository'])
try:
    value=api.request(api.root+'/contents/native-fixture/evidence.json?ref=codex%2Fmr-32-native-fixture-state')
    state=json.loads(base64.b64decode(value['content']))
except APIError as e:
    if e.status!=404:raise
    state={}
if a.action=='collect':
    proof=ci.collect(api.request,api.action_job_log,config,'checks',a.run,a.pr)
    assert proof['jobs'], 'No genuine native job was proved'
    state.setdefault('ci_evidence',{'schema_version':1,'records':{}})['records'][ci.digest(proof)]=proof
    a.output.write_text(json.dumps(state,indent=2)+'\n');result={'collected_jobs':[j['name'] for j in proof['jobs']]}
else:
    context='source' if a.pr else 'main'
    args=(api.request,api.action_job_log,config,state,'checks',a.pr,a.head)
    result=ci.plan(*args,context) if a.action=='plan' else ci.gate(*args,a.run,context)
    if a.github_output:
        with a.github_output.open('a') as f:f.write('missing='+json.dumps(result['missing'],separators=(',',':'))+'\n')
print(json.dumps(result,indent=2))
