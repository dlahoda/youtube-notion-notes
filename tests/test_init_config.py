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

    def test_main_uses_user_config_path_without_real_home(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_path = temp_path / "config" / ".env"
            output_dir = temp_path / "output"
            stdout = io.StringIO()
            stderr = io.StringIO()

            with (
                patch.object(init_config, "user_config_path", return_value=config_path),
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
