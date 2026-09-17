#!/usr/bin/env python3
"""Connect a scaffolded repository to Tracker; preview by default, never deploy."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import quote
import project
import standard


def request(path, payload=None, optional=False):
    command=['gh','api',path]
    if payload is not None: command += ['--method','POST','--input','-']
    result=subprocess.run(command,input=None if payload is None else json.dumps(payload),text=True,capture_output=True)
    if result.returncode:
        if optional and '(HTTP 404)' in result.stderr: return None
        raise ValueError('GitHub operation failed: '+result.stderr.strip())
    return json.loads(result.stdout)


def connect(root, tracker_root, workspace, python=sys.executable, apply=False):
    findings=standard.inspect(root)
    errors=[message for kind,message in findings if kind=='error']
    if errors: raise ValueError('; '.join(errors))
    data=standard.read_descriptor(root)
    if data.get('schema_version')!=2: raise ValueError('Connection requires the new project contract')
    engine=project.tracker_checkout(tracker_root,data['tracker']['revision'])
    repo=data['project']['repository'].split('github.com/')[1]
    remote=request('repos/'+repo)
    if remote.get('full_name','').lower()!=repo.lower(): raise ValueError('Unexpected project repository')
    main=request('repos/'+repo+'/git/ref/heads/main')
    if not standard.SHA.fullmatch(main.get('object',{}).get('sha','')): raise ValueError('Publish the initial main commit first')
    stage=request('repos/'+repo+'/git/ref/heads/stage',optional=True) if data['workflow']['staging'] else None
    if stage and stage['object']['sha'] != main['object']['sha']:
        comparison=request('repos/'+repo+'/compare/'+main['object']['sha']+'...'+stage['object']['sha'])
        if comparison.get('status')!='identical': raise ValueError('Existing stage differs from main; audit it before onboarding')
    code='import sys; sys.path.insert(0,sys.argv.pop(1)); from tracker.cli import main; raise SystemExit(main())'
    command=[python,'-c',code,str(engine),'--config',str(Path(root).absolute()/'tracker/config.json')]
    registration=['register-project','--workspace',str(Path(workspace).absolute()),'--project-config',str(Path(root).absolute()/'tracker/config.json'),
                  '--id',data['tracker']['workspace_id']]
    # Validate registry compatibility before any remote mutation.
    preview=subprocess.run(command+registration,capture_output=True,text=True)
    if preview.returncode: raise ValueError(preview.stderr+preview.stdout)
    result={'applied':apply,'repository':repo,'create_stage':data['workflow']['staging'] and stage is None,
            'labels':'initialize configured project labels','registry':json.loads(preview.stdout),
            'connected':False,'next':'Review/publish the registry through Tracker, verify a fresh live board, record proof, then mark adoption ready.'}
    if apply:
        if result['create_stage']: request('repos/'+repo+'/git/refs',{'ref':'refs/heads/stage','sha':main['object']['sha']})
        subprocess.run(command+['init'],check=True)
        subprocess.run(command+registration+['--apply'],check=True)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True);parser.add_argument('--tracker-root',type=Path,required=True)
    parser.add_argument('--workspace',type=Path,required=True);parser.add_argument('--python',default=sys.executable)
    parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    try:
        print(json.dumps(connect(args.root,args.tracker_root,args.workspace,args.python,args.apply),indent=2));return 0
    except (OSError,ValueError,KeyError,subprocess.SubprocessError) as error:
        print(str(error),file=sys.stderr);return 1


if __name__=='__main__': raise SystemExit(main())
