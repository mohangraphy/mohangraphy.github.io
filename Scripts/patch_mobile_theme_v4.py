#!/usr/bin/env python3
"""
patch_mobile_theme_v4.py
---------------------------
Two refinements to the mobile theme, based on user feedback on the live site:

1. Subtle sand-grain texture on the mobile background — a lightweight
   CSS-only noise texture (no image file needed), kept at very low
   opacity (0.035) so it reads as texture, not fog. Negligible effect
   on text readability at this opacity.

2. Slightly heavier base font-weight on mobile (500 instead of the
   default ~400) — Montserrat's default weight combined with this
   site's wide letter-spacing reads as "light" even when color
   contrast is technically fine. This affects all secondary text
   (menu items, subtitles, taglines) at once, since they share the
   base body font-weight.

Both scoped to the mobile media query only — desktop unaffected.

Run once, locally, AFTER patch_mobile_theme_v3.py:
    python3 patch_mobile_theme_v4.py
"""

import os
import shutil
import datetime

SCRIPT_PATH = "/Users/ncm/Pictures/Mohangraphy/Scripts/Claude_mohangraphy.py"

ANCHOR = "  header { background: rgba(244,241,234,0.97); }\n}\n"

ADDITION = """
@media (max-width: 768px) {
  body {
    font-weight: 500;
    background-color: var(--dark);
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.035'/%3E%3C/svg%3E");
    background-repeat: repeat;
  }
}
"""


def main():
    if not os.path.exists(SCRIPT_PATH):
        print(f"ERROR: could not find {SCRIPT_PATH}")
        return

    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        source = f.read()

    if "feTurbulence" in source:
        print("This file already looks patched (found feTurbulence). Stopping — nothing changed.")
        return

    if ANCHOR not in source:
        print("ERROR: could not find the expected anchor from patch_mobile_theme_v3.py.")
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
    print("Added: subtle sand-grain texture + heavier base font-weight, mobile only.")
    print(f"\nIf anything looks wrong, restore with:\n  cp {backup_path} {SCRIPT_PATH}")
    print("\nNext: run 'python3 Claude_mohangraphy.py' to deploy, then check on your phone.")
    print("If text still feels too light after this, the next step would be pushing the")
    print("text-opacity boost further — let's see how this looks first.")


if __name__ == "__main__":
    main()
