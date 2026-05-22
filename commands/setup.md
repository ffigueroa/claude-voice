---
description: Configure ElevenLabs API key and voice settings
---

Help the user configure ClaudeVoice. Follow these steps:

1. Ask the user for their ElevenLabs API key (required). They can get one at https://elevenlabs.io — go to Profile Settings → API Keys.

2. Ask if they want to customize the voice ID (optional). Default: `6w9DrrpTbLZzY7cOiy57`. They can browse voices at https://elevenlabs.io/voice-library.

3. Ask if they want to change the model (optional). Default: `eleven_flash_v2_5` (fastest). Other option: `eleven_multilingual_v2` (better quality, slower).

4. Write the config file:

```bash
mkdir -p ~/.config/claude-voice
```

Write `~/.config/claude-voice/config.json` with:
```json
{
  "api_key": "<user's key>",
  "voice_id": "<chosen or default>",
  "model": "<chosen or default>"
}
```

5. Confirm setup is complete. Tell the user to restart their Claude Code session so the watcher daemon starts, then activate with `/claude-voice:speak`.

If the user hasn't installed the plugin yet, guide them:
```
/plugin marketplace add ffigueroa/claude-voice
/plugin install claude-voice@claude-voice
```
