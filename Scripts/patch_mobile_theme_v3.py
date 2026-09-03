#!/usr/bin/env python3
"""
patch_mobile_theme_v3.py
---------------------------
Comprehensive contrast fix, following user feedback on real screenshots.

Two problems fixed:

1. HEADER BAR: `header { background: rgba(8,8,8,0.97); }` is hardcoded
   near-black, completely independent of --dark. This is why the top
   bar (and the hamburger icon sitting on it) stayed black on every
   page after the mobile theme patch. Fixed with a mobile-only override
   to a light equivalent.

2. WASHED-OUT TEXT: Muted/secondary text throughout the site uses
   partial-opacity text like rgba(var(--text-rgb), 0.4). Those opacity
   values were tuned for WHITE fading into a BLACK background — e.g.
   70% white on near-black reads as a clear light gray. The exact same
   70% opacity applied to DARK text fading into a LIGHT background
   produces a much weaker result (the math isn't symmetric), which is
   why menu items, subtitles, and captions looked "too light" in the
   screenshots.

   Fix: every distinct opacity value used site-wide (33 of them) is
   converted into its own CSS variable — e.g. rgba(var(--text-rgb),0.4)
   becomes var(--ta4) — with the ORIGINAL value preserved as the
   desktop default (zero visual change on desktop). Then, only inside
   the mobile media query, each variable is redefined with a boosted
   opacity (roughly: boosted = original + 50% of the remaining
   distance to fully solid), so faint dark-on-light text becomes
   properly legible while still preserving the original visual
   hierarchy (very faint stays fainter than solid, just not
   illegibly so).

A timestamped backup is written before any edit. If the expected code
isn't found exactly, the script stops without changing anything.

Run once, locally, AFTER patch_mobile_theme.py and patch_mobile_theme_v2.py:
    python3 patch_mobile_theme_v3.py
"""

import os
import shutil
import datetime

SCRIPT_PATH = "/Users/ncm/Pictures/Mohangraphy/Scripts/Claude_mohangraphy.py"

# desktop_alpha -> boosted_mobile_alpha (boosted = a + 0.5*(1-a), pre-computed)
ALPHA_MAP = {
    "0.3": "0.65", "0.5": "0.75", "0.4": "0.70", "0.6": "0.80",
    "0.55": "0.78", "0.35": "0.68", "0.25": "0.63", "0.15": "0.58",
    "0.1": "0.55", "0.05": "0.53", "0.12": "0.56", "0.06": "0.53",
    "0.75": "0.88", "0.45": "0.73", "0.9": "0.95", "0.85": "0.93",
    "0.7": "0.85", "0.65": "0.83", "0.2": "0.60", "0.04": "0.52",
    "0.92": "0.96", "0.8": "0.90", "0.28": "0.64", "0.58": "0.79",
    "0.38": "0.69", "0.03": "0.52", "0.82": "0.91", "0.62": "0.81",
    "0.42": "0.71", "0.32": "0.66", "0.18": "0.59", "0.14": "0.57",
    "0.07": "0.54",
}

CSS_START_MARKER = 'css = """'
HEADER_OLD = "background: rgba(8,8,8,0.97);"


def var_name(alpha_key):
    return "--ta" + alpha_key.split(".")[1]


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

    if "--ta3:" in source:
        print("This file already looks patched (found --ta3). Stopping — nothing changed.")
        return

    if "Earthy Editorial" not in source or "rgba(244,241,234,0.97)" not in source:
        print("ERROR: earlier mobile-theme patches don't look like they've been run yet.")
        print("Run patch_mobile_theme.py and patch_mobile_theme_v2.py first.")
        return

    try:
        content_start, content_end = find_css_block(source)
    except ValueError as e:
        print(f"ERROR: {e}")
        return

    css_block = source[content_start:content_end]

    if HEADER_OLD not in css_block:
        print("ERROR: could not find the expected header background rule.")
        print("Stopping without changing anything — the file may differ from what this script expects.")
        return

    # 1. Replace every existing usage with its new variable (BEFORE appending
    #    the alias definitions below, so we don't rewrite our own new code)
    replaced_counts = {}
    for alpha, boosted in ALPHA_MAP.items():
        old_expr = f"rgba(var(--text-rgb),{alpha})"
        count = css_block.count(old_expr)
        if count:
            css_block = css_block.replace(old_expr, f"var({var_name(alpha)})")
            replaced_counts[alpha] = count

    # 2. Append the alias definitions (desktop defaults — identical to the
    #    original expressions, so desktop rendering is unchanged)
    root_lines = "\n".join(
        f"  {var_name(a)}: rgba(var(--text-rgb),{a});" for a in ALPHA_MAP
    )
    alias_block = f"\n\n:root {{\n{root_lines}\n}}\n"

    # 3. Append the mobile-only boosted overrides + header fix
    mobile_lines = "\n".join(
        f"    {var_name(a)}: rgba(var(--text-rgb),{b});" for a, b in ALPHA_MAP.items()
    )
    mobile_block = (
        "\n@media (max-width: 768px) {\n"
        "  :root {\n"
        f"{mobile_lines}\n"
        "  }\n"
        "  header { background: rgba(244,241,234,0.97); }\n"
        "}\n"
    )

    css_block = css_block + alias_block + mobile_block

    new_source = source[:content_start] + css_block + source[content_end:]

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = SCRIPT_PATH + f".bak_{ts}"
    shutil.copyfile(SCRIPT_PATH, backup_path)
    print(f"Backup written: {backup_path}")

    with open(SCRIPT_PATH, "w", encoding="utf-8") as f:
        f.write(new_source)

    total = sum(replaced_counts.values())
    print(f"\nDone. {SCRIPT_PATH} updated.")
    print(f"  Converted {total} muted-text occurrences across {len(replaced_counts)} opacity levels into variables.")
    print("  Fixed header bar background (was hardcoded near-black).")
    print("  Desktop rendering is unchanged; mobile text is now boosted for contrast.")
    print(f"\nIf anything looks wrong, restore with:\n  cp {backup_path} {SCRIPT_PATH}")
    print("\nNext: run 'python3 Claude_mohangraphy.py' to deploy, then re-check")
    print("the landing page, menu, and Travel Stories page on your phone.")


if __name__ == "__main__":
    main()
