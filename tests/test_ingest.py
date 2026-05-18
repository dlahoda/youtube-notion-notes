from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import ingest
import services
import services.pipeline as pipeline
from services.notion import NotionPage


VIDEO_ID = "abc123def45"
VIDEO_URL = f"https://youtu.be/{VIDEO_ID}"


class IngestCliTests(unittest.TestCase):
    def run_ingest(
        self,
        *extra_args: str,
        note_text: str | None = "# Generated Note\n\nTags: cli\n\nBody",
        export_side_effect=None,
        assert_note_saved_before_export: bool = False,
        include_positional_url: bool = True,
        stdin_value: str = "",
    ) -> tuple[int, str, str, Mock, bool, str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            note_path = temp_path / "notes" / f"{VIDEO_ID}.md"
            transcript = Mock()
            transcript.as_text.return_value = "[00:00] Transcript\n"

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
            fake_notion_export_module = types.ModuleType("services.notion_export")
            fake_notion_export_module.export_markdown_note_to_notion = export_mock
            had_notion_export_attr = hasattr(services, "notion_export")
            original_notion_export_attr = getattr(services, "notion_export", None)
            argv = ["ingest.py"]
            if include_positional_url:
                argv.append(VIDEO_URL)
            argv.extend(extra_args)

            stdout = io.StringIO()
            stderr = io.StringIO()
            with (
                patch.dict(
                    sys.modules,
                    {"services.notion_export": fake_notion_export_module},
                ),
                patch.object(sys, "argv", argv),
                patch.object(sys, "stdin", io.StringIO(stdin_value)),
                patch.object(pipeline, "TRANSCRIPT_DIR", temp_path / "transcripts"),
                patch.object(pipeline, "PROMPT_DIR", temp_path / "prompts"),
                patch.object(pipeline, "NOTES_DIR", temp_path / "notes"),
                patch.object(ingest, "load_env_file"),
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

            note_exists = note_path.exists()
            note_content = note_path.read_text(encoding="utf-8") if note_exists else ""

            return exit_code, stdout.getvalue(), stderr.getvalue(), export_mock, note_exists, note_content

    def test_default_cli_behavior_does_not_call_notion_export(self) -> None:
        existing_notion_export_module = sys.modules.pop("services.notion_export", None)
        had_notion_export_attr = hasattr(services, "notion_export")
        original_notion_export_attr = getattr(services, "notion_export", None)

        try:
            exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest()

            self.assertEqual(exit_code, 0)
            self.assertIn("Markdown note saved:", stdout)
            self.assertEqual(stderr, "")
            self.assertTrue(note_exists)
            self.assertNotIn("services.notion_export", sys.modules)
            export_mock.assert_not_called()
        finally:
            if existing_notion_export_module is not None:
                sys.modules["services.notion_export"] = existing_notion_export_module
            if had_notion_export_attr:
                services.notion_export = original_notion_export_attr
            elif hasattr(services, "notion_export"):
                delattr(services, "notion_export")

    def test_main_converts_cli_args_to_pipeline_request(self) -> None:
        argv = [
            "ingest.py",
            "--input-json",
            json.dumps({"url": VIDEO_URL, "export": "notion"}),
            "--languages",
            "en,uk",
            "--output-name",
            "custom-name",
            "--no-note",
            "--output",
            "json",
        ]
        stdout = io.StringIO()
        stderr = io.StringIO()
        run_pipeline_mock = Mock(return_value=(0, {"ok": True}))

        with (
            patch.object(sys, "argv", argv),
            patch.object(ingest, "load_env_file"),
            patch.object(ingest, "run_pipeline", run_pipeline_mock),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            exit_code = ingest.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(json.loads(stdout.getvalue()), {"ok": True})
        run_pipeline_mock.assert_called_once_with(
            pipeline.PipelineRequest(
                url=VIDEO_URL,
                export_mode="notion",
                languages="en,uk",
                output_name="custom-name",
                no_note=True,
            ),
            human_output=False,
        )

    def test_main_converts_transcript_file_flag_to_pipeline_request(self) -> None:
        argv = [
            "ingest.py",
            VIDEO_URL,
            "--transcript-file",
            "./manual-transcript.txt",
            "--no-note",
            "--output",
            "json",
        ]
        stdout = io.StringIO()
        stderr = io.StringIO()
        run_pipeline_mock = Mock(return_value=(0, {"ok": True}))

        with (
            patch.object(sys, "argv", argv),
            patch.object(ingest, "load_env_file"),
            patch.object(ingest, "run_pipeline", run_pipeline_mock),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            exit_code = ingest.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(json.loads(stdout.getvalue()), {"ok": True})
        run_pipeline_mock.assert_called_once_with(
            pipeline.PipelineRequest(
                url=VIDEO_URL,
                export_mode="local",
                languages=None,
                output_name=None,
                no_note=True,
                transcript_file="./manual-transcript.txt",
            ),
            human_output=False,
        )

    def test_main_converts_input_json_transcript_file_to_pipeline_request(self) -> None:
        argv = [
            "ingest.py",
            "--input-json",
            json.dumps(
                {
                    "url": VIDEO_URL,
                    "transcript_file": "./manual-transcript.txt",
                    "export": "local",
                }
            ),
            "--no-note",
            "--output",
            "json",
        ]
        stdout = io.StringIO()
        stderr = io.StringIO()
        run_pipeline_mock = Mock(return_value=(0, {"ok": True}))

        with (
            patch.object(sys, "argv", argv),
            patch.object(ingest, "load_env_file"),
            patch.object(ingest, "run_pipeline", run_pipeline_mock),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            exit_code = ingest.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(json.loads(stdout.getvalue()), {"ok": True})
        run_pipeline_mock.assert_called_once_with(
            pipeline.PipelineRequest(
                url=VIDEO_URL,
                export_mode="local",
                languages=None,
                output_name=None,
                no_note=True,
                transcript_file="./manual-transcript.txt",
            ),
            human_output=False,
        )

    def test_main_converts_input_json_file_transcript_file_to_pipeline_request(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            payload_path = Path(temp_dir) / "payload.json"
            payload_path.write_text(
                json.dumps(
                    {
                        "url": VIDEO_URL,
                        "transcript_file": "./manual-transcript.txt",
                    }
                ),
                encoding="utf-8",
            )
            argv = [
                "ingest.py",
                "--input-json-file",
                str(payload_path),
                "--no-note",
                "--output",
                "json",
            ]
            stdout = io.StringIO()
            stderr = io.StringIO()
            run_pipeline_mock = Mock(return_value=(0, {"ok": True}))

            with (
                patch.object(sys, "argv", argv),
                patch.object(ingest, "load_env_file"),
                patch.object(ingest, "run_pipeline", run_pipeline_mock),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                exit_code = ingest.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(json.loads(stdout.getvalue()), {"ok": True})
        run_pipeline_mock.assert_called_once_with(
            pipeline.PipelineRequest(
                url=VIDEO_URL,
                export_mode="local",
                languages=None,
                output_name=None,
                no_note=True,
                transcript_file="./manual-transcript.txt",
            ),
            human_output=False,
        )

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

    def test_json_output_manual_fallback_writes_only_json_to_stdout(self) -> None:
        exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
            "--output",
            "json",
            note_text=None,
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
        self.assertFalse(note_exists)
        self.assertNotIn("Transcript saved:", stdout)
        self.assertNotIn("Markdown note skipped:", stdout)
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

    def test_json_output_failure_contains_stage_and_error(self) -> None:
        exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
            "--export",
            "notion",
            "--output",
            "json",
            note_text=None,
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

    def test_positional_url_behavior_still_works(self) -> None:
        exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest("--no-note")

        self.assertEqual(exit_code, 0)
        self.assertIn("Transcript saved:", stdout)
        self.assertIn("GPT prompt saved:", stdout)
        self.assertIn("Markdown note skipped: --no-note was provided.", stdout)
        self.assertEqual(stderr, "")
        self.assertFalse(note_exists)
        export_mock.assert_not_called()

    def test_transcript_file_without_positional_url_fails_through_input_error_path(self) -> None:
        exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
            "--transcript-file",
            "./manual-transcript.txt",
            "--output",
            "json",
            include_positional_url=False,
        )

        payload = json.loads(stdout)

        self.assertEqual(exit_code, 2)
        self.assertEqual(stderr, "")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["stage"], "input")
        self.assertIn("A YouTube URL is required", payload["error"])
        self.assertFalse(note_exists)
        export_mock.assert_not_called()

    def test_transcript_file_with_input_json_fails_through_input_error_path(self) -> None:
        exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
            "--input-json",
            json.dumps({"url": VIDEO_URL}),
            "--transcript-file",
            "./manual-transcript.txt",
            "--output",
            "json",
            include_positional_url=False,
        )

        payload = json.loads(stdout)

        self.assertEqual(exit_code, 2)
        self.assertEqual(stderr, "")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["stage"], "input")
        self.assertIn("positional argument when using --transcript-file", payload["error"])
        self.assertFalse(note_exists)
        export_mock.assert_not_called()

    def test_input_json_with_url_works(self) -> None:
        exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
            "--input-json",
            json.dumps({"url": VIDEO_URL}),
            "--output",
            "json",
            note_text=None,
            include_positional_url=False,
        )

        payload = json.loads(stdout)

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["url"], VIDEO_URL)
        self.assertEqual(payload["export_mode"], "local")
        self.assertFalse(note_exists)
        export_mock.assert_not_called()

    def test_input_json_with_unknown_field_fails_cleanly_in_json_output(self) -> None:
        exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
            "--input-json",
            json.dumps({"url": VIDEO_URL, "exprt": "notion"}),
            "--output",
            "json",
            include_positional_url=False,
        )

        payload = json.loads(stdout)

        self.assertEqual(exit_code, 2)
        self.assertEqual(stderr, "")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["stage"], "input")
        self.assertIn("Invalid --input-json: unsupported field 'exprt'.", payload["error"])
        self.assertFalse(note_exists)
        export_mock.assert_not_called()

    def test_input_json_with_non_string_transcript_file_fails_cleanly(self) -> None:
        exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
            "--input-json",
            json.dumps({"url": VIDEO_URL, "transcript_file": 123}),
            "--output",
            "json",
            include_positional_url=False,
        )

        payload = json.loads(stdout)

        self.assertEqual(exit_code, 2)
        self.assertEqual(stderr, "")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["stage"], "input")
        self.assertIn("field 'transcript_file' must be a string", payload["error"])
        self.assertFalse(note_exists)
        export_mock.assert_not_called()

    def test_input_json_with_empty_transcript_file_fails_cleanly(self) -> None:
        exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
            "--input-json",
            json.dumps({"url": VIDEO_URL, "transcript_file": ""}),
            "--output",
            "json",
            include_positional_url=False,
        )

        payload = json.loads(stdout)

        self.assertEqual(exit_code, 2)
        self.assertEqual(stderr, "")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["stage"], "input")
        self.assertIn("field 'transcript_file' must not be empty", payload["error"])
        self.assertFalse(note_exists)
        export_mock.assert_not_called()

    def test_input_json_with_url_and_export_notion_works(self) -> None:
        exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
            "--input-json",
            json.dumps({"url": VIDEO_URL, "export": "notion"}),
            "--output",
            "json",
            include_positional_url=False,
        )

        payload = json.loads(stdout)

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["url"], VIDEO_URL)
        self.assertEqual(payload["export_mode"], "notion")
        self.assertEqual(payload["notion_page_id"], "page-123")
        self.assertTrue(note_exists)
        export_mock.assert_called_once()

    def test_input_json_file_with_url_works(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            payload_path = Path(temp_dir) / "payload.json"
            payload_path.write_text(json.dumps({"url": VIDEO_URL}), encoding="utf-8")

            exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
                "--input-json-file",
                str(payload_path),
                "--output",
                "json",
                note_text=None,
                include_positional_url=False,
            )

        payload = json.loads(stdout)

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["url"], VIDEO_URL)
        self.assertEqual(payload["export_mode"], "local")
        self.assertFalse(note_exists)
        export_mock.assert_not_called()

    def test_input_json_file_with_unknown_field_fails_cleanly_in_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            payload_path = Path(temp_dir) / "payload.json"
            payload_path.write_text(json.dumps({"url": VIDEO_URL, "exprt": "notion"}), encoding="utf-8")

            exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
                "--input-json-file",
                str(payload_path),
                "--output",
                "json",
                include_positional_url=False,
            )

        payload = json.loads(stdout)

        self.assertEqual(exit_code, 2)
        self.assertEqual(stderr, "")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["stage"], "input")
        self.assertIn("Invalid --input-json-file: unsupported field 'exprt'.", payload["error"])
        self.assertFalse(note_exists)
        export_mock.assert_not_called()

    def test_input_json_file_with_non_string_transcript_file_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            payload_path = Path(temp_dir) / "payload.json"
            payload_path.write_text(
                json.dumps({"url": VIDEO_URL, "transcript_file": 123}),
                encoding="utf-8",
            )

            exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
                "--input-json-file",
                str(payload_path),
                "--output",
                "json",
                include_positional_url=False,
            )

        payload = json.loads(stdout)

        self.assertEqual(exit_code, 2)
        self.assertEqual(stderr, "")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["stage"], "input")
        self.assertIn("field 'transcript_file' must be a string", payload["error"])
        self.assertFalse(note_exists)
        export_mock.assert_not_called()

    def test_input_json_file_with_whitespace_transcript_file_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            payload_path = Path(temp_dir) / "payload.json"
            payload_path.write_text(
                json.dumps({"url": VIDEO_URL, "transcript_file": "   "}),
                encoding="utf-8",
            )

            exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
                "--input-json-file",
                str(payload_path),
                "--output",
                "json",
                include_positional_url=False,
            )

        payload = json.loads(stdout)

        self.assertEqual(exit_code, 2)
        self.assertEqual(stderr, "")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["stage"], "input")
        self.assertIn("field 'transcript_file' must not be empty", payload["error"])
        self.assertFalse(note_exists)
        export_mock.assert_not_called()

    def test_input_json_file_with_url_and_export_notion_works(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            payload_path = Path(temp_dir) / "payload.json"
            payload_path.write_text(json.dumps({"url": VIDEO_URL, "export": "notion"}), encoding="utf-8")

            exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
                "--input-json-file",
                str(payload_path),
                "--output",
                "json",
                include_positional_url=False,
            )

        payload = json.loads(stdout)

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["url"], VIDEO_URL)
        self.assertEqual(payload["export_mode"], "notion")
        self.assertEqual(payload["notion_page_id"], "page-123")
        self.assertTrue(note_exists)
        export_mock.assert_called_once()

    def test_input_json_file_dash_reads_from_stdin(self) -> None:
        exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
            "--input-json-file",
            "-",
            "--output",
            "json",
            note_text=None,
            include_positional_url=False,
            stdin_value=json.dumps({"url": VIDEO_URL}),
        )

        payload = json.loads(stdout)

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["url"], VIDEO_URL)
        self.assertEqual(payload["export_mode"], "local")
        self.assertFalse(note_exists)
        export_mock.assert_not_called()

    def test_missing_input_json_file_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_path = Path(temp_dir) / "missing.json"

            exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
                "--input-json-file",
                str(missing_path),
                "--output",
                "json",
                include_positional_url=False,
            )

        payload = json.loads(stdout)

        self.assertEqual(exit_code, 2)
        self.assertEqual(stderr, "")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["stage"], "input")
        self.assertIn("Unable to read --input-json-file", payload["error"])
        self.assertFalse(note_exists)
        export_mock.assert_not_called()

    def test_invalid_input_json_file_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            payload_path = Path(temp_dir) / "payload.json"
            payload_path.write_text("{not json", encoding="utf-8")

            exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
                "--input-json-file",
                str(payload_path),
                "--output",
                "json",
                include_positional_url=False,
            )

        payload = json.loads(stdout)

        self.assertEqual(exit_code, 2)
        self.assertEqual(stderr, "")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["stage"], "input")
        self.assertIn("Invalid --input-json-file", payload["error"])
        self.assertFalse(note_exists)
        export_mock.assert_not_called()

    def test_positional_url_plus_input_json_file_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            payload_path = Path(temp_dir) / "payload.json"
            payload_path.write_text(json.dumps({"url": VIDEO_URL}), encoding="utf-8")

            exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
                "--input-json-file",
                str(payload_path),
                "--output",
                "json",
            )

        payload = json.loads(stdout)

        self.assertEqual(exit_code, 2)
        self.assertEqual(stderr, "")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["stage"], "input")
        self.assertIn("either a positional URL or --input-json-file", payload["error"])
        self.assertFalse(note_exists)
        export_mock.assert_not_called()

    def test_input_json_plus_input_json_file_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            payload_path = Path(temp_dir) / "payload.json"
            payload_path.write_text(json.dumps({"url": VIDEO_URL}), encoding="utf-8")

            exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
                "--input-json",
                json.dumps({"url": VIDEO_URL}),
                "--input-json-file",
                str(payload_path),
                "--output",
                "json",
                include_positional_url=False,
            )

        payload = json.loads(stdout)

        self.assertEqual(exit_code, 2)
        self.assertEqual(stderr, "")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["stage"], "input")
        self.assertIn("either --input-json or --input-json-file", payload["error"])
        self.assertFalse(note_exists)
        export_mock.assert_not_called()

    def test_invalid_input_json_fails_cleanly(self) -> None:
        exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
            "--input-json",
            "{not json",
            "--output",
            "json",
            include_positional_url=False,
        )

        payload = json.loads(stdout)

        self.assertEqual(exit_code, 2)
        self.assertEqual(stderr, "")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["stage"], "input")
        self.assertIn("Invalid --input-json", payload["error"])
        self.assertFalse(note_exists)
        export_mock.assert_not_called()

    def test_missing_url_in_input_json_fails_cleanly(self) -> None:
        exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
            "--input-json",
            json.dumps({"export": "local"}),
            "--output",
            "json",
            include_positional_url=False,
        )

        payload = json.loads(stdout)

        self.assertEqual(exit_code, 2)
        self.assertEqual(stderr, "")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["stage"], "input")
        self.assertIn("required field 'url' is missing", payload["error"])
        self.assertFalse(note_exists)
        export_mock.assert_not_called()

    def test_positional_url_plus_input_json_fails_cleanly(self) -> None:
        exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
            "--input-json",
            json.dumps({"url": VIDEO_URL}),
            "--output",
            "json",
        )

        payload = json.loads(stdout)

        self.assertEqual(exit_code, 2)
        self.assertEqual(stderr, "")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["stage"], "input")
        self.assertIn("either a positional URL or --input-json", payload["error"])
        self.assertFalse(note_exists)
        export_mock.assert_not_called()

    def test_input_json_export_plus_export_flag_fails_cleanly(self) -> None:
        exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
            "--input-json",
            json.dumps({"url": VIDEO_URL, "export": "notion"}),
            "--export",
            "local",
            "--output",
            "json",
            include_positional_url=False,
        )

        payload = json.loads(stdout)

        self.assertEqual(exit_code, 2)
        self.assertEqual(stderr, "")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["stage"], "input")
        self.assertIn("export either in JSON input or --export", payload["error"])
        self.assertFalse(note_exists)
        export_mock.assert_not_called()

    def test_input_json_file_export_plus_export_flag_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            payload_path = Path(temp_dir) / "payload.json"
            payload_path.write_text(json.dumps({"url": VIDEO_URL, "export": "notion"}), encoding="utf-8")

            exit_code, stdout, stderr, export_mock, note_exists, _note_content = self.run_ingest(
                "--input-json-file",
                str(payload_path),
                "--export",
                "local",
                "--output",
                "json",
                include_positional_url=False,
            )

        payload = json.loads(stdout)

        self.assertEqual(exit_code, 2)
        self.assertEqual(stderr, "")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["stage"], "input")
        self.assertIn("export either in JSON input or --export", payload["error"])
        self.assertFalse(note_exists)
        export_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
