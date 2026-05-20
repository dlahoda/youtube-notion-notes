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
        initial_argv: list[str] | None = None,
    ) -> None:
        seen_argv: list[str] = []

        def fake_ingest_main() -> int:
            seen_argv[:] = sys.argv
            return 7

        with (
            patch.object(sys, "argv", initial_argv or ["ynn-command", "https://youtu.be/VIDEO_ID"]),
            patch.object(ynn_cli.ingest, "main", side_effect=fake_ingest_main) as ingest_main_mock,
        ):
            expected_restored_argv = sys.argv[:]
            exit_code = getattr(ynn_cli, entrypoint_name)()
            self.assertEqual(sys.argv, expected_restored_argv)

        self.assertEqual(exit_code, 7)
        self.assertEqual(seen_argv, expected_argv)
        ingest_main_mock.assert_called_once_with()

    def test_ynn_delegates_to_ingest_without_extra_args(self) -> None:
        self.assert_entrypoint_appends_args(
            "main",
            ["ynn-command", "https://youtu.be/VIDEO_ID"],
        )

    def test_ynn_init_dispatches_to_init_command(self) -> None:
        with (
            patch.object(sys, "argv", ["ynn", "init", "--output-dir", "~/ynn-output"]),
            patch.object(ynn_cli.init_config, "main", return_value=0) as init_main_mock,
            patch.object(ynn_cli.ingest, "main", return_value=7) as ingest_main_mock,
        ):
            exit_code = ynn_cli.main()

        self.assertEqual(exit_code, 0)
        init_main_mock.assert_called_once_with(["--output-dir", "~/ynn-output"])
        ingest_main_mock.assert_not_called()

    def test_ynn_note_does_not_dispatch_init(self) -> None:
        self.assert_entrypoint_appends_args(
            "main_note",
            ["ynn-command", "init", "--export", "local"],
            initial_argv=["ynn-command", "init"],
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
