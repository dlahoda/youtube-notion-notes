from __future__ import annotations

import unittest
from unittest.mock import patch

from youtube_notion_notes.services.notion_export import export_markdown_note_to_notion
from youtube_notion_notes.services.notion import NotionPage


class NotionExportTests(unittest.TestCase):
    def test_exports_markdown_note_with_extracted_title_tags_and_blocks(self) -> None:
        markdown = "# My Video Note\n\nTags: python, note taking\n\nBody"
        body_markdown = "# My Video Note\n\n\nBody"
        blocks = [{"type": "paragraph"}]

        with (
            patch("youtube_notion_notes.services.notion_export.markdown_to_blocks", return_value=blocks) as markdown_to_blocks,
            patch(
                "youtube_notion_notes.services.notion_export.create_notion_page",
                return_value=NotionPage(id="page-123", url="https://www.notion.so/page-123"),
            ) as create_notion_page,
        ):
            page = export_markdown_note_to_notion(markdown, "https://youtu.be/example")

        self.assertEqual(page.id, "page-123")
        self.assertEqual(page.url, "https://www.notion.so/page-123")
        markdown_to_blocks.assert_called_once_with(body_markdown)
        create_notion_page.assert_called_once_with(
            title="My Video Note",
            url="https://youtu.be/example",
            tags=["python", "note taking"],
            status="Draft",
            source="YouTube",
            children=blocks,
        )

    def test_custom_status_is_passed_through(self) -> None:
        with (
            patch("youtube_notion_notes.services.notion_export.markdown_to_blocks", return_value=[]) as markdown_to_blocks,
            patch("youtube_notion_notes.services.notion_export.create_notion_page", return_value=NotionPage(id="page-456")) as create_notion_page,
        ):
            page = export_markdown_note_to_notion(
                "# Reviewed Note",
                "https://youtu.be/reviewed",
                status="Reviewed",
            )

        self.assertEqual(page.id, "page-456")
        self.assertIsNone(page.url)
        markdown_to_blocks.assert_called_once_with("# Reviewed Note")
        create_notion_page.assert_called_once_with(
            title="Reviewed Note",
            url="https://youtu.be/reviewed",
            tags=[],
            status="Reviewed",
            source="YouTube",
            children=[],
        )

    def test_missing_h1_raises_metadata_error_and_does_not_create_page(self) -> None:
        with (
            patch("youtube_notion_notes.services.notion_export.markdown_to_blocks") as markdown_to_blocks,
            patch("youtube_notion_notes.services.notion_export.create_notion_page") as create_notion_page,
        ):
            with self.assertRaisesRegex(ValueError, "first-level '# ' heading"):
                export_markdown_note_to_notion("Tags: python\n\nNo H1", "https://youtu.be/example")

        markdown_to_blocks.assert_not_called()
        create_notion_page.assert_not_called()


if __name__ == "__main__":
    unittest.main()
