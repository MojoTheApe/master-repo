"""One-request development intake: verified Issue first, implementation second."""
import copy
import hashlib
import re
from . import commands, descriptions, identifiers, queue
from .model import tasks_from_issues


def work(api, config, store, args):
    if config.get('execution_policy'):
        from . import execution
        _, _, section = execution.read(store, config)
        execution.worker_fields(args)
    if args.issue:
        if args.title: raise ValueError('Choose an existing ID or describe a new task, not both')
        number = identifiers.resolve(api, config, args.issue)
    else:
        if not args.title or not args.module or not args.kind:
            raise ValueError('New work needs a title, module and type chosen by the agent')
        commands.validate_creation(config, args)
        normalized = lambda text: re.sub(r'\s+', ' ', identifiers.TITLE_ID.sub('', text)).strip().casefold()
        title = normalized(args.title)
        key = hashlib.sha256((api.repository + '\n' + title).encode()).hexdigest()
        state, sha = store.read(optional=True)
        intake = state.get('intakes', {}).get(key)
        rows = api.issues()
        candidates = [i for i in rows if normalized(i['title']) == title]
        if len(candidates) > 1: raise ValueError('Several tasks have this title; inspect them and use a specific ID')
        if intake and intake.get('issue'):
            number = intake['issue']
        elif candidates:
            number = candidates[0]['number']
            if intake:
                if '<!-- tracker-request: '+key+' -->' not in candidates[0].get('body', ''):
                    raise ValueError('Pending intake and existing task disagree; inspect before resuming')
                intake.update(issue=number, state='created'); store.write(state, sha)
        elif intake:
            raise ValueError('Creation result is uncertain. Inspect GitHub and rerun once the Issue is visible; no duplicate POST was sent.')
        else:
            from .delivery_policy import admission_open
            admission_open(state)
            if state.get('active'): raise ValueError(f"#{state['active']['issue']} owns the execution slot; finish or hand it off first")
            if config.get('execution_policy'):
                from .delivery_policy import execution_state
                execution.available(execution_state(state, config), execution.worker_fields(args), None)
            if getattr(args, 'included', False) and state.get('release_rollover'):
                raise ValueError('Finish release rollover before adding new Release work')
            # Read once before reserving intake. A missing/invalid file must not
            # leave an uncertain creation record; retries reuse existing Issues.
            body = descriptions.read(args.body_file, args.title)
            state.setdefault('intakes', {})[key] = {'title': args.title.strip(), 'state': 'creating'}
            store.write(state, sha)  # concurrent sessions cannot both create this request
            creation = copy.copy(args); creation.status = 'backlog'; creation.request_key = key
            result = commands.create(api, config, creation, body=body)
            number = result['number']
            latest, sha = store.read()
            latest['intakes'][key].update(issue=number, state='created'); store.write(latest, sha)
    task = tasks_from_issues([api.issue(number)], config)[0]
    if not task['module'] or not task['type']:
        raise ValueError('Classify the existing task module and type before starting it')
    if not task['priority'] and not task['archive'] and task['phase'] != 'merged':
        commands.change(api, config, store, number, priority='medium')
    return queue.start(api, config, store, number, resume=args.resume, execution_args=args)
