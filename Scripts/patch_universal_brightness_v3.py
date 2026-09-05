#!/usr/bin/env python3
"""
patch_universal_brightness_v3.py
------------------------------------
Final brightness pass, based on user feedback on live screenshots.
Blog/story pages use a separate template from gallery pages, so these
elements were never touched by earlier passes. All color-only changes
(no font-weight changes), universal (both desktop and mobile).

  .story-post-back    var(--ta28) -> var(--ta75)  (now matches .bc-back
                       used on Collections pages, per user's explicit
                       "should be the same everywhere")
  .story-post-dates   var(--ta32) -> var(--ta6)
  .story-cta-btn-ghost text var(--ta55)->var(--ta7), border var(--ta14)->var(--ta35)
  .story-end-cat      text var(--ta45)->var(--ta7), border var(--ta1)->var(--ta3)
  .story-action-cat   text var(--ta5)->var(--ta7),  border var(--ta1)->var(--ta3)
  .story-comment-date var(--ta25) -> var(--ta6)
  .blog-row-summary   var(--ta38) -> var(--ta7)

Run once, locally:
    python3 patch_universal_brightness_v3.py
"""

import os
import shutil
import datetime

SCRIPT_PATH = "/Users/ncm/Pictures/Mohangraphy/Scripts/Claude_mohangraphy.py"

REPLACEMENTS = [
    ("color: var(--ta28); cursor: pointer;", "color: var(--ta75); cursor: pointer;", "story-post-back"),
    ("color: var(--ta32); margin-bottom: clamp(24px,4vw,40px);", "color: var(--ta6); margin-bottom: clamp(24px,4vw,40px);", "story-post-dates"),
    ("border: 1px solid var(--ta14);\n  color: var(--ta55); padding: 0 20px; height: 42px;",
     "border: 1px solid var(--ta35);\n  color: var(--ta7); padding: 0 20px; height: 42px;", "story-cta-btn-ghost"),
    ("border: 1px solid var(--ta1);\n  color: var(--ta45); padding: 0 14px; height: 34px;",
     "border: 1px solid var(--ta3);\n  color: var(--ta7); padding: 0 14px; height: 34px;", "story-end-cat"),
    ("border: 1px solid var(--ta1);\n  color: var(--ta5); padding: 0 14px; height: 34px;",
     "border: 1px solid var(--ta3);\n  color: var(--ta7); padding: 0 14px; height: 34px;", "story-action-cat"),
    ("font-size: 9px; letter-spacing: 1px;\n  color: var(--ta25);\n}\n.story-comment-text",
     "font-size: 9px; letter-spacing: 1px;\n  color: var(--ta6);\n}\n.story-comment-text", "story-comment-date"),
    ("color: var(--ta38); margin-top: 5px;", "color: var(--ta7); margin-top: 5px;", "blog-row-summary"),
]


def main():
    if not os.path.exists(SCRIPT_PATH):
        print(f"ERROR: could not find {SCRIPT_PATH}")
        return

    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        source = f.read()

    if "color: var(--ta75); cursor: pointer;" in source:
        print("This file already looks patched. Stopping — nothing changed.")
        return

    for old, new, label in REPLACEMENTS:
        if old not in source:
            print(f"ERROR: could not find expected block for: {label}")
            print("Stopping without changing anything.")
            return

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = SCRIPT_PATH + f".bak_{ts}"
    shutil.copyfile(SCRIPT_PATH, backup_path)
    print(f"Backup written: {backup_path}")

    for old, new, label in REPLACEMENTS:
        source = source.replace(old, new, 1)

    with open(SCRIPT_PATH, "w", encoding="utf-8") as f:
        f.write(source)

    print(f"\nDone. {SCRIPT_PATH} updated. Brightened 7 blog/story-page elements.")
    print(f"\nIf anything looks wrong, restore with:\n  cp {backup_path} {SCRIPT_PATH}")
    print("\nNext: run 'python3 Claude_mohangraphy.py' to deploy.")


if __name__ == "__main__":
    main()
