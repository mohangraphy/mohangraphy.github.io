#!/usr/bin/env python3
"""
patch_universal_brightness.py
--------------------------------
Phase E: brightness fixes that apply to BOTH desktop and mobile, based
on user feedback that some elements were only fixed on mobile (inside
the max-width:768px media query) and still look dim on a laptop.

1. The five caption/subtitle elements from Part 1 (Get in Touch button,
   About Me subtitle, Footprints subtitle, Travel Stories subtitle,
   Join the Community eyebrow) get their bold + full-opacity treatment
   applied universally now, not just under the mobile media query.
   (Font-size stays mobile-only — that was a touch-legibility bump,
   not part of the brightness complaint.)

2. .footer-copy (the copyright line at the very bottom of every page)
   was never touched by any previous patch — brightened universally.

Run once, locally:
    python3 patch_universal_brightness.py
"""

import os
import shutil
import datetime

SCRIPT_PATH = "/Users/ncm/Pictures/Mohangraphy/Scripts/Claude_mohangraphy.py"

CSS_ANCHOR = "  --text-rgb:  255,255,255;\n}"

CSS_ADDITION = """

/* ── Universal brightness fixes (both desktop and mobile) ── */
.mob-menu-cta,
.info-page-subtitle,
.journeys-header-sub,
.stories-header-sub,
.subscribe-eyebrow {
  font-weight: 700;
  opacity: 1;
}
.footer-copy {
  opacity: 1;
  font-weight: 600;
}
"""


def main():
    if not os.path.exists(SCRIPT_PATH):
        print(f"ERROR: could not find {SCRIPT_PATH}")
        return

    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        source = f.read()

    if "Universal brightness fixes" in source:
        print("This file already looks patched. Stopping — nothing changed.")
        return

    if CSS_ANCHOR not in source:
        print("ERROR: could not find the expected :root anchor.")
        print("Stopping without changing anything — the file may differ from what this script expects.")
        return

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = SCRIPT_PATH + f".bak_{ts}"
    shutil.copyfile(SCRIPT_PATH, backup_path)
    print(f"Backup written: {backup_path}")

    new_source = source.replace(CSS_ANCHOR, CSS_ANCHOR + CSS_ADDITION, 1)

    with open(SCRIPT_PATH, "w", encoding="utf-8") as f:
        f.write(new_source)

    print(f"\nDone. {SCRIPT_PATH} updated.")
    print("Brightened on BOTH desktop and mobile: Get in Touch button, About Me")
    print("subtitle, Footprints subtitle, Travel Stories subtitle, Join the")
    print("Community eyebrow, and the footer copyright line.")
    print(f"\nIf anything looks wrong, restore with:\n  cp {backup_path} {SCRIPT_PATH}")
    print("\nNext: run 'python3 Claude_mohangraphy.py' to deploy, then check these")
    print("on your laptop browser specifically (not just mobile).")


if __name__ == "__main__":
    main()
