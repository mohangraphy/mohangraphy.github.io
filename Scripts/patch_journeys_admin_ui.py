#!/usr/bin/env python3
"""
patch_journeys_admin_ui.py
----------------------------
Part 3 of the Footprints migration.

Adds to Claude_mohangraphy.py:
  1. A "Manage Footprints" button on the admin choice screen, next to
     "Edit Tags".
  2. A new "admin-journeys-screen" form: Place name, India/World toggle,
     State/Country, Latitude, Longitude, optional Gallery link.
  3. JS functions adminOpenJourneysEditor(), adminJourneysSetType(),
     saveAdminJourney() — mirroring adminOpenTagEditor()/saveAdminTags().
  4. Updates adminBackToChoice() so "Back" works from the new screen too.

Does NOT touch _buildJourneysMap(), initJourneysMap(), switchJourneysTab(),
or anything from Part 2 (loadJourneysData/showJourneys).

A timestamped backup is written before any edit. If the expected code
isn't found exactly (e.g. already patched, or edited since), the script
stops without changing anything.

Run once, locally:
    python3 patch_journeys_admin_ui.py
"""

import os
import shutil
import datetime

SCRIPT_PATH = "/Users/ncm/Pictures/Mohangraphy/Scripts/Claude_mohangraphy.py"


# ── 1. HTML: add the button ──────────────────────────────────────────────
OLD_BUTTON_BLOCK = (
    "        '        <button class=\"btn-gold\" style=\"width:100%;height:44px\" onclick=\"adminOpenTagEditor()\">&#9998;&nbsp; Edit Tags</button>\\n'\n"
    "        '        <button class=\"btn-gold\" style=\"width:100%;height:44px\" onclick=\"closeAdminModal();openNotifyPanel(\\'blog\\')\">&#9993;&nbsp; Blog Notification</button>\\n'\n"
)
NEW_BUTTON_BLOCK = (
    "        '        <button class=\"btn-gold\" style=\"width:100%;height:44px\" onclick=\"adminOpenTagEditor()\">&#9998;&nbsp; Edit Tags</button>\\n'\n"
    "        '        <button class=\"btn-gold\" style=\"width:100%;height:44px\" onclick=\"adminOpenJourneysEditor()\">&#128205;&nbsp; Manage Footprints</button>\\n'\n"
    "        '        <button class=\"btn-gold\" style=\"width:100%;height:44px\" onclick=\"closeAdminModal();openNotifyPanel(\\'blog\\')\">&#9993;&nbsp; Blog Notification</button>\\n'\n"
)

# ── 2. HTML: add the new screen, right after the Edit Tags screen closes ──
OLD_SCREEN_END = (
    "        '        <button class=\"btn-gold\" onclick=\"saveAdminTags()\">Save</button>\\n'\n"
    "        '      </div>\\n'\n"
    "        '    </div>\\n'\n"
    "        '  </div>\\n'\n"
    "        '</div>\\n\\n'\n"
)
NEW_SCREEN_END = (
    "        '        <button class=\"btn-gold\" onclick=\"saveAdminTags()\">Save</button>\\n'\n"
    "        '      </div>\\n'\n"
    "        '    </div>\\n'\n"
    "        '    <!-- Manage Footprints screen -->\\n'\n"
    "        '    <div id=\"admin-journeys-screen\" style=\"display:none\">\\n'\n"
    "        '      <div style=\"display:flex;gap:8px;margin-bottom:14px\">\\n'\n"
    "        '        <button class=\"btn-ghost\" id=\"jform-type-india\" style=\"flex:1\" onclick=\"adminJourneysSetType(\\'india\\')\">India</button>\\n'\n"
    "        '        <button class=\"btn-ghost\" id=\"jform-type-world\" style=\"flex:1\" onclick=\"adminJourneysSetType(\\'world\\')\">World</button>\\n'\n"
    "        '      </div>\\n'\n"
    "        '      <div class=\"admin-field\"><label>Place Name</label><input id=\"jform-name\" type=\"text\" placeholder=\"e.g. Hampi\"></div>\\n'\n"
    "        '      <div class=\"admin-field\"><label id=\"jform-region-label\">State</label><input id=\"jform-region\" type=\"text\" placeholder=\"e.g. Karnataka\"></div>\\n'\n"
    "        '      <div class=\"admin-field\"><label>Latitude</label><input id=\"jform-lat\" type=\"text\" placeholder=\"e.g. 15.3350\"></div>\\n'\n"
    "        '      <div class=\"admin-field\"><label>Longitude</label><input id=\"jform-lng\" type=\"text\" placeholder=\"e.g. 76.4600\"></div>\\n'\n"
    "        '      <div class=\"admin-field\"><label>Gallery Link (optional)</label><input id=\"jform-gallery\" type=\"text\" placeholder=\"optional\"></div>\\n'\n"
    "        '      <div id=\"jform-error\" style=\"display:none;color:#e04060;font-size:9px;letter-spacing:1px;margin-bottom:10px\"></div>\\n'\n"
    "        '      <div class=\"admin-row\">\\n'\n"
    "        '        <button class=\"btn-ghost\" onclick=\"adminBackToChoice()\">&#8249; Back</button>\\n'\n"
    "        '        <button class=\"btn-gold\" onclick=\"saveAdminJourney()\">Save</button>\\n'\n"
    "        '      </div>\\n'\n"
    "        '    </div>\\n'\n"
    "        '  </div>\\n'\n"
    "        '</div>\\n\\n'\n"
)

