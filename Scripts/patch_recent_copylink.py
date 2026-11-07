#!/usr/bin/env python3
"""Recently Added: (1) Copy Link button beside View Slideshow in the page header,
(2) make the copied link (?section=recently-added) actually open the page.
Aborts without changes if anchors are not found. Safe to run once."""
import sys
path = sys.argv[1] if len(sys.argv) > 1 else "/Users/ncm/Pictures/Mohangraphy/Scripts/Claude_mohangraphy.py"
src = open(path, encoding="utf-8").read()
if "Copy link to Recently Added" in src:
    sys.exit("Already patched - nothing to do.")

# 1) header button ---------------------------------------------------------
a = r'''    + '<button class="slideshow-btn" onclick="startSlideshow(\x27gallery-new-photos\x27)">'''
i = src.find(a)
assert i >= 0 and src.count(a) == 1, "slideshow button anchor not found exactly once"
end_marker = "View Slideshow</button>'"
j = src.find(end_marker, i)
assert j >= 0, "end of slideshow button not found"
j_end = j + len(end_marker)
copy_btn = ("""    + '<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">'
    + '<button class="copy-link-btn" onclick="copyCurrentLink()" style="cursor:pointer;background:none;border:1px solid rgba(255,255,255,0.3);color:rgba(255,255,255,0.7);padding:0 14px;height:34px;font-size:10px;letter-spacing:1px;border-radius:3px;" title="Copy link to Recently Added">&#128279; Copy Link</button>'
""")
src = src[:i] + copy_btn + src[i:j_end] + "\n    + '</div>'" + src[j_end:]

# 2) deep link: ?section=recently-added ------------------------------------
b = "    if(val === 'travel-stories'){ showStoriesIndex(); return; }\n"
assert src.count(b) == 1, "deep-link anchor not found exactly once"
src = src.replace(b, b + "    if(val === 'recently-added'){\n"
    "      showNewPhotos();\n"
    "      if(!document.getElementById('gallery-new-photos')) goHome();\n"
    "      return;\n"
    "    }\n")
open(path, "w", encoding="utf-8").write(src)
print("Patched OK:", path)
