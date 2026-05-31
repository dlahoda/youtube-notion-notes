from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import youtube_notion_notes.services as services
import youtube_notion_notes.services.pipeline as pipeline
import youtube_notion_notes.services.transcript as transcript_service
from youtube_notion_notes import ingest
from youtube_notion_notes.services.note_generator import PromptTemplateError
from youtube_notion_notes.services.notion import NotionPage


VIDEO_ID = "abc123def45"
VIDEO_URL = f"https://youtu.be/{VIDEO_ID}"
FAKE_NOTION_CONFIG = {
    "OPENAI_API_KEY": "fake-openai-key",
    "NOTION_API_KEY": "fake-notion-key",
    "NOTION_DATABASE_ID": "fake-database-id",
}


class IngestCliTests(unittest.TestCase):
    def run_ingest(
        self,
        *extra_args: str,
        note_text: str | None = "# Generated Note\n\nTags: cli\n\nBody",
        export_side_effect=None,
        assert_note_saved_before_export: bool = False,
        include_positional_url: bool = True,
        stdin_value: str = "",
        prompt_side_effect: Exception | None = None,
        notion_config: dict[str, str] | None = None,
        transcript_selection_metadata: (
            transcript_service.TranscriptSelectionMetadata | None
        ) = None,
    ) -> tuple[int, str, str, Mock, bool, str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            note_path = temp_path / "notes" / f"{VIDEO_ID}.md"
            transcript = Mock()
            transcript.as_text.return_value = "[00:00] Transcript\n"
            transcript.selection_metadata = transcript_selection_metadata

            def export_effect(markdown: str, url: str) -> NotionPage:
                if assert_note_saved_before_export:
                    self.assertTrue(note_path.exists())
                    self.assertEqual(note_path.read_text(encoding="utf-8"), markdown)
                if isinstance(export_side_effect, Exception):
                    raise export_side_effect
                if export_side_effect:
                    return export_side_effect(markdown, url)
                return NotionPage(id="page-123")

            export_mock = Mock(side_effect=export_effect)
            fake_notion_export_module = types.ModuleType("youtube_notion_notes.services.notion_export")
            fake_notion_export_module.export_markdown_note_to_notion = export_mock
            had_notion_export_attr = hasattr(services, "notion_export")
            original_notion_export_attr = getattr(services, "notion_export", None)
            argv = ["ingest.py"]
            if include_positional_url:
                argv.append(VIDEO_URL)
            argv.extend(extra_args)
            env_values = {
                "OPENAI_API_KEY": "",
                "NOTION_API_KEY": "",
                "NOTION_DATABASE_ID": "",
            }
            if notion_config:
                env_values.update(notion_config)

            stdout = io.StringIO()
            stderr = io.StringIO()
            with (
                patch.dict(
                    sys.modules,
                    {"youtube_notion_notes.services.notion_export": fake_notion_export_module},
                ),
                patch.dict(os.environ, env_values),
                patch.object(sys, "argv", argv),
                patch.object(sys, "stdin", io.StringIO(stdin_value)),
                patch.object(pipeline, "TRANSCRIPT_DIR", temp_path / "transcripts"),
                patch.object(pipeline, "PROMPT_DIR", temp_path / "prompts"),
                patch.object(pipeline, "NOTES_DIR", temp_path / "notes"),
                patch.object(ingest, "load_env_file"),
                patch.object(pipeline, "parse_youtube_url", return_value=VIDEO_ID),
                patch.object(pipeline, "fetch_transcript", return_value=transcript),
                patch.object(
                    pipeline,
                    "build_manual_prompt",
                    return_value="prompt",
                    side_effect=prompt_side_effect,
                ),
                patch.object(pipeline, "generate_note_if_available", return_value=note_text),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                exit_code = ingest.main()

            if had_notion_export_attr:
                services.notion_export = original_notion_export_attr
            elif hasattr(services, "notion_export"):
                delattr(services, "notion_export")

            note_exists = note_path.exists()
            note_content = note_path.read_text(encoding="utf-8") if note_exists else ""

            return exit_code, stdout.getvalue(), stderr.getvalue(), export_mock, note_exists, note_content

    def test_default_cli_behavior_does_not_call_notion_export(self) -> None:
        existing_notion_export_module = sys.modules.pop("youtube_notion_notes.services.notion_export", None)
        had_notion_export_attr = hasattr(services, "notion_export")
        original_notion_export_attr = getattr(services, "notion_export", None)

        try:
            exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest()

            self.assertEqual(exit_code, 0)
            self.assertIn("Markdown note saved:", stdout)
            self.assertEqual(stderr, "")
            self.assertTrue(note_exists)
            self.assertNotIn("youtube_notion_notes.services.notion_export", sys.modules)
            export_mock.assert_not_called()
        finally:
            if existing_notion_export_module is not None:
                sys.modules["youtube_notion_notes.services.notion_export"] = existing_notion_export_module
            if had_notion_export_attr:
                services.notion_export = original_notion_export_attr
            elif hasattr(services, "notion_export"):
                delattr(services, "notion_export")

    def test_export_notion_passes_original_url_and_saved_markdown(self) -> None:
        note_text = "# Generated Note\n\nTags: cli\n\nBody"

        def assert_note_saved_before_export(markdown: str, url: str) -> NotionPage:
            self.assertEqual(markdown, note_text)
            self.assertEqual(url, VIDEO_URL)
            return NotionPage(id="page-123")

        exit_code, stdout, stderr, export_mock, note_exists, note_content = self.run_ingest(
            "--export",
            "notion",
            note_text=note_text,
            export_side_effect=assert_note_saved_before_export,
            assert_note_saved_before_export=True,
            notion_config=FAKE_NOTION_CONFIG,
        )

        self.assertEqual(exit_code, 0)
        self.assertIn("Notion page created: page-123", stdout)
        self.assertEqual(stderr, "")
        self.assertTrue(note_exists)
        self.assertEqual(note_content, note_text)
        export_mock.assert_called_once_with(note_text, VIDEO_URL)

    def test_export_notion_uses_explicit_env_file_before_config_preflight(self) -> None:
        note_text = "# Generated Note\n\nTags: cli\n\nBody"

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            env_file = temp_path / "notion.env"
            note_path = temp_path / "notes" / f"{VIDEO_ID}.md"
            env_file.write_text(
                "\n".join(
                    [
                        "OPENAI_API_KEY=fake-openai-key",
                        "NOTION_API_KEY=fake-notion-key",
                        "NOTION_DATABASE_ID=fake-database-id",
                    ]
                ),
                encoding="utf-8",
            )
            transcript = Mock()
            transcript.as_text.return_value = "[00:00] Transcript\n"
            export_mock = Mock(return_value=NotionPage(id="page-123"))
            fake_notion_export_module = types.ModuleType("youtube_notion_notes.services.notion_export")
            fake_notion_export_module.export_markdown_note_to_notion = export_mock
            had_notion_export_attr = hasattr(services, "notion_export")
            original_notion_export_attr = getattr(services, "notion_export", None)
            stdout = io.StringIO()
            stderr = io.StringIO()

            with (
                patch.dict(
                    sys.modules,
                    {"youtube_notion_notes.services.notion_export": fake_notion_export_module},
                ),
                patch.dict(os.environ, {}, clear=True),
                patch.object(
                    sys,
                    "argv",
                    [
                        "ingest.py",
                        VIDEO_URL,
                        "--export",
                        "notion",
                        "--env-file",
                        str(env_file),
                        "--output-dir",
                        str(temp_path),
                    ],
                ),
                patch.object(sys, "stdin", io.StringIO("")),
                patch.object(pipeline, "TRANSCRIPT_DIR", temp_path / "transcripts"),
                patch.object(pipeline, "PROMPT_DIR", temp_path / "prompts"),
                patch.object(pipeline, "NOTES_DIR", temp_path / "notes"),
                patch.object(pipeline, "parse_youtube_url", return_value=VIDEO_ID),
                patch.object(pipeline, "fetch_transcript", return_value=transcript),
                patch.object(pipeline, "build_manual_prompt", return_value="prompt"),
                patch.object(pipeline, "generate_note_if_available", return_value=note_text),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                exit_code = ingest.main()

            if had_notion_export_attr:
                services.notion_export = original_notion_export_attr
            elif hasattr(services, "notion_export"):
                delattr(services, "notion_export")

            self.assertEqual(exit_code, 0)
            self.assertIn("Notion page created: page-123", stdout.getvalue())
            self.assertEqual(stderr.getvalue(), "")
            self.assertTrue(note_path.exists())
            export_mock.assert_called_once_with(note_text, VIDEO_URL)

    def test_export_notion_failure_exits_nonzero_and_keeps_local_note(self) -> None:
        note_text = "# Generated Note\n\nBody"

        exit_code, stdout, stderr, export_mock, note_exists, note_content = self.run_ingest(
            "--export",
            "notion",
            note_text=note_text,
            export_side_effect=RuntimeError("boom"),
            notion_config=FAKE_NOTION_CONFIG,
        )

        self.assertEqual(exit_code, 1)
        self.assertIn("Markdown note saved:", stdout)
        self.assertIn("Notion export failed: boom", stderr)
        self.assertTrue(note_exists)
        self.assertEqual(note_content, note_text)
        export_mock.assert_called_once_with(note_text, VIDEO_URL)

    def test_export_notion_missing_config_fails_cleanly_in_text_output(self) -> None:
        exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
            "--export",
            "notion",
            notion_config={
                "OPENAI_API_KEY": "",
                "NOTION_API_KEY": " ",
                "NOTION_DATABASE_ID": "",
            },
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout, "")
        self.assertIn("Notion export config error:", stderr)
        self.assertIn("OPENAI_API_KEY", stderr)
        self.assertIn("NOTION_API_KEY", stderr)
        self.assertIn("NOTION_DATABASE_ID", stderr)
        self.assertNotIn("Traceback", stderr)
        self.assertFalse(note_exists)
        export_mock.assert_not_called()

    def test_export_notion_requires_a_generated_markdown_note(self) -> None:
        exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
            "--no-note",
            "--export",
            "notion",
            notion_config=FAKE_NOTION_CONFIG,
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
            notion_config=FAKE_NOTION_CONFIG,
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

    def test_json_output_manual_fallback_writes_only_json_to_stdout(self) -> None:
        selection_metadata = transcript_service.TranscriptSelectionMetadata(
            origin="manual",
            source_language="English",
            selected_language="English",
            requires_translation=False,
            selection_reason="manual_preferred_language",
        )

        exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
            "--output",
            "json",
            note_text=None,
            transcript_selection_metadata=selection_metadata,
        )

        payload = json.loads(stdout)

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["url"], VIDEO_URL)
        self.assertEqual(payload["export_mode"], "local")
        self.assertTrue(payload["transcript_path"].endswith(f"transcripts/{VIDEO_ID}.txt"))
        self.assertTrue(payload["prompt_path"].endswith(f"prompts/{VIDEO_ID}_prompt.md"))
        self.assertIsNone(payload["note_path"])
        self.assertIsNone(payload["notion_page_id"])
        self.assertEqual(payload["transcript_selection"], selection_metadata.as_dict())
        self.assertFalse(note_exists)
        self.assertNotIn("Transcript saved:", stdout)
        self.assertNotIn("Markdown note skipped:", stdout)
        export_mock.assert_not_called()

    def test_text_output_includes_concise_transcript_selection_line(self) -> None:
        selection_metadata = transcript_service.TranscriptSelectionMetadata(
            origin="manual",
            source_language="Spanish",
            selected_language="English",
            requires_translation=True,
            selection_reason="manual_translatable_to_preferred_language",
        )

        exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
            "--no-note",
            transcript_selection_metadata=selection_metadata,
        )

        self.assertEqual(exit_code, 0)
        self.assertIn("Transcript selected: manual Spanish -> English", stdout)
        self.assertIn("Transcript saved:", stdout)
        self.assertEqual(stderr, "")
        self.assertFalse(note_exists)
        export_mock.assert_not_called()

    def test_json_output_includes_notion_result_when_export_runs(self) -> None:
        page_id = "fake-page-id"
        page_url = "https://www.notion.so/Real-Canonical-Url-From-Api"

        exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
            "--export",
            "notion",
            "--output",
            "json",
            export_side_effect=lambda _markdown, _url: NotionPage(id=page_id, url=page_url),
            notion_config=FAKE_NOTION_CONFIG,
        )

        payload = json.loads(stdout)

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["export_mode"], "notion")
        self.assertTrue(payload["note_path"].endswith(f"notes/{VIDEO_ID}.md"))
        self.assertEqual(payload["notion_page_id"], page_id)
        self.assertEqual(payload["notion_page_url"], page_url)
        self.assertNotEqual(payload["notion_page_url"], "https://www.notion.so/fake-page-id")
        self.assertTrue(note_exists)
        self.assertNotIn("Notion page created:", stdout)
        export_mock.assert_called_once()

    def test_json_output_config_failure_is_valid_json_only(self) -> None:
        exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
            "--export",
            "notion",
            "--output",
            "json",
            notion_config={
                "OPENAI_API_KEY": "",
                "NOTION_API_KEY": " ",
                "NOTION_DATABASE_ID": "",
            },
        )

        payload = json.loads(stdout)

        self.assertEqual(exit_code, 1)
        self.assertEqual(stderr, "")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["stage"], "config")
        self.assertIn("OPENAI_API_KEY", payload["error"])
        self.assertIn("NOTION_API_KEY", payload["error"])
        self.assertIn("NOTION_DATABASE_ID", payload["error"])
        self.assertIsNone(payload["transcript_path"])
        self.assertIsNone(payload["prompt_path"])
        self.assertIsNone(payload["note_path"])
        self.assertIsNone(payload["notion_page_id"])
        self.assertFalse(note_exists)
        self.assertTrue(stdout.lstrip().startswith("{"))
        self.assertNotIn("Transcript saved:", stdout)
        export_mock.assert_not_called()

    def test_json_output_failure_contains_stage_and_error(self) -> None:
        exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
            "--export",
            "notion",
            "--output",
            "json",
            note_text=None,
            notion_config=FAKE_NOTION_CONFIG,
        )

        payload = json.loads(stdout)

        self.assertEqual(exit_code, 1)
        self.assertEqual(stderr, "")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["stage"], "notion_export")
        self.assertIn("--export notion requires a generated markdown note", payload["error"])
        self.assertTrue(payload["transcript_path"].endswith(f"transcripts/{VIDEO_ID}.txt"))
        self.assertTrue(payload["prompt_path"].endswith(f"prompts/{VIDEO_ID}_prompt.md"))
        self.assertIsNone(payload["note_path"])
        self.assertFalse(note_exists)
        export_mock.assert_not_called()

    def test_json_output_prompt_template_failure_is_valid_json_only(self) -> None:
        exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
            "--output",
            "json",
            prompt_side_effect=PromptTemplateError("Unable to read built-in prompt template."),
        )

        payload = json.loads(stdout)

        self.assertEqual(exit_code, 1)
        self.assertEqual(stderr, "")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["stage"], "prompt_template")
        self.assertIn("Unable to read built-in prompt template", payload["error"])
        self.assertIsNone(payload["transcript_path"])
        self.assertIsNone(payload["prompt_path"])
        self.assertIsNone(payload["note_path"])
        self.assertFalse(note_exists)
        self.assertNotIn("Prompt template error:", stdout)
        export_mock.assert_not_called()

    def test_text_output_prompt_template_failure_is_clean_error(self) -> None:
        exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
            prompt_side_effect=PromptTemplateError("Unable to format prompt template."),
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout, "")
        self.assertIn("Prompt template error: Unable to format prompt template.", stderr)
        self.assertNotIn("Traceback", stderr)
        self.assertFalse(note_exists)
        export_mock.assert_not_called()

    def test_positional_url_behavior_still_works(self) -> None:
        exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest("--no-note")

        self.assertEqual(exit_code, 0)
        self.assertIn("Transcript saved:", stdout)
        self.assertIn("GPT prompt saved:", stdout)
        self.assertIn("Markdown note skipped: --no-note was provided.", stdout)
        self.assertEqual(stderr, "")
        self.assertFalse(note_exists)
        export_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
