"""Maintained skill discovery and installation guidance; no browser credentials."""
import base64
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from urllib.parse import urlsplit

from .sync import WEB, write_page

CATALOG = Path(__file__).with_name('skills.json')
CATEGORIES = {'build': 'Websites & landing pages', 'workflow': 'Project work',
              'design': 'Design & UX', 'quality': 'Review & testing'}
TEAM_REPOSITORY = 'MojoTheApe/ai-skills'


def load_skills(path=CATALOG):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if data.get('schema_version') != 1 or not isinstance(data.get('skills'), list) or not data['skills']:
        raise ValueError('Expected a nonempty skills catalogue')
    identifiers = set()
    for skill in data['skills']:
        if not isinstance(skill, dict):
            raise ValueError('Skill records must be objects')
        identifier = skill.get('id', '')
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', identifier) or identifier in identifiers:
            raise ValueError('Skill IDs must be safe and unique')
        identifiers.add(identifier)
        if skill.get('category') not in CATEGORIES:
            raise ValueError('Unknown skill category')
        for key in ('name', 'summary', 'outcome', 'example', 'updates'):
            if not isinstance(skill.get(key), str) or not skill[key].strip():
                raise ValueError('Skill descriptions must be complete')
        for key in ('uses', 'inputs'):
            if not isinstance(skill.get(key), list) or not skill[key] or not all(isinstance(v, str) and v.strip() for v in skill[key]):
                raise ValueError('Skill use cases and inputs must be complete')
        source = skill.get('source', {})
        if not isinstance(source, dict) or not isinstance(source.get('url'), str):
            raise ValueError('Skill source must be an HTTPS link')
        url = urlsplit(source.get('url', ''))
        if url.scheme != 'https' or url.netloc != 'github.com' or url.username or url.password or not source.get('label'):
            raise ValueError('Skill sources must be original HTTPS GitHub links')
        install = skill.get('installation', {})
        if not isinstance(install, dict):
            raise ValueError('Skill installation must be specified')
        if install.get('kind') == 'team-plugin':
            if install.get('plugin') != identifier:
                raise ValueError('Team plugin must match its catalogue ID')
        elif install.get('kind') == 'github-skill':
            if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', install.get('repository', '')):
                raise ValueError('Invalid original skill repository')
            path = install.get('path', '')
            if not path or PurePosixPath(path).is_absolute() or any(p in ('', '.', '..') for p in path.split('/')) or not re.fullmatch(r'[A-Za-z0-9_./-]+', path):
                raise ValueError('Invalid original skill path')
            if not re.fullmatch(r'[a-f0-9]{40}', install.get('revision', '')):
                raise ValueError('External skill installation requires its reviewed revision')
        else:
            raise ValueError('Unknown installation method')
    return data


def install_request(skill):
    install = skill['installation']
    if install['kind'] == 'team-plugin':
        return (f"Install the {skill['name']} Codex plugin from https://github.com/{TEAM_REPOSITORY}. "
                f"Use that repository's scripts/codex_skills.py installer for --skills {install['plugin']} "
                "with --auto-update. If the catalogue is already registered, refresh it before installation. "
                "Use my own GitHub access, preserve other skills and plugins, and verify the installed "
                "plugin and hourly updater. Tell me if access or Codex plugin support is missing.")
    url = f"https://github.com/{install['repository']}/tree/{install['revision']}/{install['path']}"
    return (f"Use Skill Installer to install the {skill['name']} skill from {url}. "
            "Keep the complete supporting scripts and references, verify the download, and restore "
            "executable permissions recorded upstream if the download loses them. Preserve other "
            "skills and settings. Confirm that Codex discovers the installed skill.")


def render_skills_page(path=CATALOG):
    data = load_skills(path)
    data['categories'] = CATEGORIES
    for skill in data['skills']:
        skill['install_request'] = install_request(skill)
    template = (WEB / 'skills.html').read_text(encoding='utf-8')
    style = (WEB / 'skills.css').read_text(encoding='utf-8')
    font = base64.b64encode((WEB / 'fonts/Manrope.ttf').read_bytes()).decode('ascii')
    style = style.replace('__FONT__', font)
    script = (WEB / 'skills.js').read_text(encoding='utf-8')
    encoded = json.dumps(data, ensure_ascii=True).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    revision = hashlib.sha256((template + style + script + encoded).encode()).hexdigest()
    icon = hashlib.sha256((WEB / 'favicon.svg').read_bytes() + (WEB / 'favicon.png').read_bytes()).hexdigest()[:16]
    parts = {'__STYLE__': style, '__SCRIPT__': script, '__DATA__': encoded,
             '__REVISION__': revision, '__ICON_VERSION__': icon}
    return re.sub(r'__(?:STYLE|SCRIPT|DATA|REVISION|ICON_VERSION)__', lambda m: parts[m[0]], template)


def write_skills_page(output):
    write_page(Path(output) / 'skills', render_skills_page())
