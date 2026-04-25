#!/usr/bin/env python3
"""
deploy.py  —  Mohangraphy Safe Deploy Wrapper
----------------------------------------------
Run this instead of Claude_mohangraphy.py directly.

It will:
  1. Check the script has all required fixes
  2. Back up the current script with a datestamp
  3. Run Claude_mohangraphy.py
  4. Report success or failure clearly

Usage:
    python3 /Users/ncm/Pictures/Mohangraphy/Scripts/deploy.py
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT        = '/Users/ncm/Pictures/Mohangraphy'
SCRIPTS_DIR = os.path.join(ROOT, 'Scripts')
MAIN_SCRIPT = os.path.join(SCRIPTS_DIR, 'Claude_mohangraphy.py')
BACKUP_DIR  = os.path.join(SCRIPTS_DIR, 'Backups')

# ── Required signatures — if any are missing, fixes have been lost ─────────────
REQUIRED_SIGNATURES = [
    ('seenPaths',
     'Deduplication fix (banner count)'),
    ('display:block !important',
     'Recently Added page visibility fix'),
    ('async function subscribeVisitor',
     'Notify Me / Subscribe button fix'),
    ('.section-block:not(#gallery-new-photos)',
     'Recently Added navigation fix'),
    ('new-photo-wrap',
     'Category tags on Recently Added photos'),
    ('CAT_ORDER',
     'Category order fix (Nature · Places · Architecture · People & Culture)'),
    ('People & Culture',
     'People & Culture category rename fix'),
    ('Nature/Landscapes',
     'Landscapes sub-category fix (Mountains folded in)'),
    ('load_blog_posts',
     'Travel Stories blog system'),
    ('showStoriesIndex',
     'Travel Stories JS navigation'),
]

# ── Helpers ───────────────────────────────────────────────────────────────────
def banner(msg, char='─'):
    print('\n' + char * 55)
    print(f'  {msg}')
    print(char * 55)

def ok(msg):   print(f'  ✅  {msg}')
def fail(msg): print(f'  ❌  {msg}')
def warn(msg): print(f'  ⚠️   {msg}')
def info(msg): print(f'  ℹ️   {msg}')

# ── Step 1: Check script exists ───────────────────────────────────────────────
banner('MOHANGRAPHY SAFE DEPLOY', '═')
print(f'  {datetime.now().strftime("%d %b %Y  %H:%M:%S")}\n')

if not os.path.exists(MAIN_SCRIPT):
    fail(f'Claude_mohangraphy.py not found at:\n     {MAIN_SCRIPT}')
    sys.exit(1)

ok('Claude_mohangraphy.py found')

# ── Step 2: Read script content ───────────────────────────────────────────────
with open(MAIN_SCRIPT, 'r', encoding='utf-8') as f:
    content = f.read()

# ── Step 3: Verify all required fixes are present ────────────────────────────
banner('CHECKING REQUIRED FIXES')
all_ok = True
for signature, description in REQUIRED_SIGNATURES:
    if signature in content:
        ok(description)
    else:
        fail(f'MISSING: {description}')
        fail(f'         (signature not found: {signature!r})')
        all_ok = False

if not all_ok:
    print()
    fail('One or more required fixes are missing from Claude_mohangraphy.py.')
    warn('This means an OLD version of the file is in your Scripts folder.')
    warn('Download the latest fixed version from Claude and copy it first:')
    print()
    print('    cp ~/Downloads/Claude_mohangraphy.py \\')
    print(f'       {MAIN_SCRIPT}')
    print()
    warn('Then run deploy.py again.')
    sys.exit(1)

ok('All fixes verified — script is up to date')

# ── Step 4: Back up current script ───────────────────────────────────────────
banner('BACKING UP SCRIPT')
os.makedirs(BACKUP_DIR, exist_ok=True)
stamp     = datetime.now().strftime('%Y%m%d_%H%M')
backup_path = os.path.join(BACKUP_DIR, f'Claude_mohangraphy_{stamp}.py')
shutil.copy2(MAIN_SCRIPT, backup_path)
ok(f'Backup saved: Backups/Claude_mohangraphy_{stamp}.py')

# Clean up old backups — keep only the 10 most recent
backups = sorted([
    f for f in os.listdir(BACKUP_DIR)
    if f.startswith('Claude_mohangraphy_') and f.endswith('.py')
])
if len(backups) > 10:
    for old in backups[:-10]:
        os.remove(os.path.join(BACKUP_DIR, old))
    info(f'Cleaned up old backups — keeping 10 most recent')

# ── Step 5: Run Claude_mohangraphy.py ─────────────────────────────────────────
banner('DEPLOYING WEBSITE')
print()

result = subprocess.run(
    [sys.executable, MAIN_SCRIPT],
    cwd=ROOT
)

# ── Step 6: Result ────────────────────────────────────────────────────────────
print()
if result.returncode == 0:
    banner('DEPLOY COMPLETE ✅', '═')
    ok('Website deployed successfully to mohangraphy.com')
    ok(f'Backup kept at: Backups/Claude_mohangraphy_{stamp}.py')
    print()
else:
    banner('DEPLOY FAILED ❌', '═')
    fail('Claude_mohangraphy.py exited with an error.')
    warn('Check the output above for details.')
    warn('Your backup is safe at:')
    warn(f'  Backups/Claude_mohangraphy_{stamp}.py')
    print()
    sys.exit(result.returncode)
