from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import ingest
from youtube_notion_notes.services.pipeline import PipelineRequest


VIDEO_ID = "abc123def45"
VIDEO_URL = f"https://youtu.be/{VIDEO_ID}"


class IngestInputTests(unittest.TestCase):
    def run_ingest(
        self,
        *extra_args: str,
        include_positional_url: bool = False,
        stdin_value: str = "",
    ) -> tuple[int, str, str, Mock]:
        argv = ["ingest.py"]
        if include_positional_url:
            argv.append(VIDEO_URL)
        argv.extend(extra_args)
        stdout = io.StringIO()
        stderr = io.StringIO()
        run_pipeline_mock = Mock(return_value=(0, {"ok": True}))

        with (
            patch.object(sys, "argv", argv),
            patch.object(sys, "stdin", io.StringIO(stdin_value)),
            patch.object(ingest, "load_env_file"),
            patch.object(ingest, "run_pipeline", run_pipeline_mock),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            exit_code = ingest.main()

        return exit_code, stdout.getvalue(), stderr.getvalue(), run_pipeline_mock

    def assert_input_error(self, stdout: str, stderr: str, expected_error: str) -> None:
        payload = json.loads(stdout)

        self.assertEqual(stderr, "")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["stage"], "input")
        self.assertIn(expected_error, payload["error"])

    def test_main_converts_cli_args_to_pipeline_request(self) -> None:
        exit_code, stdout, stderr, run_pipeline_mock = self.run_ingest(
            "--input-json",
            json.dumps({"url": VIDEO_URL, "export": "notion"}),
            "--languages",
            "en,uk",
            "--output-name",
            "custom-name",
            "--no-note",
            "--output",
            "json",
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(json.loads(stdout), {"ok": True})
        run_pipeline_mock.assert_called_once_with(
            PipelineRequest(
                url=VIDEO_URL,
                export_mode="notion",
                languages="en,uk",
                output_name="custom-name",
                no_note=True,
            ),
            human_output=False,
        )

    def test_main_converts_transcript_file_flag_to_pipeline_request(self) -> None:
        exit_code, stdout, stderr, run_pipeline_mock = self.run_ingest(
            "--transcript-file",
            "./manual-transcript.txt",
            "--no-note",
            "--output",
            "json",
            include_positional_url=True,
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(json.loads(stdout), {"ok": True})
        run_pipeline_mock.assert_called_once_with(
            PipelineRequest(
                url=VIDEO_URL,
                export_mode="local",
                languages=None,
                output_name=None,
                no_note=True,
                transcript_file="./manual-transcript.txt",
            ),
            human_output=False,
        )

    def test_main_converts_output_dir_flag_to_pipeline_request(self) -> None:
        exit_code, stdout, stderr, run_pipeline_mock = self.run_ingest(
            "--output-dir",
            "./tmp-output",
            "--no-note",
            "--output",
            "json",
            include_positional_url=True,
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(json.loads(stdout), {"ok": True})
        run_pipeline_mock.assert_called_once_with(
            PipelineRequest(
                url=VIDEO_URL,
                export_mode="local",
                languages=None,
                output_name=None,
                no_note=True,
                output_dir="./tmp-output",
            ),
            human_output=False,
        )

    def test_main_loads_env_file_flag_before_running_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / "custom.env"
            env_path.write_text(
                "YNN_ENV_FILE_TEST=loaded\nEXISTING_KEY=from-file\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            stderr = io.StringIO()

            def assert_env_loaded(_request: PipelineRequest, *, human_output: bool) -> tuple[int, dict]:
                self.assertFalse(human_output)
                self.assertEqual(os.environ["YNN_ENV_FILE_TEST"], "loaded")
                self.assertEqual(os.environ["EXISTING_KEY"], "already-present")
                return 0, {"ok": True}

            run_pipeline_mock = Mock(side_effect=assert_env_loaded)

            with (
                patch.dict(os.environ, {"EXISTING_KEY": "already-present"}, clear=True),
                patch.object(
                    sys,
                    "argv",
                    [
                        "ingest.py",
                        VIDEO_URL,
                        "--env-file",
                        str(env_path),
                        "--no-note",
                        "--output",
                        "json",
                    ],
                ),
                patch.object(sys, "stdin", io.StringIO("")),
                patch.object(ingest, "run_pipeline", run_pipeline_mock),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                exit_code = ingest.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(json.loads(stdout.getvalue()), {"ok": True})
        run_pipeline_mock.assert_called_once()

    def test_missing_default_env_file_does_not_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_env_path = Path(temp_dir) / ".env"

            ingest.load_env_file(missing_env_path)

    def test_missing_explicit_env_file_fails_in_text_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_env_path = Path(temp_dir) / "missing.env"
            stdout = io.StringIO()
            stderr = io.StringIO()
            run_pipeline_mock = Mock(return_value=(0, {"ok": True}))

            with (
                patch.object(
                    sys,
                    "argv",
                    [
                        "ingest.py",
                        VIDEO_URL,
                        "--env-file",
                        str(missing_env_path),
                    ],
                ),
                patch.object(sys, "stdin", io.StringIO("")),
                patch.object(ingest, "run_pipeline", run_pipeline_mock),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                exit_code = ingest.main()

        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("Input error: Unable to read --env-file", stderr.getvalue())
        run_pipeline_mock.assert_not_called()

    def test_missing_explicit_env_file_fails_with_json_only_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_env_path = Path(temp_dir) / "missing.env"
            stdout = io.StringIO()
            stderr = io.StringIO()
            run_pipeline_mock = Mock(return_value=(0, {"ok": True}))

            with (
                patch.object(
                    sys,
                    "argv",
                    [
                        "ingest.py",
                        VIDEO_URL,
                        "--env-file",
                        str(missing_env_path),
                        "--output",
                        "json",
                    ],
                ),
                patch.object(sys, "stdin", io.StringIO("")),
                patch.object(ingest, "run_pipeline", run_pipeline_mock),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                exit_code = ingest.main()

        payload = json.loads(stdout.getvalue())

        self.assertEqual(exit_code, 2)
        self.assertEqual(stderr.getvalue(), "")
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["stage"], "input")
        self.assertIn("Unable to read --env-file", payload["error"])
        run_pipeline_mock.assert_not_called()

    def test_main_converts_input_json_transcript_file_to_pipeline_request(self) -> None:
        exit_code, stdout, stderr, run_pipeline_mock = self.run_ingest(
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
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(json.loads(stdout), {"ok": True})
        run_pipeline_mock.assert_called_once_with(
            PipelineRequest(
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
            exit_code, stdout, stderr, run_pipeline_mock = self.run_ingest(
                "--input-json-file",
                str(payload_path),
                "--no-note",
                "--output",
                "json",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(json.loads(stdout), {"ok": True})
        run_pipeline_mock.assert_called_once_with(
            PipelineRequest(
                url=VIDEO_URL,
                export_mode="local",
                languages=None,
                output_name=None,
                no_note=True,
                transcript_file="./manual-transcript.txt",
            ),
            human_output=False,
        )

    def test_input_json_with_url_maps_to_default_local_pipeline_request(self) -> None:
        exit_code, stdout, stderr, run_pipeline_mock = self.run_ingest(
            "--input-json",
            json.dumps({"url": VIDEO_URL}),
            "--output",
            "json",
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(json.loads(stdout), {"ok": True})
        run_pipeline_mock.assert_called_once_with(
            PipelineRequest(
                url=VIDEO_URL,
                export_mode="local",
                languages=None,
                output_name=None,
                no_note=False,
            ),
            human_output=False,
        )

    def test_input_json_with_url_and_export_notion_maps_pipeline_request(self) -> None:
        exit_code, stdout, stderr, run_pipeline_mock = self.run_ingest(
            "--input-json",
            json.dumps({"url": VIDEO_URL, "export": "notion"}),
            "--output",
            "json",
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(json.loads(stdout), {"ok": True})
        run_pipeline_mock.assert_called_once_with(
            PipelineRequest(
                url=VIDEO_URL,
                export_mode="notion",
                languages=None,
                output_name=None,
                no_note=False,
            ),
            human_output=False,
        )

    def test_input_json_file_with_url_maps_to_default_local_pipeline_request(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            payload_path = Path(temp_dir) / "payload.json"
            payload_path.write_text(json.dumps({"url": VIDEO_URL}), encoding="utf-8")
            exit_code, stdout, stderr, run_pipeline_mock = self.run_ingest(
                "--input-json-file",
                str(payload_path),
                "--output",
                "json",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(json.loads(stdout), {"ok": True})
        run_pipeline_mock.assert_called_once_with(
            PipelineRequest(
                url=VIDEO_URL,
                export_mode="local",
                languages=None,
                output_name=None,
                no_note=False,
            ),
            human_output=False,
        )

    def test_input_json_file_with_url_and_export_notion_maps_pipeline_request(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            payload_path = Path(temp_dir) / "payload.json"
            payload_path.write_text(json.dumps({"url": VIDEO_URL, "export": "notion"}), encoding="utf-8")
            exit_code, stdout, stderr, run_pipeline_mock = self.run_ingest(
                "--input-json-file",
                str(payload_path),
                "--output",
                "json",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(json.loads(stdout), {"ok": True})
        run_pipeline_mock.assert_called_once_with(
            PipelineRequest(
                url=VIDEO_URL,
                export_mode="notion",
                languages=None,
                output_name=None,
                no_note=False,
            ),
            human_output=False,
        )

    def test_input_json_file_dash_reads_from_stdin(self) -> None:
        exit_code, stdout, stderr, run_pipeline_mock = self.run_ingest(
            "--input-json-file",
            "-",
            "--output",
            "json",
            stdin_value=json.dumps({"url": VIDEO_URL}),
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(json.loads(stdout), {"ok": True})
        run_pipeline_mock.assert_called_once_with(
            PipelineRequest(
                url=VIDEO_URL,
                export_mode="local",
                languages=None,
                output_name=None,
                no_note=False,
            ),
            human_output=False,
        )

    def test_input_json_with_unknown_field_fails_cleanly_in_json_output(self) -> None:
        exit_code, stdout, stderr, run_pipeline_mock = self.run_ingest(
            "--input-json",
            json.dumps({"url": VIDEO_URL, "exprt": "notion"}),
            "--output",
            "json",
        )

        self.assertEqual(exit_code, 2)
        self.assert_input_error(stdout, stderr, "Invalid --input-json: unsupported field 'exprt'.")
        run_pipeline_mock.assert_not_called()

    def test_input_json_with_output_dir_field_fails_cleanly(self) -> None:
        exit_code, stdout, stderr, run_pipeline_mock = self.run_ingest(
            "--input-json",
            json.dumps({"url": VIDEO_URL, "output_dir": "./tmp-output"}),
            "--output",
            "json",
        )

        self.assertEqual(exit_code, 2)
        self.assert_input_error(stdout, stderr, "Invalid --input-json: unsupported field 'output_dir'.")
        run_pipeline_mock.assert_not_called()

    def test_input_json_file_with_unknown_field_fails_cleanly_in_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            payload_path = Path(temp_dir) / "payload.json"
            payload_path.write_text(json.dumps({"url": VIDEO_URL, "exprt": "notion"}), encoding="utf-8")
            exit_code, stdout, stderr, run_pipeline_mock = self.run_ingest(
                "--input-json-file",
                str(payload_path),
                "--output",
                "json",
            )

        self.assertEqual(exit_code, 2)
        self.assert_input_error(stdout, stderr, "Invalid --input-json-file: unsupported field 'exprt'.")
        run_pipeline_mock.assert_not_called()

    def test_missing_url_in_input_json_fails_cleanly(self) -> None:
        exit_code, stdout, stderr, run_pipeline_mock = self.run_ingest(
            "--input-json",
            json.dumps({"export": "local"}),
            "--output",
            "json",
        )

        self.assertEqual(exit_code, 2)
        self.assert_input_error(stdout, stderr, "required field 'url' is missing")
        run_pipeline_mock.assert_not_called()

    def test_invalid_input_json_fails_cleanly(self) -> None:
        exit_code, stdout, stderr, run_pipeline_mock = self.run_ingest(
            "--input-json",
            "{not json",
            "--output",
            "json",
        )

        self.assertEqual(exit_code, 2)
        self.assert_input_error(stdout, stderr, "Invalid --input-json")
        run_pipeline_mock.assert_not_called()

    def test_invalid_input_json_file_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            payload_path = Path(temp_dir) / "payload.json"
            payload_path.write_text("{not json", encoding="utf-8")
            exit_code, stdout, stderr, run_pipeline_mock = self.run_ingest(
                "--input-json-file",
                str(payload_path),
                "--output",
                "json",
            )

        self.assertEqual(exit_code, 2)
        self.assert_input_error(stdout, stderr, "Invalid --input-json-file")
        run_pipeline_mock.assert_not_called()

    def test_input_json_plus_input_json_file_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            payload_path = Path(temp_dir) / "payload.json"
            payload_path.write_text(json.dumps({"url": VIDEO_URL}), encoding="utf-8")
            exit_code, stdout, stderr, run_pipeline_mock = self.run_ingest(
                "--input-json",
                json.dumps({"url": VIDEO_URL}),
                "--input-json-file",
                str(payload_path),
                "--output",
                "json",
            )

        self.assertEqual(exit_code, 2)
        self.assert_input_error(stdout, stderr, "either --input-json or --input-json-file")
        run_pipeline_mock.assert_not_called()

    def test_positional_url_plus_input_json_fails_cleanly(self) -> None:
        exit_code, stdout, stderr, run_pipeline_mock = self.run_ingest(
            "--input-json",
            json.dumps({"url": VIDEO_URL}),
            "--output",
            "json",
            include_positional_url=True,
        )

        self.assertEqual(exit_code, 2)
        self.assert_input_error(stdout, stderr, "either a positional URL or --input-json")
        run_pipeline_mock.assert_not_called()

    def test_positional_url_plus_input_json_file_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            payload_path = Path(temp_dir) / "payload.json"
            payload_path.write_text(json.dumps({"url": VIDEO_URL}), encoding="utf-8")
            exit_code, stdout, stderr, run_pipeline_mock = self.run_ingest(
                "--input-json-file",
                str(payload_path),
                "--output",
                "json",
                include_positional_url=True,
            )

        self.assertEqual(exit_code, 2)
        self.assert_input_error(stdout, stderr, "either a positional URL or --input-json-file")
        run_pipeline_mock.assert_not_called()

    def test_input_json_export_plus_export_flag_fails_cleanly(self) -> None:
        exit_code, stdout, stderr, run_pipeline_mock = self.run_ingest(
            "--input-json",
            json.dumps({"url": VIDEO_URL, "export": "notion"}),
            "--export",
            "local",
            "--output",
            "json",
        )

        self.assertEqual(exit_code, 2)
        self.assert_input_error(stdout, stderr, "export either in JSON input or --export")
        run_pipeline_mock.assert_not_called()

    def test_input_json_file_export_plus_export_flag_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            payload_path = Path(temp_dir) / "payload.json"
            payload_path.write_text(json.dumps({"url": VIDEO_URL, "export": "notion"}), encoding="utf-8")
            exit_code, stdout, stderr, run_pipeline_mock = self.run_ingest(
                "--input-json-file",
                str(payload_path),
                "--export",
                "local",
                "--output",
                "json",
            )

        self.assertEqual(exit_code, 2)
        self.assert_input_error(stdout, stderr, "export either in JSON input or --export")
        run_pipeline_mock.assert_not_called()

    def test_input_json_with_non_string_transcript_file_fails_cleanly(self) -> None:
        exit_code, stdout, stderr, run_pipeline_mock = self.run_ingest(
            "--input-json",
            json.dumps({"url": VIDEO_URL, "transcript_file": 123}),
            "--output",
            "json",
        )

        self.assertEqual(exit_code, 2)
        self.assert_input_error(stdout, stderr, "field 'transcript_file' must be a string")
        run_pipeline_mock.assert_not_called()

    def test_input_json_with_empty_transcript_file_fails_cleanly(self) -> None:
        exit_code, stdout, stderr, run_pipeline_mock = self.run_ingest(
            "--input-json",
            json.dumps({"url": VIDEO_URL, "transcript_file": ""}),
            "--output",
            "json",
        )

        self.assertEqual(exit_code, 2)
        self.assert_input_error(stdout, stderr, "field 'transcript_file' must not be empty")
        run_pipeline_mock.assert_not_called()

    def test_input_json_file_with_non_string_transcript_file_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            payload_path = Path(temp_dir) / "payload.json"
            payload_path.write_text(
                json.dumps({"url": VIDEO_URL, "transcript_file": 123}),
                encoding="utf-8",
            )
            exit_code, stdout, stderr, run_pipeline_mock = self.run_ingest(
                "--input-json-file",
                str(payload_path),
                "--output",
                "json",
            )

        self.assertEqual(exit_code, 2)
        self.assert_input_error(stdout, stderr, "field 'transcript_file' must be a string")
        run_pipeline_mock.assert_not_called()

    def test_input_json_file_with_whitespace_transcript_file_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            payload_path = Path(temp_dir) / "payload.json"
            payload_path.write_text(
                json.dumps({"url": VIDEO_URL, "transcript_file": "   "}),
                encoding="utf-8",
            )
            exit_code, stdout, stderr, run_pipeline_mock = self.run_ingest(
                "--input-json-file",
                str(payload_path),
                "--output",
                "json",
            )

        self.assertEqual(exit_code, 2)
        self.assert_input_error(stdout, stderr, "field 'transcript_file' must not be empty")
        run_pipeline_mock.assert_not_called()

    def test_transcript_file_without_positional_url_fails_through_input_error_path(self) -> None:
        exit_code, stdout, stderr, run_pipeline_mock = self.run_ingest(
            "--transcript-file",
            "./manual-transcript.txt",
            "--output",
            "json",
        )

        self.assertEqual(exit_code, 2)
        self.assert_input_error(stdout, stderr, "A YouTube URL is required")
        run_pipeline_mock.assert_not_called()

    def test_transcript_file_with_input_json_fails_through_input_error_path(self) -> None:
        exit_code, stdout, stderr, run_pipeline_mock = self.run_ingest(
            "--input-json",
            json.dumps({"url": VIDEO_URL}),
            "--transcript-file",
            "./manual-transcript.txt",
            "--output",
            "json",
        )

        self.assertEqual(exit_code, 2)
        self.assert_input_error(stdout, stderr, "positional argument when using --transcript-file")
        run_pipeline_mock.assert_not_called()

    def test_missing_input_json_file_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_path = Path(temp_dir) / "missing.json"
            exit_code, stdout, stderr, run_pipeline_mock = self.run_ingest(
                "--input-json-file",
                str(missing_path),
                "--output",
                "json",
            )

        self.assertEqual(exit_code, 2)
        self.assert_input_error(stdout, stderr, "Unable to read --input-json-file")
        run_pipeline_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
