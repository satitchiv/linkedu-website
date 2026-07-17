#!/usr/bin/env python3
"""
Regenerate the shared top nav (<nav class="site-nav"> + <nav class="mobile-nav">)
across the 6 UK-family pages from a single data source, data/nav-uk.json, so a
future nav edit happens in one place instead of 6 hand-copy-pasted files.

Pilot scope (see data/backlog.md #B1): UK family only —
uk-home.html, prepare.html, schools.html, find-your-school.html, compare.html,
tutoring.html. Each page's nav content is preserved exactly as it ships today;
this generator only changes WHERE that content lives, not what it renders.

Usage: python3 generate-nav-uk.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / 'data' / 'nav-uk.json'

SITE_RE = re.compile(r'<nav class="site-nav">.*?</nav>', re.DOTALL)
MOBILE_RE = re.compile(r'<nav class="mobile-nav">.*?</nav>', re.DOTALL)


def main():
    data = json.loads(DATA_PATH.read_text(encoding='utf-8'))

    results = []
    for page, blocks in data.items():
        path = ROOT / page
        if not path.exists():
            results.append(f'SKIP (not found): {page}')
            continue

        content = path.read_text(encoding='utf-8')
        original = content

        content = SITE_RE.sub(
            lambda m: f'<nav class="site-nav">{blocks["desktop"]}</nav>',
            content, count=1,
        )
        content = MOBILE_RE.sub(
            lambda m: f'<nav class="mobile-nav">{blocks["mobile"]}</nav>',
            content, count=1,
        )

        if content != original:
            path.write_text(content, encoding='utf-8')
            results.append(f'OK (updated): {page}')
        else:
            results.append(f'OK (unchanged): {page}')

    print('\n'.join(results))


if __name__ == '__main__':
    main()
