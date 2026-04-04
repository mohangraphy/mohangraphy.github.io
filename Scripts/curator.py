#!/usr/bin/env python3
"""
curator.py — Mohangraphy Photo Tagger
--------------------------------------
Opens each photo in Preview alongside a local web editor that mirrors
the website's admin panel. All fields carry forward from the previous
photo — just change what's different.

Usage:
    python3 /Users/ncm/Pictures/Mohangraphy/Scripts/curator.py

Controls in the browser:
    Save & Next  — save tags and move to next photo
    Skip         — skip without saving
    Stop         — finish session
"""

import os, json, hashlib, datetime, threading, time, subprocess, sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ── Settings ──────────────────────────────────────────────────────────────────
ROOT_DIR   = "/Users/ncm/Pictures/Mohangraphy"
PHOTOS_DIR = os.path.join(ROOT_DIR, "Photos")
DATA_FILE  = os.path.join(ROOT_DIR, "Scripts/photo_metadata.json")
PORT       = 9797

CATEGORIES = [
    "Nature/Landscapes",
    "Nature/Wildlife",
    "Nature/Birds",
    "Nature/Flora",
    "Places/National",
    "Places/International",
    "Architecture",
    "People & Culture",
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

# ── HTML page ─────────────────────────────────────────────────────────────────

def build_page(state):
    photo      = state['photo']        # dict with current photo info
    prev       = state['prev']         # carry-forward values
    idx        = state['idx']
    total      = state['total']
    filename   = state['filename']
    tagged     = state['tagged']

    # Decide defaults: existing tags if already tagged, else carry-forward
    if tagged:
        def_cats    = photo.get('categories', [])
        def_state   = photo.get('state',   photo.get('place', ''))
        def_city    = photo.get('city',    '')
        def_country = photo.get('country', '')
        def_remarks = photo.get('remarks', '')
    else:
        def_cats    = prev.get('categories', [])
        def_state   = prev.get('state',   '')
        def_city    = prev.get('city',    '')
        def_country = prev.get('country', '')
        def_remarks = ''   # always blank for new photos

    today = datetime.date.today().strftime('%Y-%m-%d')
    def_date = photo.get('date_added', today) if tagged else today

    status_label = 'ALREADY TAGGED' if tagged else 'NEW PHOTO'
    status_color = '#c9a96e' if tagged else '#6ec9a9'

    # Category toggle buttons
    cat_btns = ''
    for c in CATEGORIES:
        label     = c.split('/')[-1].upper()
        selected  = 'selected' if c in def_cats else ''
        cat_btns += (
            f'<button class="cat-btn {selected}" data-cat="{c}" '
            f'onclick="toggleCat(this)">{label}</button>'
        )

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Curator — {filename}</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0d0d0d;color:#fff;font-family:'Helvetica Neue',Arial,sans-serif;
  min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}}
.card{{background:#161616;border:1px solid rgba(201,169,110,0.2);border-radius:8px;
  width:100%;max-width:520px;padding:28px 28px 24px}}
.header{{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:20px}}
.filename{{font-size:11px;color:rgba(255,255,255,0.4);letter-spacing:1px;
  word-break:break-all;flex:1;margin-right:12px}}
.progress{{font-size:11px;color:rgba(255,255,255,0.3);white-space:nowrap}}
.status{{display:inline-block;font-size:9px;letter-spacing:3px;font-weight:700;
  text-transform:uppercase;color:{status_color};margin-bottom:16px}}
.label{{font-size:8px;letter-spacing:3px;text-transform:uppercase;
  color:rgba(255,255,255,0.35);margin-bottom:8px;display:block}}
.cat-wrap{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:20px}}
.cat-btn{{padding:6px 14px;border-radius:20px;font-size:9px;font-weight:700;
  letter-spacing:2px;text-transform:uppercase;cursor:pointer;
  border:1px solid rgba(255,255,255,0.15);background:rgba(255,255,255,0.04);
  color:rgba(255,255,255,0.5);transition:all .15s}}
