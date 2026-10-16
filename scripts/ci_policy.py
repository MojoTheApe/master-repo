"""Structural mirror of the compatible Tracker native CI policy.

Keep these stdlib-only definitions aligned with tracker/ci_evidence.py.
Real paired-export validation checks the mirror against the pinned engine;
this validator never imports or executes consumer-owned code.
"""
import re


VERSION = 1


SHA = re.compile(r'[a-f0-9]{40}\Z')


DIGEST_IMAGE = re.compile(r'[^\s]+@sha256:[a-f0-9]{64}\Z')


def git_path(value):
    return (isinstance(value, str) and value and not value.startswith(('/', '-'))
            and not any(x in value.split('/') for x in ('', '.', '..'))
            and not any(c in value for c in '\n\r\\'))


def blobs(value, *, nonempty=False):
    if (not isinstance(value, dict) or nonempty and not value
            or any(not git_path(k) or not isinstance(v, str) or not SHA.fullmatch(v) for k, v in value.items())):
        raise ValueError('CI context needs explicit repository paths and immutable Git blob SHAs')


def policy(config):
    value = config.get('ci_evidence_policy')
    if value is None:
        return None
    if (not isinstance(value, dict) or set(value) != {'schema_version', 'profiles'}
            or type(value['schema_version']) is not int or value['schema_version'] not in (1, 2)
            or not isinstance(value['profiles'], dict) or not value['profiles']):
        raise ValueError('Invalid ci_evidence_policy version/fields')
    for key, p in value['profiles'].items():
        if not re.fullmatch(r'[a-z][a-z0-9_-]{0,63}', key):
            raise ValueError('CI profile names must be stable identifiers')
        if (not isinstance(p, dict) or set(p) != {'workflow_path', 'workflow_blob_sha', 'producer_files', 'jobs', 'metadata_mode', 'max_age_seconds'}
                or not git_path(p['workflow_path']) or not p['workflow_path'].startswith('.github/workflows/')
                or not isinstance(p['workflow_blob_sha'], str) or not SHA.fullmatch(p['workflow_blob_sha'])
                or p['metadata_mode'] not in ('commit', 'tree') or type(p['max_age_seconds']) is not int
                or not 1 <= p['max_age_seconds'] <= 30 * 86400 or not isinstance(p['jobs'], dict) or not p['jobs']):
            raise ValueError('CI profile needs immutable workflow, producers and explicit metadata mode')
        blobs(p['producer_files'], nonempty=True)
        ids = []
        for name, job in p['jobs'].items():
            if not isinstance(name, str) or not name.strip() or not isinstance(job, dict):
                raise ValueError('CI jobs need unique full native job names')
            if job == {'mode': 'fresh'}:
                continue
            if (set(job) != {'mode', 'workflow_job', 'runner_labels', 'producer_step', 'producer_path', 'verification_steps', 'context'}
                    or job['mode'] != 'fixed' or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_-]*', job['workflow_job'])
                    or not isinstance(job['runner_labels'], list) or not job['runner_labels']
                    or any(not isinstance(x, str) or not x or x.endswith('-latest') or x == 'self-hosted' for x in job['runner_labels'])
                    or len(set(job['runner_labels'])) != len(job['runner_labels'])
                    or not isinstance(job['producer_step'], str) or not job['producer_step']
                    or job['producer_path'] not in p['producer_files']
                    or not isinstance(job['verification_steps'], list) or not job['verification_steps']
                    or any(not isinstance(x, str) or not x for x in job['verification_steps'])
                    or len(set(job['verification_steps'])) != len(job['verification_steps'])
                    or job['producer_step'] in job['verification_steps']):
                raise ValueError('CI fixed jobs need static producer, exact native job/steps and stable runner labels')
            ids.append(job['workflow_job'])
            c = job['context']
            if (not isinstance(c, dict) or set(c) != {'container', 'host_independent', 'toolchains', 'dependencies', 'build_inputs', 'fixtures'}
                    or not isinstance(c['container'], str) or not DIGEST_IMAGE.fullmatch(c['container'])
                    or c['host_independent'] is not True
                    or not isinstance(c['toolchains'], dict) or not c['toolchains']
                    or not set(c['toolchains']) <= {'python3', 'node', 'npm'}
                    or any(not isinstance(v, str) or not re.fullmatch(r'v?\d+\.\d+\.\d+', v) for v in c['toolchains'].values())):
                raise ValueError('CI reuse needs reviewed host-independent immutable container and exact toolchains')
            blobs(c['dependencies'], nonempty=True); blobs(c['build_inputs']); blobs(c['fixtures'])
        if len(set(ids)) != len(ids):
            raise ValueError('CI workflow job aliases/matrices are unsupported; declare every real job separately')
    return value
