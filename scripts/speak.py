#!/usr/bin/env python3
"""ClaudeVoice — real-time TTS for Claude Code via ElevenLabs."""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "claude-voice"
CONFIG_FILE = CONFIG_DIR / "config.json"
LOG_FILE = CONFIG_DIR / "tts.log"
AUDIO_FILE = CONFIG_DIR / "last.mp3"
PID_FILE = CONFIG_DIR / "watcher.pid"

DEFAULT_VOICE_ID = "6w9DrrpTbLZzY7cOiy57"
DEFAULT_MODEL = "eleven_flash_v2_5"


def log(msg):
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            from datetime import datetime
            f.write(f"{datetime.now().strftime('%H:%M:%S')} | {msg}\n")
    except Exception:
        pass


def load_config(path=None):
    config_path = Path(path) if path else CONFIG_FILE
    if not config_path.exists():
        return None
    try:
        with open(config_path) as f:
            raw = json.load(f)
        if not raw.get("api_key"):
            return None
        return {
            "api_key": raw["api_key"],
            "voice_id": raw.get("voice_id", DEFAULT_VOICE_ID),
            "model": raw.get("model", DEFAULT_MODEL),
        }
    except (json.JSONDecodeError, KeyError):
        return None


def extract_tts_marker(text):
    pattern = r'<!--\s*TTS:\s*"([^"]+)"\s*-->'
    matches = re.findall(pattern, text)
    return matches[-1] if matches else None


def extract_marker_from_entry(entry):
    if entry.get("type") != "assistant":
        return None
    content = entry.get("message", {}).get("content", [])
    if isinstance(content, list):
        texts = [b.get("text", "") for b in content if b.get("type") == "text"]
        full_text = "\n".join(texts)
    elif isinstance(content, str):
        full_text = content
    else:
        return None
    return extract_tts_marker(full_text)


def speak(text, config):
    import urllib.request

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{config['voice_id']}/stream"
    payload = json.dumps({
        "text": text,
        "model_id": config["model"],
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }).encode()

    req = urllib.request.Request(url, data=payload, headers={
        "xi-api-key": config["api_key"],
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    })

    try:
        AUDIO_FILE.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(req, timeout=15) as resp:
            AUDIO_FILE.write_bytes(resp.read())
        log(f"Playing: {text}")
        subprocess.run(
            ["afplay", str(AUDIO_FILE)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        log(f"TTS error: {e}")


def find_transcripts():
    projects_dir = Path.home() / ".claude" / "projects"
    if not projects_dir.exists():
        return []
    results = []
    for p in projects_dir.rglob("*.jsonl"):
        if "/subagents/" in str(p):
            continue
        results.append(str(p))
    return results


def find_transcript():
    transcripts = find_transcripts()
    if not transcripts:
        return None
    return max(transcripts, key=lambda p: os.path.getmtime(p))


def watch(transcript_path, config):
    log(f"Watching all transcripts (started with: {transcript_path})")
    spoken_markers = set()
    file_positions = {}

    for t in find_transcripts():
        try:
            file_positions[t] = os.path.getsize(t)
        except OSError:
            file_positions[t] = 0

    while True:
        try:
            current_transcripts = find_transcripts()
            for t in current_transcripts:
                if t not in file_positions:
                    try:
                        file_positions[t] = os.path.getsize(t)
                    except OSError:
                        file_positions[t] = 0
                    log(f"New transcript: {t}")

                try:
                    current_size = os.path.getsize(t)
                except OSError:
                    continue

                pos = file_positions.get(t, 0)
                if current_size <= pos:
                    continue

                with open(t, "r") as f:
                    f.seek(pos)
                    new_data = f.read()
                    file_positions[t] = f.tell()

                for line in new_data.strip().split("\n"):
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    marker = extract_marker_from_entry(entry)
                    if marker and marker not in spoken_markers:
                        spoken_markers.add(marker)
                        log(f"Live marker: {marker}")
                        speak(marker, config)

            time.sleep(0.5)
        except KeyboardInterrupt:
            log("Watcher stopped")
            break
        except Exception as e:
            log(f"Watch error: {e}")
            time.sleep(1)


def write_pid():
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()))


def cleanup_pid():
    try:
        PID_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def is_watcher_running():
    if not PID_FILE.exists():
        return False
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, 0)
        return True
    except (ValueError, ProcessLookupError, PermissionError):
        cleanup_pid()
        return False


def daemon_main():
    config = load_config()
    if not config:
        log("No config found — exiting silently")
        return

    if is_watcher_running():
        log("Watcher already running — exiting")
        return

    transcript_path = find_transcript()
    if not transcript_path:
        log("No transcript found — exiting")
        return

    pid = os.fork()
    if pid > 0:
        return

    os.setsid()
    sys.stdin = open(os.devnull, "r")
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")

    write_pid()
    try:
        watch(transcript_path, config)
    finally:
        cleanup_pid()


def oneshot_main():
    config = load_config()
    if not config:
        log("No config — cannot speak")
        return

    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        log("No valid JSON on stdin")
        return

    transcript_path = hook_input.get("transcript_path", "")
    if not transcript_path or not Path(transcript_path).exists():
        log(f"No transcript at: {transcript_path}")
        return

    last_text = None
    with open(transcript_path, "r") as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry.get("type") == "assistant":
                    content = entry.get("message", {}).get("content", [])
                    if isinstance(content, list):
                        texts = [b.get("text", "") for b in content if b.get("type") == "text"]
                        if texts:
                            last_text = "\n".join(texts)
                    elif isinstance(content, str):
                        last_text = content
            except (json.JSONDecodeError, KeyError, TypeError):
                continue

    if last_text:
        marker = extract_tts_marker(last_text)
        if marker:
            log(f"One-shot marker: {marker}")
            speak(marker, config)


def main():
    if "--daemon" in sys.argv:
        daemon_main()
    else:
        oneshot_main()


if __name__ == "__main__":
    main()
