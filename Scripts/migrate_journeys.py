#!/usr/bin/env python3
"""
migrate_journeys.py
--------------------
One-time migration: extracts the JOURNEYS_INDIA and JOURNEYS_WORLD JS arrays
out of Claude_mohangraphy.py and writes them to journeys_data.json
(same folder as photo_metadata.json).

Run once, locally on your Mac:
    python3 migrate_journeys.py

It does NOT modify Claude_mohangraphy.py — that's a separate patch (Part 2).
Safe to re-run; it will just overwrite journeys_data.json with a fresh extract.
"""

import re
import json
import os

# ── Adjust these two paths if your layout differs ───────────────────────────
SCRIPT_PATH = "/Users/ncm/Pictures/Mohangraphy/Scripts/Claude_mohangraphy.py"
OUTPUT_PATH = "/Users/ncm/Pictures/Mohangraphy/Scripts/journeys_data.json"
# (journeys_data.json will live next to photo_metadata.json — adjust OUTPUT_PATH
#  if photo_metadata.json is in a different folder than the script)


def extract_array(source_text, var_name):
    """
    Pulls the JS array literal assigned to `var_name` (e.g. 'JOURNEYS_INDIA')
    out of the source text, using bracket-matching (not a naive regex),
    so it's robust to nested braces inside each entry.
    """
    marker = f"var {var_name} = ["
    start = source_text.find(marker)
    if start == -1:
        raise ValueError(f"Could not find '{marker}' in source file")

    # Position of the opening '[' 
    bracket_start = start + len(marker) - 1
    depth = 0
    i = bracket_start
    for i in range(bracket_start, len(source_text)):
        ch = source_text[i]
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
            if depth == 0:
                break
    else:
        raise ValueError(f"Could not find matching ']' for {var_name}")

    array_literal = source_text[bracket_start:i + 1]
    return array_literal


def js_array_to_python(array_literal):
    """
    Converts a JS array-of-object-literals string into Python data.
    Handles the specific style used in this file:
      {name:'X',state:'Y',lat:1.23,lng:4.56,uploaded:false}
    i.e. unquoted keys, single-quoted string values, bare true/false.
    """
    text = array_literal

    # Quote bare object keys:  name:  ->  "name":
    text = re.sub(r'([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:', r'\1"\2":', text)

    # Convert single-quoted strings to double-quoted (escape any embedded ")
    def sq_to_dq(m):
        inner = m.group(1)
        inner = inner.replace('\\', '\\\\').replace('"', '\\"')
        return '"' + inner + '"'
    text = re.sub(r"'((?:[^'\\]|\\.)*)'", sq_to_dq, text)

    # JS true/false -> JSON true/false (already valid JSON keywords, no change needed)
    # Remove trailing commas before ] or }
    text = re.sub(r',\s*([\]}])', r'\1', text)

    return json.loads(text)


def main():
    if not os.path.exists(SCRIPT_PATH):
        print(f"ERROR: could not find {SCRIPT_PATH}")
        print("Edit SCRIPT_PATH at the top of this script and re-run.")
        return

    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        source = f.read()

    india_literal = extract_array(source, "JOURNEYS_INDIA")
    world_literal = extract_array(source, "JOURNEYS_WORLD")

    india_data = js_array_to_python(india_literal)
    world_data = js_array_to_python(world_literal)

    print(f"Extracted {len(india_data)} India entries, {len(world_data)} World entries.")

    output = {
        "india": india_data,
        "world": world_data,
    }

    if os.path.exists(OUTPUT_PATH):
        backup_path = OUTPUT_PATH + ".bak"
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            existing = f.read()
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(existing)
        print(f"Existing {OUTPUT_PATH} backed up to {backup_path}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Wrote {OUTPUT_PATH}")
    print("\nSample India entry:", json.dumps(india_data[0], indent=2))
    print("Sample World entry:", json.dumps(world_data[0], indent=2))
    print("\nDone. Nothing in Claude_mohangraphy.py was modified.")
    print("Next: Part 2 will replace the hardcoded arrays with a fetch() call.")


if __name__ == "__main__":
    main()
