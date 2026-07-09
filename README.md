# Safari-to-MPV macOS Automation

A background service for macOS that automatically plays YouTube links from Safari in the native `mpv` media player in full screen. 

When a video starts playing in `mpv`, the active Safari tab is automatically paused to prevent double audio. If you close `mpv` or if rendering lag is detected due to heavy GPU load, focus returns to Safari and the video resumes playing natively in the browser.

---

## Features

- **Safari Interception**: Automatically detects YouTube video URLs, Shorts, and shortened `youtu.be` links in your active tab.
- **Single Window Reuse**: Reuses the active `mpv` window for new videos instead of opening multiple windows.
- **Auto-Pause & Play**: Pauses the YouTube video player in Safari when `mpv` starts playback.
- **Window Focus Management**: Brings `mpv` to the front on launch and returns focus to Safari when `mpv` is closed.
- **GPU Lag Fallback**: Monitors rendering performance. If `mpv` drops more than 15 frames in a 3-second window, it closes `mpv`, focuses Safari, and resumes native playback.
- **Manual Override**: If you close `mpv` manually (e.g. by pressing `q` or `Ctrl+C`), it remembers your choice and will not reopen `mpv` for that URL as long as the tab remains open.
- **macOS launchd Daemon**: Runs as a user LaunchAgent starting automatically on login.

---

## Prerequisites (Step-by-Step for Beginners)

Before installing, you need to configure a few dependencies and settings on your Mac. Follow these steps:

### Step 1: Install Homebrew (macOS Package Manager)
If you do not have Homebrew installed, open the **Terminal** app (press `Cmd + Space`, type `Terminal`, and hit `Enter`) and run this command:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
*Follow the on-screen prompts to complete the installation.*

### Step 2: Install mpv and yt-dlp
Run this command in the Terminal to install `mpv` and the YouTube parser library:
```bash
brew install mpv yt-dlp
```

### Step 3: Enable JavaScript from Apple Events in Safari
To allow the service to pause and resume videos in Safari:
1. Open **Safari**.
2. Click **Safari** -> **Settings** -> **Advanced** in the menu bar.
3. Check the box for **Show features for web developers** (or **Show Develop menu in menu bar**).
4. Click on the **Developer** menu in the top menu bar.
5. Select **Allow JavaScript from Apple Events** (you will be prompted to enter your Mac password).

---

## Installation

Once the prerequisites are set up, run the installer:

1. Open your Terminal and navigate to the project directory:
   ```bash
   cd ~/safari-to-mpv-automation
   ```
2. Run the installer script:
   ```bash
   ./install_safari_mpv.sh
   ```
   *This script verifies your setup, copies the daemon script and plist template into place, and loads the LaunchAgent.*

---

## How to Use

1. Click or navigate to any YouTube video in Safari.
2. After a brief loading delay, `mpv` will launch in full screen and Safari's video will pause.
3. **To Close**: Press `q` or close the `mpv` window. Focus will return to Safari.
   - If you want to continue watching that video in Safari, it will not open in `mpv` again (as long as you keep that tab open).
4. **To Switch Videos**: Click another YouTube video in Safari while `mpv` is running. The video player will automatically switch to the new video.

---

## Managing the Service

### View Service Logs
To inspect daemon activity or check for warnings:
```bash
tail -f ~/Library/Logs/SafariMpv/daemon.log
```

### Temporary Disable
To stop the background automation:
```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.user.safari-mpv.plist
```

### Re-Enable / Apply Updates
To restart the service or apply code updates:
```bash
./install_safari_mpv.sh
```

### Uninstall
To completely remove all logs, LaunchAgents, and scripts:
```bash
./uninstall_safari_mpv.sh
```

---

## File Structure

- `safari_mpv_daemon.py`: Background Python daemon.
- `com.user.safari-mpv.plist`: macOS LaunchAgent plist configuration.
- `install_safari_mpv.sh`: Installer script.
- `uninstall_safari_mpv.sh`: Uninstaller script.
