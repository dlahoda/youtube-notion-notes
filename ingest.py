from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
from pathlib import Path
from typing import Any

from services.note_generator import (
    NoteGenerationError,
    build_manual_prompt,
    generate_note_if_available,
)
from services.transcript import TranscriptError, fetch_transcript, parse_youtube_url


OUTPUT_DIR = Path("output")
TRANSCRIPT_DIR = OUTPUT_DIR / "transcripts"
PROMPT_DIR = OUTPUT_DIR / "prompts"
NOTES_DIR = OUTPUT_DIR / "notes"
PROMPT_TEMPLATE_PATH = Path("prompts") / "comprehensive_note.md"


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


def resolve_cli_input(args: argparse.Namespace) -> argparse.Namespace:
    payload: dict[str, Any] = {}

    if args.input_json is not None:
        if args.url:
            raise CliInputError("Provide either a positional URL or --input-json, not both.")
        try:
            raw_payload = json.loads(args.input_json)
        except json.JSONDecodeError as exc:
            raise CliInputError(f"Invalid --input-json: {exc.msg}.") from exc

        if not isinstance(raw_payload, dict):
            raise CliInputError("Invalid --input-json: payload must be a JSON object.")
        payload = raw_payload

        if "url" not in payload or not payload["url"]:
            raise CliInputError("Invalid --input-json: required field 'url' is missing.")
        if not isinstance(payload["url"], str):
            raise CliInputError("Invalid --input-json: field 'url' must be a string.")
        args.url = payload["url"]

        if "export" in payload:
            if args.export is not None:
                raise CliInputError("Provide export either in --input-json or --export, not both.")
            if payload["export"] not in ("local", "notion"):
                raise CliInputError(
                    "Invalid --input-json: field 'export' must be 'local' or 'notion'."
                )
            args.export = payload["export"]

    if not args.url:
        raise CliInputError("A YouTube URL is required as a positional argument or in --input-json.")

    if args.export is None:
        args.export = "local"

    return args


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


def language_preferences(cli_value: str | None) -> list[str]:
    raw_value = cli_value or os.getenv("YOUTUBE_TRANSCRIPT_LANGUAGES", "en")
    languages = [item.strip() for item in raw_value.split(",") if item.strip()]
    return languages or ["en"]


def safe_output_name(value: str) -> str:
    allowed = []
    for char in value:
        if char.isalnum() or char in ("-", "_"):
            allowed.append(char)
        else:
            allowed.append("-")
    cleaned = "".join(allowed).strip("-_")
    return cleaned or "youtube-video"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def result_contract(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "ok": False,
        "url": args.url,
        "export_mode": args.export,
        "transcript_path": None,
        "prompt_path": None,
        "note_path": None,
        "notion_page_id": None,
    }


def run_pipeline(args: argparse.Namespace, *, human_output: bool) -> tuple[int, dict[str, Any]]:
    result = result_contract(args)

    def log(message: str, *, error: bool = False) -> None:
        if human_output:
            print(message, file=sys.stderr if error else sys.stdout)

    try:
        video_id = parse_youtube_url(args.url)
        transcript = fetch_transcript(video_id, language_preferences(args.languages))
    except TranscriptError as exc:
        result["stage"] = "transcript"
        result["error"] = str(exc)
        log(f"Transcript error: {exc}", error=True)
        return 1, result

    output_name = safe_output_name(args.output_name or video_id)
    transcript_path = TRANSCRIPT_DIR / f"{output_name}.txt"
    prompt_path = PROMPT_DIR / f"{output_name}_prompt.md"
    note_path = NOTES_DIR / f"{output_name}.md"

    transcript_text = transcript.as_text()
    prompt_text = build_manual_prompt(
        template_path=PROMPT_TEMPLATE_PATH,
        video_url=args.url,
        video_id=video_id,
        transcript=transcript_text,
    )

    write_text(transcript_path, transcript_text)
    write_text(prompt_path, prompt_text)
    result["transcript_path"] = str(transcript_path)
    result["prompt_path"] = str(prompt_path)

    log(f"Transcript saved: {transcript_path}")
    log(f"GPT prompt saved: {prompt_path}")

    if args.no_note:
        log("Markdown note skipped: --no-note was provided.")
        if args.export == "notion":
            message = "Notion export skipped: --export notion requires a generated markdown note."
            result["stage"] = "notion_export"
            result["error"] = message
            log(message, error=True)
            return 1, result
        result["ok"] = True
        return 0, result

    try:
        note_text = generate_note_if_available(prompt_text)
    except NoteGenerationError as exc:
        log(f"Markdown note skipped: {exc}")
        if args.export == "notion":
            message = "Notion export skipped: --export notion requires a generated markdown note."
            result["stage"] = "notion_export"
            result["error"] = message
            log(message, error=True)
            return 1, result
        result["ok"] = True
        return 0, result

    if note_text:
        write_text(note_path, note_text)
        result["note_path"] = str(note_path)
        log(f"Markdown note saved: {note_path}")
        if args.export == "notion":
            try:
                from services.notion_export import export_markdown_note_to_notion

                notion_page = export_markdown_note_to_notion(note_text, args.url)
            except Exception as exc:
                result["stage"] = "notion_export"
                result["error"] = str(exc)
                log(f"Notion export failed: {exc}", error=True)
                return 1, result
            result["notion_page_id"] = notion_page.id
            if notion_page.url:
                result["notion_page_url"] = notion_page.url
            log(f"Notion page created: {notion_page.id}")
    else:
        log("Markdown note skipped: OPENAI_API_KEY is not configured.")
        if args.export == "notion":
            message = "Notion export skipped: --export notion requires a generated markdown note."
            result["stage"] = "notion_export"
            result["error"] = message
            log(message, error=True)
            return 1, result

    result["ok"] = True
    return 0, result


def main() -> int:
    load_env_file()
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

    if args.output == "json":
        stdout = sys.stdout
        with contextlib.redirect_stdout(sys.stderr):
            exit_code, result = run_pipeline(args, human_output=False)
        print(json.dumps(result, indent=2, sort_keys=True), file=stdout)
        return exit_code

    exit_code, _result = run_pipeline(args, human_output=True)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
