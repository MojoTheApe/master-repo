#!/usr/bin/env python3
"""Check local Markdown file links; external links/anchors are not network-tested."""

from pathlib import Path
import posixpath
import project
import re
import sys
from urllib.parse import unquote, urlparse


def main():
    root = Path(__file__).resolve().parents[1]
    broken = []
    for page in root.rglob("*.md"):
        if ".git" in page.parts:
            continue
        for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", page.read_text()):
            link = link.strip("<>")
            parsed = urlparse(link)
            if parsed.scheme or not parsed.path:
                continue
            if page.parent == root/'templates/workflow':
                # Template links are relative to their generated destination.
                destination = project.FILES[page.name]
                target_name = posixpath.normpath(posixpath.join(posixpath.dirname(destination), unquote(parsed.path)))
                generated = set(project.FILES.values()) | set(project.FORWARDS) | {'docs/repository/TRACKER.md'}
                exists = target_name in generated
            else:
                exists = (page.parent / unquote(parsed.path)).exists()
            if not exists:
                broken.append(str(page.relative_to(root)) + ": " + link)
    if broken:
        print("Broken local links:\n" + "\n".join(broken))
        return 1
    print("Local Markdown file links resolve; external URLs and anchors not checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
