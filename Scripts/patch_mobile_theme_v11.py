#!/usr/bin/env python3
"""
patch_mobile_theme_v11.py
---------------------------
One-line fix: .img-modal-panel has its own hardcoded near-black
background (#0e0e0e), completely separate from #img-modal (fixed in
v9). This panel holds both the photo info (counter/title/subtitle) and
the Like/Request Quote actions — the mobile media query that stacks it
below the photo never overrode this background, so it stayed black.

Run once, locally, AFTER patch_mobile_theme_v10.py:
    python3 patch_mobile_theme_v11.py
"""

import os
import shutil
import datetime

SCRIPT_PATH = "/Users/ncm/Pictures/Mohangraphy/Scripts/Claude_mohangraphy.py"

CSS_ANCHOR = "  #ss-img { max-width: 100vw; max-height: calc(100dvh - 52px); }\n}\n"

CSS_ADDITION = """
@media (max-width: 768px) {
  .img-modal-panel { background: var(--mid); }
}
"""


def main():
    if not os.path.exists(SCRIPT_PATH):
        print(f"ERROR: could not find {SCRIPT_PATH}")
        return

    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        source = f.read()

    if ".img-modal-panel { background: var(--mid); }" in source:
        print("This file already looks patched. Stopping — nothing changed.")
        return

    if CSS_ANCHOR not in source:
        print("ERROR: could not find the expected anchor from patch_mobile_theme_v10.py.")
        print("Make sure that script has been run first. Stopping without changing anything.")
        return

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = SCRIPT_PATH + f".bak_{ts}"
    shutil.copyfile(SCRIPT_PATH, backup_path)
    print(f"Backup written: {backup_path}")

    new_source = source.replace(CSS_ANCHOR, CSS_ANCHOR + CSS_ADDITION, 1)

    with open(SCRIPT_PATH, "w", encoding="utf-8") as f:
        f.write(new_source)

    print(f"\nDone. {SCRIPT_PATH} updated.")
    print("Fixed: img-modal-panel (info + Like/Request Quote) background on mobile.")
    print(f"\nIf anything looks wrong, restore with:\n  cp {backup_path} {SCRIPT_PATH}")
    print("\nNext: run 'python3 Claude_mohangraphy.py' to deploy, then check")
    print("clicking a photo and viewing the Like/Request Quote panel.")


if __name__ == "__main__":
    main()
