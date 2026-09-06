#!/usr/bin/env python3
"""
patch_footer_subheading_fix.py
-----------------------------------
Quick fix: .footer-section-body strong (the "Copyright Notice",
"Watermarks & Metadata", "Downloads", "Privacy", "Governing Law"
subheadings under Licensing/Copyright & Legal) used var(--ta55) at
55% brightness — but an earlier fix brightened the surrounding body
text to var(--ta7) (70%), leaving the "bold" subheadings actually
DIMMER than the text below them. Fixed by making the subheading
fully solid (var(--text)) and slightly bolder.

Run once, locally:
    python3 patch_footer_subheading_fix.py
"""

import os
import shutil
import datetime

SCRIPT_PATH = "/Users/ncm/Pictures/Mohangraphy/Scripts/Claude_mohangraphy.py"

OLD = ".footer-section-body strong { color: var(--ta55); font-weight: 600; }"
NEW = ".footer-section-body strong { color: var(--text); font-weight: 700; }"


def main():
    if not os.path.exists(SCRIPT_PATH):
        print(f"ERROR: could not find {SCRIPT_PATH}")
        return

    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        source = f.read()

    if NEW in source:
        print("This file already looks patched. Stopping — nothing changed.")
        return

    if OLD not in source:
        print("ERROR: could not find the expected rule.")
        print("Stopping without changing anything.")
        return

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = SCRIPT_PATH + f".bak_{ts}"
    shutil.copyfile(SCRIPT_PATH, backup_path)
    print(f"Backup written: {backup_path}")

    new_source = source.replace(OLD, NEW, 1)

    with open(SCRIPT_PATH, "w", encoding="utf-8") as f:
        f.write(new_source)

    print(f"\nDone. {SCRIPT_PATH} updated. Footer subheadings are now fully")
    print("solid and clearly bolder than the body text under them.")
    print(f"\nIf anything looks wrong, restore with:\n  cp {backup_path} {SCRIPT_PATH}")
    print("\nNext: run 'python3 Claude_mohangraphy.py' to deploy.")


if __name__ == "__main__":
    main()
