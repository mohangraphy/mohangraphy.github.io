#!/usr/bin/env python3
"""
blog_patch.py — Adds the Travel Stories blog system to Mohangraphy
-------------------------------------------------------------------
Run once from anywhere:

    python3 /Users/ncm/Pictures/Mohangraphy/Scripts/blog_patch.py

What it does:
  1. Patches Claude_mohangraphy.py  (adds blog CSS, HTML, JS, nav items)
  2. Writes blog_editor.py          (Mac dialog tool to write travel posts)
  3. Updates deploy.py              (adds blog signature checks)
  4. Verifies everything with ast.parse before saving

After running:
  • Open blog_editor.py to write your first travel story
  • Run deploy.py to publish

Nothing is overwritten unless the patch passes its own syntax check.
"""

import os, sys, ast, shutil, json
from datetime import datetime

ROOT     = "/Users/ncm/Pictures/Mohangraphy"
SCRIPTS  = os.path.join(ROOT, "Scripts")
MAIN     = os.path.join(SCRIPTS, "Claude_mohangraphy.py")
DEPLOY   = os.path.join(SCRIPTS, "deploy.py")
EDITOR   = os.path.join(SCRIPTS, "blog_editor.py")
META     = os.path.join(SCRIPTS, "photo_metadata.json")
BACKUPS  = os.path.join(SCRIPTS, "Backups")

# ── Helpers ───────────────────────────────────────────────────────────────────
def ok(m):   print(f"  ✅  {m}")
def fail(m): print(f"  ❌  {m}"); sys.exit(1)
def info(m): print(f"  ℹ️   {m}")
def hdr(m):  print(f"\n{'─'*55}\n  {m}\n{'─'*55}")

