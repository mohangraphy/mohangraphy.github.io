#!/usr/bin/env python3
"""
patch_mobile_theme_v10.py
---------------------------
Fixes the slideshow caption position on mobile.

Root cause: #ss-img-wrap uses flex:1 to fill all space above the fixed
52px caption bar, then centers the photo inside that space via
object-fit:contain. On a tall phone screen, a landscape photo only
fills part of that tall reserved area, leaving a large empty gap before
the caption bar shows up at the very bottom of the screen — matching
what the user reported.

Fix (mobile only): instead of the image area stretching to fill all
available space, it now sizes to the actual photo, and the whole group
(photo + caption bar) is vertically centered as one block — so the
caption always sits directly below the photo, with any leftover space
split evenly above and below, matching how it already looks on desktop.

Run once, locally, AFTER patch_mobile_theme_v9.py:
    python3 patch_mobile_theme_v10.py
"""

import os
import shutil
import datetime

SCRIPT_PATH = "/Users/ncm/Pictures/Mohangraphy/Scripts/Claude_mohangraphy.py"

CSS_ANCHOR = "  .img-modal-close { background: rgba(244,241,234,0.75); }\n}\n"

CSS_ADDITION = """
@media (max-width: 768px) {
  #ss-overlay { justify-content: center; }
  #ss-img-wrap { flex: 0 1 auto; }
  #ss-img { max-width: 100vw; max-height: calc(100dvh - 52px); }
}
"""


def main():
    if not os.path.exists(SCRIPT_PATH):
        print(f"ERROR: could not find {SCRIPT_PATH}")
        return

    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        source = f.read()

    if "#ss-overlay { justify-content: center; }" in source:
        print("This file already looks patched. Stopping — nothing changed.")
        return

    if CSS_ANCHOR not in source:
        print("ERROR: could not find the expected anchor from patch_mobile_theme_v9.py.")
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
    print("Fixed: slideshow caption now sits directly below the photo on mobile,")
    print("instead of pinned to the bottom of the screen.")
    print(f"\nIf anything looks wrong, restore with:\n  cp {backup_path} {SCRIPT_PATH}")
    print("\nNext: run 'python3 Claude_mohangraphy.py' to deploy, then check the")
    print("slideshow caption position on your phone. The photo-transition bleed")
    print("issue is intentionally NOT included here — that needs a bigger, more")
    print("careful fix in a separate session.")


if __name__ == "__main__":
    main()
