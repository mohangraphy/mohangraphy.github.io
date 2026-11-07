#!/usr/bin/env python3
"""Admin panel: adds a 'Photos + Blog Notification' option that walks you through
sending ONE combined email (workflow notification_type = both).
Aborts without changes if any anchor is missing. Safe to run once."""
import sys
path = sys.argv[1] if len(sys.argv) > 1 else "/Users/ncm/Pictures/Mohangraphy/Scripts/Claude_mohangraphy.py"
src = open(path, encoding="utf-8").read()
if "Photos + Blog Notification" in src:
    sys.exit("Already patched - nothing to do.")

def swap(old, new):
    global src
    assert src.count(old) == 1, "anchor not found exactly once: " + old[:70]
    src = src.replace(old, new)

# panel title
swap("titleEl.textContent = type === 'photos' ? 'Photo Notification' : 'Blog Notification';",
     "titleEl.textContent = type === 'photos' ? 'Photo Notification' : (type === 'both' ? 'Photos + Blog Notification' : 'Blog Notification');")
# blog dropdown must also fill for 'both'
swap("  if(type === 'blog') {\n    var sel = document.getElementById('notify-post-select');",
     "  if(type === 'blog' || type === 'both') {\n    var sel = document.getElementById('notify-post-select');")
# test button: pass the real type through
swap("notifyOpenGitHub({type:'blog', testOnly:true, post:post});",
     "notifyOpenGitHub({type:type, testOnly:true, post:post});")
# send button: read the type from the panel
swap("notifyOpenGitHub({type:'blog', testOnly:false, post:post});",
     "var _pn = document.getElementById('notify-panel');\n"
     "  var _nt = _pn ? (_pn.getAttribute('data-notify-type') || 'blog') : 'blog';\n"
     "  notifyOpenGitHub({type:_nt, testOnly:false, post:post});")
# instructions shown to you: always state notification_type
swap("  if(opts.type === 'blog' && opts.post) {",
     "  lines.push('   notification_type: ' + (opts.type || 'photos'));\n"
     "  if((opts.type === 'blog' || opts.type === 'both') && opts.post) {")
# admin menu button
btn = ("""        '        <button class="btn-gold" style="width:100%;height:44px" onclick="closeAdminModal();openNotifyPanel(\\'photos\\')">&#128247;&nbsp; Photo Notification</button>\\n'\n""")
new_btn = btn + ("""        '        <button class="btn-gold" style="width:100%;height:44px" onclick="closeAdminModal();openNotifyPanel(\\'both\\')">&#128231;&nbsp; Photos + Blog Notification</button>\\n'\n""")
swap(btn, new_btn)

open(path, "w", encoding="utf-8").write(src)
print("Patched OK:", path)
