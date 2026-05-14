#!/usr/bin/env python3
"""
Add Study in China to desktop dropdown + mobile nav across all 12 existing pages.
"""
import os

WEBSITE_DIR = os.path.dirname(os.path.abspath(__file__))

PAGES = [
    'about.html', 'compare.html', 'contact.html', 'fees.html',
    'find-your-school.html', 'guides.html', 'index.html', 'prepare.html',
    'pricing.html', 'schools.html', 'summer-camps.html', 'tutoring.html',
]

DESKTOP_ANCHOR = '<a href="tools/fees-calculator-v2c.html" class="dropdown-link"><span class="lang-th">คำนวณค่าเรียน</span><span class="lang-en">Fee Calculator</span></a>'
DESKTOP_INSERT = '\n                <a href="studyinchina.html" class="dropdown-link"><span class="lang-th">เรียนที่จีน</span><span class="lang-en">Study in China</span></a>'

MOBILE_ANCHOR = '<a href="tools/fees-calculator-v2c.html" class="mobile-nav-link" style="padding-left:32px;font-size:13px;opacity:0.75"><span class="lang-th">คำนวณค่าเรียน</span><span class="lang-en">Fee Calculator</span></a>'
MOBILE_INSERT = '\n          <a href="studyinchina.html" class="mobile-nav-link" style="padding-left:32px;font-size:13px;opacity:0.75"><span class="lang-th">เรียนที่จีน</span><span class="lang-en">Study in China</span></a>'

SKIP_MARKER = 'studyinchina.html'

results = []

for page in PAGES:
    path = os.path.join(WEBSITE_DIR, page)
    if not os.path.exists(path):
        results.append(f'SKIP (not found): {page}')
        continue

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    if SKIP_MARKER in content:
        results.append(f'SKIP (already updated): {page}')
        continue

    original = content
    desktop_done = False
    mobile_done = False

    if DESKTOP_ANCHOR in content:
        content = content.replace(DESKTOP_ANCHOR, DESKTOP_ANCHOR + DESKTOP_INSERT, 1)
        desktop_done = True

    if MOBILE_ANCHOR in content:
        content = content.replace(MOBILE_ANCHOR, MOBILE_ANCHOR + MOBILE_INSERT, 1)
        mobile_done = True

    if content != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        tag = []
        if desktop_done: tag.append('desktop')
        if mobile_done: tag.append('mobile')
        results.append(f'OK ({", ".join(tag)}): {page}')
    else:
        results.append(f'WARN (anchor not found): {page}')

print('\n'.join(results))
