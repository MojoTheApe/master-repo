"""Render one complete snapshot; failed updates preserve last-known-good data."""
from __future__ import annotations
import base64
import hashlib
import json
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from .model import payload

WEB = Path(__file__).with_name("web")


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def atomic_write(path, content):
    path = Path(path)
    content = content.encode("utf-8") if isinstance(content, str) else content
    if path.is_file() and path.read_bytes() == content:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent, prefix=".tracker-", delete=False) as f:
        f.write(content)
        temp = Path(f.name)
    temp.chmod(0o644)
    temp.replace(path)


def write_page(output, page):
    """Publish same-origin browser icons before pages that reference them."""
    output = Path(output)
    for name in ("favicon.png", "favicon.svg"):
        atomic_write(output / name, (WEB / name).read_bytes())
    atomic_write(output / "index.html", page)


def render(data):
    template = (WEB / "index.html").read_text(encoding="utf-8")
    icon_hash = hashlib.sha256((WEB / "favicon.svg").read_bytes() + (WEB / "favicon.png").read_bytes()).hexdigest()[:16]
    template = template.replace("__ICON_VERSION__", icon_hash)
    css = (WEB / "style.css").read_text(encoding="utf-8")
    font = base64.b64encode((WEB / "fonts/Manrope.ttf").read_bytes()).decode("ascii")
    css = css.replace("__FONT__", font)
    js = (WEB / "task-text.js").read_text(encoding="utf-8") + '\n' + (WEB / "app.js").read_text(encoding="utf-8")
    revision = hashlib.sha256((template + css + js).encode()).hexdigest()
    result = dict(data, revision=revision)
    digest = hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()
    result["digest"] = digest
    # JSON in a script element must not allow issue text to close that element.
    encoded = json.dumps(result, ensure_ascii=True).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    parts = {"__STYLE__": css, "__DATA__": encoded, "__APP__": js}
    # Replace only placeholders in the template, never marker-like Issue content.
    page = re.sub(r"__(?:STYLE|DATA|APP)__", lambda match: parts[match[0]], template)
    return page, result


def sync(api, config, output, *, allow_empty=False, queue=None, workspace=None, freshness_seconds=None):
    output = Path(output)
    try:
        previous = json.loads((output / "status.json").read_text())
        if not isinstance(previous, dict):
            previous = {}
    except (OSError, ValueError):
        previous = {}
    error = "fetch_failed"
    try:
        if (output / 'data.json').exists():
            saved = json.loads((output / 'data.json').read_text())
            if saved.get('project', {}).get('repository') != config['project']['repository']:
                raise ValueError('Output directory belongs to another repository')
        issues = api.issues()
        if not issues and not allow_empty and (output / "index.html").exists() and previous.get("issues") != 0:
            error = "empty_response"
            if not hasattr(api, 'confirm_empty') or not api.confirm_empty():
                raise ValueError("Unexpected empty update")
        milestones = api.request(api.root + "/milestones?state=all&per_page=100", paginate=True)
        if queue is None:
            from .queue import StateStore
            queue = StateStore(api, config["project"]["base_branch"]).read(optional=True)[0]
        error = "render_failed"
        from .queue import public_state
        data = payload(issues, config, milestones, public_state(queue))
        if workspace: data['workspace'] = workspace
        page, data = render(data)
        timestamp = now()
        error = "write_failed"
        # Publish content before its status pointer; readers verify matching digests.
        atomic_write(output / "data.json", json.dumps(data))
        write_page(output, page)
        if workspace is None:
            from .skills import write_skills_page
            write_skills_page(output)
        status = {"ok": True, "synced_at": timestamp, "digest": data["digest"],
                  "repository": config['project']['repository'],
                  "revision": data["revision"], "issues": len(data["tasks"]), "empty_confirmed": not bool(data["tasks"])}
        if freshness_seconds is not None:
            status['freshness_seconds'] = max(180, min(1080, int(freshness_seconds)))
        atomic_write(output / "status.json", json.dumps(status))
        print(f"Synced {status['issues']} issues at {timestamp}")
        return status
    except Exception:
        previous.update(ok=False, attempted_at=now(), error=error)
        atomic_write(output / "status.json", json.dumps(previous))
        raise RuntimeError(f"Sync failed ({error}); previous board preserved") from None