.cat-btn:hover{{border-color:rgba(255,255,255,0.35);color:rgba(255,255,255,0.85)}}
.cat-btn.selected{{background:rgba(201,169,110,0.15);border-color:#c9a96e;color:#c9a96e}}
.field{{margin-bottom:16px}}
input,textarea{{width:100%;background:rgba(255,255,255,0.05);
  border:1px solid rgba(201,169,110,0.15);color:#fff;padding:10px 12px;
  font-family:inherit;font-size:13px;outline:none;border-radius:3px;
  transition:border-color .2s}}
input:focus,textarea:focus{{border-color:#c9a96e}}
textarea{{min-height:72px;resize:vertical}}
.divider{{height:1px;background:rgba(255,255,255,0.07);margin:20px 0}}
.actions{{display:flex;gap:10px}}
.btn{{flex:1;height:42px;font-family:inherit;font-size:9px;font-weight:700;
  letter-spacing:3px;text-transform:uppercase;cursor:pointer;border-radius:3px;
  transition:all .2s}}
.btn-save{{background:none;border:1px solid #c9a96e;color:#c9a96e}}
.btn-save:hover{{background:#c9a96e;color:#000}}
.btn-skip{{background:none;border:1px solid rgba(255,255,255,0.15);
  color:rgba(255,255,255,0.4)}}
.btn-skip:hover{{border-color:rgba(255,255,255,0.35);color:rgba(255,255,255,0.8)}}
.btn-stop{{background:none;border:1px solid rgba(224,64,96,0.3);
  color:rgba(224,64,96,0.6)}}
.btn-stop:hover{{border-color:rgba(224,64,96,0.7);color:rgba(224,64,96,1)}}
.toast{{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);
  background:rgba(201,169,110,0.95);color:#000;font-size:10px;letter-spacing:2px;
  padding:8px 20px;border-radius:4px;opacity:0;transition:opacity .3s;pointer-events:none}}
.toast.show{{opacity:1}}
</style>
</head>
<body>
<div class="card">
  <div class="header">
    <div class="filename">{filename}</div>
    <div class="progress">{idx} / {total}</div>
  </div>
  <div class="status">{status_label}</div>

  <label class="label">Categories (click to toggle)</label>
  <div class="cat-wrap" id="cats">{cat_btns}</div>

  <div class="field">
    <label class="label">State / Country</label>
    <input id="f-state" type="text" placeholder="e.g. Tamil Nadu or Canada"
      value="{_esc(def_state)}">
  </div>
  <div class="field">
    <label class="label">City</label>
    <input id="f-city" type="text" placeholder="e.g. Megamalai or Banff"
      value="{_esc(def_city)}">
  </div>
  <div class="field">
    <label class="label">Remarks</label>
    <textarea id="f-remarks" placeholder="e.g. Great Hornbill in flight">{_esc(def_remarks)}</textarea>
  </div>
  <div class="field">
    <label class="label">Date Added</label>
    <input id="f-date" type="text" placeholder="YYYY-MM-DD"
      value="{_esc(def_date)}">
  </div>

  <div class="divider"></div>
  <div class="actions">
    <button class="btn btn-save" onclick="doSave()">Save &amp; Next</button>
    <button class="btn btn-skip" onclick="doSkip()">Skip</button>
    <button class="btn btn-stop" onclick="doStop()">Stop</button>
  </div>
</div>
<div class="toast" id="toast"></div>

<script>
function toggleCat(btn){{ btn.classList.toggle('selected'); }}

function selectedCats(){{
  return Array.from(document.querySelectorAll('.cat-btn.selected'))
    .map(b => b.getAttribute('data-cat'));
}}

function toast(msg){{
  var t=document.getElementById('toast');
  t.textContent=msg; t.classList.add('show');
  setTimeout(()=>t.classList.remove('show'),2000);
}}

function post(action, extra){{
  var body = Object.assign({{action:action}}, extra||{{}});
  fetch('/cmd',{{method:'POST',headers:{{'Content-Type':'application/json'}},
    body:JSON.stringify(body)}})
  .then(r=>r.json())
  .then(d=>{{
    if(d.status==='done'){{
      document.body.innerHTML='<div style="color:#c9a96e;font-family:Helvetica,sans-serif;'
        +'font-size:14px;letter-spacing:2px;text-align:center;margin-top:40vh">'
        +'SESSION COMPLETE — you can close this window.</div>';
    }} else if(d.status==='next'){{
      window.location.reload();
    }} else if(d.status==='saved'){{
      toast('Saved!');
      setTimeout(()=>window.location.reload(),600);
    }}
  }});
}}

function doSave(){{
  post('save',{{
    cats:    selectedCats(),
    state:   document.getElementById('f-state').value.trim(),
    city:    document.getElementById('f-city').value.trim(),
    remarks: document.getElementById('f-remarks').value.trim(),
    date:    document.getElementById('f-date').value.trim(),
  }});
}}
function doSkip(){{ post('skip'); }}
function doStop(){{ post('stop'); }}

// Keyboard shortcut: Cmd+S / Ctrl+S to save
document.addEventListener('keydown',function(e){{
  if((e.metaKey||e.ctrlKey)&&e.key==='s'){{ e.preventDefault(); doSave(); }}
}});
</script>
</body>
</html>'''

def _esc(s):
    """Escape for HTML attribute/text value."""
    return (str(s)
        .replace('&','&amp;')
        .replace('"','&quot;')
        .replace('<','&lt;')
        .replace('>','&gt;'))

# ── HTTP server ───────────────────────────────────────────────────────────────

class CuratorServer(BaseHTTPRequestHandler):

    def log_message(self, *a): pass   # suppress console noise

    def do_GET(self):
        html = build_page(self.server.state).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(html))
        self.end_headers()
        self.wfile.write(html)

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body   = json.loads(self.rfile.read(length))
        action = body.get('action')
        srv    = self.server

        today = datetime.date.today().strftime('%Y-%m-%d')

        if action == 'save':
            cats    = body.get('cats', [])
            state   = body.get('state',   '')
            city    = body.get('city',    '')
            remarks = body.get('remarks', '')
            date    = body.get('date',    today)

            # Validate date
            try:
                datetime.datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                date = today

            # Determine country vs state
            is_intl = any('International' in c for c in cats)
            if is_intl:
                country = state   # user typed country in the State/Country field
                state   = ''
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

            # Update carry-forward
            srv.prev.update({
                'categories': cats,
                'state':      state,
                'city':       city,
                'country':    country,
                'remarks':    remarks,
            })

            print(f"  ✅ {filename} | {', '.join(cats)} | {state or country} / {city}")

            # Advance to next photo
            if not self._advance(srv):
                self._json({'status': 'done'})
                srv.stop_flag = True
                return
            self._json({'status': 'next'})

        elif action == 'skip':
            # Still update carry-forward from skipped photo's existing data
            cur = srv.state['photo']
            if cur:
                srv.prev.update({
                    'categories': cur.get('categories', srv.prev.get('categories', [])),
                    'state':      cur.get('state',      srv.prev.get('state', '')),
                    'city':       cur.get('city',       srv.prev.get('city', '')),
                    'country':    cur.get('country',    srv.prev.get('country', '')),
                    'remarks':    cur.get('remarks',    ''),
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
        """Move to next photo. Returns False if no more photos."""
        srv.state['idx'] += 1
        while srv.state['idx'] <= srv.state['total']:
            i    = srv.state['idx']
            path = srv.files[i - 1]
            h    = file_hash(path)
            rel  = os.path.relpath(path, ROOT_DIR)
            fn   = os.path.basename(path)
            exists = h in srv.data

            srv.state.update({
                'hash':     h,
                'rel_path': rel,
                'filename': fn,
                'tagged':   exists,
                'photo':    srv.data.get(h, {}),
                'prev':     dict(srv.prev),
            })

            # Open photo in Preview
            subprocess.Popen(['open', path])
            return True
        return False

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

    today = datetime.date.today().strftime('%Y-%m-%d')

    # Start at first photo
    first_path = files[0]
    first_hash = file_hash(first_path)
    first_rel  = os.path.relpath(first_path, ROOT_DIR)
    first_fn   = os.path.basename(first_path)
    first_exists = first_hash in data

    server = HTTPServer(('localhost', PORT), CuratorServer)
    server.data      = data
    server.files     = files
    server.stop_flag = False
    server.prev      = {'categories':[], 'state':'', 'city':'', 'country':'', 'remarks':''}
    server.state     = {
        'idx':      1,
        'total':    total,
        'hash':     first_hash,
        'rel_path': first_rel,
        'filename': first_fn,
        'tagged':   first_exists,
        'photo':    data.get(first_hash, {}),
        'prev':     dict(server.prev),
    }

    # Open Preview for first photo
    subprocess.Popen(['open', first_path])

    # Open browser after a short delay
    def open_browser():
        time.sleep(0.6)
        subprocess.Popen(['open', f'http://localhost:{PORT}'])
    threading.Thread(target=open_browser, daemon=True).start()

    print(f"🌐 Curator running at http://localhost:{PORT}")
    print("   • Use the browser panel to tag photos")
    print("   • Cmd+S = Save & Next")
    print("   • Press Stop in browser or Ctrl+C here to quit\n")

    try:
        while not server.stop_flag:
            server.handle_request()
    except KeyboardInterrupt:
        pass

    print(f"\n✅ Session ended. {len(data)} photos in database.")

if __name__ == '__main__':
    main()
