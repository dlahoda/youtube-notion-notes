from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


@unittest.skipUnless(
    os.getenv("YNN_RUN_EDITABLE_INSTALL_SMOKE") == "1",
    "set YNN_RUN_EDITABLE_INSTALL_SMOKE=1 to run editable install smoke verification",
)
class EditableInstallSmokeTests(unittest.TestCase):
    def test_ynn_prompt_reads_packaged_template_from_non_repo_cwd(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            venv_path = temp_path / ".venv"
            run_cwd = temp_path / "outside-repo"
            output_dir = temp_path / "out"
            transcript_path = temp_path / "manual-transcript.txt"
            run_cwd.mkdir()
            transcript_path.write_text("Editable install smoke transcript.\n", encoding="utf-8")

            venv_result = subprocess.run(
                [sys.executable, "-m", "venv", "--system-site-packages", str(venv_path)],
                cwd=temp_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if venv_result.returncode != 0:
                self.skipTest("temporary Python venv could not be created")

            bin_dir = venv_path / ("Scripts" if os.name == "nt" else "bin")
            python_path = bin_dir / ("python.exe" if os.name == "nt" else "python")
            ynn_prompt_path = bin_dir / ("ynn-prompt.exe" if os.name == "nt" else "ynn-prompt")
            smoke_env = {**os.environ, "PIP_DISABLE_PIP_VERSION_CHECK": "1"}

            subprocess.run(
                [
                    str(python_path),
                    "-m",
                    "pip",
                    "install",
                    "-e",
                    str(repo_root),
                ],
                check=True,
                cwd=temp_path,
                env=smoke_env,
            )
            subprocess.run(
                [
                    str(ynn_prompt_path),
                    "https://youtu.be/abc123def45",
                    "--transcript-file",
                    str(transcript_path),
                    "--output-dir",
                    str(output_dir),
                ],
                check=True,
                cwd=run_cwd,
                env=smoke_env,
            )

            prompt_path = output_dir / "prompts" / "abc123def45_prompt.md"
            prompt_text = prompt_path.read_text(encoding="utf-8")

            self.assertIn("- Video URL: https://youtu.be/abc123def45", prompt_text)
            self.assertIn("Editable install smoke transcript.", prompt_text)
            self.assertFalse((run_cwd / "prompts" / "comprehensive_note.md").exists())


if __name__ == "__main__":
    unittest.main()
