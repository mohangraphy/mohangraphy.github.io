#!/usr/bin/env python3
"""
patch_universal_brightness_v2.py
------------------------------------
Final Phase E fix, based on user feedback on live desktop screenshots.

1. .subscribe-form input::placeholder used var(--ta3) — only 30%
   opacity, explaining the dull "Your Name" / "Your Email" placeholder
   text. Brightened to var(--ta6) (60%).

2. .footer-section-body (the paragraph text under "Licensing" and
   "Copyright & Legal" in the footer) used var(--ta38). Brightened by
   overriding its color to var(--ta7) (70%) — brighter, NOT bolder,
   per user's explicit request ("need not be bold letters but
   definitely brighter").

Both apply universally (both desktop and mobile) since neither was
mobile-specific to begin with.

Run once, locally:
    python3 patch_universal_brightness_v2.py
"""

import os
import shutil
import datetime

SCRIPT_PATH = "/Users/ncm/Pictures/Mohangraphy/Scripts/Claude_mohangraphy.py"

OLD_PLACEHOLDER = ".subscribe-form input::placeholder { color: var(--ta3); }"
NEW_PLACEHOLDER = ".subscribe-form input::placeholder { color: var(--ta6); }"

CSS_ANCHOR = """.footer-section-body {
  font-size: 12px; letter-spacing: 0.5px; line-height: 1.9;
  color: var(--ta38);
  font-family: 'Montserrat', sans-serif;
}"""
CSS_ADDITION = """
.footer-section-body { color: var(--ta7); }"""


def main():
    if not os.path.exists(SCRIPT_PATH):
        print(f"ERROR: could not find {SCRIPT_PATH}")
        return

    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        source = f.read()

    if "input::placeholder { color: var(--ta6); }" in source:
        print("This file already looks patched. Stopping — nothing changed.")
        return

    if OLD_PLACEHOLDER not in source:
        print("ERROR: could not find the expected placeholder rule.")
        print("Stopping without changing anything.")
        return

    if CSS_ANCHOR not in source:
        print("ERROR: could not find the expected .footer-section-body rule.")
        print("Stopping without changing anything.")
        return

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = SCRIPT_PATH + f".bak_{ts}"
    shutil.copyfile(SCRIPT_PATH, backup_path)
    print(f"Backup written: {backup_path}")

    new_source = source.replace(OLD_PLACEHOLDER, NEW_PLACEHOLDER, 1)
    new_source = new_source.replace(CSS_ANCHOR, CSS_ANCHOR + CSS_ADDITION, 1)

    with open(SCRIPT_PATH, "w", encoding="utf-8") as f:
        f.write(new_source)

    print(f"\nDone. {SCRIPT_PATH} updated.")
    print("Brightened: newsletter placeholder text, and footer Licensing/")
    print("Copyright body text (color only, not bold).")
    print(f"\nIf anything looks wrong, restore with:\n  cp {backup_path} {SCRIPT_PATH}")
    print("\nNext: run 'python3 Claude_mohangraphy.py' to deploy, then check.")
    print("This closes out Phase E.")


if __name__ == "__main__":
    main()
