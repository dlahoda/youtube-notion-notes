from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class ShellLauncherTests(unittest.TestCase):
    def test_ynn_run_dispatches_ynn_init_to_config_flow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            home_dir = temp_path / "home"
            config_path = home_dir / ".config" / "youtube-notion-notes" / ".env"
            output_dir = temp_path / "ynn-output"
            config_path.parent.mkdir(parents=True)
            config_path.write_text(
                "\n".join(
                    [
                        "YOUTUBE_TRANSCRIPT_LANGUAGES=en",
                        "OPENAI_API_KEY=keep-openai",
                        "NOTION_API_KEY=keep-notion",
                        "NOTION_DATABASE_ID=keep-database",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                ["./scripts/ynn-run", "ynn", "init", "--output-dir", str(output_dir)],
                cwd=REPO_ROOT,
                env={**os.environ, "HOME": str(home_dir)},
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn(f"Config ready: {config_path}", completed.stdout)
            self.assertNotIn("Transcript error:", completed.stderr)
            self.assertTrue(output_dir.is_dir())
            self.assertIn(f"YNN_OUTPUT_DIR={output_dir}\n", config_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
