#!/usr/bin/env python3
"""
patch_journeys_js.py
---------------------
Part 2 of the Footprints migration.

What it does to Claude_mohangraphy.py:
  1. Replaces the hardcoded JOURNEYS_INDIA / JOURNEYS_WORLD array literals
     with empty arrays (var JOURNEYS_INDIA = [];  var JOURNEYS_WORLD = [];)
  2. Inserts a loadJourneysData() function that fetches journeys_data.json
     once and populates those two arrays.
  3. Updates showJourneys() to call loadJourneysData() before building the
     map, so JOURNEYS_INDIA/JOURNEYS_WORLD are populated by the time
     initJourneysMap() / _buildJourneysMap() run.

_buildJourneysMap(), initJourneysMap(), switchJourneysTab() are NOT touched.

A timestamped backup of the original file is written before any edit.

Run once, locally:
    python3 patch_journeys_js.py
"""

import re
import os
import shutil
import datetime

SCRIPT_PATH = "/Users/ncm/Pictures/Mohangraphy/Scripts/Claude_mohangraphy.py"


def replace_array_with_empty(source_text, var_name):
    """Find `var NAME = [ ... ];` (bracket-matched) and replace the whole
    literal with an empty array, returning the new source text."""
    marker = f"var {var_name} = ["
    start = source_text.find(marker)
    if start == -1:
        raise ValueError(f"Could not find '{marker}' — has the file already been patched?")

    bracket_start = start + len(marker) - 1
    depth = 0
    end = None
    for i in range(bracket_start, len(source_text)):
        ch = source_text[i]
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
            if depth == 0:
                end = i
                break
    if end is None:
        raise ValueError(f"Could not find matching ']' for {var_name}")

    before = source_text[:start]
    after = source_text[end + 1:]
    return before + f"var {var_name} = []" + after


OLD_SHOW_JOURNEYS = """function showJourneys(){
  hideAll();
  var pg = document.getElementById('page-journeys');
  if(pg){ pg.classList.add('visible'); pg.scrollTop=0; window.scrollTo(0,0); }
  setActiveTab('journeys');
  syncUrl('footprints');
  loadLeaflet(function(){
    setTimeout(function(){
      initJourneysMap();
      setTimeout(function(){
        if(_journeysMapIndia) _journeysMapIndia.invalidateSize();
        if(_journeysMapWorld) _journeysMapWorld.invalidateSize();
      }, 300);
    }, 100);
  });
}"""

NEW_SHOW_JOURNEYS = """var _journeysDataLoaded = false;

function loadJourneysData(cb){
  if(_journeysDataLoaded){ cb(); return; }
  fetch('journeys_data.json')
    .then(function(r){ return r.json(); })
    .then(function(data){
      JOURNEYS_INDIA = data.india || [];
      JOURNEYS_WORLD = data.world || [];
      _journeysDataLoaded = true;
      cb();
    })
    .catch(function(err){
      console.error('Failed to load journeys_data.json', err);
      cb();
    });
}

function showJourneys(){
  hideAll();
  var pg = document.getElementById('page-journeys');
  if(pg){ pg.classList.add('visible'); pg.scrollTop=0; window.scrollTo(0,0); }
  setActiveTab('journeys');
  syncUrl('footprints');
  loadJourneysData(function(){
    loadLeaflet(function(){
      setTimeout(function(){
        initJourneysMap();
        setTimeout(function(){
          if(_journeysMapIndia) _journeysMapIndia.invalidateSize();
          if(_journeysMapWorld) _journeysMapWorld.invalidateSize();
        }, 300);
      }, 100);
    });
  });
}"""


def main():
    if not os.path.exists(SCRIPT_PATH):
        print(f"ERROR: could not find {SCRIPT_PATH}")
        return

    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        source = f.read()

    if "loadJourneysData" in source:
        print("This file already looks patched (found loadJourneysData). Stopping — nothing changed.")
        return

    if OLD_SHOW_JOURNEYS not in source:
        print("ERROR: could not find the expected showJourneys() function exactly as expected.")
        print("Stopping without changing anything — the file may have been edited since this script was written.")
        return

    # Backup first
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = SCRIPT_PATH + f".bak_{ts}"
    shutil.copyfile(SCRIPT_PATH, backup_path)
    print(f"Backup written: {backup_path}")

    # 1. Empty out the two arrays
    source = replace_array_with_empty(source, "JOURNEYS_INDIA")
    source = replace_array_with_empty(source, "JOURNEYS_WORLD")
    print("Emptied JOURNEYS_INDIA and JOURNEYS_WORLD array literals.")

    # 2. Swap in the new showJourneys() + loadJourneysData()
    source = source.replace(OLD_SHOW_JOURNEYS, NEW_SHOW_JOURNEYS)
    print("Inserted loadJourneysData() and updated showJourneys().")

    with open(SCRIPT_PATH, "w", encoding="utf-8") as f:
        f.write(source)

    print(f"\nDone. {SCRIPT_PATH} updated.")
    print("If anything looks wrong, restore with:")
    print(f"  cp {backup_path} {SCRIPT_PATH}")
    print("\nNext: Part 3 will add the 'Manage Footprints' admin button + form,")
    print("and Part 4 will extend patch_tags.py with the /journeys/add endpoint.")


if __name__ == "__main__":
    main()
