# Safari-to-MPV macOS Automation

A lightweight, robust background automation for macOS that automatically plays YouTube links from Safari in `mpv` in full screen, pauses Safari's playback to prevent dual audio streams, handles window focus, and falls back to Safari automatically if GPU rendering lag is detected.

## Features

- **Safari Integration**: Detects active YouTube links (standard videos, Shorts, and shortened `youtu.be` links) in Safari.
- **Single Instance Control**: Plays subsequent videos in the *same* `mpv` window instead of launching multiple windows.
- **Auto-Pause & Play**: Automatically pauses YouTube in Safari when `mpv` playback starts.
- **Window Management**: Automatically focuses `mpv` on launch and returns focus to Safari when `mpv` is closed.
- **Smart GPU Lag Fallback**: Detects if your GPU is overloading and dropping too many frames. If rendering stutter is detected, it auto-closes `mpv`, focuses Safari, resumes the native player, and blacklists the video to prevent a launch loop.
- **Playback Control Guard**: If you manually close/quit `mpv` (e.g. by pressing `q` or `Ctrl+C`), it remembers your choice and will not attempt to reopen `mpv` for that URL as long as the page is open.
- **Persistent LaunchAgent**: Runs silently as a macOS user daemon.

## Features

- **Safari Integration**: Detects active YouTube links (standard videos, Shorts, and shortened `youtu.be` links) in Safari.
- **Single Instance Control**: Plays subsequent videos in the *same* `mpv` window instead of launching multiple windows.
- **Auto-Pause & Play**: Automatically pauses YouTube in Safari when `mpv` playback starts.
- **Window Management**: Automatically focuses `mpv` on launch and returns focus to Safari when `mpv` is closed.
- **Smart GPU Lag Fallback**: Detects if your GPU is overloading and dropping too many frames. If rendering stutter is detected, it auto-closes `mpv`, focuses Safari, resumes the native player, and blacklists the video to prevent a launch loop.
- **Playback Control Guard**: If you manually close/quit `mpv` (e.g. by pressing `q` or `Ctrl+C`), it remembers your choice and will not attempt to reopen `mpv` for that URL as long as the page is open.
- **Persistent LaunchAgent**: Runs silently as a macOS user daemon.

## Installation

1. Clone or download this repository.
2. Ensure you have the dependencies installed:
   ```bash
   brew install mpv yt-dlp
   ```
3. Enable JavaScript from Apple Events in Safari:
   - Go to **Safari** -> **Settings** -> **Advanced**.
   - Check **Show features for web developers** (or **Show Develop menu in menu bar**).
   - Click the **Developer** menu in the menu bar, and check **Allow JavaScript from Apple Events** (authenticate when prompted).
4. Run the installer script:
   ```bash
   ./install_safari_mpv.sh
   ```

## Enable / Disable / Uninstall

- **Apply Updates / Enable**:
  ```bash
  ./install_safari_mpv.sh
  ```
- **Disable Background Service**:
  ```bash
  launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.user.safari-mpv.plist
  ```
- **Uninstall Completely**:
  ```bash
  ./uninstall_safari_mpv.sh
  ```

## File Structure

- `safari_mpv_daemon.py`: The background Python daemon.
- `com.user.safari-mpv.plist`: The macOS LaunchAgent plist configuration.
- `install_safari_mpv.sh`: Configures paths, permissions, and loads the service.
- `uninstall_safari_mpv.sh`: Cleans up all files, logs, and configurations.
