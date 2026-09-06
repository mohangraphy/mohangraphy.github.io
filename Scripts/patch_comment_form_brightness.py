#!/usr/bin/env python3
"""
patch_comment_form_brightness.py
-------------------------------------
Final mobile brightness fix, based on user feedback comparing the
blog comment form to the (already-fixed) newsletter form.

1. .story-end-form input/textarea never had an explicit ::placeholder
   rule, so "Your name", "your@email.com", "Share your thoughts..."
   relied on weak browser-default placeholder styling — dim against
   the input's own boosted-fill background. Added an explicit rule.

2. The "Notify me when new photos..." checkbox label used a HARDCODED
   inline style: color:rgba(255,255,255,0.45) — completely bypassing
   the site's theme variable system (it's inline, not in the
   stylesheet), so none of the earlier contrast fixes ever reached it.
   Replaced with var(--ta45), the same properly-boosted variable used
   everywhere else at that opacity level.

Run once, locally:
    python3 patch_comment_form_brightness.py
"""

import os
import shutil
import datetime

SCRIPT_PATH = "/Users/ncm/Pictures/Mohangraphy/Scripts/Claude_mohangraphy.py"

OLD_INPUT_RULE = """.story-end-form input,
.story-end-form textarea {
  width: 100%; background: var(--ta05);
  border: 1px solid rgba(201,169,110,0.15);
  color: var(--text); padding: 10px 14px;
  font-family: 'Montserrat', sans-serif; font-size: 13px;
  outline: none; margin-bottom: 12px;
  transition: border-color .25s; -webkit-appearance: none;
}"""
NEW_INPUT_RULE = """.story-end-form input,
.story-end-form textarea {
  width: 100%; background: var(--ta05);
  border: 1px solid rgba(201,169,110,0.15);
  color: var(--text); padding: 10px 14px;
  font-family: 'Montserrat', sans-serif; font-size: 13px;
  outline: none; margin-bottom: 12px;
  transition: border-color .25s; -webkit-appearance: none;
}
.story-end-form input::placeholder,
.story-end-form textarea::placeholder { color: var(--ta5); }"""

OLD_CHECKBOX_LABEL = "color:rgba(255,255,255,0.45);line-height:1.6;"
NEW_CHECKBOX_LABEL = "color:var(--ta45);line-height:1.6;"


def main():
    if not os.path.exists(SCRIPT_PATH):
        print(f"ERROR: could not find {SCRIPT_PATH}")
        return

    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        source = f.read()

    if "story-end-form input::placeholder" in source:
        print("This file already looks patched. Stopping — nothing changed.")
        return

    if OLD_INPUT_RULE not in source:
        print("ERROR: could not find the expected .story-end-form input rule.")
        print("Stopping without changing anything.")
        return

    if OLD_CHECKBOX_LABEL not in source:
        print("ERROR: could not find the expected checkbox label style.")
        print("Stopping without changing anything.")
        return

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = SCRIPT_PATH + f".bak_{ts}"
    shutil.copyfile(SCRIPT_PATH, backup_path)
    print(f"Backup written: {backup_path}")

    new_source = source.replace(OLD_INPUT_RULE, NEW_INPUT_RULE, 1)
    new_source = new_source.replace(OLD_CHECKBOX_LABEL, NEW_CHECKBOX_LABEL, 1)

    with open(SCRIPT_PATH, "w", encoding="utf-8") as f:
        f.write(new_source)

    print(f"\nDone. {SCRIPT_PATH} updated.")
    print("Brightened: comment form placeholder text, and the 'Notify me' checkbox label.")
    print(f"\nIf anything looks wrong, restore with:\n  cp {backup_path} {SCRIPT_PATH}")
    print("\nNext: run 'python3 Claude_mohangraphy.py' to deploy, then compare")
    print("the comment form to the newsletter form again.")


if __name__ == "__main__":
    main()
