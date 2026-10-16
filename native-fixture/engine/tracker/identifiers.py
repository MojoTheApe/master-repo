"""Stable public task IDs; GitHub Issue numbers remain the storage keys."""
import re

TITLE_ID = re.compile(r'^([a-z][a-z0-9]*-\d+[a-z]?)\s*:\s*', re.I)


def validate(config):
    project = config['project']
    prefix = project.get('id_prefix')
    if prefix is None: return  # previously exported clients remain readable
    if not re.fullmatch(r'[A-Z]{2,8}', prefix):
        raise ValueError('Project ID prefix must contain 2–8 uppercase letters')
    offset = project.get('id_offset', 0)
    if type(offset) is not int or offset < 0:
        raise ValueError('Project ID offset must be a nonnegative integer')
    legacy = project.get('legacy_task_ids', {})
    if not isinstance(legacy, dict) or len(set(legacy.values())) != len(legacy):
        raise ValueError('Legacy task IDs must be a unique Issue-to-ID mapping')
    for number, value in legacy.items():
        if not re.fullmatch(r'[1-9]\d*', number) or not re.fullmatch(prefix + r'-[1-9]\d*', value):
            raise ValueError('Invalid legacy task ID mapping')
        if int(value.split('-')[1]) >= offset:
            raise ValueError('Reserve the legacy ID range below the new Issue offset')


def task_id(issue, config):
    project = config['project']; number = issue['number']
    if project.get('id_prefix'):
        return project.get('legacy_task_ids', {}).get(str(number),
            f"{project['id_prefix']}-{number + project.get('id_offset', 0)}")
    alias = TITLE_ID.match(issue['title'])
    return alias[1].lower() if alias else f'#{number}'


def resolve(api, config, value):
    raw = str(value).strip()
    if re.fullmatch(r'#?[1-9]\d*', raw):
        number = int(raw.lstrip('#'))
    else:
        project = config['project']; prefix = project.get('id_prefix')
        if prefix:
            if not re.fullmatch(prefix + r'-[1-9]\d*', raw, re.I):
                raise ValueError(f'Use a {prefix} task ID or a GitHub Issue number from this project')
            legacy = {v.upper(): int(k) for k, v in project.get('legacy_task_ids', {}).items()}
            number = legacy.get(raw.upper(), int(raw.split('-')[1]) - project.get('id_offset', 0))
            if number <= 0: raise ValueError('Unknown legacy task ID')
        else:
            matches = [i['number'] for i in api.issues() if task_id(i, config).casefold() == raw.casefold()]
            if len(matches) != 1: raise ValueError('Task ID is missing or ambiguous in this project')
            number = matches[0]
    issue = api.issue(number)
    if 'pull_request' in issue: raise ValueError('Choose a task Issue, not a pull request')
    if not re.fullmatch(r'#?[1-9]\d*', raw) and task_id(issue, config).casefold() != raw.casefold():
        raise ValueError('Task ID does not match the verified Issue')
    return number
