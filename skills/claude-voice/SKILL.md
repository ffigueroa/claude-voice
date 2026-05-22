---
name: claude-voice
description: Adds text-to-speech to Claude Code responses. When active, Claude includes spoken summary markers that a background watcher converts to audio via ElevenLabs.
---

# ClaudeVoice

When this skill is active, include a brief spoken summary at the end of every response as an HTML comment marker:

<!-- TTS: "Brief conversational summary" -->

## Rules

- 1-2 sentences max, conversational tone, as if talking to a colleague
- Summarize what you did or your answer — don't read the full response verbatim
- Skip code snippets, file paths, line numbers, and technical details
- Use the same language the user speaks (Spanish if they write in Spanish, English if English, etc.)
- For simple acknowledgments, keep it very short ("Done.", "Got it.", "Dale, listo.")
- For errors or problems, explain what went wrong briefly
- ALWAYS include the marker, even for short responses
- Include markers in intermediate responses too (between tool calls) — the watcher picks them up live. Every text block you write should have a marker so the user hears progress updates in real-time.

## Examples

<!-- TTS: "Fixed the audio bug and deployed it." -->
<!-- TTS: "There are three options. I recommend the second one because it's simpler." -->
<!-- TTS: "Done, committed." -->
<!-- TTS: "Found the problem. The ring buffer was only storing twenty seconds." -->

## Deactivation

To stop voice output, the user will say "mute", "silencio", "desactiva la voz", or run `/claude-voice:mute`. When they do, stop including TTS markers and confirm silently (no marker in that response).
