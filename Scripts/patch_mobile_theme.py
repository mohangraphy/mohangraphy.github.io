#!/usr/bin/env python3
"""
patch_mobile_theme.py
------------------------
Adds a mobile-only ("Earthy Editorial") color scheme to Claude_mohangraphy.py,
activated only on screens 768px wide or narrower (phones / small tablets).
Desktop is completely unaffected.

What it does, all scoped to the CSS block (the `css` variable) only:
  1. Adds two new CSS variables to :root — --text and --text-rgb — and
     points body's text color at --text instead of the hardcoded #fff.
     (This doesn't change how anything looks; #fff and var(--text) render
     identically until --text is overridden.)
  2. Replaces all other hardcoded "color: #fff" / "color:#fff" and
     "rgba(255,255,255,alpha)" occurrences in the stylesheet with the new
     variables, so muted/secondary text (borders, dividers, translucent
     labels) also responds to the theme change. Purely mechanical —
     same colors render until overridden.
  3. Adds a `@media (max-width: 768px) { :root { ... } }` block at the
     end of the stylesheet that overrides --dark (background), --gold /
     --gold2 (accent), --text and --text-rgb with the Earthy Editorial
     palette (Warm Sand background, Deep Espresso Brown text, Terracotta
     accent). Because --dark and --gold are already used as variables
     throughout the stylesheet (backgrounds, accents, borders), this one
     override cascades everywhere automatically.

A timestamped backup is written before any edit. If the expected code
isn't found exactly, the script stops without changing anything.

Run once, locally:
    python3 patch_mobile_theme.py
"""

import os
import shutil
import datetime

SCRIPT_PATH = "/Users/ncm/Pictures/Mohangraphy/Scripts/Claude_mohangraphy.py"

CSS_START_MARKER = 'css = """'
OLD_ROOT_BLOCK = """  --dark:  #080808;
  --mid:   #161616;
  --hdr:   80px;
}"""
NEW_ROOT_BLOCK = """  --dark:  #080808;
  --mid:   #161616;
  --hdr:   80px;
  --text:      #fff;
  --text-rgb:  255,255,255;
}"""

MOBILE_MEDIA_BLOCK = """

/* ── MOBILE THEME — Earthy Editorial (phones / small screens only) ── */
@media (max-width: 768px) {
  :root {
    --dark:      #F4F1EA;
    --mid:       #EAE5D9;
    --gold:      #C27D5F;
    --gold2:     #D9A184;
    --text:      #2B1E13;
    --text-rgb:  43,30,19;
  }
}
"""


def find_css_block(source):
    start_idx = source.find(CSS_START_MARKER)
    if start_idx == -1:
        raise ValueError(f"Could not find '{CSS_START_MARKER}' marker")
    content_start = start_idx + len(CSS_START_MARKER)
    end_idx = source.find('"""', content_start)
    if end_idx == -1:
        raise ValueError("Could not find closing triple-quote for css block")
    return content_start, end_idx


def main():
    if not os.path.exists(SCRIPT_PATH):
        print(f"ERROR: could not find {SCRIPT_PATH}")
        return

    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        source = f.read()

    if "Earthy Editorial" in source:
        print("This file already looks patched (found 'Earthy Editorial'). Stopping — nothing changed.")
        return

    try:
        content_start, content_end = find_css_block(source)
    except ValueError as e:
        print(f"ERROR: {e}")
        return

    css_block = source[content_start:content_end]

    if OLD_ROOT_BLOCK not in css_block:
        print("ERROR: could not find the expected :root block inside the css section.")
        print("Stopping without changing anything — the file may differ from what this script expects.")
        return

    # 1. Add --text / --text-rgb variables
    new_css_block = css_block.replace(OLD_ROOT_BLOCK, NEW_ROOT_BLOCK, 1)

    # 2. Point hardcoded white text/opacity at the new variables
    n1 = new_css_block.count("color: #fff")
    n2 = new_css_block.count("color:#fff")
    n3 = new_css_block.count("rgba(255,255,255,")
    new_css_block = new_css_block.replace("color: #fff", "color: var(--text)")
    new_css_block = new_css_block.replace("color:#fff", "color:var(--text)")
    new_css_block = new_css_block.replace("rgba(255,255,255,", "rgba(var(--text-rgb),")

    # 3. Append the mobile media query at the end of the stylesheet
    new_css_block = new_css_block + MOBILE_MEDIA_BLOCK

    new_source = source[:content_start] + new_css_block + source[content_end:]

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = SCRIPT_PATH + f".bak_{ts}"
    shutil.copyfile(SCRIPT_PATH, backup_path)
    print(f"Backup written: {backup_path}")

    with open(SCRIPT_PATH, "w", encoding="utf-8") as f:
        f.write(new_source)

    print(f"\nDone. {SCRIPT_PATH} updated.")
    print(f"  Replaced {n1} × 'color: #fff', {n2} × 'color:#fff', {n3} × 'rgba(255,255,255,' with variables.")
    print("  Added @media (max-width: 768px) block with the Earthy Editorial palette")
    print("  (Terracotta accent). Desktop styles are untouched.")
    print(f"\nIf anything looks wrong, restore with:\n  cp {backup_path} {SCRIPT_PATH}")
    print("\nNext: run the site build (python3 Claude_mohangraphy.py) to deploy,")
    print("then check the site on a phone (or shrink your browser window below")
    print("768px wide) to see the new mobile theme.")


if __name__ == "__main__":
    main()
