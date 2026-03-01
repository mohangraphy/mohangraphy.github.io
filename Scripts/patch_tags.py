"""
patch_tags.py — Local tag-patch server for Mohangraphy admin

HOW IT WORKS:
  1. Run this script on your Mac (it starts a tiny server on port 9393)
  2. Open index.html in your browser
  3. Press Ctrl+Shift+A to enable admin mode
  4. Right-click any photo → "Edit tags (admin)"
  5. Fill in the modal and click Save
  6. This script receives the change and updates photo_metadata.json instantly
  7. Run deploy.py to rebuild and publish

The server runs until you press Ctrl+C.
"""

import json
import os
import hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler

ROOT_DIR  = "/Users/ncm/Pictures/Mohangraphy"
DATA_FILE = os.path.join(ROOT_DIR, "Scripts/photo_metadata.json")
PORT      = 9393

# ── helpers ──────────────────────────────────────────────────────────────────

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_hash(filepath):
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

def find_hash_for_rel_path(data, rel_path):
    """Find the MD5 hash key for a given relative path in the metadata."""
    for h, info in data.items():
        if info.get("path", "") == rel_path:
            return h
    return None

def rel_to_abs(rel_path):
    return os.path.join(ROOT_DIR, rel_path)

# ── request handler ───────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        pass   # suppress default access log

    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors()
        self.end_headers()

    def do_POST(self):
        if self.path != "/patch":
            self.send_response(404)
            self.end_headers()
            return

        length  = int(self.headers.get("Content-Length", 0))
        body    = self.rfile.read(length)
        payload = json.loads(body)

        cats    = payload.get("categories", [])
        state   = payload.get("state", "").strip()
        city    = payload.get("city",  "").strip()
        remarks = payload.get("remarks", "").strip()
        photos  = payload.get("photos", [])   # list of rel paths

        data    = load_data()
        updated = 0
        skipped = []

        for rel_path in photos:
            abs_path = rel_to_abs(rel_path)

            if not os.path.exists(abs_path):
                skipped.append(rel_path + " (file not found)")
                continue

            h = find_hash_for_rel_path(data, rel_path)

            if not h:
                # New entry — compute hash and add
                h = get_hash(abs_path)

            filename = os.path.basename(rel_path)
            existing = data.get(h, {})

            # Merge: only overwrite fields that were provided
            entry = {
                "path":       rel_path,
                "filename":   filename,
                "categories": cats    if cats    else existing.get("categories", []),
                "state":      state   if state   else existing.get("state",      ""),
                "city":       city    if city    else existing.get("city",       ""),
                "remarks":    remarks if remarks else existing.get("remarks",    ""),
            }
            data[h] = entry
            updated += 1
            print(f"  ✓ Updated: {filename}")
            print(f"    cats   : {entry['categories']}")
            print(f"    state  : {entry['state']!r}  city: {entry['city']!r}")
            print(f"    remarks: {entry['remarks']!r}")

        save_data(data)

        if skipped:
            print(f"  ⚠ Skipped: {skipped}")

        # Send response
        resp = json.dumps({"updated": updated, "skipped": skipped}).encode()
        self.send_response(200)
        self.send_cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(resp))
        self.end_headers()
        self.wfile.write(resp)

        print(f"\n  → {updated} photo(s) updated in {DATA_FILE}")
        print(   "  → Run deploy.py to publish changes.\n")


# ── entry point ───────────────────────────────────────────────────────────────

def run():
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    print("─" * 54)
    print("  Mohangraphy Tag Patch Server")
    print(f"  Listening on http://localhost:{PORT}")
    print("─" * 54)
    print()
    print("  Steps:")
    print("  1. Open index.html in your browser")
    print("  2. Press Ctrl+Shift+A  →  admin mode ON")
    print("  3. Right-click a photo →  Edit tags (admin)")
    print("  4. Fill modal and click Save")
    print("  5. Press Ctrl+C here when done, then run deploy.py")
    print()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
        print("  Run deploy.py to publish your tag changes.\n")

if __name__ == "__main__":
    run()
