from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from youtube_notion_notes.services.note_generator import (
    NoteGenerationError,
    PromptTemplateError,
    build_manual_prompt,
    generate_note_if_available,
)
from youtube_notion_notes.services.transcript import (
    TranscriptError,
    TranscriptSelectionMetadata,
    fetch_transcript,
    parse_youtube_url,
    transcript_file_selection_metadata,
)


OUTPUT_DIR = Path("output")
TRANSCRIPT_DIR = OUTPUT_DIR / "transcripts"
PROMPT_DIR = OUTPUT_DIR / "prompts"
NOTES_DIR = OUTPUT_DIR / "notes"
OUTPUT_DIR_ENV_VAR = "YNN_OUTPUT_DIR"
REQUIRED_NOTION_EXPORT_ENV_VARS = (
    "OPENAI_API_KEY",
    "NOTION_API_KEY",
    "NOTION_DATABASE_ID",
)


@dataclass(frozen=True)
class PipelineRequest:
    url: str
    export_mode: str
    languages: str | None
    output_name: str | None
    no_note: bool
    transcript_file: str | None = None
    output_dir: str | None = None


@dataclass(frozen=True)
class PipelineOutputPaths:
    transcript_dir: Path
    prompt_dir: Path
    notes_dir: Path


def output_paths_for_request(request: PipelineRequest) -> PipelineOutputPaths:
    if request.output_dir:
        output_root = Path(request.output_dir)
    elif os.getenv(OUTPUT_DIR_ENV_VAR):
        output_root = Path(os.environ[OUTPUT_DIR_ENV_VAR])
    else:
        output_root = OUTPUT_DIR

    if output_root == OUTPUT_DIR:
        return PipelineOutputPaths(
            transcript_dir=TRANSCRIPT_DIR,
            prompt_dir=PROMPT_DIR,
            notes_dir=NOTES_DIR,
        )

    return PipelineOutputPaths(
        transcript_dir=output_root / "transcripts",
        prompt_dir=output_root / "prompts",
        notes_dir=output_root / "notes",
    )


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


def read_transcript_file(path_value: str) -> str:
    try:
        transcript_text = Path(path_value).read_text(encoding="utf-8")
    except OSError as exc:
        raise TranscriptError(f"Unable to read --transcript-file '{path_value}': {exc.strerror}.") from exc
    if not transcript_text.strip():
        raise TranscriptError(f"--transcript-file '{path_value}' is empty or contains only whitespace.")
    return transcript_text


def result_contract(request: PipelineRequest) -> dict[str, Any]:
    return {
        "ok": False,
        "url": request.url,
        "export_mode": request.export_mode,
        "transcript_path": None,
        "prompt_path": None,
        "note_path": None,
        "notion_page_id": None,
        "transcript_selection": None,
    }


def format_transcript_selection(metadata: TranscriptSelectionMetadata) -> str | None:
    if metadata.origin == "transcript_file":
        return "Transcript selected: transcript file"

    if not metadata.source_language:
        return None

    if metadata.requires_translation and metadata.selected_language:
        return (
            f"Transcript selected: {metadata.origin} "
            f"{metadata.source_language} -> {metadata.selected_language}"
        )

    return f"Transcript selected: {metadata.origin} {metadata.source_language}"


def missing_notion_export_config() -> list[str]:
    return [
        name
        for name in REQUIRED_NOTION_EXPORT_ENV_VARS
        if not os.getenv(name, "").strip()
    ]


def run_pipeline(request: PipelineRequest, *, human_output: bool) -> tuple[int, dict[str, Any]]:
    result = result_contract(request)

    def log(message: str, *, error: bool = False) -> None:
        if human_output:
            print(message, file=sys.stderr if error else sys.stdout)

    if request.export_mode == "notion":
        missing_config = missing_notion_export_config()
        if missing_config:
            missing_names = ", ".join(missing_config)
            message = f"Notion export config error: missing required config: {missing_names}."
            result["stage"] = "config"
            result["error"] = message
            log(message, error=True)
            return 1, result

    try:
        video_id = parse_youtube_url(request.url)
        if request.transcript_file:
            transcript_text = read_transcript_file(request.transcript_file)
            selection_metadata = transcript_file_selection_metadata()
        else:
            transcript = fetch_transcript(video_id, language_preferences(request.languages))
            transcript_text = transcript.as_text()
            raw_selection_metadata = getattr(transcript, "selection_metadata", None)
            selection_metadata = (
                raw_selection_metadata
                if isinstance(raw_selection_metadata, TranscriptSelectionMetadata)
                else None
            )
    except TranscriptError as exc:
        result["stage"] = "transcript"
        result["error"] = str(exc)
        log(f"Transcript error: {exc}", error=True)
        return 1, result

    if selection_metadata is not None:
        result["transcript_selection"] = selection_metadata.as_dict()
        selection_line = format_transcript_selection(selection_metadata)
        if selection_line:
            log(selection_line)

    output_name = safe_output_name(request.output_name or video_id)
    output_paths = output_paths_for_request(request)
    transcript_path = output_paths.transcript_dir / f"{output_name}.txt"
    prompt_path = output_paths.prompt_dir / f"{output_name}_prompt.md"
    note_path = output_paths.notes_dir / f"{output_name}.md"

    try:
        prompt_text = build_manual_prompt(
            video_url=request.url,
            video_id=video_id,
            transcript=transcript_text,
        )
    except PromptTemplateError as exc:
        result["stage"] = "prompt_template"
        result["error"] = str(exc)
        log(f"Prompt template error: {exc}", error=True)
        return 1, result

    write_text(transcript_path, transcript_text)
    write_text(prompt_path, prompt_text)
    result["transcript_path"] = str(transcript_path)
    result["prompt_path"] = str(prompt_path)

    log(f"Transcript saved: {transcript_path}")
    log(f"GPT prompt saved: {prompt_path}")

    if request.no_note:
        log("Markdown note skipped: --no-note was provided.")
        if request.export_mode == "notion":
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
        if request.export_mode == "notion":
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
        if request.export_mode == "notion":
            try:
                from youtube_notion_notes.services.notion_export import export_markdown_note_to_notion

                notion_page = export_markdown_note_to_notion(note_text, request.url)
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
        if request.export_mode == "notion":
            message = "Notion export skipped: --export notion requires a generated markdown note."
            result["stage"] = "notion_export"
            result["error"] = message
            log(message, error=True)
            return 1, result

    result["ok"] = True
    return 0, result
