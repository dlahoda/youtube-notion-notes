from __future__ import annotations

import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import services
import services.pipeline as pipeline


VIDEO_ID = "abc123def45"
VIDEO_URL = f"https://youtu.be/{VIDEO_ID}"


class PipelineServiceTests(unittest.TestCase):
    def run_pipeline(
        self,
        *,
        export_mode: str = "local",
        no_note: bool = False,
        note_text: str | None = "# Generated Note\n\nTags: pipeline\n\nBody",
        notion_page_id: str = "page-123",
        notion_page_url: str | None = None,
        assert_note_saved_before_export: bool = False,
    ) -> tuple[int, dict, Mock, dict[str, str | bool]]:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            transcript_path = temp_path / "transcripts" / f"{VIDEO_ID}.txt"
            prompt_path = temp_path / "prompts" / f"{VIDEO_ID}_prompt.md"
            note_path = temp_path / "notes" / f"{VIDEO_ID}.md"
            transcript = Mock()
            transcript.as_text.return_value = "[00:00] Transcript\n"

            def export_effect(markdown: str, url: str) -> types.SimpleNamespace:
                if assert_note_saved_before_export:
                    self.assertTrue(note_path.exists())
                    self.assertEqual(note_path.read_text(encoding="utf-8"), markdown)
                return types.SimpleNamespace(id=notion_page_id, url=notion_page_url)

            export_mock = Mock(side_effect=export_effect)
            fake_notion_export_module = types.ModuleType("services.notion_export")
            fake_notion_export_module.export_markdown_note_to_notion = export_mock

            request = pipeline.PipelineRequest(
                url=VIDEO_URL,
                export_mode=export_mode,
                languages=None,
                output_name=None,
                no_note=no_note,
            )

            with (
                patch.dict(sys.modules, {"services.notion_export": fake_notion_export_module}),
                patch.object(services, "notion_export", fake_notion_export_module, create=True),
                patch.object(pipeline, "TRANSCRIPT_DIR", temp_path / "transcripts"),
                patch.object(pipeline, "PROMPT_DIR", temp_path / "prompts"),
                patch.object(pipeline, "NOTES_DIR", temp_path / "notes"),
                patch.object(pipeline, "parse_youtube_url", return_value=VIDEO_ID) as parse_mock,
                patch.object(pipeline, "fetch_transcript", return_value=transcript) as fetch_mock,
                patch.object(pipeline, "build_manual_prompt", return_value="prompt") as prompt_mock,
                patch.object(pipeline, "generate_note_if_available", return_value=note_text) as note_mock,
            ):
                exit_code, result = pipeline.run_pipeline(request, human_output=False)

            snapshot: dict[str, str | bool] = {
                "transcript_exists": transcript_path.exists(),
                "transcript_text": transcript_path.read_text(encoding="utf-8")
                if transcript_path.exists()
                else "",
                "prompt_exists": prompt_path.exists(),
                "prompt_text": prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else "",
                "note_exists": note_path.exists(),
                "note_text": note_path.read_text(encoding="utf-8") if note_path.exists() else "",
                "parse_called": parse_mock.called,
                "fetch_called": fetch_mock.called,
                "prompt_called": prompt_mock.called,
                "note_called": note_mock.called,
            }

            return exit_code, result, export_mock, snapshot

    def test_manual_fallback_local_mode_writes_transcript_and_prompt_only(self) -> None:
        exit_code, result, export_mock, snapshot = self.run_pipeline(note_text=None)

        self.assertEqual(exit_code, 0)
        self.assertTrue(result["ok"])
        self.assertEqual(result["url"], VIDEO_URL)
        self.assertEqual(result["export_mode"], "local")
        self.assertTrue(result["transcript_path"].endswith(f"transcripts/{VIDEO_ID}.txt"))
        self.assertTrue(result["prompt_path"].endswith(f"prompts/{VIDEO_ID}_prompt.md"))
        self.assertIsNone(result["note_path"])
        self.assertIsNone(result["notion_page_id"])
        self.assertTrue(snapshot["transcript_exists"])
        self.assertEqual(snapshot["transcript_text"], "[00:00] Transcript\n")
        self.assertTrue(snapshot["prompt_exists"])
        self.assertEqual(snapshot["prompt_text"], "prompt")
        self.assertFalse(snapshot["note_exists"])
        export_mock.assert_not_called()

    def test_no_note_with_notion_export_returns_notion_export_failure(self) -> None:
        exit_code, result, export_mock, snapshot = self.run_pipeline(
            export_mode="notion",
            no_note=True,
        )

        self.assertEqual(exit_code, 1)
        self.assertFalse(result["ok"])
        self.assertEqual(result["stage"], "notion_export")
        self.assertIn("--export notion requires a generated markdown note", result["error"])
        self.assertTrue(snapshot["transcript_exists"])
        self.assertTrue(snapshot["prompt_exists"])
        self.assertFalse(snapshot["note_exists"])
        self.assertFalse(snapshot["note_called"])
        export_mock.assert_not_called()

    def test_generated_note_local_mode_writes_note_and_skips_notion_export(self) -> None:
        note_text = "# Generated Note\n\nBody"

        exit_code, result, export_mock, snapshot = self.run_pipeline(note_text=note_text)

        self.assertEqual(exit_code, 0)
        self.assertTrue(result["ok"])
        self.assertTrue(result["note_path"].endswith(f"notes/{VIDEO_ID}.md"))
        self.assertEqual(snapshot["note_text"], note_text)
        export_mock.assert_not_called()

    def test_generated_note_notion_mode_saves_note_before_export_and_returns_page_details(self) -> None:
        note_text = "# Generated Note\n\nTags: notion\n\nBody"
        notion_page_url = "https://www.notion.so/Generated-Note-page-123"

        exit_code, result, export_mock, snapshot = self.run_pipeline(
            export_mode="notion",
            note_text=note_text,
            notion_page_id="page-123",
            notion_page_url=notion_page_url,
            assert_note_saved_before_export=True,
        )

        self.assertEqual(exit_code, 0)
        self.assertTrue(result["ok"])
        self.assertTrue(result["note_path"].endswith(f"notes/{VIDEO_ID}.md"))
        self.assertEqual(result["notion_page_id"], "page-123")
        self.assertEqual(result["notion_page_url"], notion_page_url)
        self.assertEqual(snapshot["note_text"], note_text)
        export_mock.assert_called_once_with(note_text, VIDEO_URL)


if __name__ == "__main__":
    unittest.main()
