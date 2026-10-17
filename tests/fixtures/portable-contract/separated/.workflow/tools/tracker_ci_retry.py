"""Canonical stdlib-only rules for explicitly selected bounded CI retries.

Structural policy validation is also used by a trusted fixed Master snapshot.
Selection and artifact support never activate private state or dispatch work.
"""


def policy(config):
    if 'ci_retry_policy' not in config:
        return None
    value = config['ci_retry_policy']
    if (not isinstance(value, dict) or set(value) != {'schema_version', 'max_executions'}
            or type(value['schema_version']) is not int or value['schema_version'] != 1
            or type(value['max_executions']) is not int or value['max_executions'] not in (1, 2)):
        raise ValueError('CI retry policy needs schema_version 1 and explicit max_executions 1 or 2')
    return value
