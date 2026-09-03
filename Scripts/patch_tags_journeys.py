#!/usr/bin/env python3
"""
patch_tags_journeys.py
------------------------
Part 4 of the Footprints migration.

Adds to patch_tags.py:
  1. JOURNEYS_FILE path constant (next to DATA_FILE), pointing at
     journeys_data.json in the site root (next to index.html) — same
     location the browser fetches it from (see Part 1/2 notes).
  2. Routes POST /journeys/add to a new handle_journeys_add().
  3. handle_journeys_add(): validates the payload (type, name, state/
     country, lat, lng), loads journeys_data.json, appends the new
     place to the correct list ("india" or "world"), writes it back,
     and responds {"ok": true} — matching what the admin-panel JS
     (Part 3) expects.

Does not touch handle_patch, handle_delete, handle_deploy, or anything
else already in patch_tags.py.

A timestamped backup is written before any edit. If the expected code
isn't found exactly, the script stops without changing anything.

Run once, locally:
    python3 patch_tags_journeys.py
"""

import os
import shutil
import datetime

SCRIPT_PATH = "/Users/ncm/Pictures/Mohangraphy/Scripts/patch_tags.py"


OLD_PATHS = """ROOT_DIR    = "/Users/ncm/Pictures/Mohangraphy"
DATA_FILE   = os.path.join(ROOT_DIR, "Scripts/photo_metadata.json")
MAIN_SCRIPT = os.path.join(ROOT_DIR, "Scripts/Claude_mohangraphy.py")
PORT        = 9393"""

NEW_PATHS = """ROOT_DIR      = "/Users/ncm/Pictures/Mohangraphy"
DATA_FILE     = os.path.join(ROOT_DIR, "Scripts/photo_metadata.json")
MAIN_SCRIPT   = os.path.join(ROOT_DIR, "Scripts/Claude_mohangraphy.py")
# journeys_data.json lives at the site root (next to index.html), NOT in
# Scripts/, because the browser fetches it relative to index.html.
JOURNEYS_FILE = os.path.join(ROOT_DIR, "journeys_data.json")
PORT          = 9393"""


OLD_ROUTES = """        if self.path == "/patch":
            self.handle_patch(payload)
        elif self.path == "/delete":
            self.handle_delete(payload)
        elif self.path == "/deploy":
            self.handle_deploy()
        else:
            self.send_response(404)
            self.end_headers()"""

NEW_ROUTES = """        if self.path == "/patch":
            self.handle_patch(payload)
        elif self.path == "/delete":
            self.handle_delete(payload)
        elif self.path == "/journeys/add":
            self.handle_journeys_add(payload)
        elif self.path == "/deploy":
            self.handle_deploy()
        else:
            self.send_response(404)
            self.end_headers()"""


OLD_HANDLE_DELETE_DEF = "    def handle_delete(self, payload):"

NEW_JOURNEYS_HANDLER = '''    def load_journeys(self):
        if not os.path.exists(JOURNEYS_FILE):
            return {"india": [], "world": []}
        with open(JOURNEYS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_journeys(self, data):
        with open(JOURNEYS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def handle_journeys_add(self, payload):
        place_type = payload.get("type", "").strip().lower()
        name       = payload.get("name", "").strip()
        lat        = payload.get("lat")
        lng        = payload.get("lng")

        if place_type not in ("india", "world"):
            self.send_json(400, {"ok": False, "error": "type must be 'india' or 'world'"})
            return
        if not name:
            self.send_json(400, {"ok": False, "error": "Place name is required"})
            return
        try:
            lat = float(lat)
            lng = float(lng)
        except (TypeError, ValueError):
            self.send_json(400, {"ok": False, "error": "Latitude/longitude must be numbers"})
            return

        entry = {"name": name, "lat": lat, "lng": lng, "uploaded": False}
        if place_type == "india":
            state = payload.get("state", "").strip()
            if not state:
                self.send_json(400, {"ok": False, "error": "State is required"})
                return
            entry["state"] = state
        else:
            country = payload.get("country", "").strip()
            if not country:
                self.send_json(400, {"ok": False, "error": "Country is required"})
                return
            entry["country"] = country

        data = self.load_journeys()
        data.setdefault("india", [])
        data.setdefault("world", [])
        data[place_type].append(entry)
        self.save_journeys(data)

        print(f"  \\u2713 Added footprint: {name} ({place_type})")
        self.send_json(200, {"ok": True, "entry": entry})

    def handle_delete(self, payload):'''


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

    if "handle_journeys_add" in source:
        print("This file already looks patched (found handle_journeys_add). Stopping — nothing changed.")
        return

    try:
        new_source = source
        new_source = patch(new_source, OLD_PATHS, NEW_PATHS, "path constants")
        new_source = patch(new_source, OLD_ROUTES, NEW_ROUTES, "do_POST routing")
        new_source = patch(new_source, OLD_HANDLE_DELETE_DEF, NEW_JOURNEYS_HANDLER, "handle_journeys_add insertion point")
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

    print(f"\\nDone. {SCRIPT_PATH} updated.")
    print("Added: JOURNEYS_FILE path, POST /journeys/add route, handle_journeys_add().")
    print("\\nNext steps:")
    print("  1. Restart patch_tags.py (Ctrl+C it if running, then run it again)")
    print("     so it picks up the new endpoint.")
    print("  2. Open the site, unlock admin, click 'Manage Footprints', add a test place.")
    print("  3. Check journeys_data.json (site root) to confirm the entry was added.")
    print("  4. Deploy, then confirm the new pin shows on the map.")
    print(f"\\nIf anything looks wrong, restore with:\\n  cp {backup_path} {SCRIPT_PATH}")


if __name__ == "__main__":
    main()
