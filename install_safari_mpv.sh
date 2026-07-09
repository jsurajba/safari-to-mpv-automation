#!/bin/bash

# Set strict error handling
set -e

echo "=== Safari-to-MPV Automation Installer ==="

# Check dependencies
echo "Checking dependencies..."
MISSING_DEPS=()

if ! command -v mpv &> /dev/null; then
    MISSING_DEPS+=("mpv")
fi

if ! command -v yt-dlp &> /dev/null; then
    MISSING_DEPS+=("yt-dlp")
fi

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo "Missing dependencies: ${MISSING_DEPS[*]}"
    if command -v brew &> /dev/null; then
        echo "Homebrew is installed. Would you like to install the missing dependencies via Homebrew? (y/n)"
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            echo "Installing dependencies..."
            brew install "${MISSING_DEPS[@]}"
        else
            echo "Error: Cannot proceed without dependencies. Please install ${MISSING_DEPS[*]} manually."
            exit 1
        fi
    else
        echo "Error: Homebrew is not found. Please install Homebrew and then install mpv and yt-dlp."
        echo "Visit https://brew.sh for installation instructions."
        exit 1
    fi
else
    echo "All dependencies (mpv, yt-dlp) are satisfied."
fi

# Define paths
APP_DIR="$HOME/Library/Application Support/SafariMpv"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_NAME="com.user.safari-mpv.plist"
DAEMON_NAME="safari_mpv_daemon.py"

echo "Creating application directory..."
mkdir -p "$APP_DIR"
mkdir -p "$HOME/Library/Logs/SafariMpv"

echo "Copying files..."
# Check if the files exist in the current folder before copying
if [ -f "$DAEMON_NAME" ]; then
    cp "$DAEMON_NAME" "$APP_DIR/$DAEMON_NAME"
elif [ -f "$APP_DIR/$DAEMON_NAME" ]; then
    echo "Daemon already exists in application directory."
else
    echo "Error: $DAEMON_NAME not found in current folder or destination."
    exit 1
fi

if [ -f "$PLIST_NAME" ]; then
    PYTHON_PATH=$(which python3 || echo "/opt/homebrew/bin/python3")
    sed -e "s|{{HOME}}|$HOME|g" -e "s|{{PYTHON_PATH}}|$PYTHON_PATH|g" "$PLIST_NAME" > "$LAUNCH_AGENTS_DIR/$PLIST_NAME"
elif [ -f "$LAUNCH_AGENTS_DIR/$PLIST_NAME" ]; then
    echo "LaunchAgent plist already exists in LaunchAgents directory."
else
    echo "Error: $PLIST_NAME not found in current folder or destination."
    exit 1
fi

echo "Setting permissions..."
chmod +x "$APP_DIR/$DAEMON_NAME"
chmod 644 "$LAUNCH_AGENTS_DIR/$PLIST_NAME"

# Bootstrap / Load LaunchAgent
echo "Loading LaunchAgent..."
USER_ID=$(id -u)

# Unload first if already loaded to apply changes
launchctl bootout "gui/$USER_ID" "$LAUNCH_AGENTS_DIR/$PLIST_NAME" &> /dev/null || true
launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_NAME" &> /dev/null || true

# Modern way bootstrap, fallback to old load
if launchctl bootstrap "gui/$USER_ID" "$LAUNCH_AGENTS_DIR/$PLIST_NAME" &> /dev/null; then
    echo "LaunchAgent loaded successfully (modern)."
else
    if launchctl load "$LAUNCH_AGENTS_DIR/$PLIST_NAME" &> /dev/null; then
        echo "LaunchAgent loaded successfully (legacy)."
      else
        echo "Warning: Could not load LaunchAgent. You may need to load it manually using:"
        echo "launchctl bootstrap gui/$USER_ID $LAUNCH_AGENTS_DIR/$PLIST_NAME"
      fi
fi

echo "--------------------------------------------------------"
echo "INSTALLATION COMPLETE!"
echo "--------------------------------------------------------"
echo "IMPORTANT: For the automatic Safari video pause feature to work, you must:"
echo "1. Open Safari -> Settings -> Advanced."
echo "2. Check 'Show features for web developers' (or 'Show Develop menu' on older macOS)."
echo "3. Go to the 'Developer' menu in the Safari menu bar."
echo "4. Enable 'Allow JavaScript from Apple Events'."
echo "--------------------------------------------------------"
echo "The automation is now running in the background and will start automatically at login."
echo "Logs are available at: ~/Library/Logs/SafariMpv/daemon.log"
echo "--------------------------------------------------------"
