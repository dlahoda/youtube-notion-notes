# Installation

Requires Python 3.10+.
Using a virtual environment is recommended, especially on Linux/WSL systems with externally managed Python environments.

## Platform support

WSL/Linux is the primary supported path. On Windows, WSL is recommended because it uses the same Linux-style setup, launcher, environment, and shell workflow.

macOS is expected to work, but should be smoke-tested separately before claiming strong support.

Native Windows PowerShell support is best-effort and partial. Direct Python CLI usage and editable package console entrypoints may work when Python is installed on Windows. Repo-local shell launchers, bash wrappers, make-based developer shortcuts, and Unix-style environment examples are not the primary supported path on native Windows.

## Editable install

From the repository root, use the installed CLI flow:

```bash
python -m pip install -e .
ynn init --output-dir ~/ynn-output
ynn-prompt "https://youtu.be/VIDEO_ID"
```

The first command installs the editable package and console scripts. This is the recommended editable/developer install path while working from the repository checkout. Because an editable install depends on that checkout path, do not delete or move the repository after `python -m pip install -e .` if you want its installed console scripts to keep working.

The minimal first successful path stops at `ynn-prompt`.

`ynn-note` is optional and needs OpenAI config for automatic markdown note generation. `ynn-notion` is optional and needs OpenAI plus Notion config.

## Regular local install

Use a regular local install when you want console scripts copied into the environment without depending on this checkout after installation:

```bash
python -m pip install .
```

## Fallback developer virtualenv

Use this path for local development, tests, direct `python ingest.py` usage, n8n troubleshooting, or when you do not want to install editable console entrypoints.

WSL/macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Windows PowerShell, only if Python is installed on Windows:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
Copy-Item .env.example .env
```

## Optional OpenAI dependency

OpenAI mode is not required for `ynn-prompt`, `--no-note`, transcript capture, or prompt generation. Install it only if you want `ynn`, `ynn-note`, or direct `python ingest.py` usage to generate markdown notes automatically, then set `OPENAI_API_KEY` through `ynn init`, `.env`, or another supported config source.

For the installed-package path from the repository root, install the optional OpenAI dependency with:

```bash
python -m pip install ".[openai]"
```

For the direct repo-local developer path, install the OpenAI requirements file:

WSL/macOS/Linux:

```bash
python -m pip install -r requirements-openai.txt
```

Windows PowerShell, only if Python is installed on Windows:

```powershell
py -m pip install -r requirements-openai.txt
```

## Daily launcher setup

The editable installed CLI setup above is the recommended `v1.0.0` path. Repo-local launcher wrappers remain available for WSL/macOS/Linux shell compatibility:

```bash
bash ./scripts/install-launchers.sh
```

The wrappers install into `~/.local/bin`, call `./scripts/ynn-run` in this repo by absolute path, and change to the repository root before invoking `./ingest.py` for normal pipeline runs. `ynn init` is routed to the same config setup flow as the installed console script. That keeps `.env` loading and output paths aligned with normal repo-local CLI usage. Because the wrappers point back to this repo by absolute path, they are not portable after the repository is deleted or moved.

## Installed CLI details

Editable package entrypoints run the packaged CLI implementation. The built-in prompt template is package-owned data, so installed commands do not require a repo-local `./prompts/comprehensive_note.md` file in the current working directory.

After setup, daily use can continue through `ynn-prompt`, `ynn-note`, and `ynn-notion` as needed.

`ynn` is also available as the default command:

```bash
ynn "https://youtu.be/VIDEO_ID"
```

Installed commands use the configured output root from `ynn init`, unless overridden for a run with `--output-dir PATH`.
