# Footprints Feature — How It Works

*A simple reference for the Mohangraphy "Footprints" map, written September 2026.*

---

## What changed

Before: the list of places on the Footprints map (India + World tabs) was
typed directly into the website's code. Adding a new place meant editing
code by hand.

Now: the places live in a separate, simple data file
(`journeys_data.json`). You can add a new place through a form on the
website's admin panel — no code editing required.

---

## The one-time setup (already done)

This part only had to be done once, and doesn't need to be repeated:

1. **Extracted the old hardcoded places** into a new file,
   `journeys_data.json`, stored at the root of the website folder
   (next to `index.html`).
2. **Updated the website code** so the map now *loads* the places from
   that file when the page opens, instead of having them baked in.
3. **Added a "📍 Manage Footprints" button** to the admin panel, next to
   the existing "Edit Tags" button. It opens a small form: place name,
   India or World, State/Country, and coordinates (auto-filled — see
   below).
4. **Taught the background helper program** (`patch_tags.py`) how to
   save a new place into `journeys_data.json` when you click Save on
   that form.
5. **Set up `patch_tags.py` to start automatically** every time you log
   into your Mac, and to keep running quietly in the background. This
   means you never have to manually start anything — the admin panel
   just works whenever you open it.

---

## How to add a new place, going forward

1. Open the website.
2. Unlock the admin panel (as usual).
3. Click **📍 Manage Footprints**.
4. Fill in:
   - **Place Name** (e.g. "Hampi")
   - **India / World** toggle
   - **State** (if India) or **Country** (if World)
5. Click out of that field — the **latitude and longitude fill in
   automatically** (using an online map lookup). You can also click
   "Re-check Coordinates" if you want it to look again, or type the
   numbers in yourself if needed.
6. Click **Save**. You should see "Place added."
7. Click **Deploy Now** (same button you already use for tag edits) to
   publish the change to the live site.

That's the whole process — no scripts, no code editing.

---

## What you should NOT need to do anymore

- ❌ Editing `Claude_mohangraphy.py` by hand to add a place
- ❌ Manually starting `patch_tags.py` before using the admin panel —
  it now runs automatically in the background at all times

The **only** time you'd still run a script yourself is if you (or I,
in a future chat) make a *code* change to `Claude_mohangraphy.py` or
`patch_tags.py` — that's a developer task, not a routine "add a place"
task.

---

## Behind the scenes (for reference)

| Piece | What it is | Where it lives |
|---|---|---|
| `journeys_data.json` | The actual list of places (India + World) | Website root folder, next to `index.html` |
| `Claude_mohangraphy.py` | Builds the website pages; the map-loading code and the admin form live here | `Scripts/` folder |
| `patch_tags.py` | Small background helper program that saves admin panel changes (tags, places) and can trigger a deploy | `Scripts/` folder |
| LaunchAgent | A macOS setting that auto-starts `patch_tags.py` at login | `~/Library/LaunchAgents/com.mohangraphy.patchserver.plist` |

### If the admin panel ever says "Server offline"

This means the background helper program (`patch_tags.py`) isn't
running for some reason (e.g. your Mac restarted and something went
wrong with the auto-start). To check and fix it:

```bash
# Check if it's running (should show a line with "Python ... LISTEN")
lsof -i :9393

# If nothing shows up, start it again manually as a one-off:
cd /Users/ncm/Pictures/Mohangraphy/Scripts
python3 patch_tags.py
```

If it keeps happening, that's worth flagging in a future chat so the
auto-start can be looked at again.

### Log files (only needed if troubleshooting)

```bash
cat /Users/ncm/Pictures/Mohangraphy/Scripts/patch_tags.log
cat /Users/ncm/Pictures/Mohangraphy/Scripts/patch_tags.err.log
```

---

## The one-time setup scripts (for the record)

These were each run once, in order, and don't need to be run again
unless something needs to be redone from scratch:

1. `migrate_journeys.py` — extracted the old hardcoded places into
   `journeys_data.json`
2. `patch_journeys_js.py` — made the website load places from that
   file instead of hardcoded code
3. `patch_journeys_admin_ui.py` + `patch_journeys_admin_ui_v2.py` —
   added the "Manage Footprints" button and form, with auto-coordinate
   lookup
4. `patch_tags_journeys.py` — taught `patch_tags.py` how to save new
   places
5. `setup_autostart.sh` — set up `patch_tags.py` to run automatically
   in the background
