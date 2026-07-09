# Safari-to-MPV macOS Automation

A high-performance, seamless background service for macOS that automatically intercepts YouTube links opened in Safari and plays them in the native `mpv` media player in full screen. 

As soon as the video starts playing in `mpv`, Safari automatically pauses its playback so you never hear dual audio streams. If you close the video player or if it stutters due to heavy GPU load, focus returns to Safari and playback resumes natively in your browser.

---

## Features

- ⚡️ **Zero-Latency Interception**: Automatically detects standard videos, Shorts, and shortened `youtu.be` links.
- 📺 **No Window Clutter**: Plays subsequent videos in the *same* `mpv` player window rather than opening duplicates.
- ⏸️ **Auto-Pause & Play**: Safari automatically pauses the browser-side player as soon as `mpv` starts rendering.
- 🔄 **Bidirectional Window Focus**: Forces `mpv` to focus in full screen on startup, and automatically returns focus to Safari upon exit.
- 🛡️ **Stutter & GPU Overload Fallback**: Monitors rendering performance. If `mpv` drops more than 15 frames in a 3-second window due to GPU load (e.g., hitting 100% capacity), it auto-closes the player, focuses Safari, and resumes native playback.
- 🚫 **Manual Playback Override**: If you manually close `mpv` (e.g., by pressing `q` or `Ctrl+C`), it remembers your choice and will not attempt to reopen `mpv` for that URL as long as that tab is open.
- 🎛️ **Background Daemon**: Runs silently as a native macOS LaunchAgent, starting automatically when you log in.

---

## Prerequisites (Step-by-Step for Beginners)

Before installing, you need to configure a few dependencies and settings on your Mac. Follow these simple steps:

### Step 1: Install Homebrew (macOS Package Manager)
If you don't have Homebrew installed, open the **Terminal** app (press `Cmd + Space`, type `Terminal`, and hit `Enter`) and paste this command:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
*Follow the on-screen prompts to complete the installation.*

### Step 2: Install mpv and yt-dlp
Paste this command into your Terminal to install the media player and its YouTube integration library:
```bash
brew install mpv yt-dlp
```

### Step 3: Enable JavaScript from Apple Events in Safari
To allow the background service to pause and resume videos in Safari:
1. Open **Safari**.
2. In the top-left menu bar, click **Safari** -> **Settings** -> **Advanced**.
3. At the very bottom, check the box for **Show features for web developers** (or **Show Develop menu in menu bar** on older macOS versions).
4. Click on the new **Developer** menu that appears in the menu bar.
5. Click **Allow JavaScript from Apple Events** (you will be prompted to enter your Mac password).

---

## Installation

Once you have completed the prerequisites, you are ready to install the automation:

1. Open your Terminal and navigate to this folder, or run:
   ```bash
   cd ~/safari-to-mpv-automation
   ```
2. Run the installer script:
   ```bash
   ./install_safari_mpv.sh
   ```
   *This script verifies your installations, creates the background configuration files, and starts the background service.*

---

## How to Use It

1. Open Safari and click or search any YouTube video.
2. After a brief buffering delay, `mpv` will launch in full screen, and Safari's video will automatically pause.
3. **To Close**: Press `q` or click the close button on the `mpv` window.
   * Focus will instantly return to Safari.
   * If you want to continue watching that video in Safari, it will not open in `mpv` again (as long as you keep that tab open).
4. **To Switch Videos**: Simply click another YouTube video in Safari while `mpv` is running. The video player will instantly switch to the new video in full screen.

---

## Managing the Service

### View Service Logs (For Debugging)
To see what the automation is doing in real-time, inspect the logs:
```bash
tail -f ~/Library/Logs/SafariMpv/daemon.log
```

### Temporary Disable
If you want to temporarily stop the background automation, run:
```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.user.safari-mpv.plist
```

### Re-Enable / Apply Updates
If you update the scripts or want to turn it back on, run:
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

- `safari_mpv_daemon.py`: The background Python service script that polls Safari and manages `mpv`'s lifecycle.
- `com.user.safari-mpv.plist`: The LaunchAgent configuration mapping paths and permissions.
- `install_safari_mpv.sh`: The installer script that bootstraps the service.
- `uninstall_safari_mpv.sh`: The clean uninstaller script.
