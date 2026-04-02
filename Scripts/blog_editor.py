#!/usr/bin/env python3
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

KNOWN_PLACES_DEFAULT = ["Aihole", "Badami", "Banff", "Megamalai", "Munnar", "Pattadhakal"]

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
