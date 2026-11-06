#!/usr/bin/env python3
"""Footprints auto-link: markers get gallery buttons automatically from the
galleries the build actually generates, so new cities (e.g. Coimbatore) work
without hand-editing journeys_data.json. Safe to run once; aborts if no match."""
import sys
path = sys.argv[1] if len(sys.argv) > 1 else "/Users/ncm/Pictures/Mohangraphy/Scripts/Claude_mohangraphy.py"
src = open(path, encoding="utf-8").read()

if "_autoLinkJourneys" in src:
    sys.exit("Already patched - nothing to do.")

old = """      JOURNEYS_INDIA = data.india || [];
      JOURNEYS_WORLD = data.world || [];
      _journeysDataLoaded = true;"""
new = """      JOURNEYS_INDIA = data.india || [];
      JOURNEYS_WORLD = data.world || [];
      _autoLinkJourneys();
      _journeysDataLoaded = true;"""
assert src.count(old) == 1, "loader block not found exactly once"
src = src.replace(old, new)

anchor = "var _journeysDataLoaded = false;\n"
assert src.count(anchor) == 1, "anchor not found exactly once"
func = anchor + """
/* Auto-link map markers to galleries that exist in the page.
   Only fills places that have no manual 'galleries' list. */
function _autoLinkJourneys(){
  var ids = Array.prototype.map.call(
    document.querySelectorAll('.section-block[id^="gallery-"]'),
    function(b){ return b.id; });
  function norm(s){ return (s||'').toLowerCase().replace(/[^a-z0-9]/g,''); }
  function link(list, marker, isWorld){
    list.forEach(function(p){
      if(p.galleries && p.galleries.length) return;
      var want = norm(p.name);
      if(!want) return;
      var found = ids.filter(function(id){
        var i = id.indexOf(marker);
        if(i < 0) return false;
        var rest = norm(id.slice(i + marker.length));
        return isWorld ? (rest.length > want.length && rest.slice(-want.length) === want)
                       : (rest === want);
      });
      if(found.length){ p.galleries = found; p.uploaded = true; }
    });
  }
  link(JOURNEYS_INDIA, '-india-', false);
  link(JOURNEYS_WORLD, '-overseas-', true);
}
"""
src = src.replace(anchor, func)
open(path, "w", encoding="utf-8").write(src)
print("Patched OK:", path)
