"""Standalone brand studies published alongside the authenticated workspace."""
import base64
import hashlib
import json
import xml.etree.ElementTree as ET
from .sync import WEB, atomic_write


def render_logo_page():
    template = (WEB / 'logo.html').read_text(encoding='utf-8')
    style = (WEB / 'logo.css').read_text(encoding='utf-8')
    script = (WEB / 'logo.js').read_text(encoding='utf-8')
    for token, name in [('__FONT__', 'Inter-Regular.ttf'), ('__FONT_SEMIBOLD__', 'Inter-SemiBold.ttf')]:
        font = base64.b64encode((WEB / 'fonts' / name).read_bytes()).decode('ascii')
        style = style.replace(token, font)
    original = ET.fromstring((WEB / 'brand/1654-original.svg').read_text())
    paths = [dict(d=p.attrib['d'], fill=p.attrib['fill']) for p in original.iter('{http://www.w3.org/2000/svg}path') if p.attrib.get('fill', '').startswith('#')]
    script = script.replace('__BRAND__', json.dumps(paths))
    revision = hashlib.sha256((template + style + script).encode()).hexdigest()
    return template.replace('__REVISION__', revision).replace('__STYLE__', style).replace('__SCRIPT__', script)


def write_logo_page(output):
    atomic_write(output / 'logo' / 'index.html', render_logo_page())
