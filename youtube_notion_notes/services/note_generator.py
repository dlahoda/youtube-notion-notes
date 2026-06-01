from __future__ import annotations

from importlib import resources
import os
from pathlib import Path
import string


DEFAULT_PROMPT_TEMPLATE = "resources/comprehensive_note.md"
REQUIRED_PROMPT_PLACEHOLDERS = {"video_url", "video_id", "transcript"}


class NoteGenerationError(Exception):
    """Raised when optional note generation cannot complete."""


class PromptTemplateError(Exception):
    """Raised when the manual prompt template cannot be loaded or formatted."""


def read_default_prompt_template() -> str:
    try:
        return (
            resources.files("youtube_notion_notes.services")
            .joinpath(DEFAULT_PROMPT_TEMPLATE)
            .read_text(encoding="utf-8")
        )
    except Exception as exc:
        raise PromptTemplateError(
            f"Unable to read built-in prompt template '{DEFAULT_PROMPT_TEMPLATE}': {exc}"
        ) from exc


def validate_prompt_template(template: str, *, source: str) -> None:
    try:
        parsed_fields = [
            field_name
            for _literal_text, field_name, _format_spec, _conversion in string.Formatter().parse(template)
            if field_name is not None
        ]
    except ValueError as exc:
        raise PromptTemplateError(f"Invalid prompt template formatting in {source}: {exc}") from exc

    placeholders = {field_name.split(".", 1)[0].split("[", 1)[0] for field_name in parsed_fields}
    missing_placeholders = sorted(REQUIRED_PROMPT_PLACEHOLDERS - placeholders)
    if missing_placeholders:
        missing = ", ".join(f"{{{placeholder}}}" for placeholder in missing_placeholders)
        raise PromptTemplateError(f"Prompt template {source} is missing required placeholder(s): {missing}.")


def build_manual_prompt(
    video_url: str,
    video_id: str,
    transcript: str,
    template_path: Path | str | None = None,
) -> str:
    if template_path is None:
        template = read_default_prompt_template()
        template_source = f"built-in template '{DEFAULT_PROMPT_TEMPLATE}'"
    else:
        prompt_template_path = Path(template_path).expanduser()
        template_source = f"template '{prompt_template_path}'"
        try:
            template = prompt_template_path.read_text(encoding="utf-8")
        except (FileNotFoundError, OSError, UnicodeDecodeError) as exc:
            raise PromptTemplateError(f"Unable to read prompt template '{prompt_template_path}': {exc}") from exc

    validate_prompt_template(template, source=template_source)
    try:
        return template.format(
            video_url=video_url,
            video_id=video_id,
            transcript=transcript,
        )
    except (KeyError, IndexError, AttributeError, ValueError) as exc:
        raise PromptTemplateError(f"Unable to format prompt template {template_source}: {exc}") from exc


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
