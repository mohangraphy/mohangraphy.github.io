#!/usr/bin/env python3
"""
patch_mobile_theme_v7.py
---------------------------
Phase 1 of the consistency pass, based on user feedback.

Five elements share the identical pattern: `color: var(--gold); opacity: .7`
(or .8), with no font-weight set. That dimmed opacity was tuned to read
well against the old dark background — against the new light background
it renders as washed-out pastel, which is why these all looked "too
light" in the screenshots:

  - .mob-menu-cta          "GET IN TOUCH" button (mobile menu)
  - .info-page-subtitle    subtitle under About Me / Contact page titles
  - .journeys-header-sub   subtitle under "FOOTPRINTS"
  - .stories-header-sub    subtitle under "TRAVEL STORIES"
  - .subscribe-eyebrow     "JOIN THE COMMUNITY" eyebrow text

Fix: mobile-only override — full opacity, bold weight, slightly larger
text. Desktop is untouched.

Run once, locally, AFTER patch_mobile_theme_v6.py:
    python3 patch_mobile_theme_v7.py
"""

import os
import shutil
import datetime

SCRIPT_PATH = "/Users/ncm/Pictures/Mohangraphy/Scripts/Claude_mohangraphy.py"

ANCHOR = "  .cat-card-placeholder { background: linear-gradient(135deg, var(--mid) 0%, var(--dark) 100%); }\n}\n"

ADDITION = """
@media (max-width: 768px) {
  .mob-menu-cta,
  .info-page-subtitle,
  .journeys-header-sub,
  .stories-header-sub,
  .subscribe-eyebrow {
    font-weight: 700;
    opacity: 1;
  }
  .info-page-subtitle,
  .journeys-header-sub,
  .stories-header-sub,
  .subscribe-eyebrow {
    font-size: 10px;
  }
}
"""


def main():
    if not os.path.exists(SCRIPT_PATH):
        print(f"ERROR: could not find {SCRIPT_PATH}")
        return

    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        source = f.read()

    if ".subscribe-eyebrow {\n    font-weight: 700;" in source:
        print("This file already looks patched. Stopping — nothing changed.")
        return

    if ANCHOR not in source:
        print("ERROR: could not find the expected anchor from patch_mobile_theme_v6.py.")
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
    print("Bolded + brightened: Get in Touch button, About Me subtitle,")
    print("Footprints subtitle, Travel Stories subtitle, Join the Community eyebrow.")
    print(f"\nIf anything looks wrong, restore with:\n  cp {backup_path} {SCRIPT_PATH}")
    print("\nNext: run 'python3 Claude_mohangraphy.py' to deploy, then check")
    print("those five spots. Phases 2 (nav cleanup) and 3 (heading alignment)")
    print("are separate — let's confirm this looks right first.")


if __name__ == "__main__":
    main()
