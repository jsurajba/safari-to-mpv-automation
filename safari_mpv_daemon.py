#!/usr/bin/env python3
import os
import sys
import time
import socket
import json
import subprocess
import re
import urllib.parse
import logging
from logging.handlers import RotatingFileHandler

# Add Homebrew and standard paths to PATH environment variable
extra_paths = ["/opt/homebrew/bin", "/usr/local/bin"]
paths = os.environ.get("PATH", "").split(os.pathsep)
for p in extra_paths:
    if p not in paths:
        paths.insert(0, p)
os.environ["PATH"] = os.pathsep.join(paths)

# Path configuration
HOME = os.path.expanduser("~")
APP_DIR = os.path.join(HOME, "Library/Application Support/SafariMpv")
LOG_DIR = os.path.join(HOME, "Library/Logs/SafariMpv")
LOG_FILE = os.path.join(LOG_DIR, "daemon.log")
SOCKET_PATH = "/tmp/mpv-safari.sock"

# Make sure directories exist
os.makedirs(APP_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Set up logging with rotation
logger = logging.getLogger("SafariMpv")
logger.setLevel(logging.INFO)

# Rotate at 2MB, keep 3 backups
handler = RotatingFileHandler(LOG_FILE, maxBytes=2*1024*1024, backupCount=3)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Also log to stdout for debugging when run manually
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

js_warning_shown = False

def extract_video_id(url):
    if not url:
        return None
    try:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.lower()
        if 'youtube.com' not in domain and 'youtu.be' not in domain:
            return None
        
        if 'youtu.be' in domain:
            # Shortened URL: youtu.be/<id>
            path = parsed.path.strip('/')
            if path:
                return path.split('?')[0]
        elif 'shorts/' in parsed.path:
            # Shorts URL: youtube.com/shorts/<id>
            parts = parsed.path.strip('/').split('/')
            for i, part in enumerate(parts):
                if part == 'shorts' and i + 1 < len(parts):
                    return parts[i+1].split('?')[0]
        elif 'watch' in parsed.path:
            # Regular watch URL: youtube.com/watch?v=<id>
            query = urllib.parse.parse_qs(parsed.query)
            v_list = query.get('v')
            if v_list:
                return v_list[0]
    except Exception as e:
        logger.error(f"Error parsing URL {url}: {e}")
    return None

def is_safari_running():
    try:
        proc = subprocess.run(["pgrep", "-x", "Safari"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return proc.returncode == 0
    except Exception:
        return False

def get_safari_active_url():
    applescript = '''
    if application "Safari" is running then
        tell application "Safari"
            if (count of windows) > 0 then
                return URL of current tab of front window
            end if
        end tell
    end if
    return ""
    '''
    try:
        proc = subprocess.run(
            ["osascript", "-e", applescript],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=2
        )
        if proc.returncode == 0:
            return proc.stdout.strip()
        else:
            logger.error(f"AppleScript error getting Safari URL: {proc.stderr.strip()}")
    except Exception as e:
        logger.error(f"Exception running AppleScript for Safari URL: {e}")
    return ""

def pause_safari_video(video_id, js_warning_callback):
    applescript = f'''
    if application "Safari" is running then
        tell application "Safari"
            set found to false
            repeat with w in windows
                repeat with t in tabs of w
                    try
                        set tabURL to URL of t
                        if tabURL contains "{video_id}" then
                            try
                                tell t to do JavaScript "document.querySelectorAll('video').forEach(v => v.pause());"
                                set found to true
                            on error errText number errNum
                                if errNum is 8 or errText contains "JavaScript" then
                                    return "JS_DISABLED"
                                end if
                            end try
                        end if
                    end try
                end repeat
            end repeat
            return found
        end tell
    end if
    return false
    '''
    try:
        proc = subprocess.run(
            ["osascript", "-e", applescript],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        if proc.returncode != 0:
            err_msg = proc.stderr.strip()
            logger.error(f"AppleScript error pausing Safari video {video_id}: {err_msg}")
            if "JavaScript from Apple Events" in err_msg or "do JavaScript" in err_msg:
                js_warning_callback()
            return False
        
        output = proc.stdout.strip()
        if output == "JS_DISABLED":
            js_warning_callback()
            return False
        return output == "true"
    except Exception as e:
        logger.error(f"Exception running AppleScript to pause video {video_id}: {e}")
    return False

def show_notification(message, title="Safari MPV Automation"):
    applescript = f'display notification "{message}" with title "{title}"'
    try:
        subprocess.run(["osascript", "-e", applescript])
    except Exception:
        pass

def handle_js_warning():
    global js_warning_shown
    if not js_warning_shown:
        msg = "Please enable 'Allow JavaScript from Apple Events' in Safari Developer menu to auto-pause videos."
        logger.warning(msg)
        show_notification(msg)
        js_warning_shown = True

def focus_mpv():
    applescript = '''
    tell application "System Events"
        try
            set frontmost of process "mpv" to true
        end try
    end tell
    '''
    try:
        subprocess.run(["osascript", "-e", applescript], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def focus_safari():
    applescript = '''
    tell application "Safari"
        activate
    end tell
    tell application "System Events"
        try
            set frontmost of process "Safari" to true
        end try
    end tell
    '''
    try:
        subprocess.run(["osascript", "-e", applescript], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def play_safari_video(video_id, timestamp=None):
    if timestamp is not None and isinstance(timestamp, (int, float)):
        js = f"document.querySelectorAll('video').forEach(v => {{ v.currentTime = {timestamp}; v.play(); }});"
    else:
        js = "document.querySelectorAll('video').forEach(v => v.play());"
        
    applescript = f'''
    if application "Safari" is running then
        tell application "Safari"
            repeat with w in windows
                repeat with t in tabs of w
                    try
                        set tabURL to URL of t
                        if tabURL contains "{video_id}" then
                            tell t to do JavaScript "{js}"
                        end if
                    end try
                end repeat
            end repeat
        end tell
    end if
    '''
    try:
        subprocess.run(["osascript", "-e", applescript], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def clean_blacklisted_ids(blacklisted_ids):
    if not blacklisted_ids:
        return
    applescript = '''
    if application "Safari" is running then
        tell application "Safari"
            set urlList to {}
            repeat with w in windows
                repeat with t in tabs of w
                    try
                        copy URL of t to end of urlList
                    end try
                end repeat
            end repeat
            return urlList
        end tell
    end if
    return ""
    '''
    try:
        proc = subprocess.run(
            ["osascript", "-e", applescript],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=3
        )
        if proc.returncode == 0:
            urls = proc.stdout.strip()
            to_remove = []
            for vid in blacklisted_ids:
                if vid not in urls:
                    to_remove.append(vid)
            for vid in to_remove:
                blacklisted_ids.remove(vid)
                logger.info(f"Removed video {vid} from blacklist (no longer open in Safari).")
    except Exception as e:
        logger.error(f"Error cleaning blacklist: {e}")

class MpvController:
    def __init__(self, socket_path=SOCKET_PATH):
        self.socket_path = socket_path
        self.sock = None
        self.proc = None
        self.request_id = 0
        self.buffer = ""

    def connect(self):
        if self.sock:
            return True
        if os.path.exists(self.socket_path):
            try:
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                s.settimeout(0.2)
                s.connect(self.socket_path)
                self.sock = s
                self.buffer = ""
                logger.info("Connected to mpv IPC socket.")
                return True
            except Exception:
                try:
                    os.unlink(self.socket_path)
                except Exception:
                    pass
        return False

    def is_running(self):
        if not self.sock:
            return self.connect()
        # Verify connection by sending a client-name request
        res = self.send_command(["get_property", "client-name"])
        if res and res.get("error") == "success":
            return True
        self.disconnect()
        return self.connect()

    def launch(self, url):
        self.quit()
        if os.path.exists(self.socket_path):
            try:
                os.unlink(self.socket_path)
            except Exception:
                pass
        
        mpv_path = "/opt/homebrew/bin/mpv"
        if not os.path.exists(mpv_path):
            mpv_path = "mpv"  # fallback
            
        cmd = [
            mpv_path,
            f"--input-ipc-server={self.socket_path}",
            "--no-terminal",
            "--force-window=yes",
            "--title=Safari MPV Player",
            "--keep-open=no",
            "--fullscreen",
            url
        ]
        logger.info(f"Launching mpv process: {' '.join(cmd)}")
        try:
            out_file = open(os.path.join(LOG_DIR, "mpv_stdout.log"), "a")
            err_file = open(os.path.join(LOG_DIR, "mpv_stderr.log"), "a")
        except Exception:
            out_file = subprocess.DEVNULL
            err_file = subprocess.DEVNULL
        self.proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=out_file, stderr=err_file)
        
        # Wait up to 3 seconds for socket creation
        for _ in range(30):
            if os.path.exists(self.socket_path):
                if self.connect():
                    return True
            time.sleep(0.1)
        logger.error("Failed to connect to mpv socket after launch.")
        return False

    def send_command(self, cmd_args):
        if not self.sock:
            return None
        self.request_id += 1
        req_id = self.request_id
        payload = json.dumps({"command": cmd_args, "request_id": req_id}) + "\n"
        try:
            self.sock.sendall(payload.encode('utf-8'))
            
            # Read socket until we get the response with request_id
            start_time = time.time()
            while time.time() - start_time < 2.0:
                while "\n" in self.buffer:
                    line, self.buffer = self.buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        if data.get("request_id") == req_id:
                            return data
                    except Exception:
                        pass
                
                # Receive more data
                try:
                    chunk = self.sock.recv(4096).decode('utf-8')
                    if not chunk:
                        logger.warning("Socket closed by peer while reading.")
                        self.disconnect()
                        return None
                    self.buffer += chunk
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error(f"Socket read error: {e}")
                    self.disconnect()
                    return None
        except Exception as e:
            logger.error(f"Error sending command {cmd_args} to mpv: {e}")
            self.disconnect()
        return None

    def load_file(self, url):
        res = self.send_command(["loadfile", url, "replace"])
        # Ensure fullscreen is maintained/asserted on video load
        self.send_command(["set_property", "fullscreen", True])
        return res and res.get("error") == "success"

    def get_playback_time(self):
        res = self.send_command(["get_property", "time-pos"])
        if res and res.get("error") == "success":
            return res.get("data")
        return None

    def is_lagging(self):
        res = self.send_command(["get_property", "paused-for-cache"])
        if res and res.get("error") == "success":
            return res.get("data") is True
        return False

    def get_dropped_frame_count(self):
        res = self.send_command(["get_property", "frame-drop-count"])
        if res and res.get("error") == "success":
            return res.get("data")
        res = self.send_command(["get_property", "vo-drop-frame-count"])
        if res and res.get("error") == "success":
            return res.get("data")
        return None

    def disconnect(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
        self.buffer = ""

    def quit(self):
        if hasattr(self, '_in_quit') and self._in_quit:
            return
        self._in_quit = True
        try:
            if self.sock:
                try:
                    self.sock.sendall(json.dumps({"command": ["quit"], "request_id": 999}).encode() + b"\n")
                except Exception:
                    pass
            if self.proc:
                try:
                    self.proc.terminate()
                    self.proc.wait(timeout=1.0)
                except Exception:
                    try:
                        self.proc.kill()
                    except Exception:
                        pass
                self.proc = None
            self.disconnect()
        finally:
            self._in_quit = False

    def close(self):
        self.quit()

def main():
    logger.info("Safari MPV Automation daemon started.")
    
    mpv = MpvController()
    current_video_id = None
    playback_started = False
    
    # Trackers for lag/stalls and blacklist
    blacklisted_video_ids = set()
    stall_ticks = 0
    load_ticks = 0
    frame_drop_history = []
    last_time_pos = 0.0
    
    while True:
        try:
            # Periodically clean up the blacklist (every 10 seconds approx)
            if int(time.time()) % 10 == 0:
                clean_blacklisted_ids(blacklisted_video_ids)
                
            # 1. Check if Safari is running
            if not is_safari_running():
                if current_video_id:
                    if not mpv.is_running():
                        logger.info("Safari is closed and mpv is closed. Resetting tracked video ID.")
                        current_video_id = None
                        playback_started = False
                time.sleep(2.0)
                continue
            
            # 2. Get Safari active tab URL
            url = get_safari_active_url()
            video_id = extract_video_id(url)
            
            # 3. Handle state transitions
            if video_id:
                # Skip if the active tab video is currently blacklisted
                if video_id in blacklisted_video_ids:
                    # If this blacklisted URL is our currently tracked video but mpv is dead, reset tracking state
                    if current_video_id == video_id and not mpv.is_running():
                        current_video_id = None
                        playback_started = False
                    time.sleep(1.0)
                    continue
                
                if video_id != current_video_id:
                    logger.info(f"New video detected: {video_id} (URL: {url})")
                    
                    if mpv.is_running():
                        logger.info(f"Switching existing mpv instance to new video {video_id}")
                        success = mpv.load_file(url)
                        if not success:
                            logger.warning("Failed to load URL in running mpv, attempting relaunch.")
                            mpv.launch(url)
                    else:
                        logger.info(f"Launching new mpv instance for video {video_id}")
                        mpv.launch(url)
                        
                    current_video_id = video_id
                    playback_started = False
                    load_ticks = 0
                    stall_ticks = 0
                    frame_drop_history = []
                    last_time_pos = 0.0
                else:
                    # Same video ID.
                    if not playback_started:
                        if mpv.is_running():
                            # Check for initial load timeout
                            load_ticks += 1
                            if load_ticks > 15:
                                logger.warning(f"Video {video_id} took too long to load (>15s). Auto-closing and blacklisting.")
                                blacklisted_video_ids.add(video_id)
                                mpv.close()
                                current_video_id = None
                                playback_started = False
                                focus_safari()
                                play_safari_video(video_id, 0.0)
                                continue
                                
                            time_pos = mpv.get_playback_time()
                            if time_pos is not None and isinstance(time_pos, (int, float)):
                                logger.info(f"Playback started in mpv (time-pos={time_pos:.2f}s). Pausing Safari.")
                                paused = pause_safari_video(video_id, handle_js_warning)
                                if paused:
                                    logger.info("Successfully paused YouTube tab in Safari.")
                                else:
                                    logger.warning("Could not pause video in Safari (tab might not be loaded or JS disabled).")
                                # Switch window to focus mpv
                                focus_mpv()
                                playback_started = True
                                last_time_pos = time_pos
                        else:
                            logger.info("mpv was closed before playback started. Resetting state, blacklisting, and focusing Safari.")
                            blacklisted_video_ids.add(video_id)
                            current_video_id = None
                            playback_started = False
                            focus_safari()
                            play_safari_video(video_id, 0.0)
                    else:
                        # Playback already started.
                        if mpv.is_running():
                            # 1. Check if the player is stalling/lagging (network cache)
                            if mpv.is_lagging():
                                stall_ticks += 1
                                if stall_ticks > 5:
                                    logger.warning(f"Video {video_id} is stalling/lagging too much (>5s). Auto-closing and blacklisting.")
                                    blacklisted_video_ids.add(video_id)
                                    mpv.close()
                                    current_video_id = None
                                    playback_started = False
                                    focus_safari()
                                    play_safari_video(video_id, last_time_pos)
                                    continue
                            else:
                                stall_ticks = 0
                                
                            # 2. Check for GPU rendering lag (vo frame drops)
                            drop_count = mpv.get_dropped_frame_count()
                            if drop_count is not None and isinstance(drop_count, int):
                                now = time.time()
                                frame_drop_history.append((now, drop_count))
                                # Keep only past 3 seconds of history
                                frame_drop_history = [entry for entry in frame_drop_history if now - entry[0] <= 3.0]
                                if len(frame_drop_history) >= 2:
                                    drops_in_window = frame_drop_history[-1][1] - frame_drop_history[0][1]
                                    if drops_in_window > 15:
                                        logger.warning(f"Video {video_id} is dropping frames ({drops_in_window} drops in last 3s) indicating GPU overload/lag. Auto-closing and blacklisting.")
                                        blacklisted_video_ids.add(video_id)
                                        mpv.close()
                                        current_video_id = None
                                        playback_started = False
                                        focus_safari()
                                        play_safari_video(video_id, last_time_pos)
                                        continue
                                        
                            # 3. Save playback time for resume
                            time_pos = mpv.get_playback_time()
                            if time_pos is not None and isinstance(time_pos, (int, float)):
                                last_time_pos = time_pos
                        else:
                            logger.info(f"mpv was closed. Resetting state, blacklisting, focusing Safari, and resuming at {last_time_pos:.2f}s.")
                            blacklisted_video_ids.add(video_id)
                            current_video_id = None
                            playback_started = False
                            focus_safari()
                            play_safari_video(video_id, last_time_pos)
            else:
                # Not a YouTube video URL in Safari's active tab.
                if current_video_id:
                    if not mpv.is_running():
                        logger.info("Active video page changed in Safari and mpv is closed. Resetting state and focusing Safari.")
                        current_video_id = None
                        playback_started = False
                        focus_safari()
            
            time.sleep(1.0)
            
        except KeyboardInterrupt:
            logger.info("Daemon stopping due to keyboard interrupt.")
            break
        except Exception as e:
            logger.error(f"Unhandled error in main loop: {e}", exc_info=True)
            time.sleep(2.0)
            
    mpv.close()
    logger.info("Daemon exited.")

if __name__ == '__main__':
    main()
