from __future__ import annotations

import unittest

from youtube_notion_notes.services.markdown_to_notion import markdown_to_blocks


def block_text(block: dict) -> str:
    block_type = block["type"]
    return block[block_type]["rich_text"][0]["text"]["content"]


class MarkdownToNotionTests(unittest.TestCase):
    def test_headings(self) -> None:
        blocks = markdown_to_blocks("# One\n## Two\n### Three")

        self.assertEqual([block["type"] for block in blocks], ["heading_1", "heading_2", "heading_3"])
        self.assertEqual([block_text(block) for block in blocks], ["One", "Two", "Three"])

    def test_consecutive_plain_lines_become_one_paragraph(self) -> None:
        blocks = markdown_to_blocks("First line\nsecond line\n\nNext paragraph")

        self.assertEqual([block["type"] for block in blocks], ["paragraph", "paragraph"])
        self.assertEqual(block_text(blocks[0]), "First line\nsecond line")
        self.assertEqual(block_text(blocks[1]), "Next paragraph")

    def test_bullets_numbered_items_and_quotes(self) -> None:
        blocks = markdown_to_blocks("- Bullet\n1. Numbered\n> Quoted")

        self.assertEqual(
            [block["type"] for block in blocks],
            ["bulleted_list_item", "numbered_list_item", "quote"],
        )
        self.assertEqual([block_text(block) for block in blocks], ["Bullet", "Numbered", "Quoted"])

    def test_fenced_code_block_preserves_internal_line_breaks(self) -> None:
        blocks = markdown_to_blocks("```\nprint('hello')\nprint('bye')\n```")

        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["type"], "code")
        self.assertEqual(block_text(blocks[0]), "print('hello')\nprint('bye')")
        self.assertEqual(blocks[0]["code"]["language"], "plain text")

    def test_unclosed_fenced_code_block_becomes_code_block(self) -> None:
        blocks = markdown_to_blocks("Before\n\n```\nunfinished\ncode")

        self.assertEqual([block["type"] for block in blocks], ["paragraph", "code"])
        self.assertEqual(block_text(blocks[1]), "unfinished\ncode")

    def test_mixed_markdown(self) -> None:
        blocks = markdown_to_blocks(
            "# Title\n\n"
            "Intro line\ncontinued intro\n\n"
            "- First\n"
            "- Second\n"
            "1. Ordered\n"
            "> Note\n\n"
            "```\nalpha\nbeta\n```\n\n"
            "Done"
        )

        self.assertEqual(
            [block["type"] for block in blocks],
            [
                "heading_1",
                "paragraph",
                "bulleted_list_item",
                "bulleted_list_item",
                "numbered_list_item",
                "quote",
                "code",
                "paragraph",
            ],
        )
        self.assertEqual(block_text(blocks[1]), "Intro line\ncontinued intro")
        self.assertEqual(block_text(blocks[6]), "alpha\nbeta")
        self.assertEqual(block_text(blocks[7]), "Done")


if __name__ == "__main__":
    unittest.main()
