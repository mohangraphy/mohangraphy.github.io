#!/usr/bin/env python3
"""
curator.py — Mohangraphy Photo Tagger
--------------------------------------
Run:  python3 /Users/ncm/Pictures/Mohangraphy/Scripts/curator.py

Opens a browser window with the photo on the LEFT and the tagging
form on the RIGHT — side by side, no toggling needed.

Keyboard shortcuts (in browser):
  Cmd+S  →  Save & Next
  S      →  Skip
"""

import os, json, hashlib, datetime, threading, time, subprocess, sys
from http.server import HTTPServer, BaseHTTPRequestHandler

# ── Settings ──────────────────────────────────────────────────────────────────
ROOT_DIR   = "/Users/ncm/Pictures/Mohangraphy"
PHOTOS_DIR = os.path.join(ROOT_DIR, "Photos")
DATA_FILE  = os.path.join(ROOT_DIR, "Scripts/photo_metadata.json")
PORT       = 9797

# Categories stored in photo_metadata.json
# These map to the website's 4 collections:
#   Landscape     ← Nature/Landscapes
#   Flora & Fauna ← Nature/Wildlife, Nature/Birds, Nature/Flora
#   Architecture  ← Architecture
#   People & Culture ← People & Culture
# National/International determines India vs Overseas filter pill
CATEGORIES = [
    "Nature/Landscapes",      # → Landscape
    "Nature/Wildlife",        # → Flora & Fauna
    "Nature/Birds",           # → Flora & Fauna
    "Nature/Flora",           # → Flora & Fauna
    "Places/National",        # → India filter
    "Places/International",   # → Overseas filter
    "Architecture",           # → Architecture
    "People & Culture",       # → People & Culture
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def file_hash(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    by_path = {}
    for _, info in raw.items():
        p = info.get('path')
        if p:
            by_path[p] = info
    result = {}
    for path, info in by_path.items():
        full = os.path.join(ROOT_DIR, path)
        if os.path.exists(full):
            result[file_hash(full)] = info
    return result

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def scan_photos():
    files = []
    for root, _, names in os.walk(PHOTOS_DIR):
        for n in sorted(names):
            if n.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                files.append(os.path.join(root, n))
    return files

def _esc(s):
    return (str(s)
        .replace('&', '&amp;').replace('"', '&quot;')
        .replace('<', '&lt;').replace('>', '&gt;'))

# ── HTML page ─────────────────────────────────────────────────────────────────

def build_page(state):
    photo    = state['photo']
    prev     = state['prev']
    idx      = state['idx']
    total    = state['total']
    filename = state['filename']
    tagged   = state['tagged']
    imgpath  = state['img_url']   # served via /photo

    if tagged:
        def_cats    = photo.get('categories', [])
        def_state   = photo.get('state',   photo.get('place', ''))
        def_city    = photo.get('city',    '')
        def_country = photo.get('country', '')
        def_remarks = photo.get('remarks', '')
        def_date    = photo.get('date_added', datetime.date.today().strftime('%Y-%m-%d'))
    else:
        def_cats    = prev.get('categories', [])
        def_state   = prev.get('state',   '')
        def_city    = prev.get('city',    '')
        def_country = prev.get('country', '')
        def_remarks = ''
        def_date    = prev.get('date', datetime.date.today().strftime('%Y-%m-%d'))

    status_label = 'ALREADY TAGGED' if tagged else 'NEW PHOTO'
    status_color = '#c9a96e' if tagged else '#6ec9a9'

    # Friendly labels showing what each tag maps to on the website
    CAT_LABELS = {
        "Nature/Landscapes":    "Landscapes  →  Landscape",
        "Nature/Wildlife":      "Wildlife  →  Flora & Fauna",
        "Nature/Birds":         "Birds  →  Flora & Fauna",
        "Nature/Flora":         "Flora  →  Flora & Fauna",
        "Places/National":      "National  →  India",
        "Places/International": "International  →  Overseas",
        "Architecture":         "Architecture",
        "People & Culture":     "People & Culture",
    }

    cat_btns = ''
    for c in CATEGORIES:
        label    = CAT_LABELS.get(c, c.split('/')[-1].upper())
        selected = 'selected' if c in def_cats else ''
        cat_btns += (
            f'<button class="cat-btn {selected}" data-cat="{c}" '
            f'onclick="toggleCat(this)">{label}</button>'
        )

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Curator {idx}/{total}</title>
<style>
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{
  height: 100%; background: #0a0a0a; color: #fff;
  font-family: 'Helvetica Neue', Arial, sans-serif; overflow: hidden;
}}

/* ── Layout: photo left, form right ── */
.layout {{
  display: grid;
  grid-template-columns: 1fr 400px;
  height: 100vh;
}}

/* ── Photo pane ── */
.photo-pane {{
  background: #000;
  display: flex; align-items: center; justify-content: center;
  overflow: hidden; position: relative;
}}
.photo-pane img {{
  max-width: 100%; max-height: 100vh;
  object-fit: contain; display: block;
  user-select: none;
}}
.photo-info {{
  position: absolute; bottom: 0; left: 0; right: 0;
  padding: 10px 14px;
  background: linear-gradient(to top, rgba(0,0,0,0.8) 0%, transparent 100%);
  font-size: 11px; letter-spacing: 1px;
  color: rgba(255,255,255,0.5);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
.photo-progress {{
  position: absolute; top: 12px; right: 14px;
  font-size: 11px; letter-spacing: 2px;
  color: rgba(255,255,255,0.35);
}}

/* ── Form pane ── */
.form-pane {{
  background: #141414;
  border-left: 1px solid rgba(201,169,110,0.15);
  display: flex; flex-direction: column;
  overflow-y: auto;
}}
.form-inner {{ padding: 24px 22px 80px; }}

.status {{
  display: inline-block; font-size: 9px; letter-spacing: 3px;
  font-weight: 700; text-transform: uppercase;
  color: {status_color}; margin-bottom: 18px;
}}

.label {{
  font-size: 8px; letter-spacing: 3px; text-transform: uppercase;
  color: rgba(255,255,255,0.35); margin-bottom: 8px; display: block;
}}

/* Category buttons */
.cat-wrap {{ display: flex; flex-wrap: wrap; gap: 7px; margin-bottom: 20px; }}
.cat-btn {{
  padding: 6px 12px; border-radius: 20px;
  font-size: 9px; font-weight: 700; letter-spacing: 2px;
  text-transform: uppercase; cursor: pointer;
  border: 1px solid rgba(255,255,255,0.15);
  background: rgba(255,255,255,0.04);
  color: rgba(255,255,255,0.5); transition: all .15s;
}}
.cat-btn:hover {{ border-color: rgba(255,255,255,0.4); color: rgba(255,255,255,0.9); }}
.cat-btn.selected {{
  background: rgba(201,169,110,0.15);
  border-color: #c9a96e; color: #c9a96e;
}}

/* Fields */
.field {{ margin-bottom: 14px; }}
input, textarea {{
  width: 100%; background: rgba(255,255,255,0.05);
  border: 1px solid rgba(201,169,110,0.15);
  color: #fff; padding: 9px 11px;
  font-family: inherit; font-size: 13px;
  outline: none; border-radius: 3px; transition: border-color .2s;
}}
input:focus, textarea:focus {{ border-color: #c9a96e; }}
textarea {{ min-height: 64px; resize: vertical; }}

.divider {{ height: 1px; background: rgba(255,255,255,0.07); margin: 18px 0; }}

/* Action buttons */
.actions {{ display: flex; gap: 8px; margin-top: 4px; }}
.btn {{
  flex: 1; height: 40px; font-family: inherit;
  font-size: 9px; font-weight: 700; letter-spacing: 3px;
  text-transform: uppercase; cursor: pointer;
  border-radius: 3px; transition: all .2s;
}}
.btn-save {{ background: none; border: 1px solid #c9a96e; color: #c9a96e; }}
.btn-save:hover {{ background: #c9a96e; color: #000; }}
.btn-skip {{ background: none; border: 1px solid rgba(255,255,255,0.15); color: rgba(255,255,255,0.4); }}
.btn-skip:hover {{ border-color: rgba(255,255,255,0.4); color: rgba(255,255,255,0.85); }}
.btn-stop {{ background: none; border: 1px solid rgba(224,64,96,0.3); color: rgba(224,64,96,0.6); }}
.btn-stop:hover {{ border-color: rgba(224,64,96,0.8); color: rgb(224,64,96); }}

/* Toast */
.toast {{
  position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
  background: rgba(201,169,110,0.95); color: #000;
  font-size: 10px; letter-spacing: 2px; padding: 8px 20px;
  border-radius: 4px; opacity: 0; transition: opacity .3s;
  pointer-events: none; z-index: 999;
}}
.toast.show {{ opacity: 1; }}

/* Keyboard hint */
.hint {{
  font-size: 9px; letter-spacing: 1px; color: rgba(255,255,255,0.2);
  text-align: center; margin-top: 10px;
}}
</style>
</head>
<body>
<div class="layout">

  <!-- LEFT: Photo -->
  <div class="photo-pane">
    <img src="/photo" alt="{_esc(filename)}">
    <div class="photo-info">{_esc(filename)}</div>
    <div class="photo-progress">{idx} / {total}</div>
  </div>

  <!-- RIGHT: Tagging form -->
  <div class="form-pane">
    <div class="form-inner">

      <div class="status">{status_label}</div>

      <label class="label">Categories</label>
      <div class="cat-wrap" id="cats">{cat_btns}</div>

      <div class="field">
        <label class="label">State / Country</label>
        <input id="f-state" type="text"
          placeholder="e.g. Tamil Nadu  or  Canada"
          value="{_esc(def_state)}">
      </div>
      <div class="field">
        <label class="label">City</label>
        <input id="f-city" type="text"
          placeholder="e.g. Megamalai  or  Banff"
          value="{_esc(def_city)}">
      </div>
      <div class="field">
        <label class="label">Remarks</label>
        <textarea id="f-remarks"
          placeholder="e.g. Great Hornbill in flight">{_esc(def_remarks)}</textarea>
      </div>
      <div class="field">
        <label class="label">Date Added</label>
        <input id="f-date" type="text"
          placeholder="YYYY-MM-DD"
          value="{_esc(def_date)}">
      </div>

      <div class="divider"></div>
      <div class="actions">
        <button class="btn btn-save" onclick="doSave()">Save &amp; Next</button>
        <button class="btn btn-skip" onclick="doSkip()">Skip</button>
        <button class="btn btn-stop" onclick="doStop()">Stop</button>
      </div>
      <div class="hint">Cmd+S = Save &nbsp;|&nbsp; S = Skip</div>

    </div>
  </div>
</div>
<div class="toast" id="toast"></div>

<script>
function toggleCat(btn) {{ btn.classList.toggle('selected'); }}

function selectedCats() {{
  return Array.from(document.querySelectorAll('.cat-btn.selected'))
    .map(b => b.getAttribute('data-cat'));
}}

function toast(msg) {{
  var t = document.getElementById('toast');
  t.textContent = msg; t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 1800);
}}

function post(action, extra) {{
  fetch('/cmd', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify(Object.assign({{action}}, extra || {{}}))
  }})
  .then(r => r.json())
  .then(d => {{
    if (d.status === 'done') {{
      document.body.innerHTML =
        '<div style="color:#c9a96e;font-family:Helvetica,sans-serif;font-size:14px;'
        + 'letter-spacing:2px;text-align:center;margin-top:40vh;">'
        + 'SESSION COMPLETE — you can close this window.</div>';
    }} else if (d.status === 'next' || d.status === 'saved') {{
      window.location.reload();
    }}
  }});
}}

function doSave() {{
  post('save', {{
    cats:    selectedCats(),
    state:   document.getElementById('f-state').value.trim(),
    city:    document.getElementById('f-city').value.trim(),
    remarks: document.getElementById('f-remarks').value.trim(),
    date:    document.getElementById('f-date').value.trim(),
  }});
}}
function doSkip() {{ post('skip'); }}
function doStop() {{ post('stop'); }}

document.addEventListener('keydown', function(e) {{
  // Ignore when typing in a field
  if (['INPUT','TEXTAREA'].includes(e.target.tagName)) {{
    if ((e.metaKey || e.ctrlKey) && e.key === 's') {{
      e.preventDefault(); doSave();
    }}
    return;
  }}
  if ((e.metaKey || e.ctrlKey) && e.key === 's') {{ e.preventDefault(); doSave(); }}
  else if (e.key === 's' || e.key === 'S') {{ doSkip(); }}
}});
</script>
</body>
</html>'''

# ── HTTP server ───────────────────────────────────────────────────────────────

class CuratorServer(BaseHTTPRequestHandler):

    def log_message(self, *a): pass

    def do_GET(self):
        parsed = self.path.split('?')[0]

        if parsed == '/photo':
            # Serve the current photo directly
            photo_path = self.server.state.get('full_path', '')
            if photo_path and os.path.exists(photo_path):
                ext = os.path.splitext(photo_path)[1].lower()
                mime = 'image/jpeg' if ext in ('.jpg', '.jpeg') else \
                       'image/png'  if ext == '.png' else \
                       'image/webp' if ext == '.webp' else 'image/jpeg'
                with open(photo_path, 'rb') as f:
                    data = f.read()
                self.send_response(200)
                self.send_header('Content-Type', mime)
                self.send_header('Content-Length', len(data))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_error(404)
            return

        # Default: serve the curator page
        html = build_page(self.server.state).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(html))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(html)

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body   = json.loads(self.rfile.read(length))
        action = body.get('action')
        srv    = self.server
        today  = datetime.date.today().strftime('%Y-%m-%d')

        if action == 'save':
            cats    = body.get('cats',    [])
            state   = body.get('state',   '').strip()
            city    = body.get('city',    '').strip()
            remarks = body.get('remarks', '').strip()
            date    = body.get('date',    today).strip()

            try:
                datetime.datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                date = today

            is_intl = any('International' in c for c in cats)
            if is_intl:
                country = state; state = ''
            else:
                country = ''

            h        = srv.state['hash']
            rel_path = srv.state['rel_path']
            filename = srv.state['filename']

            srv.data[h] = {
                'path':       rel_path,
                'filename':   filename,
                'categories': cats,
                'state':      state,
                'city':       city,
                'country':    country,
                'remarks':    remarks,
                'date_added': date,
            }
            save_data(srv.data)

            srv.prev.update({
                'categories': cats,
                'state':      state,
                'city':       city,
                'country':    country,
                'remarks':    remarks,
                'date':       date,
            })

            print(f"  ✅ {filename} | {', '.join(cats)} | {state or country} / {city}")

            if not self._advance(srv):
                self._json({'status': 'done'})
                srv.stop_flag = True
                return
            self._json({'status': 'next'})

        elif action == 'skip':
            cur = srv.state['photo']
            if cur:
                srv.prev.update({
                    'categories': cur.get('categories', srv.prev.get('categories', [])),
                    'state':      cur.get('state',      srv.prev.get('state', '')),
                    'city':       cur.get('city',       srv.prev.get('city', '')),
                    'country':    cur.get('country',    srv.prev.get('country', '')),
                    'remarks':    cur.get('remarks',    ''),
                    'date':       cur.get('date_added', srv.prev.get('date', today)),
                })
            if not self._advance(srv):
                self._json({'status': 'done'})
                srv.stop_flag = True
                return
            self._json({'status': 'next'})

        elif action == 'stop':
            self._json({'status': 'done'})
            srv.stop_flag = True

    def _advance(self, srv):
        srv.state['idx'] += 1
        if srv.state['idx'] > srv.state['total']:
            return False
        i    = srv.state['idx']
        path = srv.files[i - 1]
        h    = file_hash(path)
        rel  = os.path.relpath(path, ROOT_DIR)
        fn   = os.path.basename(path)
        srv.state.update({
            'hash':      h,
            'rel_path':  rel,
            'filename':  fn,
            'full_path': path,
            'img_url':   '/photo',
            'tagged':    h in srv.data,
            'photo':     srv.data.get(h, {}),
            'prev':      dict(srv.prev),
        })
        return True

    def _json(self, obj):
        body = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    data  = load_data()
    files = scan_photos()
    total = len(files)

    if total == 0:
        print("No photos found in", PHOTOS_DIR)
        sys.exit(0)

    print(f"📊 Metadata loaded: {len(data)} tagged photos")
    print(f"📷 Found {total} photos\n")

    first_path = files[0]
    first_hash = file_hash(first_path)
    today      = datetime.date.today().strftime('%Y-%m-%d')

    server           = HTTPServer(('localhost', PORT), CuratorServer)
    server.data      = data
    server.files     = files
    server.stop_flag = False
    server.prev      = {
        'categories': [], 'state': '', 'city': '',
        'country': '', 'remarks': '', 'date': today
    }
    server.state = {
        'idx':       1,
        'total':     total,
        'hash':      first_hash,
        'rel_path':  os.path.relpath(first_path, ROOT_DIR),
        'filename':  os.path.basename(first_path),
        'full_path': first_path,
        'img_url':   '/photo',
        'tagged':    first_hash in data,
        'photo':     data.get(first_hash, {}),
        'prev':      dict(server.prev),
    }

    def open_browser():
        time.sleep(0.5)
        subprocess.Popen(['open', f'http://localhost:{PORT}'])

    threading.Thread(target=open_browser, daemon=True).start()

    print(f"🌐 Curator running at http://localhost:{PORT}")
    print("   Photo + form side by side in browser")
    print("   Cmd+S = Save & Next  |  S = Skip  |  Click Stop to quit\n")

    try:
        while not server.stop_flag:
            server.handle_request()
    except KeyboardInterrupt:
        pass

    print(f"\n✅ Session ended. {len(data)} photos in database.")

if __name__ == '__main__':
    main()
