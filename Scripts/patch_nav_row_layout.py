#!/usr/bin/env python3
"""
patch_nav_row_layout.py
--------------------------
Follow-up to patch_nav_cleanup.py (Part C), based on user feedback.

1. Adds a new .page-nav-row CSS class: a flex row with Copy Link on the
   left and the Back button on the right, applied to both platforms.

2. Restructures three places to use this row instead of stacking Copy
   Link below the breadcrumb bar:
     - Category/sub-nav pages (#bc-bar)
     - Gallery pages (#gal-bc-bar)
     - Blog post pages — these had a COMPLETELY SEPARATE back-link
       ("\u2039 Travel Stories", via .story-post-back) that Part C never
       touched since blog posts use a different template. Replaced
       with the same Copy Link + "\u2190 Back" row, and removed the old
       standalone Copy Link button that used to sit further down the
       page (now merged into the top row).

Run once, locally:
    python3 patch_nav_row_layout.py
"""

import os
import shutil
import datetime

SCRIPT_PATH = "/Users/ncm/Pictures/Mohangraphy/Scripts/Claude_mohangraphy.py"

# ── 1. New CSS rule, inserted right after the html{} base rule ──────────
CSS_ANCHOR = "html { scroll-behavior: smooth; font-size: 16px; }\n"
CSS_ADDITION = """.page-nav-row {
  display: flex; justify-content: space-between; align-items: center;
  gap: 10px; flex-wrap: wrap; margin-bottom: 10px;
}
"""

# ── 2a. Sub-nav (category) breadcrumb + copy link ────────────────────────
OLD_A = '\'  <div class="breadcrumb-bar" id="bc-bar"></div>\\n\''
NEW_A = ('\'  <div class="page-nav-row">\\n'
         '    <button class="copy-link-btn" onclick="copyCurrentLink()" style="cursor:pointer;background:none;border:1px solid rgba(255,255,255,0.3);color:rgba(255,255,255,0.7);padding:4px 10px;font-size:10px;letter-spacing:1px;border-radius:3px;" title="Copy link to this page">&#128279; Copy Link</button>\\n'
         '    <div class="breadcrumb-bar" id="bc-bar"></div>\\n'
         '  </div>\\n\'')
OLD_A2 = '        \'  <button class="copy-link-btn" onclick="copyCurrentLink()" style="cursor:pointer;background:none;border:1px solid rgba(255,255,255,0.3);color:rgba(255,255,255,0.7);padding:4px 10px;font-size:10px;letter-spacing:1px;margin:0 0 10px 0;border-radius:3px;" title="Copy link to this page">&#128279; Copy Link</button>\\n\'\n'

# ── 2b. Gallery breadcrumb + copy link ───────────────────────────────────
OLD_B = '\'  <div class="breadcrumb-bar" id="gal-bc-bar"></div>\\n\''
NEW_B = ('\'  <div class="page-nav-row">\\n'
         '    <button class="copy-link-btn" onclick="copyCurrentLink()" style="cursor:pointer;background:none;border:1px solid rgba(255,255,255,0.3);color:rgba(255,255,255,0.7);padding:4px 10px;font-size:10px;letter-spacing:1px;border-radius:3px;" title="Copy link to this gallery">&#128279; Copy Link</button>\\n'
         '    <div class="breadcrumb-bar" id="gal-bc-bar"></div>\\n'
         '  </div>\\n\'')
OLD_B2 = '        \'  <button class="copy-link-btn" onclick="copyCurrentLink()" style="cursor:pointer;background:none;border:1px solid rgba(255,255,255,0.3);color:rgba(255,255,255,0.7);padding:4px 10px;font-size:10px;letter-spacing:1px;margin:0 0 10px 0;border-radius:3px;" title="Copy link to this gallery">&#128279; Copy Link</button>\\n\'\n'

# ── 2c. Blog post header ─────────────────────────────────────────────────
OLD_C = ('\'<button class="story-post-back" onclick="closeStoryPost()">\'\n'
         '                \'\\u2039 Travel Stories</button>\\n\'')
NEW_C = ('\'<div class="page-nav-row">\'\n'
         '                \'<button class="copy-link-btn" onclick="copyCurrentLink()" style="cursor:pointer;background:none;border:1px solid rgba(255,255,255,0.3);color:rgba(255,255,255,0.7);padding:4px 10px;font-size:10px;letter-spacing:1px;border-radius:3px;" title="Copy link to this story">&#128279; Copy Link</button>\'\n'
         '                \'<button class="story-post-back" onclick="closeStoryPost()">&larr; Back</button></div>\\n\'')
OLD_C2 = ('                + \'<button class="copy-link-btn" onclick="copyCurrentLink()" style="cursor:pointer;background:none;border:1px solid rgba(255,255,255,0.3);color:rgba(255,255,255,0.7);padding:4px 10px;font-size:10px;letter-spacing:1px;margin:6px 0;border-radius:3px;" title="Copy link to this story">&#128279; Copy Link</button>\\n\'\n')


def patch(source, old, new, label, required=True):
    count = source.count(old)
    if count == 0:
        if required:
            raise ValueError(f"Could not find expected block for: {label}")
        return source, 0
    return source.replace(old, new, 1), count


def main():
    if not os.path.exists(SCRIPT_PATH):
        print(f"ERROR: could not find {SCRIPT_PATH}")
        return

    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        source = f.read()

    if ".page-nav-row {" in source:
        print("This file already looks patched. Stopping — nothing changed.")
        return

    try:
        new_source = source
        new_source, _ = patch(new_source, CSS_ANCHOR, CSS_ANCHOR + CSS_ADDITION, "CSS anchor")
        new_source, _ = patch(new_source, OLD_A, NEW_A, "sub-nav breadcrumb row")
        new_source, _ = patch(new_source, OLD_A2, "", "sub-nav old copy-link button")
        new_source, _ = patch(new_source, OLD_B, NEW_B, "gallery breadcrumb row")
        new_source, _ = patch(new_source, OLD_B2, "", "gallery old copy-link button")
        new_source, _ = patch(new_source, OLD_C, NEW_C, "blog post header row")
        new_source, _ = patch(new_source, OLD_C2, "", "blog post old copy-link button")
    except ValueError as e:
        print(f"ERROR: {e}")
        print("Stopping without changing anything — the file may differ from what this script expects.")
        return

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = SCRIPT_PATH + f".bak_{ts}"
    shutil.copyfile(SCRIPT_PATH, backup_path)
    print(f"Backup written: {backup_path}")

    with open(SCRIPT_PATH, "w", encoding="utf-8") as f:
        f.write(new_source)

    print(f"\nDone. {SCRIPT_PATH} updated.")
    print("Copy Link + Back are now on one row (Copy Link left, Back right) on:")
    print("  - Category pages, Gallery pages, and Blog post pages")
    print("Blog posts no longer show '\u2039 Travel Stories' — replaced with the same pattern.")
    print(f"\nIf anything looks wrong, restore with:\n  cp {backup_path} {SCRIPT_PATH}")
    print("\nNext: run 'python3 Claude_mohangraphy.py' to deploy, then check all three")
    print("page types. Also worth a hard-refresh test on the Landscape category page")
    print("on mobile to rule out the caching issue mentioned earlier.")


if __name__ == "__main__":
    main()
