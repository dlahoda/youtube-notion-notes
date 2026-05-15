from __future__ import annotations

import unittest

from services.note_metadata import extract_note_metadata, extract_note_tags, extract_note_title


class NoteMetadataTests(unittest.TestCase):
    def test_extracts_normal_h1_title(self) -> None:
        self.assertEqual(extract_note_title("# Title\n\nBody"), "Title")

    def test_extracts_title_with_surrounding_whitespace(self) -> None:
        self.assertEqual(extract_note_title("  #   Title with spaces   \n\nBody"), "Title with spaces")

    def test_missing_h1_title_raises_value_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "first-level '# ' heading"):
            extract_note_title("## Subtitle\n\nInline # text")

    def test_title_inside_fenced_code_block_is_ignored(self) -> None:
        with self.assertRaisesRegex(ValueError, "first-level '# ' heading"):
            extract_note_title("```python\n# Fake title\n```")

    def test_real_title_after_fenced_code_block_is_extracted(self) -> None:
        markdown = "```python\n# Fake title\n```\n\n# Real title"

        self.assertEqual(extract_note_title(markdown), "Real title")

    def test_indented_code_line_is_not_treated_as_title(self) -> None:
        with self.assertRaisesRegex(ValueError, "first-level '# ' heading"):
            extract_note_title("    # Code title")

    def test_parses_normal_tags_line(self) -> None:
        self.assertEqual(extract_note_tags("Tags: a, b, c"), ["a", "b", "c"])

    def test_tags_marker_is_case_insensitive(self) -> None:
        self.assertEqual(extract_note_tags("tags: a, b"), ["a", "b"])

    def test_multi_word_tags_keep_internal_spaces(self) -> None:
        self.assertEqual(
            extract_note_tags("Tags: python, software architecture, note taking"),
            ["python", "software architecture", "note taking"],
        )

    def test_extra_spaces_around_commas_are_trimmed(self) -> None:
        self.assertEqual(extract_note_tags("Tags:  a  ,   b, c   "), ["a", "b", "c"])

    def test_empty_tag_entries_are_ignored(self) -> None:
        self.assertEqual(extract_note_tags("Tags: a, , b,,   , c"), ["a", "b", "c"])

    def test_missing_tags_line_returns_empty_list(self) -> None:
        self.assertEqual(extract_note_tags("# Title\n\nNo tags here"), [])

    def test_tags_inside_fenced_code_block_are_ignored(self) -> None:
        self.assertEqual(extract_note_tags("```\nTags: fake\n```\n\nNo tags here"), [])

    def test_extract_note_metadata_combines_title_and_tags(self) -> None:
        metadata = extract_note_metadata("# Title\n\nTags: one, two")

        self.assertEqual(metadata.title, "Title")
        self.assertEqual(metadata.tags, ["one", "two"])


if __name__ == "__main__":
    unittest.main()
