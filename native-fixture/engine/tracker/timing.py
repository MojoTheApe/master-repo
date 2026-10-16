"""Observed process durations. Timing records never grant workflow ownership."""
from datetime import datetime, timezone
import re
from .sync import now

KINDS = ('implementing', 'reviewing', 'merging')


def stamp(value):
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return parsed.timestamp() if parsed.utcoffset() is not None else None
    except (ValueError, TypeError, AttributeError, OverflowError):
        return None


def utc(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat(timespec='seconds')


def project(state):
    """Reconstruct intervals from durable audit events; publish numbers and UTC only."""
    as_of = now(); cutoff = stamp(as_of)
    spans, opened, observed = {}, {}, set()
    def start(n, kind, at):
        if type(n) is not int or n <= 0 or at is None or at > cutoff:
            return
        key = (str(n), kind); observed.add(key)
        opened.setdefault(key, at)
    def stop(n, kind, at):
        key = (str(n), kind)
        begun = opened.pop(key, None)
        if begun is not None and at is not None and begun <= at <= cutoff:
            spans.setdefault(key, []).append((begun, at))

    section = state.get('execution', {})
    history = section.get('history', [])
    prs = {}
    batches = dict(section.get('batches', {}))
    if section.get('integration'):
        batches[section['integration']['id']] = section['integration']
    for event in history:
        if event.get('event') == 'handed-off':
            prs[event.get('pr')] = [event.get('issue')]
        row = event.get('review', {})
        if row.get('pr'):
            prs[row['pr']] = row.get('issues', [])
        row = event.get('batch', {})
        if row.get('id'):
            batches.setdefault(row['id'], row)
    for row in [*section.get('completed', {}).values(), *section.get('source_reviews', {}).values(), section.get('review') or {}]:
        if row.get('pr'):
            prs[row['pr']] = row.get('issues', [])

    events = list(history)
    # Existing staged v1 sources have a real stage timestamp even before timer support.
    workflow = state.get('delivery_workflow', {})
    for row in [workflow.get('stage', {}), *workflow.get('promotions', {}).values()]:
        if row.get('issues') and not row.get('batch_id'):
            events.append(dict(event='source-staged', issues=row['issues'], at=row.get('recorded_at')))
    for e in sorted(events, key=lambda e: stamp(e.get('at')) or 0):
        at = stamp(e.get('at')); name = e.get('event')
        if at is None or at > cutoff:
            continue
        n = e.get('issue')
        if name in ('claimed', 'takeover'):
            start(n, 'implementing', at)
        elif name in ('handed-off', 'stopped', 'archived'):
            stop(n, 'implementing', at)
        if name in ('review-acquired', 'review-resumed'):
            for n in e.get('issues', prs.get(e.get('pr'), [])):
                start(n, 'reviewing', at)
        elif name in ('source-approved', 'review-returned', 'integrated', 'source-staged'):
            for n in e.get('issues', e.get('review', {}).get('issues', [e.get('issue')])):
                stop(n, 'reviewing', at)
        batch = e.get('batch') or batches.get(e.get('batch_id'), {})
        if name in ('batch-frozen', 'batch-refreshed'):
            for n in batch.get('issues', []):
                start(n, 'merging', at)
        elif name in ('approval-returned', 'batch-review-returned', 'batch-integrated', 'batch-cancelled'):
            for n in batch.get('issues', []):
                stop(n, 'merging', at)

    for row in state.get('timing_history', []):
        kind = row.get('kind'); begin = stamp(row.get('started_at')); end = stamp(row.get('finished_at'))
        if kind in KINDS and begin is not None and end is not None and begin <= end <= cutoff:
            key = (str(row['issue']), kind); observed.add(key); spans.setdefault(key, []).append((begin, end))

    owners = {}
    def running(n, kind, since, owner=None):
        at = stamp(since)
        if at is None or at > cutoff:
            return
        key = (str(n), kind); observed.add(key)
        owners[key] = (opened.get(key, at), owner)
    for claim in section.get('claims', {}).values():
        if claim.get('state') == 'implementing':
            running(claim['issue'], 'implementing', claim.get('started_at'))
    for lane in [*section.get('source_reviews', {}).values(), section.get('review') or {}]:
        if lane.get('state') == 'reviewing' and not lane.get('batch_id'):
            for n in lane['issues']:
                if section.get('tasks', {}).get(str(n), {}).get('state') == 'reviewing':
                    running(n, 'reviewing', lane.get('started_at'), lane['actor'])
    batch = section.get('integration')
    if batch and batch.get('state') in ('assembling', 'reviewing', 'stage'):
        for n in batch['issues']:
            running(n, 'merging', batch.get('started_at'), batch['actor'])
    active = state.get('active')
    if active and not active.get('timing_finished_at'):
        running(active['issue'], 'implementing', active.get('started_at'))
    for row in state.get('activity_timers', {}).values():
        if row.get('kind') in ('reviewing', 'merging'):
            for n in row.get('issues', []):
                running(n, row['kind'], row.get('started_at'), row.get('actor'))

    result = {}
    for key in sorted(observed):
        merged = []
        for begin, end in sorted(spans.get(key, [])):
            if merged and begin <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
            else:
                merged.append((begin, end))
        record = {'seconds': int(sum(end - begin for begin, end in merged)), 'since': None}
        if key in opened and key not in owners:
            record['partial'] = True
        if key in owners:
            begin, owner = owners[key]
            # A takeover/retry cannot count a closed interval twice.
            begin = max(begin, max((end for _, end in merged), default=begin))
            record['since'] = utc(begin)
            if isinstance(owner, str) and re.fullmatch(r'(?:Reviewer|Coordinator)-[A-Za-z0-9]{4,32}', owner):
                record['owner'] = owner
        result.setdefault(key[0], {})[key[1]] = record
    return {'as_of': as_of, 'tasks': result}


def end_work(state, number):
    active = state.get('active')
    if active and active['issue'] == number and not active.get('timing_finished_at'):
        active['timing_finished_at'] = now()
        state.setdefault('timing_history', []).append(dict(issue=number, kind='implementing',
            started_at=active['started_at'], finished_at=active['timing_finished_at']))
        return True
    return False


def end_observations(state, number):
    changed = False
    for kind, row in list(state.get('activity_timers', {}).items()):
        if number in row['issues']:
            state.setdefault('timing_history', []).append(dict(issue=number, kind=kind,
                started_at=row['started_at'], finished_at=now()))
            row['issues'].remove(number)
            if not row['issues']:
                del state['activity_timers'][kind]
            changed = True
    return changed


def legacy_timer(api, config, store, args):
    """Optional observations for legacy projects with no source-review claims."""
    from . import delivery_policy as rules, identifiers, model
    if rules.execution_policy(config):
        raise ValueError('Execution projects derive timers from their actual claims; use their ownership commands')
    state, sha = store.read(optional=True)
    active = state.setdefault('activity_timers', {})
    row = active.get(args.kind)
    if args.action == 'start':
        rules.admission_open(state)
        if not re.fullmatch(r'(?:Reviewer|Coordinator)-[A-Za-z0-9]{4,32}', args.actor or '') or not re.fullmatch(r'[A-Za-z0-9_-]{4,100}', args.session or ''):
            raise ValueError('Supply the actual neutral actor and opaque session')
        role = 'Reviewer-' if args.kind == 'reviewing' else 'Coordinator-'
        if not args.actor.startswith(role):
            raise ValueError('Use the process actor role')
        numbers = [identifiers.resolve(api, config, n) for n in args.issues]
        if not numbers or len(numbers) != len(set(numbers)):
            raise ValueError('Specify distinct actual process tasks')
        if row:
            if (row['actor'], row['session'], row['issues']) != (args.actor, args.session, numbers):
                raise ValueError('Another actual run owns this observation; finish it first')
            return {'state': 'running', 'resumed': True}
        if any(set(numbers) & set(r['issues']) for r in active.values()):
            raise ValueError('A task already has an observed process')
        for n in numbers:
            task = model.tasks_from_issues([api.issue(n)], config)[0]
            if task['archive'] or task['phase'] != 'review':
                raise ValueError('Legacy review/merge observations require actual Review tasks')
        active[args.kind] = dict(kind=args.kind, actor=args.actor, session=args.session, issues=numbers, started_at=now())
    else:
        if not row or (row['actor'], row['session']) != (args.actor, args.session):
            raise ValueError('Only the recorded actor/session may stop its observation')
        ended = now()
        for n in row['issues']:
            state.setdefault('timing_history', []).append(dict(issue=n, kind=args.kind, started_at=row['started_at'], finished_at=ended))
        del active[args.kind]
    store.write(state, sha)
    return {'state': 'running' if args.action == 'start' else 'stopped'}
