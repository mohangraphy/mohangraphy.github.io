#!/usr/bin/env python3
"""
patch_mobile_theme_v9.py
---------------------------
Final round for the black-background and transition issues.

1. #img-modal — a SEPARATE full-screen photo viewer (opened by clicking
   a photo) from the slideshow (#ss-overlay) fixed earlier. Same
   hardcoded-black bug pattern, never touched until now. Adds mobile
   overrides for the modal background and its nav/close buttons.

2. Slideshow transition fix, round 2: the previous fix (300ms -> 500ms)
   matched the CSS fade duration, but didn't guarantee the new photo was
   actually DECODED and ready to paint before the fade-in started — on
   some mobile browsers this still let a stale frame show briefly,
   especially with differently-shaped photos. Fixed by waiting for
   img.decode() to resolve before removing the fade class, so the new
   photo is guaranteed fully ready before it's revealed.

Run once, locally, AFTER patch_mobile_theme_v8.py:
    python3 patch_mobile_theme_v9.py
"""

import os
import shutil
import datetime

SCRIPT_PATH = "/Users/ncm/Pictures/Mohangraphy/Scripts/Claude_mohangraphy.py"

CSS_ANCHOR = "  #ss-pause-lbl { background: rgba(244,241,234,0.85); }\n}\n"

CSS_ADDITION = """
@media (max-width: 768px) {
  #img-modal { background: var(--dark); }
  .img-modal-nav { background: rgba(244,241,234,0.55); }
  .img-modal-nav:hover { background: rgba(244,241,234,0.8); }
  .img-modal-close { background: rgba(244,241,234,0.75); }
}
"""

OLD_REVEAL = """  _ssFade = setTimeout(function(){
    var img2 = document.getElementById('ss-img');
    if(!img2) return;
    if(entry.thumb) img2.src = entry.thumb;
    img2.classList.remove('ss-fade');
    if(entry.full && entry.full !== entry.thumb){"""
NEW_REVEAL = """  _ssFade = setTimeout(function(){
    var img2 = document.getElementById('ss-img');
    if(!img2) return;
    var reveal = function(){ var i4 = document.getElementById('ss-img'); if(i4) i4.classList.remove('ss-fade'); };
    if(entry.thumb) img2.src = entry.thumb;
    if(img2.decode){ img2.decode().then(reveal).catch(reveal); } else { reveal(); }
    if(entry.full && entry.full !== entry.thumb){"""


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

    if "#img-modal { background: var(--dark); }" in source:
        print("This file already looks patched. Stopping — nothing changed.")
        return

    try:
        new_source = source
        new_source = patch(new_source, CSS_ANCHOR, CSS_ANCHOR + CSS_ADDITION, "CSS anchor (v8 block)")
        new_source = patch(new_source, OLD_REVEAL, NEW_REVEAL, "slideshow reveal logic")
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
    print("Fixed: img-modal (click-a-photo viewer) background on mobile,")
    print("and the slideshow now waits for full image decode before revealing.")
    print(f"\nIf anything looks wrong, restore with:\n  cp {backup_path} {SCRIPT_PATH}")
    print("\nNext: run 'python3 Claude_mohangraphy.py' to deploy, then test both:")
    print("clicking a photo directly, and a slideshow transition between a")
    print("4x3 and 16x9 photo.")


if __name__ == "__main__":
    main()
