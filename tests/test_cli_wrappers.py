from __future__ import annotations

import unittest

import ingest
import ynn_cli
from youtube_notion_notes import ingest as package_ingest
from youtube_notion_notes import ynn_cli as package_ynn_cli


class CliWrapperCompatibilityTests(unittest.TestCase):
    def test_top_level_ingest_wrapper_exposes_package_main(self) -> None:
        self.assertIs(ingest.main, package_ingest.main)


    def test_top_level_ynn_cli_wrapper_exposes_package_entrypoints(self) -> None:
        self.assertIs(ynn_cli.main, package_ynn_cli.main)
        self.assertIs(ynn_cli.main_note, package_ynn_cli.main_note)
        self.assertIs(ynn_cli.main_notion, package_ynn_cli.main_notion)
        self.assertIs(ynn_cli.main_prompt, package_ynn_cli.main_prompt)


if __name__ == "__main__":
    unittest.main()
