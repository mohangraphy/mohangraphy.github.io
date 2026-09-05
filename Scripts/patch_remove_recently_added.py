#!/usr/bin/env python3
"""
patch_remove_recently_added.py
-----------------------------------
Batch 2, based on user feedback.

1. Removes the "Recently Added" wide card that appears as the 5th tile
   in the landing page's Collections grid (the one showing "Photos
   added in the last 14 days").

2. On every blog post page, removes the whole "For More Photos"
   section (its title + the "[Place] Photos"/"Browse Collections"
   button + the "Recently Added" button), while KEEPING "Explore
   Collections" and its four category buttons right below it.

Run once, locally:
    python3 patch_remove_recently_added.py
"""

import os
import shutil
import datetime

SCRIPT_PATH = "/Users/ncm/Pictures/Mohangraphy/Scripts/Claude_mohangraphy.py"

# ── 1. Landing page "Recently Added" wide card ───────────────────────────
OLD_CARD = """        # 5th card — Recently Added
        '\\n<div class="cat-card cat-card-wide" onclick="showNewPhotos()" role="button" tabindex="0"'
        ' style="grid-column:1/-1;aspect-ratio:auto;min-height:120px;">'
        '<div class="cat-card-bar" style="position:relative;padding:clamp(16px,3vw,28px) clamp(16px,4vw,44px);'
        'background:linear-gradient(135deg,rgba(201,169,110,0.12) 0%,rgba(201,169,110,0.04) 100%);">'
        '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">'
        '<div>'
        '<div class="cat-card-name" style="color:var(--gold);">Recently Added</div>'
        '<div class="cat-card-count" id="ra-card-count">Photos added in the last 14 days</div>'
        '</div>'
        '<div style="font-size:28px;color:var(--gold);opacity:0.5;">&#10022;</div>'
        '</div>'
        '</div>'
        '</div>\\n'
"""

# ── 2. Blog post "For More Photos" section ───────────────────────────────
OLD_DISCOVER = """                  '<div class="story-end-discover-title">For More Photos</div>'
                  '<div class="story-end-gallery-btns">'
                  + ('<button class="story-end-gallery-btn" onclick="showStoryGallery(\\'' + _ea(pid) + '\\',\\'' + _ea(place_tag) + '\\')">'
                     '&#9654;&nbsp; ' + _eh(place_tag) + ' Photos</button>'
                     if place_photos else
                     '<button class="story-end-gallery-btn" onclick="goHome()">'
                     '&#9654;&nbsp; Browse Collections</button>')
                  + '<button class="story-end-gallery-btn-ghost" onclick="showNewPhotos()">'
                    '&#10022;&nbsp; Recently Added</button>'
                  + '</div>'
"""


def main():
    if not os.path.exists(SCRIPT_PATH):
        print(f"ERROR: could not find {SCRIPT_PATH}")
        return

    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        source = f.read()

    if "5th card — Recently Added" not in source and "For More Photos" not in source:
        print("This file already looks patched. Stopping — nothing changed.")
        return

    found_card = OLD_CARD in source
    found_discover = OLD_DISCOVER in source

    if not found_card and not found_discover:
        print("ERROR: could not find either expected block.")
        print("Stopping without changing anything — the file may differ from what this script expects.")
        return

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = SCRIPT_PATH + f".bak_{ts}"
    shutil.copyfile(SCRIPT_PATH, backup_path)
    print(f"Backup written: {backup_path}")

    if found_card:
        source = source.replace(OLD_CARD, "", 1)
        print("Removed: landing page 'Recently Added' wide card.")
    else:
        print("Skipped: landing page card block not found (may already be removed).")

    if found_discover:
        source = source.replace(OLD_DISCOVER, "", 1)
        print("Removed: blog post 'For More Photos' section (kept Explore Collections).")
    else:
        print("Skipped: blog post 'For More Photos' block not found (may already be removed).")

    with open(SCRIPT_PATH, "w", encoding="utf-8") as f:
        f.write(source)

    print(f"\nDone. {SCRIPT_PATH} updated.")
    print(f"\nIf anything looks wrong, restore with:\n  cp {backup_path} {SCRIPT_PATH}")
    print("\nNext: run 'python3 Claude_mohangraphy.py' to deploy, then check the")
    print("landing page and a blog post page.")


if __name__ == "__main__":
    main()
