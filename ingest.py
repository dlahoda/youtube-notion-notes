from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch a YouTube transcript and create a ready-to-paste GPT prompt."
    )
    parser.add_argument("url", help="YouTube URL to ingest")
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
        "--no-note",
        action="store_true",
        help="Skip optional OpenAI markdown note generation.",
    )
    parser.add_argument(
        "--export",
        choices=("local", "notion"),
        default="local",
        help="Export target. Defaults to local-only output.",
    )
    return parser.parse_args()


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


def main() -> int:
    load_env_file()
    args = parse_args()

    try:
        video_id = parse_youtube_url(args.url)
        transcript = fetch_transcript(video_id, language_preferences(args.languages))
    except TranscriptError as exc:
        print(f"Transcript error: {exc}", file=sys.stderr)
        return 1

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

    print(f"Transcript saved: {transcript_path}")
    print(f"GPT prompt saved: {prompt_path}")

    if args.no_note:
        print("Markdown note skipped: --no-note was provided.")
        if args.export == "notion":
            print(
                "Notion export skipped: --export notion requires a generated markdown note.",
                file=sys.stderr,
            )
            return 1
        return 0

    try:
        note_text = generate_note_if_available(prompt_text)
    except NoteGenerationError as exc:
        print(f"Markdown note skipped: {exc}")
        if args.export == "notion":
            print(
                "Notion export skipped: --export notion requires a generated markdown note.",
                file=sys.stderr,
            )
            return 1
        return 0

    if note_text:
        write_text(note_path, note_text)
        print(f"Markdown note saved: {note_path}")
        if args.export == "notion":
            try:
                from services.notion_export import export_markdown_note_to_notion

                notion_page_id = export_markdown_note_to_notion(note_text, args.url)
            except Exception as exc:
                print(f"Notion export failed: {exc}", file=sys.stderr)
                return 1
            print(f"Notion page created: {notion_page_id}")
    else:
        print("Markdown note skipped: OPENAI_API_KEY is not configured.")
        if args.export == "notion":
            print(
                "Notion export skipped: --export notion requires a generated markdown note.",
                file=sys.stderr,
            )
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
