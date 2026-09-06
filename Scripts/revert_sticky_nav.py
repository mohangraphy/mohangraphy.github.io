#!/usr/bin/env python3
"""
revert_sticky_nav.py
------------------------
Undoes JUST the sticky positioning added to .page-nav-row in
patch_nav_fixes_batch1.py. That change caused body text to visibly
scroll behind the Copy Link/Back bar mid-page (since sticky content
scrolls underneath a stuck element by design) — not what was wanted.
The bc-back background fix and footer-title bold fix from Batch 1 are
left untouched.

Run once, locally:
    python3 revert_sticky_nav.py
"""

import os
import shutil
import datetime

SCRIPT_PATH = "/Users/ncm/Pictures/Mohangraphy/Scripts/Claude_mohangraphy.py"

OLD = """.page-nav-row {
  display: flex; justify-content: space-between; align-items: center;
  gap: 10px; flex-wrap: wrap; margin-bottom: 10px;
  position: sticky; top: var(--hdr); z-index: 1500;
  background: var(--dark); padding: 8px 0;
}"""
NEW = """.page-nav-row {
  display: flex; justify-content: space-between; align-items: center;
  gap: 10px; flex-wrap: wrap; margin-bottom: 10px;
}"""


def main():
    if not os.path.exists(SCRIPT_PATH):
        print(f"ERROR: could not find {SCRIPT_PATH}")
        return

    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        source = f.read()

    if OLD not in source:
        if NEW in source:
            print("This file already looks reverted. Stopping — nothing changed.")
        else:
            print("ERROR: could not find the expected sticky rule to revert.")
            print("Stopping without changing anything.")
        return

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = SCRIPT_PATH + f".bak_{ts}"
    shutil.copyfile(SCRIPT_PATH, backup_path)
    print(f"Backup written: {backup_path}")

    new_source = source.replace(OLD, NEW, 1)

    with open(SCRIPT_PATH, "w", encoding="utf-8") as f:
        f.write(new_source)

    print(f"\nDone. {SCRIPT_PATH} updated. Sticky positioning removed —")
    print("Copy Link/Back now scroll normally with the page again.")
    print(f"\nIf anything looks wrong, restore with:\n  cp {backup_path} {SCRIPT_PATH}")
    print("\nNext: run 'python3 Claude_mohangraphy.py' to deploy.")


if __name__ == "__main__":
    main()