# ── 3. JS: extend adminBackToChoice() so it also hides the new screen ─────
OLD_BACK_FN = """function adminBackToChoice(){
  document.getElementById('admin-edit-screen').style.display='none';
  document.getElementById('admin-choice-screen').style.display='block';
}"""
NEW_BACK_FN = """function adminBackToChoice(){
  document.getElementById('admin-edit-screen').style.display='none';
  var jscreen = document.getElementById('admin-journeys-screen');
  if(jscreen) jscreen.style.display='none';
  document.getElementById('admin-choice-screen').style.display='block';
}

var _jformType = 'india';

function adminOpenJourneysEditor(){
  document.getElementById('admin-choice-screen').style.display='none';
  document.getElementById('admin-journeys-screen').style.display='block';
  document.getElementById('jform-name').value='';
  document.getElementById('jform-region').value='';
  document.getElementById('jform-lat').value='';
  document.getElementById('jform-lng').value='';
  document.getElementById('jform-gallery').value='';
  document.getElementById('jform-error').style.display='none';
  adminJourneysSetType('india');
}

function adminJourneysSetType(type){
  _jformType = type;
  document.getElementById('jform-type-india').classList.toggle('selected', type==='india');
  document.getElementById('jform-type-world').classList.toggle('selected', type==='world');
  document.getElementById('jform-region-label').textContent = type==='india' ? 'State' : 'Country';
}

function saveAdminJourney(){
  var name = document.getElementById('jform-name').value.trim();
  var region = document.getElementById('jform-region').value.trim();
  var lat = parseFloat(document.getElementById('jform-lat').value);
  var lng = parseFloat(document.getElementById('jform-lng').value);
  var gallery = document.getElementById('jform-gallery').value.trim();
  var errEl = document.getElementById('jform-error');

  if(!name || !region || isNaN(lat) || isNaN(lng)){
    errEl.textContent = 'Please fill in name, state/country, latitude and longitude.';
    errEl.style.display='block';
    return;
  }
  errEl.style.display='none';

  var payload = {
    type: _jformType,
    name: name,
    lat: lat,
    lng: lng,
    gallery: gallery
  };
  if(_jformType === 'india'){ payload.state = region; }
  else { payload.country = region; }

  fetch('http://localhost:9393/journeys/add',{
    method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)
  }).then(function(r){return r.json();})
    .then(function(resp){
      if(resp && resp.ok){
        showToast('✓ Place added. Run deploy to publish.');
        adminBackToChoice();
      } else {
        errEl.textContent = (resp && resp.error) || 'Save failed.';
        errEl.style.display='block';
      }
    })
    .catch(function(){
      errEl.textContent = 'Server offline. Start patch_tags.py, then try again.';
      errEl.style.display='block';
    });
}"""


def patch(source, old, new, label):
    if new in source or (old not in source and new.split("\n")[0] in source):
        print(f"  (skip) {label} — already present")
        return source
    if old not in source:
        raise ValueError(f"Could not find expected block for: {label}")
    return source.replace(old, new, 1)


def main():
    if not os.path.exists(SCRIPT_PATH):
        print(f"ERROR: could not find {SCRIPT_PATH}")
        return

    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        source = f.read()

    if "adminOpenJourneysEditor" in source:
        print("This file already looks patched (found adminOpenJourneysEditor). Stopping — nothing changed.")
        return

    try:
        new_source = source
        new_source = patch(new_source, OLD_BUTTON_BLOCK, NEW_BUTTON_BLOCK, "admin choice button")
        new_source = patch(new_source, OLD_SCREEN_END, NEW_SCREEN_END, "admin-journeys-screen HTML")
        new_source = patch(new_source, OLD_BACK_FN, NEW_BACK_FN, "adminBackToChoice + new JS functions")
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
    print("Added: 'Manage Footprints' button, its form screen, and the JS to submit it.")
    print("Note: it POSTs to http://localhost:9393/journeys/add, which doesn't exist yet —")
    print("that's Part 4 (patch_tags.py). Until then, Save will show 'Server offline'.")
    print(f"\nIf anything looks wrong, restore with:\n  cp {backup_path} {SCRIPT_PATH}")


if __name__ == "__main__":
    main()
