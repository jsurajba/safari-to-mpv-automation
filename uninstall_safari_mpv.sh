#!/bin/bash

echo "=== Safari-to-MPV Automation Uninstaller ==="

# Define paths
APP_DIR="$HOME/Library/Application Support/SafariMpv"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$LAUNCH_AGENTS_DIR/com.user.safari-mpv.plist"
LOG_DIR="$HOME/Library/Logs/SafariMpv"

echo "Unloading LaunchAgent..."
USER_ID=$(id -u)

# Unload
launchctl bootout "gui/$USER_ID" "$PLIST_PATH" &> /dev/null || true
launchctl unload "$PLIST_PATH" &> /dev/null || true

echo "Removing LaunchAgent plist..."
if [ -f "$PLIST_PATH" ]; then
    rm "$PLIST_PATH"
    echo "Removed $PLIST_PATH"
fi

echo "Removing application directory..."
if [ -d "$APP_DIR" ]; then
    rm -rf "$APP_DIR"
    echo "Removed $APP_DIR"
fi

echo "Removing log directory..."
if [ -d "$LOG_DIR" ]; then
    rm -rf "$LOG_DIR"
    echo "Removed $LOG_DIR"
fi

# Clean up temporary socket
if [ -S "/tmp/mpv-safari.sock" ]; then
    rm "/tmp/mpv-safari.sock"
    echo "Removed Unix socket"
fi

echo "--------------------------------------------------------"
echo "UNINSTALLATION COMPLETE!"
echo "--------------------------------------------------------"
echo "The automation has been completely removed from your system."
echo "--------------------------------------------------------"
