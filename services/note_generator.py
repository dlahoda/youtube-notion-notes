from __future__ import annotations

import os
from pathlib import Path


class NoteGenerationError(Exception):
    """Raised when optional note generation cannot complete."""


def build_manual_prompt(
    template_path: Path,
    video_url: str,
    video_id: str,
    transcript: str,
) -> str:
    template = template_path.read_text(encoding="utf-8")
    return template.format(
        video_url=video_url,
        video_id=video_id,
        transcript=transcript,
    )


def generate_note_if_available(prompt: str) -> str | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise NoteGenerationError(
            "OPENAI_API_KEY is set, but the openai package is not installed."
        ) from exc

    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    client = OpenAI(api_key=api_key)

    try:
        response = client.responses.create(
            model=model,
            input=prompt,
        )
    except Exception as exc:
        raise NoteGenerationError(f"OpenAI generation failed: {exc}") from exc

    note_text = getattr(response, "output_text", None)
    if not note_text:
        raise NoteGenerationError("OpenAI response did not include text output.")

    return note_text
