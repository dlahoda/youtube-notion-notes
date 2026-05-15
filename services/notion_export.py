from __future__ import annotations

from services.markdown_to_notion import markdown_to_blocks
from services.note_metadata import extract_note_metadata
from services.notion import create_notion_page


def export_markdown_note_to_notion(markdown: str, url: str, status: str = "Draft") -> str:
    metadata = extract_note_metadata(markdown)
    blocks = markdown_to_blocks(markdown)

    return create_notion_page(
        title=metadata.title,
        url=url,
        tags=metadata.tags,
        status=status,
        source="YouTube",
        children=blocks,
    )
