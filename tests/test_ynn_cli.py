from __future__ import annotations

import sys
import unittest
from unittest.mock import patch

from youtube_notion_notes import ynn_cli


class YnnCliEntrypointTests(unittest.TestCase):
    def assert_entrypoint_appends_args(
        self,
        entrypoint_name: str,
        expected_argv: list[str],
    ) -> None:
        seen_argv: list[str] = []

        def fake_ingest_main() -> int:
            seen_argv[:] = sys.argv
            return 7

        with (
            patch.object(sys, "argv", ["ynn-command", "https://youtu.be/VIDEO_ID"]),
            patch.object(ynn_cli.ingest, "main", side_effect=fake_ingest_main) as ingest_main_mock,
        ):
            exit_code = getattr(ynn_cli, entrypoint_name)()
            self.assertEqual(sys.argv, ["ynn-command", "https://youtu.be/VIDEO_ID"])

        self.assertEqual(exit_code, 7)
        self.assertEqual(seen_argv, expected_argv)
        ingest_main_mock.assert_called_once_with()

    def test_ynn_delegates_to_ingest_without_extra_args(self) -> None:
        self.assert_entrypoint_appends_args(
            "main",
            ["ynn-command", "https://youtu.be/VIDEO_ID"],
        )

    def test_ynn_note_appends_local_export(self) -> None:
        self.assert_entrypoint_appends_args(
            "main_note",
            ["ynn-command", "https://youtu.be/VIDEO_ID", "--export", "local"],
        )

    def test_ynn_notion_appends_notion_export(self) -> None:
        self.assert_entrypoint_appends_args(
            "main_notion",
            ["ynn-command", "https://youtu.be/VIDEO_ID", "--export", "notion"],
        )

    def test_ynn_prompt_appends_no_note(self) -> None:
        self.assert_entrypoint_appends_args(
            "main_prompt",
            ["ynn-command", "https://youtu.be/VIDEO_ID", "--no-note"],
        )


if __name__ == "__main__":
    unittest.main()
