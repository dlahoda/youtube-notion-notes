from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from youtube_notion_notes.config import ConfigFileError, load_runtime_config


class RuntimeConfigTests(unittest.TestCase):
    def test_load_runtime_config_applies_priority_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            user_env = temp_path / "user.env"
            cwd_env = temp_path / ".env"
            explicit_env = temp_path / "explicit.env"
            user_env.write_text(
                "\n".join(
                    [
                        "ONLY_USER=from-user",
                        "CWD_VALUE=from-user",
                        "PROCESS_VALUE=from-user",
                        "EXPLICIT_VALUE=from-user",
                    ]
                ),
                encoding="utf-8",
            )
            cwd_env.write_text(
                "\n".join(
                    [
                        "CWD_VALUE=from-cwd",
                        "PROCESS_VALUE=from-cwd",
                        "EXPLICIT_VALUE=from-cwd",
                    ]
                ),
                encoding="utf-8",
            )
            explicit_env.write_text(
                "\n".join(
                    [
                        "EXPLICIT_VALUE=from-explicit",
                        "PROCESS_VALUE=from-explicit",
                    ]
                ),
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {
                    "PROCESS_VALUE": "from-process",
                    "EXPLICIT_VALUE": "from-process",
                },
                clear=True,
            ):
                load_runtime_config(
                    explicit_env_file=explicit_env,
                    cwd_env_file=cwd_env,
                    user_env_file=user_env,
                )

                self.assertEqual(os.environ["ONLY_USER"], "from-user")
                self.assertEqual(os.environ["CWD_VALUE"], "from-cwd")
                self.assertEqual(os.environ["PROCESS_VALUE"], "from-explicit")
                self.assertEqual(os.environ["EXPLICIT_VALUE"], "from-explicit")

    def test_cwd_env_does_not_override_process_environment(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            user_env = temp_path / "missing-user.env"
            cwd_env = temp_path / ".env"
            cwd_env.write_text("YNN_OUTPUT_DIR=from-cwd\n", encoding="utf-8")

            with patch.dict(os.environ, {"YNN_OUTPUT_DIR": "from-process"}, clear=True):
                load_runtime_config(cwd_env_file=cwd_env, user_env_file=user_env)

                self.assertEqual(os.environ["YNN_OUTPUT_DIR"], "from-process")

    def test_user_config_fills_missing_values_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            user_env = temp_path / "user.env"
            cwd_env = temp_path / "missing-cwd.env"
            user_env.write_text(
                "YNN_OUTPUT_DIR=from-user\nOPENAI_API_KEY=from-user\n",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"OPENAI_API_KEY": "from-process"}, clear=True):
                load_runtime_config(cwd_env_file=cwd_env, user_env_file=user_env)

                self.assertEqual(os.environ["YNN_OUTPUT_DIR"], "from-user")
                self.assertEqual(os.environ["OPENAI_API_KEY"], "from-process")

    def test_missing_user_config_does_not_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            with patch.dict(os.environ, {}, clear=True):
                load_runtime_config(
                    cwd_env_file=temp_path / "missing-cwd.env",
                    user_env_file=temp_path / "missing-user.env",
                )

                self.assertNotIn("YNN_OUTPUT_DIR", os.environ)

    def test_missing_explicit_env_file_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            with self.assertRaisesRegex(ConfigFileError, "Unable to read --env-file"):
                load_runtime_config(
                    explicit_env_file=temp_path / "missing.env",
                    cwd_env_file=temp_path / "missing-cwd.env",
                    user_env_file=temp_path / "missing-user.env",
                )


if __name__ == "__main__":
    unittest.main()
