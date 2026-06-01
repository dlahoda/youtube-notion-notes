from __future__ import annotations

import re
from dataclasses import dataclass


H1_PATTERN = re.compile(r"^ {0,3}# (.+)$")


@dataclass
class NoteMetadata:
    title: str
    tags: list[str]


def extract_note_metadata(markdown: str) -> NoteMetadata:
    return NoteMetadata(
        title=extract_note_title(markdown),
        tags=extract_note_tags(markdown),
    )


def extract_note_title(markdown: str) -> str:
    for line in _metadata_lines(markdown):
        if not line.strip():
            continue

        match = H1_PATTERN.match(line)
        if not match:
            continue

        title = match.group(1).strip()
        if title:
            return title

    raise ValueError("Markdown note must include a first-level '# ' heading for the title.")


def extract_note_tags(markdown: str) -> list[str]:
    for line in _metadata_lines(markdown):
        stripped = line.strip()
        if _is_tags_metadata_line(stripped):
            raw_tags = stripped.split(":", 1)[1]
            return [tag.strip() for tag in raw_tags.split(",") if tag.strip()]

    return []


def remove_tags_metadata_lines(markdown: str) -> str:
    lines: list[str] = []
    in_code_block = False

    for line in markdown.splitlines(keepends=True):
        stripped = line.strip()

        if stripped.startswith("```"):
            in_code_block = not in_code_block
            lines.append(line)
            continue

        if not in_code_block and _is_tags_metadata_line(stripped):
            continue

        lines.append(line)

    return "".join(lines)


def _metadata_lines(markdown: str) -> list[str]:
    lines: list[str] = []
    in_code_block = False

    for line in markdown.splitlines():
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue

        if not in_code_block:
            lines.append(line)

    return lines


def _is_tags_metadata_line(stripped_line: str) -> bool:
    return stripped_line.lower().startswith("tags:")
