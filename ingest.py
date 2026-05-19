from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
from pathlib import Path
from typing import Any

from services.pipeline import PipelineRequest, run_pipeline


JSON_INPUT_FIELDS = {"url", "transcript_file", "export"}


class CliInputError(Exception):
    def __init__(self, message: str, *, stage: str = "input") -> None:
        super().__init__(message)
        self.stage = stage


class IngestArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliInputError(message)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = IngestArgumentParser(
        description="Fetch a YouTube transcript and create a ready-to-paste GPT prompt."
    )
    parser.add_argument("url", nargs="?", help="YouTube URL to ingest")
    parser.add_argument(
        "--input-json",
        default=None,
        help='Structured JSON input payload, for example: {"url":"https://youtu.be/VIDEO_ID"}',
    )
    parser.add_argument(
        "--input-json-file",
        default=None,
        help="Path to a structured JSON input payload, or '-' to read it from stdin.",
    )
    parser.add_argument(
        "--languages",
        default=None,
        help="Comma-separated transcript language preferences, for example: en,uk",
    )
    parser.add_argument(
        "--output-name",
        default=None,
        help="Optional filename stem. Defaults to the YouTube video id.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output root for transcript, prompt, and note files. Defaults to ./output.",
    )
    parser.add_argument(
        "--env-file",
        default=None,
        help="Env file to load before running the pipeline. Defaults to ./.env when it exists.",
    )
    parser.add_argument(
        "--transcript-file",
        default=None,
        help="Read transcript text from a UTF-8 file while keeping the positional YouTube URL as source metadata.",
    )
    parser.add_argument(
        "--output",
        choices=("text", "json"),
        default="text",
        help="Result output format. Defaults to human-readable text.",
    )
    parser.add_argument(
        "--no-note",
        action="store_true",
        help="Skip optional OpenAI markdown note generation.",
    )
    parser.add_argument(
        "--export",
        choices=("local", "notion"),
        default=None,
        help="Export target. Defaults to local-only output.",
    )
    args = parser.parse_args(argv)
    return resolve_cli_input(args)


def input_error_result(message: str, *, stage: str = "input") -> dict[str, Any]:
    return {
        "ok": False,
        "stage": stage,
        "error": message,
    }


def requested_json_output(argv: list[str]) -> bool:
    for index, arg in enumerate(argv):
        if arg == "--output" and index + 1 < len(argv):
            return argv[index + 1] == "json"
        if arg.startswith("--output="):
            return arg.split("=", 1)[1] == "json"
    return False


def load_json_payload(raw_json: str, *, source: str) -> dict[str, Any]:
    try:
        raw_payload = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise CliInputError(f"Invalid {source}: {exc.msg}.") from exc

    if not isinstance(raw_payload, dict):
        raise CliInputError(f"Invalid {source}: payload must be a JSON object.")
    return raw_payload


def apply_json_payload(args: argparse.Namespace, payload: dict[str, Any], *, source: str) -> None:
    unsupported_fields = sorted(set(payload) - JSON_INPUT_FIELDS)
    if unsupported_fields:
        raise CliInputError(f"Invalid {source}: unsupported field '{unsupported_fields[0]}'.")

    if "url" not in payload or not payload["url"]:
        raise CliInputError(f"Invalid {source}: required field 'url' is missing.")
    if not isinstance(payload["url"], str):
        raise CliInputError(f"Invalid {source}: field 'url' must be a string.")
    args.url = payload["url"]

    if "export" in payload:
        if args.export is not None:
            raise CliInputError("Provide export either in JSON input or --export, not both.")
        if payload["export"] not in ("local", "notion"):
            raise CliInputError(f"Invalid {source}: field 'export' must be 'local' or 'notion'.")
        args.export = payload["export"]

    if "transcript_file" in payload:
        if not isinstance(payload["transcript_file"], str):
            raise CliInputError(f"Invalid {source}: field 'transcript_file' must be a string.")
        if not payload["transcript_file"].strip():
            raise CliInputError(f"Invalid {source}: field 'transcript_file' must not be empty.")
        args.transcript_file = payload["transcript_file"]


def read_json_payload_file(path_value: str) -> str:
    if path_value == "-":
        return sys.stdin.read()

    path = Path(path_value)
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CliInputError(f"Unable to read --input-json-file '{path_value}': {exc.strerror}.") from exc


def resolve_cli_input(args: argparse.Namespace) -> argparse.Namespace:
    payload: dict[str, Any] = {}
    positional_url = args.url
    cli_transcript_file = args.transcript_file

    if args.input_json is not None and args.input_json_file is not None:
        raise CliInputError("Provide either --input-json or --input-json-file, not both.")

    if args.input_json is not None:
        if args.url:
            raise CliInputError("Provide either a positional URL or --input-json, not both.")
        payload = load_json_payload(args.input_json, source="--input-json")
        apply_json_payload(args, payload, source="--input-json")

    if args.input_json_file is not None:
        if args.url:
            raise CliInputError("Provide either a positional URL or --input-json-file, not both.")
        payload = load_json_payload(read_json_payload_file(args.input_json_file), source="--input-json-file")
        apply_json_payload(args, payload, source="--input-json-file")

    if cli_transcript_file and not positional_url:
        raise CliInputError("A YouTube URL is required as a positional argument when using --transcript-file.")

    if not args.url:
        raise CliInputError(
            "A YouTube URL is required as a positional argument, --input-json, or --input-json-file."
        )

    if args.export is None:
        args.export = "local"

    return args


def build_pipeline_request(args: argparse.Namespace) -> PipelineRequest:
    return PipelineRequest(
        url=args.url,
        export_mode=args.export,
        languages=args.languages,
        output_name=args.output_name,
        no_note=args.no_note,
        transcript_file=args.transcript_file,
        output_dir=args.output_dir,
    )


def load_env_file(path: Path = Path(".env")) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def main() -> int:
    output_mode = "json" if requested_json_output(sys.argv[1:]) else "text"
    try:
        args = parse_args()
    except CliInputError as exc:
        if output_mode == "json":
            print(
                json.dumps(
                    input_error_result(str(exc), stage=exc.stage),
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            print(f"Input error: {exc}", file=sys.stderr)
        return 2

    load_env_file(Path(args.env_file) if args.env_file else Path(".env"))

    if args.output == "json":
        stdout = sys.stdout
        with contextlib.redirect_stdout(sys.stderr):
            exit_code, result = run_pipeline(build_pipeline_request(args), human_output=False)
        print(json.dumps(result, indent=2, sort_keys=True), file=stdout)
        return exit_code

    exit_code, _result = run_pipeline(build_pipeline_request(args), human_output=True)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
