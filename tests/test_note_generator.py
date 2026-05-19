from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from services.note_generator import PromptTemplateError, build_manual_prompt, read_default_prompt_template


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

    def test_read_default_prompt_template_wraps_missing_resource_error(self) -> None:
        resource = Mock()
        resource.joinpath.return_value.read_text.side_effect = FileNotFoundError("missing template")

        with patch("services.note_generator.resources.files", return_value=resource):
            with self.assertRaises(PromptTemplateError) as context:
                read_default_prompt_template()

        self.assertIn("Unable to read built-in prompt template", str(context.exception))
        self.assertIn("resources/comprehensive_note.md", str(context.exception))

    def test_build_manual_prompt_wraps_unreadable_default_template(self) -> None:
        resource = Mock()
        resource.joinpath.return_value.read_text.side_effect = OSError("permission denied")

        with patch("services.note_generator.resources.files", return_value=resource):
            with self.assertRaises(PromptTemplateError) as context:
                build_manual_prompt(
                    "https://youtu.be/abc123def45",
                    "abc123def45",
                    "Default transcript.",
                )

        self.assertIn("Unable to read built-in prompt template", str(context.exception))

    def test_build_manual_prompt_rejects_template_missing_required_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = Path(temp_dir) / "missing-transcript.md"
            template_path.write_text(
                "URL={video_url}\nID={video_id}\n",
                encoding="utf-8",
            )

            with self.assertRaises(PromptTemplateError) as context:
                build_manual_prompt(
                    "https://youtu.be/abc123def45",
                    "abc123def45",
                    "Custom transcript.",
                    template_path,
                )

        self.assertIn("missing required placeholder", str(context.exception))
        self.assertIn("{transcript}", str(context.exception))

    def test_build_manual_prompt_wraps_invalid_template_formatting(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = Path(temp_dir) / "invalid-template.md"
            template_path.write_text(
                "URL={video_url}\nID={video_id}\nTranscript={transcript}\nBroken={missing}",
                encoding="utf-8",
            )

            with self.assertRaises(PromptTemplateError) as context:
                build_manual_prompt(
                    "https://youtu.be/abc123def45",
                    "abc123def45",
                    "Custom transcript.",
                    template_path,
                )

        self.assertIn("Unable to format prompt template", str(context.exception))
        self.assertIn("missing", str(context.exception))


if __name__ == "__main__":
    unittest.main()
