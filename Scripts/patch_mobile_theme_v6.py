#!/usr/bin/env python3
"""
patch_mobile_theme_v6.py
---------------------------
Three fixes, based on user feedback on the live mobile site:

1. Category card names/counts (.cat-card-name, .cat-card-count) sit
   directly on top of a photo, behind a fixed dark gradient scrim —
   same as desktop. These should NOT follow the light-theme text
   color; they're forced back to fixed white/near-white, matching
   how desktop already renders them, since the underlying photo's
   brightness has nothing to do with the site's color theme.

2. Sub-tile rows (place names, e.g. under a category) turned out to
   be a different bug: .sub-tile / .sub-tile--city have their OWN
   hardcoded near-black backgrounds (#111, #0e0e0e, etc.), same bug
   class as the header/footer/menu fixed earlier. The text itself
   was already correctly darkened by the earlier contrast fix — it
   just had nowhere visible to sit. Fixed by theming those
   backgrounds with the existing --mid/--dark variables.

3. .bc-current (the active category name in the breadcrumb, e.g.
   "LANDSCAPE" next to "HOME") gets a font-weight boost, matching
   the other bold requests.

Run once, locally, AFTER patch_mobile_theme_v5.py:
    python3 patch_mobile_theme_v6.py
"""

import os
import shutil
import datetime

SCRIPT_PATH = "/Users/ncm/Pictures/Mohangraphy/Scripts/Claude_mohangraphy.py"

ANCHOR = "    color: rgba(194,125,95,0.85);\n  }\n}\n"

ADDITION = """
@media (max-width: 768px) {
  /* Text overlaid directly on photos stays fixed white, like desktop,
     since the underlying image brightness has nothing to do with theme */
  .cat-card-name { color: #fff; }
  .cat-card-count { color: rgba(255,255,255,0.6); }

  /* Breadcrumb current category — bolder */
  .bc-current { font-weight: 700; }

  /* Sub-tile rows (place names) sit on their own hardcoded dark panels —
     theme those backgrounds so the already-correct text becomes visible */
  .sub-tile { background: var(--mid); }
  .sub-tile:hover, .sub-tile:active { background: var(--dark); }
  .sub-tile--city { background: var(--dark); }
  .sub-tile--city:hover, .sub-tile--city:active { background: var(--mid); }
  .sub-tile-thumb-placeholder { background: var(--mid); }
  .cat-card { background: var(--mid); }
  .cat-card-placeholder { background: linear-gradient(135deg, var(--mid) 0%, var(--dark) 100%); }
}
"""


def main():
    if not os.path.exists(SCRIPT_PATH):
        print(f"ERROR: could not find {SCRIPT_PATH}")
        return

    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        source = f.read()

    if ".cat-card-name { color: #fff; }" in source:
        print("This file already looks patched. Stopping — nothing changed.")
        return

    if ANCHOR not in source:
        print("ERROR: could not find the expected anchor from patch_mobile_theme_v5.py.")
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
    print("Fixed: category card overlay text (fixed white), sub-tile row")
    print("backgrounds (place names now visible), bolded breadcrumb category name.")
    print(f"\nIf anything looks wrong, restore with:\n  cp {backup_path} {SCRIPT_PATH}")
    print("\nNext: run 'python3 Claude_mohangraphy.py' to deploy, then check")
    print("Collections > Landscape (card names + breadcrumb) and the place list.")


if __name__ == "__main__":
    main()
