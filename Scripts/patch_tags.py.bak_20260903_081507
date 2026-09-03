"""
patch_tags.py — Local tag-patch server for Mohangraphy admin

HOW IT WORKS:
  1. Run this script on your Mac (it starts a tiny server on port 9393)
  2. Open index.html in your browser (or mohangraphy.com while local)
  3. Press Ctrl+Shift+A to enable admin mode
  4. Right-click any photo → "Edit tags"
  5. Edit tags, then click Save Tags or Deploy Now
  6. Press Ctrl+C here when done

Endpoints:
  POST /patch   — update tags for one or more photos
  POST /delete  — remove photo(s) from metadata
  POST /deploy  — run Claude_mohangraphy.py to rebuild + push to GitHub
"""

import json
import os
import hashlib
import subprocess
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

ROOT_DIR    = "/Users/ncm/Pictures/Mohangraphy"
DATA_FILE   = os.path.join(ROOT_DIR, "Scripts/photo_metadata.json")
MAIN_SCRIPT = os.path.join(ROOT_DIR, "Scripts/Claude_mohangraphy.py")
PORT        = 9393

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
    for h, info in data.items():
        if info.get("path", "") == rel_path:
            return h
    return None

def rel_to_abs(rel_path):
    return os.path.join(ROOT_DIR, rel_path)

# ── request handler ───────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        pass

    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors()
        self.end_headers()

    def send_json(self, code, obj):
        resp = json.dumps(obj).encode()
        self.send_response(code)
        self.send_cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(resp))
        self.end_headers()
        self.wfile.write(resp)

    def do_POST(self):
        length  = int(self.headers.get("Content-Length", 0))
        body    = self.rfile.read(length)
        try:
            payload = json.loads(body) if body else {}
        except Exception:
            payload = {}

        if self.path == "/patch":
            self.handle_patch(payload)
        elif self.path == "/delete":
            self.handle_delete(payload)
        elif self.path == "/deploy":
            self.handle_deploy()
        else:
            self.send_response(404)
            self.end_headers()

    def handle_patch(self, payload):
        cats    = payload.get("categories", [])
        state   = payload.get("state", "").strip()
        city    = payload.get("city",  "").strip()
        remarks = payload.get("remarks", "").strip()
        photos  = payload.get("photos", [])

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
                h = get_hash(abs_path)

            filename = os.path.basename(rel_path)
            existing = data.get(h, {})

            entry = {
                "path":       rel_path,
                "filename":   filename,
                "categories": cats    if cats    else existing.get("categories", []),
                "state":      state   if state   else existing.get("state",      ""),
                "city":       city    if city    else existing.get("city",       ""),
                "remarks":    remarks if remarks else existing.get("remarks",    ""),
                "date_added": existing.get("date_added", ""),
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
        print(f"\n  → {updated} photo(s) updated.\n")
        self.send_json(200, {"updated": updated, "skipped": skipped})

    def handle_delete(self, payload):
        photos = payload.get("photos", [])
        data   = load_data()
        removed = []

        for rel_path in photos:
            h = find_hash_for_rel_path(data, rel_path)
            if h and h in data:
                filename = data[h].get("filename", rel_path.split("/")[-1])
                del data[h]
                removed.append(filename)
                print(f"  🗑  Removed from metadata: {filename}")

        save_data(data)
        print(f"\n  → {len(removed)} photo(s) removed from metadata.")
        print(  "  → Run deploy (or click Deploy Now) to publish.\n")
        self.send_json(200, {"removed": removed})

    def handle_deploy(self):
        print("\n  ▶  Deploy triggered from browser admin panel...")
        def run():
            result = subprocess.run(
                [sys.executable, MAIN_SCRIPT],
                cwd=ROOT_DIR,
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print("  ✅ Deploy complete — site is live.")
            else:
                print("  ❌ Deploy failed:")
                print(result.stderr[-500:] if result.stderr else "(no output)")
        threading.Thread(target=run, daemon=True).start()
        # Respond immediately — deploy runs in background
        self.send_json(200, {"ok": True, "message": "Deploy started"})


# ── entry point ───────────────────────────────────────────────────────────────

def run():
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    print("─" * 54)
    print("  Mohangraphy Admin Server  —  v2")
    print(f"  Listening on http://localhost:{PORT}")
    print("─" * 54)
    print()
    print("  In your browser:")
    print("  1. Press Ctrl+Shift+A  →  admin mode ON")
    print("  2. Right-click any photo  →  Edit tags")
    print("  3. Edit, then click  Save Tags  or  Deploy Now")
    print()
    print("  Press Ctrl+C to stop.")
    print()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.\n")

if __name__ == "__main__":
    run()

