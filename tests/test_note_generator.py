from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from services.note_generator import build_manual_prompt


class NoteGeneratorTests(unittest.TestCase):
    def test_build_manual_prompt_uses_default_template_without_template_path(self) -> None:
        prompt = build_manual_prompt(
            "https://youtu.be/abc123def45",
            "abc123def45",
            "Default transcript.",
        )

        self.assertIn("- Video URL: https://youtu.be/abc123def45", prompt)
        self.assertIn("- Video ID: abc123def45", prompt)
        self.assertIn("Default transcript.", prompt)

    def test_build_manual_prompt_allows_explicit_template_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = Path(temp_dir) / "custom-template.md"
            template_path.write_text(
                "URL={video_url}\nID={video_id}\nTranscript={transcript}",
                encoding="utf-8",
            )

            prompt = build_manual_prompt(
                "https://youtu.be/abc123def45",
                "abc123def45",
                "Custom transcript.",
                template_path,
            )

        self.assertEqual(
            prompt,
            "URL=https://youtu.be/abc123def45\nID=abc123def45\nTranscript=Custom transcript.",
        )


if __name__ == "__main__":
    unittest.main()
