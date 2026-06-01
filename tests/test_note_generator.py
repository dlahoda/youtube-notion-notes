from __future__ import annotations

from importlib import resources
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from youtube_notion_notes.services.note_generator import PromptTemplateError, build_manual_prompt, read_default_prompt_template


class NoteGeneratorTests(unittest.TestCase):
    def test_pyproject_includes_moved_service_prompt_package_data(self) -> None:
        pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
        pyproject_text = pyproject_path.read_text(encoding="utf-8")
        package_data_table = pyproject_text.split("[tool.setuptools.package-data]", 1)[1]

        self.assertIn('"youtube_notion_notes.services" = ["resources/*.md"]', package_data_table)
        self.assertNotIn('services = ["resources/*.md"]', package_data_table)

    def test_build_manual_prompt_uses_default_template_without_template_path(self) -> None:
        prompt = build_manual_prompt(
            "https://youtu.be/abc123def45",
            "abc123def45",
            "Default transcript.",
        )

        self.assertIn("- Video URL: https://youtu.be/abc123def45", prompt)
        self.assertIn("- Video ID: abc123def45", prompt)
        self.assertIn("Default transcript.", prompt)

    def test_read_default_prompt_template_uses_moved_service_package(self) -> None:
        with patch(
            "youtube_notion_notes.services.note_generator.resources.files",
            wraps=resources.files,
        ) as files_mock:
            template = read_default_prompt_template()

        files_mock.assert_called_once_with("youtube_notion_notes.services")
        self.assertIn("# Transcript", template)
        self.assertIn("{transcript}", template)

    def test_build_manual_prompt_does_not_read_cwd_prompt_template(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd_path = Path(temp_dir)
            cwd_prompt_path = cwd_path / "prompts" / "comprehensive_note.md"
            cwd_prompt_path.parent.mkdir()
            cwd_prompt_path.write_text(
                "CWD TEMPLATE SHOULD NOT BE USED {video_url} {video_id} {transcript}",
                encoding="utf-8",
            )

            original_cwd = Path.cwd()
            try:
                os.chdir(cwd_path)
                prompt = build_manual_prompt(
                    "https://youtu.be/abc123def45",
                    "abc123def45",
                    "Transcript from a non-repo cwd.",
                )
            finally:
                os.chdir(original_cwd)

        self.assertIn("- Video URL: https://youtu.be/abc123def45", prompt)
        self.assertIn("Transcript from a non-repo cwd.", prompt)
        self.assertNotIn("CWD TEMPLATE SHOULD NOT BE USED", prompt)

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

    def test_build_manual_prompt_expands_home_in_custom_template_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_home = Path(temp_dir) / "home"
            template_path = fake_home / "prompts" / "youtube-note-current.md"
            template_path.parent.mkdir(parents=True)
            template_path.write_text(
                "URL={video_url}\nID={video_id}\nTranscript={transcript}",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"HOME": str(fake_home)}):
                prompt = build_manual_prompt(
                    "https://youtu.be/abc123def45",
                    "abc123def45",
                    "Home-expanded transcript.",
                    "~/prompts/youtube-note-current.md",
                )

        self.assertEqual(
            prompt,
            "URL=https://youtu.be/abc123def45\nID=abc123def45\nTranscript=Home-expanded transcript.",
        )

    def test_read_default_prompt_template_wraps_missing_resource_error(self) -> None:
        resource = Mock()
        resource.joinpath.return_value.read_text.side_effect = FileNotFoundError("missing template")

        with patch("youtube_notion_notes.services.note_generator.resources.files", return_value=resource):
            with self.assertRaises(PromptTemplateError) as context:
                read_default_prompt_template()

        self.assertIn("Unable to read built-in prompt template", str(context.exception))
        self.assertIn("resources/comprehensive_note.md", str(context.exception))

    def test_build_manual_prompt_wraps_unreadable_default_template(self) -> None:
        resource = Mock()
        resource.joinpath.return_value.read_text.side_effect = OSError("permission denied")

        with patch("youtube_notion_notes.services.note_generator.resources.files", return_value=resource):
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
