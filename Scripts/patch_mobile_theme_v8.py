#!/usr/bin/env python3
"""
patch_mobile_theme_v8.py
---------------------------
Phase B: slideshow/lightbox fixes, based on user feedback.

CSS (mobile only) — same recurring bug pattern as header/footer/menu:
these five elements have their OWN hardcoded black/near-black
backgrounds, independent of the theme. Their TEXT already correctly
uses the boosted --taXX variables from earlier patches, so fixing just
the backgrounds makes everything visible automatically:
  - #ss-overlay   (full-screen slideshow background)
  - #ss-bar       (bottom bar holding counter/caption/hint)
  - .ss-nav-btn   (prev/next circular buttons)
  - #ss-close     (close button)
  - #ss-pause-lbl (the "PAUSED" pill shown over the photo)

JS (both desktop and mobile — real logic bugs, not styling):
  1. Fade transition timing: the old photo fades out over 500ms
     (transition: opacity 0.5s) but the code swapped to the new photo's
     source after only 300ms, interrupting the fade-out mid-way. Fixed
     by waiting the full 500ms before swapping, so one photo always
     finishes fading out before the next fades in.
  2. Auto-close at the end: the slideshow scheduler simply stopped
     advancing on the last photo instead of closing. Fixed to close
     the slideshow after the last photo's normal display duration.

Run once, locally, AFTER patch_mobile_theme_v7.py:
    python3 patch_mobile_theme_v8.py
"""

import os
import shutil
import datetime

SCRIPT_PATH = "/Users/ncm/Pictures/Mohangraphy/Scripts/Claude_mohangraphy.py"

CSS_ANCHOR = "    font-size: 10px;\n  }\n}\n"

CSS_ADDITION = """
@media (max-width: 768px) {
  #ss-overlay { background: var(--dark); }
  #ss-bar { background: var(--mid); }
  .ss-nav-btn { background: rgba(244,241,234,0.55); }
  .ss-nav-btn:hover { background: rgba(244,241,234,0.8); }
  #ss-close { background: rgba(244,241,234,0.75); }
  #ss-pause-lbl { background: rgba(244,241,234,0.85); }
}
"""

OLD_FADE_TIMING = """      hi.src = entry.full;
    }
  }, 300);"""
NEW_FADE_TIMING = """      hi.src = entry.full;
    }
  }, 500);"""

OLD_SCHEDULE = """function _ssSchedule(){
  clearTimeout(_ssTimer);
  if(!_ssPaused && _ssIdx < _ssPhotos.length - 1){
    _ssTimer = setTimeout(function(){ _ssShow(_ssIdx + 1); _ssSchedule(); }, _ssDur);
  }
}"""
NEW_SCHEDULE = """function _ssSchedule(){
  clearTimeout(_ssTimer);
  if(_ssPaused) return;
  if(_ssIdx < _ssPhotos.length - 1){
    _ssTimer = setTimeout(function(){ _ssShow(_ssIdx + 1); _ssSchedule(); }, _ssDur);
  } else {
    _ssTimer = setTimeout(function(){ ssClose(); }, _ssDur);
  }
}"""


def patch(source, old, new, label):
    if old not in source:
        raise ValueError(f"Could not find expected block for: {label}")
    return source.replace(old, new, 1)


def main():
    if not os.path.exists(SCRIPT_PATH):
        print(f"ERROR: could not find {SCRIPT_PATH}")
        return

    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        source = f.read()

    if "#ss-overlay { background: var(--dark); }" in source:
        print("This file already looks patched. Stopping — nothing changed.")
        return

    try:
        new_source = source
        new_source = patch(new_source, CSS_ANCHOR, CSS_ANCHOR + CSS_ADDITION, "CSS anchor (v7 block)")
        new_source = patch(new_source, OLD_FADE_TIMING, NEW_FADE_TIMING, "fade transition timing")
        new_source = patch(new_source, OLD_SCHEDULE, NEW_SCHEDULE, "auto-close scheduler")
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
    print("Fixed: slideshow background/buttons on mobile, fade transition")
    print("timing (bleed-through), and auto-close at the end of the slideshow.")
    print(f"\nIf anything looks wrong, restore with:\n  cp {backup_path} {SCRIPT_PATH}")
    print("\nNext: run 'python3 Claude_mohangraphy.py' to deploy, then run a")
    print("slideshow through to the end on both mobile and laptop.")


if __name__ == "__main__":
    main()
