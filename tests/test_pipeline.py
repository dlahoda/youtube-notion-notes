from __future__ import annotations

import os
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
        transcript_file_text: str | None = None,
        use_custom_output_dir: bool = False,
        use_env_output_dir: bool = False,
    ) -> tuple[int, dict, Mock, dict]:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            request_output_root = temp_path / "custom-output"
            env_output_root = temp_path / "env-output"
            output_root = temp_path
            if use_env_output_dir:
                output_root = env_output_root
            if use_custom_output_dir:
                output_root = request_output_root
            transcript_path = output_root / "transcripts" / f"{VIDEO_ID}.txt"
            prompt_path = output_root / "prompts" / f"{VIDEO_ID}_prompt.md"
            note_path = output_root / "notes" / f"{VIDEO_ID}.md"
            transcript_file_path = temp_path / "manual-transcript.txt"
            if transcript_file_text is not None:
                transcript_file_path.write_text(transcript_file_text, encoding="utf-8")
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
                transcript_file=str(transcript_file_path) if transcript_file_text is not None else None,
                output_dir=str(request_output_root) if use_custom_output_dir else None,
            )

            with (
                patch.dict(os.environ, {"YNN_OUTPUT_DIR": str(env_output_root) if use_env_output_dir else ""}),
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
                "prompt_kwargs": prompt_mock.call_args.kwargs if prompt_mock.call_args else {},
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

    def test_transcript_file_mode_does_not_call_fetch_transcript(self) -> None:
        exit_code, result, export_mock, snapshot = self.run_pipeline(
            no_note=True,
            transcript_file_text="Manual transcript text.\n",
        )

        self.assertEqual(exit_code, 0)
        self.assertTrue(result["ok"])
        self.assertTrue(snapshot["parse_called"])
        self.assertFalse(snapshot["fetch_called"])
        export_mock.assert_not_called()

    def test_empty_transcript_file_fails_during_transcript_stage(self) -> None:
        exit_code, result, export_mock, snapshot = self.run_pipeline(
            transcript_file_text="",
        )

        self.assertEqual(exit_code, 1)
        self.assertFalse(result["ok"])
        self.assertEqual(result["stage"], "transcript")
        self.assertIn("empty or contains only whitespace", result["error"])
        self.assertFalse(snapshot["fetch_called"])
        self.assertFalse(snapshot["prompt_called"])
        self.assertFalse(snapshot["note_called"])
        self.assertFalse(snapshot["transcript_exists"])
        self.assertFalse(snapshot["prompt_exists"])
        self.assertFalse(snapshot["note_exists"])
        export_mock.assert_not_called()

    def test_whitespace_only_transcript_file_fails_during_transcript_stage(self) -> None:
        exit_code, result, export_mock, snapshot = self.run_pipeline(
            transcript_file_text=" \n\t\n",
        )

        self.assertEqual(exit_code, 1)
        self.assertFalse(result["ok"])
        self.assertEqual(result["stage"], "transcript")
        self.assertIn("empty or contains only whitespace", result["error"])
        self.assertFalse(snapshot["fetch_called"])
        self.assertFalse(snapshot["prompt_called"])
        self.assertFalse(snapshot["note_called"])
        self.assertFalse(snapshot["transcript_exists"])
        self.assertFalse(snapshot["prompt_exists"])
        self.assertFalse(snapshot["note_exists"])
        export_mock.assert_not_called()

    def test_transcript_file_mode_saves_manual_text_to_transcript_output_path(self) -> None:
        manual_text = "Manual transcript line one.\nManual transcript line two.\n"

        exit_code, result, _export_mock, snapshot = self.run_pipeline(
            no_note=True,
            transcript_file_text=manual_text,
        )

        self.assertEqual(exit_code, 0)
        self.assertTrue(result["transcript_path"].endswith(f"transcripts/{VIDEO_ID}.txt"))
        self.assertTrue(snapshot["transcript_exists"])
        self.assertEqual(snapshot["transcript_text"], manual_text)

    def test_transcript_file_mode_builds_prompt_with_manual_text_and_original_url(self) -> None:
        manual_text = "Manual prompt transcript.\n"

        exit_code, result, _export_mock, snapshot = self.run_pipeline(
            no_note=True,
            transcript_file_text=manual_text,
        )

        self.assertEqual(exit_code, 0)
        self.assertTrue(result["ok"])
        self.assertTrue(snapshot["prompt_called"])
        self.assertEqual(snapshot["prompt_kwargs"]["video_url"], VIDEO_URL)
        self.assertEqual(snapshot["prompt_kwargs"]["video_id"], VIDEO_ID)
        self.assertEqual(snapshot["prompt_kwargs"]["transcript"], manual_text)

    def test_custom_output_dir_writes_pipeline_files_under_requested_root(self) -> None:
        exit_code, result, export_mock, snapshot = self.run_pipeline(
            no_note=True,
            use_custom_output_dir=True,
        )

        self.assertEqual(exit_code, 0)
        self.assertTrue(result["ok"])
        self.assertIn("custom-output", Path(result["transcript_path"]).parts)
        self.assertIn("transcripts", Path(result["transcript_path"]).parts)
        self.assertIn("custom-output", Path(result["prompt_path"]).parts)
        self.assertIn("prompts", Path(result["prompt_path"]).parts)
        self.assertIsNone(result["note_path"])
        self.assertTrue(snapshot["transcript_exists"])
        self.assertTrue(snapshot["prompt_exists"])
        self.assertFalse(snapshot["note_exists"])
        export_mock.assert_not_called()

    def test_output_dir_flag_wins_over_ynn_output_dir(self) -> None:
        exit_code, result, _export_mock, snapshot = self.run_pipeline(
            no_note=True,
            use_custom_output_dir=True,
            use_env_output_dir=True,
        )

        self.assertEqual(exit_code, 0)
        self.assertTrue(result["ok"])
        self.assertIn("custom-output", Path(result["transcript_path"]).parts)
        self.assertNotIn("env-output", Path(result["transcript_path"]).parts)
        self.assertTrue(snapshot["transcript_exists"])
        self.assertTrue(snapshot["prompt_exists"])

    def test_ynn_output_dir_is_used_when_output_dir_is_omitted(self) -> None:
        exit_code, result, _export_mock, snapshot = self.run_pipeline(
            no_note=True,
            use_env_output_dir=True,
        )

        self.assertEqual(exit_code, 0)
        self.assertTrue(result["ok"])
        self.assertIn("env-output", Path(result["transcript_path"]).parts)
        self.assertIn("env-output", Path(result["prompt_path"]).parts)
        self.assertTrue(snapshot["transcript_exists"])
        self.assertTrue(snapshot["prompt_exists"])

    def test_default_output_dir_is_used_when_no_override_is_set(self) -> None:
        exit_code, result, _export_mock, snapshot = self.run_pipeline(no_note=True)

        self.assertEqual(exit_code, 0)
        self.assertTrue(result["ok"])
        self.assertTrue(result["transcript_path"].endswith(f"transcripts/{VIDEO_ID}.txt"))
        self.assertNotIn("custom-output", Path(result["transcript_path"]).parts)
        self.assertNotIn("env-output", Path(result["transcript_path"]).parts)
        self.assertTrue(snapshot["transcript_exists"])
        self.assertTrue(snapshot["prompt_exists"])

    def test_output_paths_default_to_cwd_output_root(self) -> None:
        request = pipeline.PipelineRequest(
            url=VIDEO_URL,
            export_mode="local",
            languages=None,
            output_name=None,
            no_note=True,
        )

        with patch.dict(os.environ, {"YNN_OUTPUT_DIR": ""}):
            output_paths = pipeline.output_paths_for_request(request)

        self.assertEqual(output_paths.transcript_dir, Path("output") / "transcripts")
        self.assertEqual(output_paths.prompt_dir, Path("output") / "prompts")
        self.assertEqual(output_paths.notes_dir, Path("output") / "notes")


if __name__ == "__main__":
    unittest.main()
