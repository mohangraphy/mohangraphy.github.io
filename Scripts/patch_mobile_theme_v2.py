#!/usr/bin/env python3
"""
patch_mobile_theme_v2.py
---------------------------
Follow-up fix to patch_mobile_theme.py.

The mobile hamburger menu (#mobile-menu) and its submenu panel
(.mob-menu-sub) have their own hardcoded backgrounds — rgba(0,0,0,0.95)
and rgba(0,0,0,0.4) — independent of the --dark variable. That's why,
after the mobile theme patch, menu text (now dark espresso brown) became
invisible against a panel that stayed solid black.

This adds a second @media (max-width: 768px) block that overrides just
those two panel backgrounds to translucent Warm Sand / Pale Beige,
matching the rest of the mobile theme. Nothing else is touched.

Run once, locally, AFTER patch_mobile_theme.py:
    python3 patch_mobile_theme_v2.py
"""

import os
import shutil
import datetime

SCRIPT_PATH = "/Users/ncm/Pictures/Mohangraphy/Scripts/Claude_mohangraphy.py"

ANCHOR = """    --text-rgb:  43,30,19;
  }
}
"""

ADDITION = """
@media (max-width: 768px) {
  #mobile-menu { background: rgba(244,241,234,0.97); }
  .mob-menu-sub { background: rgba(234,229,217,0.6); }
}
"""


def main():
    if not os.path.exists(SCRIPT_PATH):
        print(f"ERROR: could not find {SCRIPT_PATH}")
        return

    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        source = f.read()

    if "rgba(244,241,234,0.97)" in source:
        print("This file already looks patched (found the mobile-menu fix). Stopping — nothing changed.")
        return

    if "Earthy Editorial" not in source:
        print("ERROR: patch_mobile_theme.py doesn't look like it's been run yet.")
        print("Run that first, then re-run this script.")
        return

    if ANCHOR not in source:
        print("ERROR: could not find the expected anchor text from the previous patch.")
        print("Stopping without changing anything — the file may differ from what this script expects.")
        return

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = SCRIPT_PATH + f".bak_{ts}"
    shutil.copyfile(SCRIPT_PATH, backup_path)
    print(f"Backup written: {backup_path}")

    new_source = source.replace(ANCHOR, ANCHOR + ADDITION, 1)

    with open(SCRIPT_PATH, "w", encoding="utf-8") as f:
        f.write(new_source)

    print(f"\nDone. {SCRIPT_PATH} updated.")
    print("Fixed: #mobile-menu and .mob-menu-sub backgrounds now follow the mobile theme.")
    print(f"\nIf anything looks wrong, restore with:\n  cp {backup_path} {SCRIPT_PATH}")
    print("\nNext: run 'python3 Claude_mohangraphy.py' to deploy, then check the")
    print("hamburger menu on your phone again.")


if __name__ == "__main__":
    main()
