from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_TEXT = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")


class PackagingConfigurationTests(unittest.TestCase):
    def test_console_scripts_point_to_package_entrypoints(self) -> None:
        self.assertIn('ynn = "youtube_notion_notes.ynn_cli:main"', PYPROJECT_TEXT)
        self.assertIn('ynn-note = "youtube_notion_notes.ynn_cli:main_note"', PYPROJECT_TEXT)
        self.assertIn('ynn-notion = "youtube_notion_notes.ynn_cli:main_notion"', PYPROJECT_TEXT)
        self.assertIn('ynn-prompt = "youtube_notion_notes.ynn_cli:main_prompt"', PYPROJECT_TEXT)
        self.assertNotIn('ynn = "ynn_cli:main"', PYPROJECT_TEXT)

    def test_top_level_py_modules_are_not_packaged(self) -> None:
        self.assertNotIn("py-modules", PYPROJECT_TEXT)
        self.assertIn(
            'packages = ["youtube_notion_notes", "youtube_notion_notes.services"]',
            PYPROJECT_TEXT,
        )
        self.assertIn(
            '"youtube_notion_notes.services" = ["resources/*.md"]',
            PYPROJECT_TEXT,
        )
