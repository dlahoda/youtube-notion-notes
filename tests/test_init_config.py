from __future__ import annotations

import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from youtube_notion_notes import init_config


class InitConfigTests(unittest.TestCase):
    def test_init_creates_user_config_and_output_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_path = temp_path / "home" / ".config" / "youtube-notion-notes" / ".env"
            output_dir = temp_path / "ynn-output"

            returned_path = init_config.init_output_dir(str(output_dir), config_path=config_path)

            self.assertEqual(returned_path, config_path)
            self.assertEqual(config_path.read_text(encoding="utf-8"), f"YNN_OUTPUT_DIR={output_dir}\n")
            self.assertTrue(output_dir.is_dir())

    def test_init_preserves_existing_output_dir_value(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_path = temp_path / "config" / ".env"
            existing_output_dir = temp_path / "existing-output"
            requested_output_dir = temp_path / "requested-output"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                f"OPENAI_API_KEY=keep-me\nYNN_OUTPUT_DIR={existing_output_dir}\n",
                encoding="utf-8",
            )

            init_config.init_output_dir(str(requested_output_dir), config_path=config_path)

            self.assertEqual(
                config_path.read_text(encoding="utf-8"),
                f"OPENAI_API_KEY=keep-me\nYNN_OUTPUT_DIR={existing_output_dir}\n",
            )
            self.assertTrue(existing_output_dir.is_dir())
            self.assertFalse(requested_output_dir.exists())

    def test_init_appends_output_dir_without_rewriting_existing_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_path = temp_path / "config" / ".env"
            output_dir = temp_path / "output"
            config_path.parent.mkdir(parents=True)
            config_path.write_text("OPENAI_API_KEY=keep-me", encoding="utf-8")

            init_config.init_output_dir(str(output_dir), config_path=config_path)

            self.assertEqual(
                config_path.read_text(encoding="utf-8"),
                f"OPENAI_API_KEY=keep-me\nYNN_OUTPUT_DIR={output_dir}\n",
            )
            self.assertTrue(output_dir.is_dir())

    def test_init_expands_home_in_output_dir_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            fake_home = temp_path / "home"
            config_path = temp_path / "config" / ".env"
            expected_output_dir = fake_home / "ynn-output"

            with patch.dict(os.environ, {"HOME": str(fake_home)}):
                init_config.init_output_dir("~/ynn-output", config_path=config_path)

            self.assertEqual(
                config_path.read_text(encoding="utf-8"),
                f"YNN_OUTPUT_DIR={expected_output_dir}\n",
            )
            self.assertTrue(expected_output_dir.is_dir())

    def test_init_appends_optional_values_when_provided(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_path = temp_path / "config" / ".env"
            output_dir = temp_path / "output"

            with (
                patch.object(init_config.getpass, "getpass", side_effect=["openai-key", "notion-key"]),
                patch("builtins.input", return_value="notion-database-id"),
            ):
                init_config.init_user_config(str(output_dir), config_path=config_path)

            self.assertEqual(
                config_path.read_text(encoding="utf-8"),
                "\n".join(
                    [
                        f"YNN_OUTPUT_DIR={output_dir}",
                        "OPENAI_API_KEY=openai-key",
                        "NOTION_API_KEY=notion-key",
                        "NOTION_DATABASE_ID=notion-database-id",
                        "",
                    ]
                ),
            )
            self.assertTrue(output_dir.is_dir())

    def test_init_skips_empty_optional_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_path = temp_path / "config" / ".env"
            output_dir = temp_path / "output"

            with (
                patch.object(init_config.getpass, "getpass", side_effect=["", ""]),
                patch("builtins.input", return_value=""),
            ):
                init_config.init_user_config(str(output_dir), config_path=config_path)

            self.assertEqual(config_path.read_text(encoding="utf-8"), f"YNN_OUTPUT_DIR={output_dir}\n")
            self.assertTrue(output_dir.is_dir())

    def test_init_preserves_existing_optional_values_without_duplication(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_path = temp_path / "config" / ".env"
            output_dir = temp_path / "output"
            config_path.parent.mkdir(parents=True)
            config_text = "\n".join(
                [
                    f"YNN_OUTPUT_DIR={output_dir}",
                    "OPENAI_API_KEY=keep-openai",
                    "NOTION_API_KEY=keep-notion",
                    "NOTION_DATABASE_ID=keep-database",
                    "",
                ]
            )
            config_path.write_text(config_text, encoding="utf-8")

            with (
                patch.object(init_config.getpass, "getpass") as getpass_mock,
                patch("builtins.input") as input_mock,
                contextlib.redirect_stdout(io.StringIO()),
            ):
                init_config.init_user_config(str(temp_path / "requested-output"), config_path=config_path)

            self.assertEqual(config_path.read_text(encoding="utf-8"), config_text)
            getpass_mock.assert_not_called()
            input_mock.assert_not_called()
            self.assertTrue(output_dir.is_dir())

    def test_main_uses_user_config_path_without_real_home(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_path = temp_path / "config" / ".env"
            output_dir = temp_path / "output"
            stdout = io.StringIO()
            stderr = io.StringIO()

            with (
                patch.object(init_config, "user_config_path", return_value=config_path),
                patch.object(init_config.getpass, "getpass", side_effect=["", ""]),
                patch("builtins.input", return_value=""),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                exit_code = init_config.main(["--output-dir", str(output_dir)])

            self.assertEqual(exit_code, 0)
            self.assertIn(f"Config ready: {config_path}", stdout.getvalue())
            self.assertEqual(stderr.getvalue(), "")
            self.assertTrue(config_path.exists())
            self.assertTrue(output_dir.is_dir())


if __name__ == "__main__":
    unittest.main()
