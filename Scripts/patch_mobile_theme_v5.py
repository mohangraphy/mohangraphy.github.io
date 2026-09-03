#!/usr/bin/env python3
"""
patch_mobile_theme_v5.py
---------------------------
Two fixes, based on user feedback on the live mobile site:

1. Footer / "Join the Community" / Copyright banner backgrounds — same
   bug class as the header and mobile menu: each has its OWN hardcoded
   dark background, independent of --dark, so they stayed black even
   after the mobile theme was applied. Fixed with mobile-only overrides
   using the existing --dark/--mid variables (so footer gets a subtly
   different shade from the page body, as before).

2. Bolder terracotta text — specifically the mobile menu's tap/hover
   state and the blog listing's location/date caption lines below each
   title, per user's explicit examples. Font-weight bumped to 700 and
   opacity raised slightly, mobile only.

Run once, locally, AFTER patch_mobile_theme_v4.py:
    python3 patch_mobile_theme_v5.py
"""

import os
import shutil
import datetime

SCRIPT_PATH = "/Users/ncm/Pictures/Mohangraphy/Scripts/Claude_mohangraphy.py"

ANCHOR = "    background-repeat: repeat;\n  }\n}\n"

ADDITION = """
@media (max-width: 768px) {
  .mob-menu-item:hover, .mob-menu-subitem:hover { font-weight: 700; }
  .blog-row-loc, .blog-post-loc { font-weight: 700; opacity: .95; }
  footer { background: var(--mid); }
  #subscribe-section {
    background: linear-gradient(160deg, var(--mid) 0%, var(--dark) 50%, var(--mid) 100%);
  }
  #copyright-banner {
    background: rgba(244,241,234,0.95);
    color: rgba(194,125,95,0.85);
  }
}
"""


def main():
    if not os.path.exists(SCRIPT_PATH):
        print(f"ERROR: could not find {SCRIPT_PATH}")
        return

    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        source = f.read()

    if "#copyright-banner {\n    background: rgba(244,241,234,0.95);" in source:
        print("This file already looks patched. Stopping — nothing changed.")
        return

    if ANCHOR not in source:
        print("ERROR: could not find the expected anchor from patch_mobile_theme_v4.py.")
        print("Make sure that script has been run first. Stopping without changing anything.")
        return

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = SCRIPT_PATH + f".bak_{ts}"
    shutil.copyfile(SCRIPT_PATH, backup_path)
    print(f"Backup written: {backup_path}")

    new_source = source.replace(ANCHOR, ANCHOR + ADDITION, 1)

    with open(SCRIPT_PATH, "w", encoding="utf-8") as f:
        f.write(new_source)

    print(f"\nDone. {SCRIPT_PATH} updated.")
    print("Fixed: footer, Join the Community section, and copyright banner backgrounds.")
    print("Bolded: mobile menu tap state, blog location/date captions.")
    print(f"\nIf anything looks wrong, restore with:\n  cp {backup_path} {SCRIPT_PATH}")
    print("\nNext: run 'python3 Claude_mohangraphy.py' to deploy, then scroll all the way")
    print("down on the home page and check the menu/blog list again.")


if __name__ == "__main__":
    main()
