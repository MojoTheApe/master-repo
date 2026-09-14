#!/usr/bin/env python3
"""Check local Markdown file links; external links/anchors are not network-tested."""

from pathlib import Path
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
            target = page.parent / unquote(parsed.path)
            if not target.exists():
                broken.append(str(page.relative_to(root)) + ": " + link)
    if broken:
        print("Broken local links:\n" + "\n".join(broken))
        return 1
    print("Local Markdown file links resolve; external URLs and anchors not checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
