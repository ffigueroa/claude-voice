import json
import os
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import speak


class TestExtractTTSMarker(unittest.TestCase):
    def test_basic_marker(self):
        text = 'Some response <!-- TTS: "Hello world" -->'
        self.assertEqual(speak.extract_tts_marker(text), "Hello world")

    def test_no_marker(self):
        text = "Just a regular response"
        self.assertIsNone(speak.extract_tts_marker(text))

    def test_multiple_markers_returns_last(self):
        text = '<!-- TTS: "First" --> stuff <!-- TTS: "Second" -->'
        self.assertEqual(speak.extract_tts_marker(text), "Second")

    def test_marker_with_spanish(self):
        text = '<!-- TTS: "Listo, arreglé el bug del audio." -->'
        self.assertEqual(speak.extract_tts_marker(text), "Listo, arreglé el bug del audio.")

    def test_marker_with_extra_whitespace(self):
        text = '<!--  TTS:  "Spaced out"  -->'
        self.assertEqual(speak.extract_tts_marker(text), "Spaced out")


class TestLoadConfig(unittest.TestCase):
    def test_load_valid_config(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({
                "api_key": "sk_test123",
                "voice_id": "voice123",
                "model": "eleven_flash_v2_5"
            }, f)
            f.flush()
            config = speak.load_config(f.name)
        os.unlink(f.name)
        self.assertEqual(config["api_key"], "sk_test123")
        self.assertEqual(config["voice_id"], "voice123")
        self.assertEqual(config["model"], "eleven_flash_v2_5")

    def test_load_missing_config_returns_none(self):
        config = speak.load_config("/nonexistent/path/config.json")
        self.assertIsNone(config)

    def test_load_config_with_defaults(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"api_key": "sk_test"}, f)
            f.flush()
            config = speak.load_config(f.name)
        os.unlink(f.name)
        self.assertEqual(config["api_key"], "sk_test")
        self.assertEqual(config["voice_id"], "6w9DrrpTbLZzY7cOiy57")
        self.assertEqual(config["model"], "eleven_flash_v2_5")


class TestExtractMarkerFromEntry(unittest.TestCase):
    def test_extracts_marker_from_assistant(self):
        entry = {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "text", "text": 'Done <!-- TTS: "All done" -->'}
                ]
            }
        }
        self.assertEqual(speak.extract_marker_from_entry(entry), "All done")

    def test_skips_non_assistant(self):
        entry = {
            "type": "user",
            "message": {
                "content": [
                    {"type": "text", "text": '<!-- TTS: "Nope" -->'}
                ]
            }
        }
        self.assertIsNone(speak.extract_marker_from_entry(entry))

    def test_handles_string_content(self):
        entry = {
            "type": "assistant",
            "message": {
                "content": 'Hello <!-- TTS: "Hi there" -->'
            }
        }
        self.assertEqual(speak.extract_marker_from_entry(entry), "Hi there")

    def test_handles_no_marker_in_assistant(self):
        entry = {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "text", "text": "No marker here"}
                ]
            }
        }
        self.assertIsNone(speak.extract_marker_from_entry(entry))


if __name__ == "__main__":
    unittest.main()
