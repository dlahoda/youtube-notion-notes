from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import ingest


VIDEO_ID = "abc123def45"
VIDEO_URL = f"https://youtu.be/{VIDEO_ID}"


class IngestCliTests(unittest.TestCase):
    def run_ingest(
        self,
        *extra_args: str,
        note_text: str | None = "# Generated Note\n\nTags: cli\n\nBody",
        export_side_effect=None,
        assert_note_saved_before_export: bool = False,
    ) -> tuple[int, str, str, Mock, bool, str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            note_path = temp_path / "notes" / f"{VIDEO_ID}.md"
            transcript = Mock()
            transcript.as_text.return_value = "[00:00] Transcript\n"

            def export_effect(markdown: str, url: str) -> str:
                if assert_note_saved_before_export:
                    self.assertTrue(note_path.exists())
                    self.assertEqual(note_path.read_text(encoding="utf-8"), markdown)
                if isinstance(export_side_effect, Exception):
                    raise export_side_effect
                if export_side_effect:
                    return export_side_effect(markdown, url)
                return "page-123"

            export_mock = Mock(side_effect=export_effect)

            stdout = io.StringIO()
            stderr = io.StringIO()
            with (
                patch.object(sys, "argv", ["ingest.py", VIDEO_URL, *extra_args]),
                patch.object(ingest, "TRANSCRIPT_DIR", temp_path / "transcripts"),
                patch.object(ingest, "PROMPT_DIR", temp_path / "prompts"),
                patch.object(ingest, "NOTES_DIR", temp_path / "notes"),
                patch.object(ingest, "load_env_file"),
                patch.object(ingest, "parse_youtube_url", return_value=VIDEO_ID),
                patch.object(ingest, "fetch_transcript", return_value=transcript),
                patch.object(ingest, "build_manual_prompt", return_value="prompt"),
                patch.object(ingest, "generate_note_if_available", return_value=note_text),
                patch.object(ingest, "export_markdown_note_to_notion", export_mock),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                exit_code = ingest.main()

            note_exists = note_path.exists()
            note_content = note_path.read_text(encoding="utf-8") if note_exists else ""

            return exit_code, stdout.getvalue(), stderr.getvalue(), export_mock, note_exists, note_content

    def test_default_cli_behavior_does_not_call_notion_export(self) -> None:
        exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest()

        self.assertEqual(exit_code, 0)
        self.assertIn("Markdown note saved:", stdout)
        self.assertEqual(stderr, "")
        self.assertTrue(note_exists)
        export_mock.assert_not_called()

    def test_export_notion_passes_original_url_and_saved_markdown(self) -> None:
        note_text = "# Generated Note\n\nTags: cli\n\nBody"

        def assert_note_saved_before_export(markdown: str, url: str) -> str:
            self.assertEqual(markdown, note_text)
            self.assertEqual(url, VIDEO_URL)
            return "page-123"

        exit_code, stdout, stderr, export_mock, note_exists, note_content = self.run_ingest(
            "--export",
            "notion",
            note_text=note_text,
            export_side_effect=assert_note_saved_before_export,
            assert_note_saved_before_export=True,
        )

        self.assertEqual(exit_code, 0)
        self.assertIn("Notion page created: page-123", stdout)
        self.assertEqual(stderr, "")
        self.assertTrue(note_exists)
        self.assertEqual(note_content, note_text)
        export_mock.assert_called_once_with(note_text, VIDEO_URL)

    def test_export_notion_failure_exits_nonzero_and_keeps_local_note(self) -> None:
        note_text = "# Generated Note\n\nBody"

        exit_code, stdout, stderr, export_mock, note_exists, note_content = self.run_ingest(
            "--export",
            "notion",
            note_text=note_text,
            export_side_effect=RuntimeError("boom"),
        )

        self.assertEqual(exit_code, 1)
        self.assertIn("Markdown note saved:", stdout)
        self.assertIn("Notion export failed: boom", stderr)
        self.assertTrue(note_exists)
        self.assertEqual(note_content, note_text)
        export_mock.assert_called_once_with(note_text, VIDEO_URL)

    def test_export_notion_requires_a_generated_markdown_note(self) -> None:
        exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
            "--no-note",
            "--export",
            "notion",
        )

        self.assertEqual(exit_code, 1)
        self.assertIn("Markdown note skipped: --no-note was provided.", stdout)
        self.assertIn("Notion export skipped: --export notion requires a generated markdown note.", stderr)
        self.assertFalse(note_exists)
        export_mock.assert_not_called()

    def test_export_notion_does_not_run_when_openai_note_is_unavailable(self) -> None:
        exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
            "--export",
            "notion",
            note_text=None,
        )

        self.assertEqual(exit_code, 1)
        self.assertIn("Markdown note skipped: OPENAI_API_KEY is not configured.", stdout)
        self.assertIn("Notion export skipped: --export notion requires a generated markdown note.", stderr)
        self.assertFalse(note_exists)
        export_mock.assert_not_called()

    def test_export_local_is_explicit_local_only(self) -> None:
        exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest("--export", "local")

        self.assertEqual(exit_code, 0)
        self.assertIn("Markdown note saved:", stdout)
        self.assertEqual(stderr, "")
        self.assertTrue(note_exists)
        export_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
