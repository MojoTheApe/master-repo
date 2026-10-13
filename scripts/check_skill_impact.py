#!/usr/bin/env python3
"""Require an explicit Project Workflow assessment for source/process changes."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

SKILL = '.agents/skills/project-workflow/'


def requires_assessment(path):
    if path.startswith(SKILL):
        return True
    if path in ('AGENTS.md', 'CLAUDE.md', 'standard.md', 'compatibility.json', 'delivery.json'):
        return True
    if path.startswith(('profiles/', 'templates/', 'scripts/', '.github/')):
        return True
    return path.startswith('docs/') and path not in ('docs/CHANGELOG.md', 'docs/repository/CHANGELOG.md')


def assess(body, paths):
    relevant = [p for p in paths if requires_assessment(p)]
    if not relevant:
        return 'No standards or skill changes requiring assessment'
    if not isinstance(body, str) or len(body) > 65536:
        raise ValueError('PR body must contain the Project Workflow impact assessment')
    decisions = re.findall(r'^Project Workflow impact:[ \t]*([^\r\n]*)$', body, re.M)
    reasons = re.findall(r'^Project Workflow reason:[ \t]*(\S[^\r\n]*)$', body, re.M)
    if len(decisions) != 1 or decisions[0].strip() not in ('updated', 'no-impact') or len(reasons) != 1 or len(reasons[0].strip()) < 12:
        raise ValueError('Include exactly one impact line (updated or no-impact) and one concrete reason line')
    decisions[0] = decisions[0].strip()
    changed_skill = any(p.startswith(SKILL) for p in paths)
    if decisions[0] == 'updated' and not changed_skill:
        raise ValueError('An updated assessment requires skill changes in the same PR')
    if decisions[0] == 'no-impact' and changed_skill:
        raise ValueError('Skill changes require the updated assessment')
    return 'Project Workflow impact: ' + decisions[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--event', type=Path, required=True)
    args = parser.parse_args()
    try:
        event = json.loads(args.event.read_text())
        pr = event['pull_request']
        base, head = pr['base']['sha'], pr['head']['sha']
        if not all(re.fullmatch('[0-9a-f]{40}', value) for value in (base, head)):
            raise ValueError('Expected immutable base/head commit SHAs')
        diff = subprocess.check_output(['git', 'diff', '--no-renames', '--name-only', '-z', base + '...' + head])
        paths = [p for p in diff.decode().split('\0') if p]
        print(assess(pr.get('body'), paths))
        return 0
    except (KeyError, OSError, ValueError, subprocess.SubprocessError) as error:
        print('Project Workflow assessment failed: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
