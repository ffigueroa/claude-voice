# ClaudeVoice

Real-time text-to-speech for Claude Code using ElevenLabs. Hear Claude's responses spoken aloud as they happen — even during multi-step tool calls.

## How it works

Claude includes short spoken summaries as HTML comment markers in responses. A background daemon watches the conversation transcript and sends new markers to ElevenLabs for audio playback in real-time.

## Requirements

- macOS (uses `afplay` for audio playback)
- Python 3.8+
- [ElevenLabs](https://elevenlabs.io) API key

## Install

In Claude Code:

```
/plugin marketplace add ffigueroa/claude-voice
/plugin install claude-voice@claude-voice
```

Then reload or restart Claude Code.

## Setup

Run the setup command and enter your ElevenLabs API key:

```
/claude-voice:setup
```

Restart Claude Code after setup so the background watcher starts.

## Usage

```
/claude-voice:speak    — activate voice output
/claude-voice:mute     — deactivate voice output
```

## Configuration

Config is stored at `~/.config/claude-voice/config.json`:

```json
{
  "api_key": "sk_your_elevenlabs_key",
  "voice_id": "6w9DrrpTbLZzY7cOiy57",
  "model": "eleven_flash_v2_5"
}
```

- **voice_id**: Browse voices at [ElevenLabs Voice Library](https://elevenlabs.io/voice-library)
- **model**: `eleven_flash_v2_5` (fast) or `eleven_multilingual_v2` (higher quality)

## Logs

Check `~/.config/claude-voice/tts.log` for debugging.

## License

MIT
