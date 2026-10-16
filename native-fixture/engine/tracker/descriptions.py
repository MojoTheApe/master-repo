"""Check description structure; the author remains responsible for meaning."""
from pathlib import Path
import re


def _visible_lines(body):
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    fence = None
    for line in body.splitlines():
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence = None
            continue
        if marker:
            fence = marker[1]
            continue
        if line.startswith(('    ', '\t')):
            continue
        yield line


def validate(body, title=''):
    lines = list(_visible_lines(body))
    headings = [(i, re.match(r'^ {0,3}#{1,6}\s+(.+?)\s*#*\s*$', line)) for i, line in enumerate(lines)]
    headings = [(i, match[1].strip()) for i, match in headings if match]
    if not headings or headings[0][1].casefold() != 'description':
        raise ValueError('Begin the task body with a Description heading and a plain-English explanation of what changes and why. Put working context and criteria in Specifications below it.')
    start = headings[0][0] + 1
    end = headings[1][0] if len(headings) > 1 else len(lines)
    prose = []
    for line in lines[start:end]:
        if re.match(r'^\s*(?:[-*+]\s|\d+[.)]\s|>\s|\|)', line):
            continue
        line = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', line)
        line = re.sub(r'<[^>]*>|https?://\S+', '', line)
        plain = re.sub(r'[^\w\s]|_', '', line).strip().casefold()
        if plain and plain not in {'todo', 'tbd', 'na', 'none', 'no response', 'description', 'description goes here', 'write description here'}:
            prose.append(plain)
    text = ' '.join(prose)
    normalized_title = re.sub(r'[^\w\s]|_', '', title).strip().casefold()
    if not re.search(r'[^\W\d_]\w*\s+[^\W\d_]', text) or text == normalized_title:
        raise ValueError('Description needs real prose, not an empty template, checklist, placeholder or repeated title. Explain the request from available context; state unknowns without inventing requirements.')
    if len(headings) < 2 or headings[1][1].casefold() != 'specifications':
        raise ValueError('Follow Description with a Specifications section. Put context, scope, acceptance criteria, technical notes and handoff inside it; see the task template.')
    specification = []
    for line in lines[headings[1][0] + 1:]:
        if re.match(r'^\s*#{1,6}\s', line):
            continue
        plain = re.sub(r'^\s*(?:[-*+]\s*(?:\[[ xX]\]\s*)?|\d+[.)]\s*)', '', line)
        plain = re.sub(r'<[^>]*>|https?://\S+', '', plain)
        plain = re.sub(r'[^\w\s]|_', '', plain).strip().casefold()
        if plain not in {'todo', 'tbd', 'na', 'none', 'no response', 'specifications', 'specifications go here'}:
            specification.append(plain)
    if not re.search(r'[^\W\d_]\w*\s+[^\W\d_]', ' '.join(specification)):
        raise ValueError('Specifications needs verified working context or concrete criteria, not empty headings or placeholders. For an idea, record what is known and what remains undecided.')
    return body


def read(path, title=''):
    if not path:
        raise ValueError('New tasks require --body-file with a filled Description section. The agent writes it from the request and project context.')
    return validate(Path(path).read_text(encoding='utf-8'), title)
