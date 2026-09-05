#!/usr/bin/env python3
"""
patch_nav_fixes_batch1.py
----------------------------
Batch 1 of navigation/consistency fixes, based on user feedback.

1. .bc-back's background used var(--ta06) — meant as a barely-visible
   6% tint, but the earlier text-contrast boost (which correctly fixed
   dim TEXT) also boosted this BACKGROUND use of the same variable to
   53% opacity, turning it into a solid, ugly-looking fill. Removed
   entirely so it matches the plain-text style already used correctly
   on blog post pages (.story-post-back).

2. .page-nav-row (Copy Link + Back, added in Part C) is now
   position:sticky, staying visible just below the header as the page
   scrolls, instead of scrolling away with the content.

3. .footer-section-title (the "LICENSING" / "COPYRIGHT & LEGAL"
   headings) gets font-weight:700 so it's clearly bolder than the body
   text under it, on both platforms.

Run once, locally:
    python3 patch_nav_fixes_batch1.py
"""

import os
import shutil
import datetime

SCRIPT_PATH = "/Users/ncm/Pictures/Mohangraphy/Scripts/Claude_mohangraphy.py"

OLD_BC_BACK = "cursor: pointer; background: var(--ta06);"
NEW_BC_BACK = "cursor: pointer; background: none;"

OLD_PAGE_NAV_ROW = """.page-nav-row {
  display: flex; justify-content: space-between; align-items: center;
  gap: 10px; flex-wrap: wrap; margin-bottom: 10px;
}"""
NEW_PAGE_NAV_ROW = """.page-nav-row {
  display: flex; justify-content: space-between; align-items: center;
  gap: 10px; flex-wrap: wrap; margin-bottom: 10px;
  position: sticky; top: var(--hdr); z-index: 1500;
  background: var(--dark); padding: 8px 0;
}"""

OLD_FOOTER_TITLE = """.footer-section-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 16px; letter-spacing: 4px;
  color: var(--gold); text-transform: uppercase;
  margin-bottom: 14px;
}"""
NEW_FOOTER_TITLE = """.footer-section-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 16px; letter-spacing: 4px; font-weight: 700;
  color: var(--gold); text-transform: uppercase;
  margin-bottom: 14px;
}"""


def patch(source, old, new, label):
    if old not in source:
        raise ValueError(f"Could not find expected block for: {label}")
    return source.replace(old, new, 1)


def main():
    if not os.path.exists(SCRIPT_PATH):
        print(f"ERROR: could not find {SCRIPT_PATH}")
        return

    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        source = f.read()

    if "cursor: pointer; background: none;" in source and "position: sticky; top: var(--hdr); z-index: 1500;" in source:
        print("This file already looks patched. Stopping — nothing changed.")
        return

    try:
        new_source = source
        new_source = patch(new_source, OLD_BC_BACK, NEW_BC_BACK, "bc-back background")
        new_source = patch(new_source, OLD_PAGE_NAV_ROW, NEW_PAGE_NAV_ROW, "page-nav-row sticky")
        new_source = patch(new_source, OLD_FOOTER_TITLE, NEW_FOOTER_TITLE, "footer-section-title bold")
    except ValueError as e:
        print(f"ERROR: {e}")
        print("Stopping without changing anything — the file may differ from what this script expects.")
        return

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = SCRIPT_PATH + f".bak_{ts}"
    shutil.copyfile(SCRIPT_PATH, backup_path)
    print(f"Backup written: {backup_path}")

    with open(SCRIPT_PATH, "w", encoding="utf-8") as f:
        f.write(new_source)

    print(f"\nDone. {SCRIPT_PATH} updated.")
    print("Fixed: Back button background removed (matches blog page style),")
    print("Copy Link + Back now sticky near the header, footer subheadings bolded.")
    print(f"\nIf anything looks wrong, restore with:\n  cp {backup_path} {SCRIPT_PATH}")
    print("\nNext: run 'python3 Claude_mohangraphy.py' to deploy, then check.")
    print("If the sticky row doesn't stay put while scrolling, let me know —")
    print("some parent container might have overflow settings that block it.")


if __name__ == "__main__":
    main()
