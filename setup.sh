#!/usr/bin/env bash
# One-time setup for the ad engine in a fresh workspace. Safe to re-run.
set -e
command -v ffmpeg >/dev/null || { echo "ffmpeg missing - install it (apt-get install -y ffmpeg)"; exit 1; }
PIP="pip install -q"
python3 -m pip --version >/dev/null 2>&1 && PIP="python3 -m pip install -q --break-system-packages"
python3 -c "import faster_whisper" 2>/dev/null || $PIP faster-whisper
python3 -c "import mediapipe, cv2" 2>/dev/null || $PIP mediapipe opencv-python-headless
python3 -c "import playwright" 2>/dev/null || { $PIP playwright; [ -n "$PLAYWRIGHT_BROWSERS_PATH" ] || python3 -m playwright install chromium; }
echo "setup done"
