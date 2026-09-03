#!/bin/bash
# setup_autostart.sh
# -------------------
# One-time setup: makes patch_tags.py start automatically whenever you log
# into your Mac, and keeps it running in the background — so you never have
# to manually run it again. The admin panel will just work whenever you
# open it.
#
# Run once:
#   chmod +x setup_autostart.sh
#   ./setup_autostart.sh

set -e

SCRIPTS_DIR="/Users/ncm/Pictures/Mohangraphy/Scripts"
PATCH_SCRIPT="$SCRIPTS_DIR/patch_tags.py"
PYTHON_BIN=$(which python3)
PLIST_NAME="com.mohangraphy.patchserver"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"
LOG_OUT="$SCRIPTS_DIR/patch_tags.log"
LOG_ERR="$SCRIPTS_DIR/patch_tags.err.log"

if [ ! -f "$PATCH_SCRIPT" ]; then
    echo "ERROR: could not find $PATCH_SCRIPT"
    exit 1
fi

echo "Using python3 at: $PYTHON_BIN"

# If a manually-started patch_tags.py is already running, stop it first
# so it doesn't conflict with the auto-started one on the same port.
EXISTING_PID=$(pgrep -f "$PATCH_SCRIPT" || true)
if [ -n "$EXISTING_PID" ]; then
    echo "Stopping manually-running patch_tags.py (pid $EXISTING_PID)..."
    kill $EXISTING_PID
    sleep 1
fi

mkdir -p "$HOME/Library/LaunchAgents"

cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PLIST_NAME</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_BIN</string>
        <string>$PATCH_SCRIPT</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$SCRIPTS_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$LOG_OUT</string>
    <key>StandardErrorPath</key>
    <string>$LOG_ERR</string>
</dict>
</plist>
EOF

echo "Wrote LaunchAgent: $PLIST_PATH"

# Load it now (also takes effect automatically on every future login)
launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"

sleep 1
if pgrep -f "$PATCH_SCRIPT" > /dev/null; then
    echo ""
    echo "✅ patch_tags.py is now running in the background, and will"
    echo "   auto-start every time you log in. You never need to run it"
    echo "   manually again — just open the site and use the admin panel."
    echo ""
    echo "Logs (if you ever need to check what it's doing):"
    echo "   $LOG_OUT"
    echo "   $LOG_ERR"
else
    echo ""
    echo "⚠ Something may be off — patch_tags.py doesn't appear to be running."
    echo "  Check the log for errors:"
    echo "   cat $LOG_ERR"
fi
