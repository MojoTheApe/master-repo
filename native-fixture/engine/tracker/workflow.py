"""Project-defined stages with stable semantic actions for agents."""
import re
from .delivery_policy import policy, batch_mode

BASE_PHASES = ('idea', 'backlog', 'todo', 'in_progress', 'review', 'merged')
PHASES = ('idea', 'backlog', 'todo', 'in_progress', 'review', 'stage', 'merged')
BATCH_PHASES = ('idea', 'backlog', 'todo', 'in_progress', 'review', 'approved', 'stage', 'merged')
NAMES = dict(zip(PHASES, ('Idea', 'Backlog', 'To Do', 'In Progress', 'Review', 'Stage', 'Merged')))
COLORS = dict(zip(PHASES, ('D0D5D9', 'B3C5DD', '6B91B5', '2B5B96', 'D5AA55', '9276B5', '6B9571')))
NAMES['approved'], COLORS['approved'] = 'Approved', '70A89A'


def stages(config):
    rows = []
    for item in config.get('workflow', BASE_PHASES):
        if isinstance(item, str):
            rows.append({'id': item, 'name': config.get('completion_label', 'Merged') if item == 'merged' else NAMES.get(item, item),
                         'phase': item, 'color': COLORS.get(item, '81918E')})
        else:
            rows.append(dict(item, color=item.get('color', COLORS.get(item.get('phase'), '81918E'))))
    return rows


def validate(config):
    delivery = policy(config)
    rows = stages(config)
    ids = [r.get('id') for r in rows]
    if not rows or len(ids) != len(set(ids)):
        raise ValueError('Workflow stages must be nonempty and unique')
    for row in rows:
        if not isinstance(row.get('id'), str) or not re.fullmatch(r'[a-z][a-z0-9_\-]*', row['id']):
            raise ValueError('Invalid workflow stage ID')
        if row['id'] in ('all', 'archive', 'release'):
            raise ValueError('Workflow stage ID conflicts with workspace navigation')
        if row.get('phase') not in BATCH_PHASES or not isinstance(row.get('name'), str) or not row['name'].strip():
            raise ValueError('Every workflow stage needs a name and a supported semantic phase')
        if row['id'] in BATCH_PHASES and row['phase'] != row['id']:
            raise ValueError('Reserved semantic stage IDs cannot change their meaning')
        if not re.fullmatch(r'[0-9A-Fa-f]{6}', row.get('color', '')):
            raise ValueError('Workflow color must be a six-digit hex color')
    for phase in ('idea', 'in_progress', 'review', 'merged'):
        if not any(r['phase'] == phase for r in rows):
            raise ValueError('Workflow requires semantic phase: ' + phase)
    stage_rows = [r for r in rows if r['phase'] == 'stage']
    enabled = bool(delivery and delivery['staging']['enabled'])
    if len(stage_rows) != int(enabled):
        raise ValueError('Stage column must match the delivery staging option')
    if enabled and not (next(i for i,r in enumerate(rows) if r['phase']=='review')
                       < rows.index(stage_rows[0]) < next(i for i,r in enumerate(rows) if r['phase']=='merged')):
        raise ValueError('Stage must follow Review and precede Merged')
    approved = [r for r in rows if r['phase'] == 'approved']
    if len(approved) != int(batch_mode(config)):
        raise ValueError('Approved column must match execution policy schema 2')
    integration = rows.index(stage_rows[0]) if stage_rows else next(i for i,r in enumerate(rows) if r['phase']=='merged')
    if approved and not (next(i for i,r in enumerate(rows) if r['phase']=='review')
                         < rows.index(approved[0]) < integration):
        raise ValueError('Approved must follow Review and precede Stage or Merged')
    return rows


def phase(config, stage):
    return next((r['phase'] for r in stages(config) if r['id'] == stage), None)


def target(config, action):
    """An exact stage ID wins; otherwise select the first stage of that phase."""
    rows = stages(config)
    row = next((r for r in rows if r['id'] == action), None)
    row = row or next((r for r in rows if r['phase'] == action), None)
    if row is None:
        raise ValueError('Project has no workflow stage for: ' + action)
    return row['id']
