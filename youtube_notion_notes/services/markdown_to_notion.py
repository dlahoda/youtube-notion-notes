from __future__ import annotations

import re


NUMBERED_LIST_PATTERN = re.compile(r"^\d+\. (.+)$")


def markdown_to_blocks(markdown: str) -> list[dict]:
    blocks: list[dict] = []
    paragraph_lines: list[str] = []
    code_lines: list[str] = []
    in_code_block = False

    def flush_paragraph() -> None:
        if not paragraph_lines:
            return
        blocks.append(_text_block("paragraph", "\n".join(paragraph_lines)))
        paragraph_lines.clear()

    for line in markdown.splitlines():
        stripped = line.strip()

        if in_code_block:
            if stripped.startswith("```"):
                blocks.append(_code_block("\n".join(code_lines)))
                code_lines.clear()
                in_code_block = False
            else:
                code_lines.append(line)
            continue

        if stripped.startswith("```"):
            flush_paragraph()
            in_code_block = True
            code_lines.clear()
            continue

        if not stripped:
            flush_paragraph()
            continue

        line_block = _line_block(line)
        if line_block is not None:
            flush_paragraph()
            blocks.append(line_block)
            continue

        paragraph_lines.append(stripped)

    if in_code_block:
        blocks.append(_code_block("\n".join(code_lines)))
    else:
        flush_paragraph()

    return blocks


def _line_block(line: str) -> dict | None:
    for marker, block_type in (
        ("### ", "heading_3"),
        ("## ", "heading_2"),
        ("# ", "heading_1"),
        ("- ", "bulleted_list_item"),
        ("> ", "quote"),
    ):
        if line.startswith(marker):
            return _text_block(block_type, line.removeprefix(marker).strip())

    numbered_match = NUMBERED_LIST_PATTERN.match(line)
    if numbered_match:
        return _text_block("numbered_list_item", numbered_match.group(1).strip())

    return None


def _text_block(block_type: str, text: str) -> dict:
    return {
        "object": "block",
        "type": block_type,
        block_type: {
            "rich_text": _rich_text(text),
        },
    }


def _code_block(text: str) -> dict:
    return {
        "object": "block",
        "type": "code",
        "code": {
            "rich_text": _rich_text(text),
            "language": "plain text",
        },
    }


def _rich_text(text: str) -> list[dict]:
    return [
        {
            "type": "text",
            "text": {
                "content": text,
            },
        }
    ]