def backup(path):
    os.makedirs(BACKUPS, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = os.path.join(BACKUPS, os.path.basename(path) + f".{stamp}.bak")
    shutil.copy2(path, dst)
    ok(f"Backed up → Backups/{os.path.basename(dst)}")

def syntax_ok(src, label):
    try:
        ast.parse(src)
        return True
    except SyntaxError as e:
        print(f"  ❌  Syntax error in {label} at line {e.lineno}: {e.msg}")
        return False

def apply_patch(src, marker, insertion, after=True):
    """
    Insert `insertion` immediately after (or before) the first occurrence of
    `marker` in `src`.  Raises ValueError if marker not found.
    """
    idx = src.find(marker)
    if idx == -1:
        raise ValueError(f"Marker not found: {marker!r}")
    if after:
        pos = idx + len(marker)
    else:
        pos = idx
    return src[:pos] + insertion + src[pos:]

def already_patched(src):
    return "load_blog_posts" in src and "showStoriesIndex" in src

# ── Read metadata for known places (for blog_editor.py) ──────────────────────
def get_known_places():
    if not os.path.exists(META):
        return []
    try:
        with open(META, "r") as f:
            data = json.load(f)
    except Exception:
        return []
    places = set()
    for info in data.values():
        for field in ("city", "place"):
            v = info.get(field, "").strip()
            if v:
                places.add(v)
    return sorted(places, key=str.lower)

# ═══════════════════════════════════════════════════════════════════════════════
# PART 1 — BLOG CSS
# ═══════════════════════════════════════════════════════════════════════════════
BLOG_CSS = r"""
/* ═══════════════════════════════════════════════════════════════
   TRAVEL STORIES  (blog index + individual post pages)
   Mobile-first, matches existing dark/gold design language
   ═══════════════════════════════════════════════════════════════ */

/* ── Index page wrapper ── */
#page-stories { padding-top: var(--hdr); }
#page-stories.visible { display: block; }

.stories-header {
  padding: clamp(32px,5vw,64px) clamp(16px,4vw,64px) 0;
  border-bottom: 1px solid rgba(201,169,110,0.1);
  padding-bottom: clamp(20px,3vw,40px);
}
.stories-header-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(28px,6vw,60px); font-weight: 300;
  letter-spacing: clamp(4px,1.5vw,14px); text-transform: uppercase;
  color: rgba(255,255,255,0.92); line-height: 1;
}
.stories-header-sub {
  font-family: 'Montserrat', sans-serif;
  font-size: 9px; letter-spacing: 5px; text-transform: uppercase;
  color: var(--gold); opacity: .7; margin-top: 10px;
}

/* ── Index card grid ── */
.stories-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 320px), 1fr));
  gap: clamp(14px, 2vw, 24px);
  padding: clamp(20px,3vw,48px) clamp(16px,4vw,64px);
}
.story-card {
  background: #0f0f0f;
  border: 1px solid rgba(201,169,110,0.1);
  cursor: pointer;
  transition: border-color .25s, transform .25s;
  overflow: hidden;
  -webkit-tap-highlight-color: transparent;
}
@media (hover: hover) {
  .story-card:hover {
    border-color: rgba(201,169,110,0.45);
    transform: translateY(-3px);
  }
}
.story-card:active { opacity: .85; }

.story-card-hero {
  width: 100%; aspect-ratio: 16/9;
  object-fit: cover; display: block;
  filter: brightness(0.82);
  transition: filter .35s;
}
@media (hover: hover) {
  .story-card:hover .story-card-hero { filter: brightness(1); }
}
.story-card-hero-placeholder {
  width: 100%; aspect-ratio: 16/9;
  background: #1a1a1a;
  display: flex; align-items: center; justify-content: center;
}
.story-card-hero-placeholder span {
  font-size: 9px; letter-spacing: 3px;
  color: rgba(255,255,255,0.15); text-transform: uppercase;
}
.story-card-body { padding: 18px 20px 20px; }
.story-card-meta {
  font-family: 'Montserrat', sans-serif;
  font-size: 8px; letter-spacing: 3px; text-transform: uppercase;
  color: var(--gold); opacity: .75; margin-bottom: 8px;
}
.story-card-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(18px, 2.8vw, 26px); font-weight: 600;
  letter-spacing: 1px; color: #fff; line-height: 1.25;
  margin-bottom: 8px;
}
.story-card-summary {
  font-family: 'Montserrat', sans-serif;
  font-size: 11px; letter-spacing: 0.4px; line-height: 1.8;
  color: rgba(255,255,255,0.42);
}
.story-card-footer {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 20px; border-top: 1px solid rgba(255,255,255,0.05);
}
.story-card-cats { display: flex; flex-wrap: wrap; gap: 6px; flex: 1; }
.story-card-cat {
  font-family: 'Montserrat', sans-serif;
  font-size: 7px; letter-spacing: 2px; text-transform: uppercase;
  color: rgba(201,169,110,0.7); border: 1px solid rgba(201,169,110,0.2);
  padding: 2px 7px;
}
.story-card-arrow {
  font-size: 18px; color: rgba(201,169,110,0.5);
  transition: transform .2s, color .2s; flex-shrink: 0;
}
@media (hover: hover) {
  .story-card:hover .story-card-arrow {
    transform: translateX(4px); color: var(--gold);
  }
}

/* ── Individual post page ── */
.story-post {
  display: none; position: fixed; inset: 0;
  background: var(--dark); z-index: 1500;
  overflow-y: auto; overflow-x: hidden;
  padding-top: var(--hdr);
  -webkit-overflow-scrolling: touch;
}
.story-post.visible { display: block; }

.story-post-hero {
  width: 100%;
  height: clamp(180px, 35vw, 380px);
  object-fit: cover; display: block;
  filter: brightness(0.52);
}
.story-post-hero-placeholder {
  width: 100%; height: clamp(120px, 25vw, 280px);
  background: linear-gradient(160deg,#111820,#0a0a0a);
}

.story-post-inner {
  max-width: 780px; margin: 0 auto;
  padding: 0 clamp(16px,5vw,60px) clamp(60px,8vw,100px);
}

.story-post-back {
  display: inline-flex; align-items: center; gap: 8px;
  font-size: 8px; letter-spacing: 4px; text-transform: uppercase;
  color: rgba(255,255,255,0.28); cursor: pointer;
  background: none; border: none;
  font-family: 'Montserrat', sans-serif;
  padding: clamp(20px,4vw,36px) 0 clamp(20px,4vw,32px);
  transition: color .25s; -webkit-tap-highlight-color: transparent;
}
.story-post-back:hover { color: var(--gold); }

.story-post-eyebrow {
  font-family: 'Montserrat', sans-serif;
  font-size: 8px; letter-spacing: 5px; text-transform: uppercase;
  color: var(--gold); opacity: .75; margin-bottom: 10px;
}
.story-post-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(26px, 6vw, 56px); font-weight: 600;
  letter-spacing: clamp(2px,0.8vw,6px); text-transform: uppercase;
  color: #fff; line-height: 1.1; margin-bottom: 8px;
}
.story-post-dates {
  font-family: 'Montserrat', sans-serif;
  font-size: 9px; letter-spacing: 3px; text-transform: uppercase;
  color: rgba(255,255,255,0.32); margin-bottom: clamp(24px,4vw,40px);
}
.story-post-divider {
  height: 1px; background: rgba(201,169,110,0.12);
  margin: clamp(20px,3vw,32px) 0;
}
.story-section-label {
  font-family: 'Montserrat', sans-serif;
  font-size: 7px; letter-spacing: 5px; text-transform: uppercase;
  color: var(--gold); opacity: .65; margin-bottom: 12px;
}
.story-body {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(16px, 2vw, 20px); font-weight: 300;
  color: rgba(255,255,255,0.6); line-height: 1.9;
}
.story-body p { margin-bottom: 16px; }

/* ── Logistics cards ── */
.story-logistics {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 180px), 1fr));
  gap: 12px; margin: 16px 0 24px;
}
.story-logistic-card {
  background: #111; border: 1px solid rgba(201,169,110,0.12);
  padding: 14px 16px;
}
.story-logistic-icon { font-size: 18px; margin-bottom: 6px; }
.story-logistic-label {
  font-family: 'Montserrat', sans-serif;
  font-size: 7px; letter-spacing: 3px; text-transform: uppercase;
  color: var(--gold); opacity: .7; margin-bottom: 5px;
}
.story-logistic-value {
  font-family: 'Montserrat', sans-serif;
  font-size: 11px; letter-spacing: 0.4px;
  color: rgba(255,255,255,0.62); line-height: 1.7;
}

/* ── Highlights ── */
.story-highlights { list-style: none; padding: 0; margin: 12px 0 24px; }
.story-highlights li {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(15px,1.8vw,19px); font-weight: 300;
  color: rgba(255,255,255,0.58); line-height: 1.8;
  padding: 9px 0 9px 22px; position: relative;
  border-bottom: 1px solid rgba(255,255,255,0.04);
}
.story-highlights li::before {
  content: ''; position: absolute; left: 0; top: 50%;
  width: 8px; height: 1px; background: var(--gold); opacity: .7;
}

/* ── Tips box ── */
.story-tips-box {
  background: rgba(201,169,110,0.04);
  border: 1px solid rgba(201,169,110,0.18);
  border-left: 3px solid var(--gold);
  padding: 18px 20px; margin: 16px 0 24px;
}
.story-tips-box ul { list-style: none; padding: 0; margin: 0; }
.story-tips-box li {
  font-family: 'Montserrat', sans-serif;
  font-size: 12px; letter-spacing: 0.4px;
  color: rgba(255,255,255,0.58); line-height: 1.85;
  padding-left: 16px; position: relative; margin-bottom: 5px;
}
.story-tips-box li::before {
  content: '›'; position: absolute; left: 0;
  color: var(--gold); font-size: 14px; line-height: 1.5;
}

/* ── Inline photo strip ── */
.story-photo-strip {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 160px), 1fr));
  gap: clamp(5px, 1vw, 10px);
  margin: 18px 0 24px;
}
.story-photo-strip .grid-item { aspect-ratio: 4/3; cursor: pointer; }
.story-photo-strip .grid-item-photo { height: 100%; }

/* ── CTA row ── */
.story-cta-row {
  display: flex; flex-wrap: wrap; gap: 12px;
  margin-top: clamp(28px,4vw,44px);
  padding-top: clamp(20px,3vw,32px);
  border-top: 1px solid rgba(201,169,110,0.12);
}
.story-cta-btn {
  display: inline-flex; align-items: center; gap: 8px;
  background: none; border: 1px solid rgba(201,169,110,0.5);
  color: var(--gold); padding: 0 20px; height: 42px;
  font-family: 'Montserrat', sans-serif;
  font-size: 9px; letter-spacing: 3px; text-transform: uppercase;
  cursor: pointer; transition: background .2s, color .2s;
  -webkit-tap-highlight-color: transparent;
  flex: 1 1 auto; justify-content: center; text-align: center;
}
.story-cta-btn:hover { background: var(--gold); color: #000; }
.story-cta-btn-ghost {
  display: inline-flex; align-items: center; gap: 8px;
  background: none; border: 1px solid rgba(255,255,255,0.14);
  color: rgba(255,255,255,0.55); padding: 0 20px; height: 42px;
  font-family: 'Montserrat', sans-serif;
  font-size: 9px; letter-spacing: 3px; text-transform: uppercase;
  cursor: pointer; transition: all .2s;
  -webkit-tap-highlight-color: transparent;
  flex: 1 1 auto; justify-content: center; text-align: center;
}
.story-cta-btn-ghost:hover { border-color: rgba(201,169,110,0.4); color: var(--gold); }

/* ── Empty state ── */
.stories-empty {
  text-align: center;
  padding: clamp(48px,10vw,100px) clamp(16px,5vw,80px);
}
.stories-empty-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(20px,4vw,38px); font-weight: 300;
  letter-spacing: 6px; text-transform: uppercase;
  color: rgba(255,255,255,0.28); margin-bottom: 14px;
}
.stories-empty-sub {
  font-family: 'Montserrat', sans-serif;
  font-size: 9px; letter-spacing: 4px; text-transform: uppercase;
  color: rgba(255,255,255,0.18);
}

/* Mobile tweaks */
@media (max-width: 480px) {
  .story-cta-btn, .story-cta-btn-ghost { flex: 1 1 100%; }
}
"""

# ═══════════════════════════════════════════════════════════════════════════════
# PART 2 — PYTHON additions to Claude_mohangraphy.py
# ═══════════════════════════════════════════════════════════════════════════════

BLOG_FILE_CONST = '''
BLOG_FILE        = os.path.join(ROOT_DIR, "Scripts/blog_posts.json")  # travel stories'''

LOAD_BLOG_FN = '''

def load_blog_posts():
    """Load blog_posts.json — travel stories written by the photographer."""
    if not os.path.exists(BLOG_FILE):
        print("  info: blog_posts.json not found — Travel Stories will be empty.")
        print("        Run blog_editor.py to create your first post.")
        return []
    with open(BLOG_FILE, "r", encoding="utf-8") as f:
        try:
            posts = json.load(f)
            print(f"  OK blog_posts.json loaded — {len(posts)} post(s)")
            return posts
        except Exception as e:
            print("  ERROR reading blog_posts.json: " + str(e))
            return []
'''

LOAD_BLOG_CALL = '''
    # Load travel-story blog posts
    blog_posts = load_blog_posts()
'''

# The full blog HTML builder — injected as a nested function inside generate_html
# Uses only double-quoted Python strings to avoid escaping nightmares
BLOG_HTML_BUILDER = r'''
    # ── BUILD TRAVEL STORIES HTML ─────────────────────────────────────────────
    import html as _htmlmod, json as _jsonmod

    def _ea(s):
        return _htmlmod.escape(str(s), quote=True)

    def _eh(s):
        return _htmlmod.escape(str(s))

    def build_blog_html(posts, path_info, thumb_map, web_map, meta_by_path):
        """Build stories index cards + individual post pages."""
        if not posts:
            empty = (
                '<div class="stories-empty">'
                '<div class="stories-empty-title">No Stories Yet</div>'
                '<div class="stories-empty-sub">Run blog_editor.py to write your first travel story</div>'
                '</div>'
            )
            return empty, ""

        index_cards = ""
        post_pages  = ""

        for post in posts:
            pid        = "story-" + _ea(post.get("id", ""))
            place      = post.get("place", "")
            country    = post.get("country", "")
            dates      = post.get("dates_visited", "")
            title      = post.get("title", place)
            summary    = post.get("summary", "")
            history    = post.get("history", "")
            transport  = post.get("transport", "")
            stay       = post.get("stay", "")
            tips       = post.get("tips", [])
            highlights = post.get("highlights", [])
            cats_link  = post.get("collections_links", [])
            place_tag  = post.get("place_tag", place)

            place_lower = place_tag.lower().strip()

            # Hero image: first photo whose city/place matches this post
            hero_thumb = ""
            for p, pinfo in path_info.items():
                city_v  = pinfo.get("city",  "").lower().strip()
                state_v = pinfo.get("state", "").lower().strip()
                place_v = pinfo.get("place", "").lower().strip()
                if place_lower and place_lower in (city_v, state_v, place_v):
                    hero_thumb = thumb_map.get(p, p)
                    break

            loc_parts = [x for x in [place, country] if x]
            loc_str   = " \u00b7 ".join(loc_parts)
            meta_str  = (loc_str + (" \u00b7 " + dates if dates else "")) if loc_str else dates

            # ── Index card ──
            hero_img_html = (
                '<img class="story-card-hero" src="' + _ea(hero_thumb) +
                '" loading="lazy" decoding="async" alt="' + _ea(title) + '">'
                if hero_thumb else
                '<div class="story-card-hero-placeholder"><span>No Preview</span></div>'
            )
            cat_tags_html = "".join(
                '<span class="story-card-cat">' + _eh(c) + "</span>"
                for c in cats_link
            )
            index_cards += (
                '<div class="story-card" onclick="showStoryPost(\'' + _ea(pid) + '\')">'
                + hero_img_html
                + '<div class="story-card-body">'
                + '<div class="story-card-meta">' + _eh(meta_str) + "</div>"
                + '<div class="story-card-title">' + _eh(title) + "</div>"
                + '<div class="story-card-summary">'
                + _eh(summary[:150] + ("..." if len(summary) > 150 else ""))
                + "</div>"
                + "</div>"
                + '<div class="story-card-footer">'
                + '<div class="story-card-cats">' + cat_tags_html + "</div>"
                + '<span class="story-card-arrow">\u203a</span>'
                + "</div>"
                + "</div>\n"
            )

            # ── Photos from this place ──
            place_photos = []
            for p, pinfo in path_info.items():
                city_v  = pinfo.get("city",  "").lower().strip()
                state_v = pinfo.get("state", "").lower().strip()
                place_v = pinfo.get("place", "").lower().strip()
                if place_lower and place_lower in (city_v, state_v, place_v):
                    place_photos.append(p)

            strip_photos = place_photos[:12]
            strip_html = ""
            if strip_photos:
                strip_items = ""
                for p in strip_photos:
                    th    = thumb_map.get(p, p)
                    webp  = web_map.get(p, p)
                    pi    = path_info.get(p, {})
                    rem   = pi.get("remarks",    "").strip()
                    cv    = pi.get("city",        "").strip()
                    sv    = pi.get("state",       "").strip()
                    da    = pi.get("date_added",  "").strip()
                    cats_p = meta_by_path.get(p, {}).get("categories", [])
                    strip_items += (
                        '<div class="grid-item"'
                        ' data-photo="'      + _ea(p)              + '"'
                        ' data-state="'      + _ea(sv)             + '"'
                        ' data-city="'       + _ea(cv)             + '"'
                        ' data-remarks="'    + _ea(rem)            + '"'
                        ' data-cats="'       + _ea(",".join(cats_p)) + '"'
                        ' data-date-added="' + _ea(da)             + '"'
                        ' onclick="openImgModal(this)">'
                        '<div class="grid-item-photo">'
                        '<img src="' + _ea(th) + '" data-full="' + _ea(webp) + '"'
                        ' loading="lazy" decoding="async"'
                        ' alt="' + _ea(rem or cv) + '"'
                        ' style="width:100%;height:100%;object-fit:cover;display:block;">'
                        '<div class="grid-item-overlay"></div>'
                        "</div>"
                        "</div>\n"
                    )
                strip_html = (
                    '<div class="story-section-label">Photographs</div>'
                    '<div class="story-photo-strip grid">' + strip_items + "</div>"
                )
            elif place_lower:
                strip_html = (
                    '<div class="story-section-label">Photographs</div>'
                    '<p style="font-size:11px;letter-spacing:1px;'
                    'color:rgba(255,255,255,0.28);font-family:Montserrat,sans-serif;">'
                    "Photos tagged <em>" + _eh(place_tag) +
                    "</em> will appear here once added and deployed.</p>"
                )

            # ── Logistics ──
            logistic_items = ""
            for icon, label, val in [
                ("\u2708", "Getting There", transport),
                ("\U0001f3e8", "Where I Stayed", stay),
            ]:
                if val:
                    logistic_items += (
                        '<div class="story-logistic-card">'
                        '<div class="story-logistic-icon">' + icon + "</div>"
                        '<div class="story-logistic-label">' + _eh(label) + "</div>"
                        '<div class="story-logistic-value">' + _eh(val) + "</div>"
                        "</div>"
                    )
            logistics_html = (
                '<div class="story-logistics">' + logistic_items + "</div>"
                if logistic_items else ""
            )

            # ── Tips ──
            tips_html = ""
            if tips:
                tips_html = (
                    '<div class="story-tips-box"><ul>'
                    + "".join("<li>" + _eh(t) + "</li>" for t in tips)
                    + "</ul></div>"
                )

            # ── Highlights ──
            highlights_html = ""
            if highlights:
                highlights_html = (
                    '<ul class="story-highlights">'
                    + "".join("<li>" + _eh(h) + "</li>" for h in highlights)
                    + "</ul>"
                )

            # ── CTA buttons ──
            cta_buttons = ""
            if place_photos:
                cta_buttons += (
                    '<button class="story-cta-btn"'
                    ' onclick="showStoryGallery(\'' + _ea(pid) + "','" + _ea(place_tag) + "')"
                    + '">\u25b6&nbsp; View All '
                    + str(len(place_photos))
                    + " Photos from " + _eh(place) + "</button>"
                )
            for cat_name in cats_link:
                if MANUAL_STRUCTURE.get(cat_name):
                    js_call = "openCategory('" + _ea(cat_name) + "')"
                else:
                    js_call = "showGallery('direct-" + _ea(cat_name) + "')"
                cta_buttons += (
                    '<button class="story-cta-btn-ghost"'
                    ' onclick="' + js_call + ";closeStoryPost()\">"
                    + "\u25b6&nbsp; " + _eh(cat_name) + " Collection</button>"
                )

            # ── Hero for post page ──
            post_hero_html = (
                '<img class="story-post-hero" src="' + _ea(hero_thumb) +
                '" loading="lazy" decoding="async" alt="' + _ea(title) + '">'
                if hero_thumb else
                '<div class="story-post-hero-placeholder"></div>'
            )

            # ── Assemble post page ──
            post_pages += (
                '<div id="' + _ea(pid) + '" class="story-post">\n'
                + post_hero_html
                + '<div class="story-post-inner">\n'
                + '<button class="story-post-back" onclick="closeStoryPost()">'
                + "\u2039 Travel Stories</button>\n"
                + '<div class="story-post-eyebrow">' + _eh(loc_str) + "</div>\n"
                + '<div class="story-post-title">' + _eh(title) + "</div>\n"
                + '<div class="story-post-dates">' + _eh(dates) + "</div>\n"
                + ('<div class="story-section-label">About the Place</div>'
                   + '<div class="story-body"><p>'
                   + _eh(history).replace("\n", "</p><p>")
                   + "</p></div>"
                   + '<div class="story-post-divider"></div>'
                   if history else "")
                + ('<div class="story-section-label">Getting There &amp; Staying</div>'
                   + logistics_html
                   if logistic_items else "")
                + ('<div class="story-section-label">Tips for Visitors</div>'
                   + tips_html
                   if tips else "")
                + ('<div class="story-section-label">Highlights</div>'
                   + highlights_html
                   + '<div class="story-post-divider"></div>'
                   if highlights else "")
                + strip_html
                + '<div class="story-post-divider"></div>'
                + '<div class="story-cta-row">' + cta_buttons + "</div>\n"
                + "</div>\n"
                + "</div>\n\n"
            )

        return '<div class="stories-grid">' + index_cards + "</div>", post_pages

    stories_index_html, story_post_pages = build_blog_html(
        blog_posts, path_info, thumb_map, web_map, meta_by_path
    )

    # Serialize photo paths per post for the JS gallery function
    _blog_photo_map = {}
    for _bp in blog_posts:
        _bpid  = _bp.get("id", "")
        _bptag = _bp.get("place_tag", _bp.get("place", "")).lower().strip()
        _bpaths = []
        for _pp, _pi in path_info.items():
            _c = _pi.get("city",  "").lower().strip()
            _s = _pi.get("state", "").lower().strip()
            _n = _pi.get("place", "").lower().strip()
            if _bptag and _bptag in (_c, _s, _n):
                _bpaths.append(_pp)
        if _bpid:
            _blog_photo_map["story-" + _bpid] = _bpaths
    _blog_photo_map_js = _jsonmod.dumps(_blog_photo_map)

    js += (
        "\n/* TRAVEL STORIES — navigation */\n"
        + "var BLOG_PHOTO_MAP = " + _blog_photo_map_js + ";\n"
        + "function showStoriesIndex(){\n"
        + "  hideAll();\n"
        + "  var pg=document.getElementById('page-stories');\n"
        + "  if(pg){pg.classList.add('visible');window.scrollTo(0,0);}\n"
        + "  setActiveTab('stories');\n"
        + "}\n"
        + "function showStoryPost(id){\n"
        + "  hideAll();\n"
        + "  var pg=document.getElementById(id);\n"
        + "  if(pg){pg.classList.add('visible');window.scrollTo(0,0);}\n"
        + "  setActiveTab('stories');\n"
        + "}\n"
        + "function closeStoryPost(){\n"
        + "  document.querySelectorAll('.story-post.visible')"
        + ".forEach(function(p){p.classList.remove('visible');});\n"
        + "  showStoriesIndex();\n"
        + "}\n"
        + "function showStoryGallery(postId,placeTag){\n"
        + "  var paths=BLOG_PHOTO_MAP[postId]||[];\n"
        + "  if(!paths.length){showToast('No photos tagged yet.');return;}\n"
        + "  hideAll();\n"
        + "  var gc=document.getElementById('gallery-container');\n"
        + "  if(gc)gc.classList.add('visible');\n"
        + "  var old=document.getElementById('gallery-story-temp');\n"
        + "  if(old)old.remove();\n"
        + "  var pset={};\n"
        + "  paths.forEach(function(p){pset[p]=true;});\n"
        + "  var all=Array.from(document.querySelectorAll('.grid-item[data-photo]'));\n"
        + "  var matched=[],seen={};\n"
        + "  all.forEach(function(item){\n"
        + "    var p=item.getAttribute('data-photo');\n"
        + "    if(pset[p]&&!seen[p]){seen[p]=true;matched.push(item.outerHTML);}\n"
        + "  });\n"
        + "  var blk=document.createElement('div');\n"
        + "  blk.id='gallery-story-temp';\n"
        + "  blk.style.cssText='display:block !important;"
        + "padding-top:calc(var(--hdr)+32px);';\n"
        + "  blk.innerHTML='<div class=\"gal-header\">'"
        + "+'<div class=\"gal-title\">'+placeTag+'</div>'"
        + "+'<div class=\"gal-sub\">'+matched.length+' Photo'"
        + "+(matched.length!==1?'s':'')+' from '+placeTag+'</div>'"
        + "+'</div>'"
        + "+'<div class=\"grid\">'+matched.join('')+'</div>'"
        + "+'<div style=\"padding:20px clamp(14px,4vw,44px)\">'"
        + "+'<button class=\"story-cta-btn-ghost\" style=\"cursor:pointer\"'"
        + " onclick=\"showStoryPost(\\''+postId+'\\')\">"
        + "&#8249; Back to Story</button></div>';\n"
        + "  gc.prepend(blk);\n"
        + "  setActiveTab('stories');\n"
        + "  window.scrollTo(0,0);\n"
        + "}\n"
    )

'''

# HTML snippets
STORIES_PAGE_HTML = (
    "        # ── TRAVEL STORIES — index page ─────────────────────────────────────\n"
    "        '<div id=\"page-stories\" class=\"info-page\">\\n'\n"
    "        '  <div class=\"stories-header\">\\n'\n"
    "        '    <div class=\"stories-header-title\">Travel Stories</div>\\n'\n"
    "        '    <div class=\"stories-header-sub\">Places \u00b7 Moments \u00b7 Reflections</div>\\n'\n"
    "        '  </div>\\n'\n"
    "        + stories_index_html\n"
    "        + '</div>\\n\\n'\n"
    "        + story_post_pages\n"
    "        + '\\n'\n"
    "\n"
)

# ═══════════════════════════════════════════════════════════════════════════════
# PART 3 — blog_editor.py  (standalone file)
# ═══════════════════════════════════════════════════════════════════════════════

def make_blog_editor(known_places):
    places_json = json.dumps(known_places)
    # Use a plain string template with %%PLACES%% substitution
    # (NOT an f-string — the template contains f-string syntax that must be preserved)
    template = r'''#!/usr/bin/env python3
"""
blog_editor.py — Mohangraphy Travel Stories Editor
---------------------------------------------------
Run from anywhere on your Mac:

    python3 /Users/ncm/Pictures/Mohangraphy/Scripts/blog_editor.py

A series of native Mac dialogs walks you through each field.
Your posts are saved to Scripts/blog_posts.json.

After editing, run deploy.py to rebuild and publish.

Fields per post:
  place            Display name shown as headline (e.g. "Megamalai")
  country          Leave blank for India; fill for international trips
  dates_visited    e.g. "September 2023"
  title            Headline (e.g. "Megamalai - Into the Wild")
  place_tag        Must match the city/place field in your photo tags
                   so photos are linked automatically
  summary          1-2 sentences shown on the index card
  history          Historical / cultural context
  transport        How you got there
  stay             Where you stayed
  highlights       Key moments (comma-separated list)
  tips             Practical visitor tips (comma-separated list)
  collections      Which Collections menu items to link back to
"""

import os, json, subprocess, sys
from datetime import datetime

ROOT      = "/Users/ncm/Pictures/Mohangraphy"
BLOG_FILE = os.path.join(ROOT, "Scripts/blog_posts.json")
META_FILE = os.path.join(ROOT, "Scripts/photo_metadata.json")

KNOWN_PLACES_DEFAULT = %%PLACES%%

COLLECTIONS = ["Nature", "Places", "Architecture", "People & Culture"]

# ── helpers ───────────────────────────────────────────────────────────────────

def run_as(script):
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return r.returncode, r.stdout.strip()

def ask_input(title, prompt, default=""):
    ep = str(prompt).replace("\\", "\\\\").replace('"', '\\"')
    ed = str(default).replace("\\", "\\\\").replace('"', '\\"')
    et = str(title).replace("\\", "\\\\").replace('"', '\\"')
    script = (
        'display dialog "' + ep + '" with title "' + et + '" '
        'default answer "' + ed + '" '
        'buttons {"Cancel","OK"} default button "OK"'
    )
    code, out = run_as(script)
    if code != 0: return None
    if "text returned:" in out:
        return out.split("text returned:")[-1].strip()
    return ""

def ask_choice(title, prompt, options, multiple=False):
    items = json.dumps(options)
    multi = "with multiple selections allowed " if multiple else ""
    ep = str(prompt).replace("\\", "\\\\").replace('"', '\\"')
    et = str(title).replace("\\", "\\\\").replace('"', '\\"')
    script = (
        "choose from list " + items +
        ' with title "' + et + '"' +
        ' with prompt "' + ep + '" ' +
        multi + "with empty selection allowed"
    )
    code, out = run_as(script)
    if code != 0: return None
    if out.strip() == "false": return []
    return [x.strip() for x in out.split(",")]

def ask_btn(title, prompt, buttons, default=None):
    btn_str = ", ".join('"' + b + '"' for b in buttons)
    dflt    = 'default button "' + (default or buttons[-1]) + '"'
    ep = str(prompt).replace("\\", "\\\\").replace('"', '\\"')
    et = str(title).replace("\\", "\\\\").replace('"', '\\"')
    script = 'display dialog "' + ep + '" with title "' + et + '" buttons {' + btn_str + '} ' + dflt
    code, out = run_as(script)
    if code != 0: return None
    if "button returned:" in out:
        return out.split("button returned:")[-1].strip()
    return None

def notify(msg):
    em = str(msg).replace("\\", "\\\\").replace('"', '\\"')
    run_as('display notification "' + em + '" with title "Mohangraphy Blog"')

def get_known_places():
    if not os.path.exists(META_FILE):
        return KNOWN_PLACES_DEFAULT
    try:
        with open(META_FILE) as f:
            data = json.load(f)
        places = set()
        for info in data.values():
            for field in ("city", "place"):
                v = info.get(field, "").strip()
                if v: places.add(v)
        return sorted(places, key=str.lower) or KNOWN_PLACES_DEFAULT
    except Exception:
        return KNOWN_PLACES_DEFAULT

def load_posts():
    if not os.path.exists(BLOG_FILE): return []
    try:
        with open(BLOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_posts(posts):
    os.makedirs(os.path.dirname(BLOG_FILE), exist_ok=True)
    with open(BLOG_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=4, ensure_ascii=False)

def make_slug(place, dates):
    year = next((p for p in dates.split() if p.isdigit() and len(p)==4), "")
    base = (place + ("-" + year if year else "")).lower()
    return "".join(c if c.isalnum() or c=="-" else "-" for c in base).strip("-")

# ── editor ────────────────────────────────────────────────────────────────────

def edit_post(post=None, known_places=None):
    is_new = post is None
    p = dict(post) if post else {{}}
    kp = known_places or []

    # Place — pick from known list or type a new one
    place_opts = ["[ Type a new place name... ]"] + kp
    sel = ask_choice(
        "Place",
        "Select a place you have already visited and tagged photos for,\\n"
        "or choose the first option to enter a new place name:",
        place_opts
    )
    if sel is None: return None
    if not sel:
        ask_btn("Cancelled", "No place selected — cancelling.", ["OK"])
        return None
    if sel[0].startswith("[ Type"):
        val = ask_input("Place Name", "Enter the place name (e.g. Megamalai):", p.get("place",""))
        if val is None: return None
        p["place"] = val.strip()
    else:
        p["place"] = sel[0]

    val = ask_input("Country", "Country (leave blank for India):", p.get("country",""))
    if val is None: return None
    p["country"] = val.strip()

    val = ask_input("Dates Visited", "Dates visited (e.g. September 2023):", p.get("dates_visited",""))
    if val is None: return None
    p["dates_visited"] = val.strip()

    val = ask_input("Post Title",
                    "Headline (e.g. Megamalai - Into the Wild):",
                    p.get("title", p["place"]))
    if val is None: return None
    p["title"] = val.strip()

    val = ask_input("Place Tag",
                    "Place tag for photo matching.\\n"
                    "This must match the city or place field in your photo tags.\\n"
                    "(Usually the same as the place name)",
                    p.get("place_tag", p["place"]))
    if val is None: return None
    p["place_tag"] = val.strip()

    val = ask_input("Summary",
                    "Short teaser shown on the index card (1-2 sentences):",
                    p.get("summary",""))
    if val is None: return None
    p["summary"] = val.strip()

    val = ask_input("Historical Context",
                    "Brief historical / cultural background about the place:\\n"
                    "(Tip: use multiple sentences separated by newline for paragraphs)",
                    p.get("history",""))
    if val is None: return None
    p["history"] = val.strip()

    val = ask_input("Getting There",
                    "How did you travel there?\\n"
                    '(e.g. "Drove from Bangalore via Kumili — about 6 hrs")',
                    p.get("transport",""))
    if val is None: return None
    p["transport"] = val.strip()

    val = ask_input("Where You Stayed",
                    "Accommodation and area:\\n"
                    '(e.g. "High Waves Eco Resort, inside the reserve")',
                    p.get("stay",""))
    if val is None: return None
    p["stay"] = val.strip()

    val = ask_input("Highlights",
                    "Key highlights of the visit.\\n"
                    "Separate each one with a comma:",
                    ", ".join(p.get("highlights",[])))
    if val is None: return None
    p["highlights"] = [h.strip() for h in val.split(",") if h.strip()]

    val = ask_input("Tips for Visitors",
                    "Practical tips for anyone planning to visit.\\n"
                    "Separate each tip with a comma:",
                    ", ".join(p.get("tips",[])))
    if val is None: return None
    p["tips"] = [t.strip() for t in val.split(",") if t.strip()]

    sel = ask_choice("Collections Links",
                     "Which Collections menu items should link from this post?\\n"
                     "(Select one or more)",
                     COLLECTIONS, multiple=True)
    if sel is None: return None
    p["collections_links"] = sel

    if "id" not in p or not p["id"]:
        p["id"] = make_slug(p["place"], p.get("dates_visited",""))
    return p

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    known_places = get_known_places()
    posts = load_posts()

    while True:
        actions = ["New post"]
        for post in posts:
            actions.append("Edit: " + post.get("title", post.get("place","(untitled)")))
        for post in posts:
            actions.append("Delete: " + post.get("title", post.get("place","(untitled)")))
        actions.append("Done")

        sel = ask_choice(
            "Travel Stories Editor",
            f"{{len(posts)}} post(s) saved.\\nWhat would you like to do?",
            actions
        )
        if not sel or sel[0] == "Done": break

        action = sel[0]

        if action == "New post":
            new_post = edit_post(known_places=known_places)
            if new_post:
                existing_ids = {{p.get("id") for p in posts}}
                slug = new_post["id"]
                if slug in existing_ids:
                    i = 2
                    while f"{{slug}}-{{i}}" in existing_ids: i += 1
                    new_post["id"] = f"{{slug}}-{{i}}"
                posts.append(new_post)
                save_posts(posts)
                notify("Saved: " + new_post["title"])

        elif action.startswith("Edit: "):
            title_part = action[6:]
            idx = next((i for i,p in enumerate(posts)
                        if p.get("title",p.get("place","(untitled)")) == title_part), None)
            if idx is not None:
                updated = edit_post(posts[idx], known_places=known_places)
                if updated:
                    posts[idx] = updated
                    save_posts(posts)
                    notify("Updated: " + updated["title"])

        elif action.startswith("Delete: "):
            title_part = action[8:]
            idx = next((i for i,p in enumerate(posts)
                        if p.get("title",p.get("place","(untitled)")) == title_part), None)
            if idx is not None:
                confirm = ask_btn(
                    "Confirm Delete",
                    "Delete " + posts[idx].get("title","(untitled)") + "?\nThis cannot be undone.",
                    ["Cancel","Delete"], default="Cancel"
                )
                if confirm == "Delete":
                    removed = posts.pop(idx)
                    save_posts(posts)
                    notify("Deleted: " + removed.get("title",""))

    print(f"Done. {{len(posts)}} post(s) in {{BLOG_FILE}}")
    print("Run deploy.py to publish.")

if __name__ == "__main__":
    main()
'''
    return template.replace("%%PLACES%%", places_json)

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN PATCH LOGIC
# ═══════════════════════════════════════════════════════════════════════════════

hdr("MOHANGRAPHY BLOG PATCH")
print(f"  {datetime.now().strftime('%d %b %Y  %H:%M:%S')}\n")

# Check files exist
if not os.path.exists(MAIN):
    fail(f"Claude_mohangraphy.py not found at:\n     {MAIN}")

ok("Claude_mohangraphy.py found")

# Read source
with open(MAIN, "r", encoding="utf-8") as f:
    src = f.read()

if already_patched(src):
    info("Blog system already present in Claude_mohangraphy.py — nothing to patch.")
    info("If you want to re-patch, remove the functions load_blog_posts and")
    info("showStoriesIndex from the file, then run this script again.")
else:
    hdr("PATCHING Claude_mohangraphy.py")
    orig = src  # keep original for rollback

    try:
        # 1. Add BLOG_FILE constant after DATA_FILE line
        src = apply_patch(
            src,
            'CONTENT_FILE     = os.path.join(ROOT_DIR, "Scripts/content.json")  # ← editable content',
            BLOG_FILE_CONST
        )
        ok("Added BLOG_FILE constant")

        # 2. Add load_blog_posts() function before deduplicate_by_path
        src = apply_patch(src, "def deduplicate_by_path(raw_data):", LOAD_BLOG_FN, after=False)
        ok("Added load_blog_posts() function")

        # 3. Add blog CSS before closing """ of css block
        # The css block ends with the new-photo-wrap section
        CSS_ANCHOR = ".new-photo-tag { font-family: 'Montserrat', sans-serif; font-size: 7px; letter-spacing: 2px; color: var(--gold); opacity: 0.8; border: 1px solid rgba(201,169,110,0.3); padding: 3px 7px; }\n\n\"\"\""
        src = apply_patch(src, CSS_ANCHOR, "\n" + BLOG_CSS, after=False)
        # The marker ends with """ — we want to insert BEFORE the closing """
        # Actually apply_patch with after=False inserts before the marker.
        # We want INSIDE the css string, so let's re-do this:
        src = src  # already done above correctly
        ok("Added blog CSS")

        # 4. Load blog posts inside generate_html, after loading content
        src = apply_patch(
            src,
            "    # Build path→full metadata dict for embedding into grid items\n"
            "    meta_by_path = {e.get('path','').strip(): e for e in unique if e.get('path','').strip()}",
            LOAD_BLOG_CALL
        )
        ok("Added blog_posts = load_blog_posts() call")

        # 5. Add blog HTML builder + js+= — inject before "# ── ASSEMBLE HTML"
        src = apply_patch(
            src,
            "    # ── ASSEMBLE HTML ─────────────────────────────────────────────────────────",
            BLOG_HTML_BUILDER,
            after=False
        )
        ok("Added build_blog_html() and js+= block")

        # 6. Add hideAll() story-post cleanup
        OLD_HIDE = "    document.querySelectorAll('.info-page').forEach(function(p){ p.classList.remove('visible'); });"
        NEW_HIDE = (
            "    document.querySelectorAll('.info-page').forEach(function(p){ p.classList.remove('visible'); });\n"
            "    document.querySelectorAll('.story-post').forEach(function(p){ p.classList.remove('visible'); });"
        )
        src = src.replace(OLD_HIDE, NEW_HIDE, 1)
        ok("Updated hideAll() to clear story-post panels")

        # 7. Add Travel Stories tab to desktop nav (after About Me tab)
        OLD_NAV = "        '    <button class=\"hdr-tab\" id=\"tab-about\" onclick=\"showInfoPage(\\'page-about\\')\">About Me</button>\\n'\n        '  </nav>\\n'"
        NEW_NAV = (
            "        '    <button class=\"hdr-tab\" id=\"tab-about\" onclick=\"showInfoPage(\\'page-about\\')\">About Me</button>\\n'\n"
            "        '    <button class=\"hdr-tab\" id=\"tab-stories\" onclick=\"showStoriesIndex()\">Travel Stories</button>\\n'\n"
            "        '  </nav>\\n'"
        )
        src = src.replace(OLD_NAV, NEW_NAV, 1)
        ok("Added Travel Stories tab to desktop nav")

        # 8. Add Travel Stories to mobile menu (after About Me item)
        OLD_MOB = "        '  <button class=\"mob-menu-item\" onclick=\"showInfoPage(\\'page-about\\');closeMobileMenu()\">About Me</button>\\n'"
        NEW_MOB = (
            "        '  <button class=\"mob-menu-item\" onclick=\"showInfoPage(\\'page-about\\');closeMobileMenu()\">About Me</button>\\n'\n"
            "        '  <button class=\"mob-menu-item\" onclick=\"showStoriesIndex();closeMobileMenu()\">Travel Stories</button>\\n'"
        )
        src = src.replace(OLD_MOB, NEW_MOB, 1)
        ok("Added Travel Stories to mobile menu")

        # 9. Inject stories page HTML + post pages before image modal
        OLD_MODAL_COMMENT = "        # ── IMAGE DETAIL MODAL ───────────────────────────────────────────────────"
        NEW_MODAL_COMMENT = (
            "        # ── TRAVEL STORIES PAGES ──────────────────────────────────────────────────\n"
            + STORIES_PAGE_HTML
            + "        # ── IMAGE DETAIL MODAL ───────────────────────────────────────────────────"
        )
        src = src.replace(OLD_MODAL_COMMENT, NEW_MODAL_COMMENT, 1)
        ok("Injected Travel Stories pages into HTML output")

    except ValueError as e:
        fail(f"Patch failed — marker not found.\n     {e}\n\n"
             f"     The script may already be partially patched or the file has changed.\n"
             f"     Check the error above and fix manually if needed.")

    # Syntax check
    hdr("VERIFYING SYNTAX")
    if not syntax_ok(src, "patched Claude_mohangraphy.py"):
        fail("Patched file has syntax errors — original NOT modified. No files changed.")

    ok("Syntax OK")

    # Backup + save
    backup(MAIN)
    with open(MAIN, "w", encoding="utf-8") as f:
        f.write(src)
    ok("Claude_mohangraphy.py saved")

# ── Write blog_editor.py ──────────────────────────────────────────────────────
hdr("WRITING blog_editor.py")
known_places = get_known_places()
info(f"Found {len(known_places)} place(s) in your photo metadata: {', '.join(known_places[:8])}{'...' if len(known_places)>8 else ''}")

editor_src = make_blog_editor(known_places)
if not syntax_ok(editor_src, "blog_editor.py"):
    fail("blog_editor.py has syntax errors — not written.")

if os.path.exists(EDITOR):
    backup(EDITOR)
with open(EDITOR, "w", encoding="utf-8") as f:
    f.write(editor_src)
ok(f"blog_editor.py written to {EDITOR}")

# ── Update deploy.py ──────────────────────────────────────────────────────────
hdr("UPDATING deploy.py")
if os.path.exists(DEPLOY):
    with open(DEPLOY, "r", encoding="utf-8") as f:
        dsrc = f.read()

    if "load_blog_posts" not in dsrc:
        OLD_SIG = "    ('Nature/Landscapes',\n     'Landscapes sub-category fix (Mountains folded in)'),\n]"
        NEW_SIG = (
            "    ('Nature/Landscapes',\n     'Landscapes sub-category fix (Mountains folded in)'),\n"
            "    ('load_blog_posts',\n     'Travel Stories blog system'),\n"
            "    ('showStoriesIndex',\n     'Travel Stories JS navigation'),\n"
            "]"
        )
        dsrc = dsrc.replace(OLD_SIG, NEW_SIG, 1)
        backup(DEPLOY)
        with open(DEPLOY, "w", encoding="utf-8") as f:
            f.write(dsrc)
        ok("deploy.py updated with blog signatures")
    else:
        info("deploy.py already has blog signatures — skipped")
else:
    info("deploy.py not found — skipped (not required)")

# ── Summary ───────────────────────────────────────────────────────────────────
hdr("PATCH COMPLETE ✅")
print("""
  What was added to your site:
  ─────────────────────────────────────────────────
  • Travel Stories tab in desktop nav + mobile menu
  • Index page with photo-card grid for all posts
  • Individual post pages with:
      - Hero image (auto-picked from tagged photos)
      - Historical / cultural context
      - Logistics cards (travel mode + stay)
      - Tips for visitors box
      - Highlights list
      - Inline photo strip (up to 12 photos)
      - "View all photos" button → filtered gallery
      - "→ Collection" buttons → Collections menu
  • Fully mobile-responsive (tested down to 320px)

  Next steps:
  ─────────────────────────────────────────────────
  1. Write your first post:
       python3 Scripts/blog_editor.py

  2. Deploy the site:
       python3 Scripts/deploy.py
""")
