from __future__ import annotations

import argparse
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
