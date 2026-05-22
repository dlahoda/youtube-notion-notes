# YouTube Notion Notes

Python CLI that turns one YouTube URL into a local transcript and a ready-to-paste ChatGPT prompt. If OpenAI API config is present, it can also generate a markdown note. Notion export is opt-in after a markdown note is generated locally.

Production n8n automation and web UI are intentionally not implemented.

## Platform support

WSL/Linux is the primary supported path. On Windows, WSL is recommended because it uses the same Linux-style setup, launcher, environment, and shell workflow.

macOS is expected to work, but should be smoke-tested separately before claiming strong support.

Native Windows PowerShell support is best-effort and partial. Direct Python CLI usage and editable package console entrypoints may work when Python is installed on Windows. Repo-local shell launchers, bash wrappers, make-based developer shortcuts, and Unix-style environment examples are not the primary supported path on native Windows.

## Recommended installed CLI setup

Requires Python 3.10+.
Using a virtual environment is recommended, especially on Linux/WSL systems with externally managed Python environments.

From the repository root, use the installed CLI flow:

```bash
python -m pip install -e .
ynn init --output-dir ~/ynn-output
ynn-prompt "https://youtu.be/VIDEO_ID"
ynn-note "https://youtu.be/VIDEO_ID"
ynn-notion "https://youtu.be/VIDEO_ID"
```

The first command installs the editable package and console scripts. This is the recommended editable/developer install path while working from the repository checkout. Because an editable install depends on that checkout path, do not delete or move the repository after `python -m pip install -e .` if you want its installed console scripts to keep working.

Use a regular local install when you want console scripts copied into the environment without depending on this checkout after installation:

```bash
python -m pip install .
```

The `ynn init --output-dir ~/ynn-output` command is the first-time setup helper.

`ynn init --output-dir PATH` creates or updates:

```text
~/.config/youtube-notion-notes/.env
```

During setup, `ynn init` can optionally collect transcript language preferences, `OPENAI_API_KEY`, `NOTION_API_KEY`, and `NOTION_DATABASE_ID`. Existing user config values are preserved by default. Empty prompt input skips that value.

After setup, daily use is through `ynn-prompt`, `ynn-note`, and `ynn-notion`.

`ynn` is also available as the default command:

```bash
ynn "https://youtu.be/VIDEO_ID"
```

Installed commands use the configured output root from `ynn init`, unless overridden for a run with `--output-dir PATH`.

## Command requirements

| Command | What it does | OpenAI required? | Notion required? |
| --- | --- | --- | --- |
| `ynn-prompt` | Builds the transcript and ChatGPT-ready prompt, then stops. It does not call OpenAI and does not create a Notion page. | No | No |
| `ynn` | Runs the default local pipeline and can create a generated markdown note when OpenAI config is available. | Only for automatic markdown note generation | No |
| `ynn-note` | Runs local note mode and can create a generated markdown note when OpenAI config is available. | Only for automatic markdown note generation | No |
| `ynn-notion` | Generates a markdown note locally, then exports it to Notion. | Yes | Yes: `NOTION_API_KEY` and `NOTION_DATABASE_ID` |

## Fallback/developer virtualenv setup

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

## Direct repo-local CLI

The direct `python ingest.py` CLI remains the lower-level contract and fallback path. Use it for local development, tests, n8n integration, JSON mode, troubleshooting, or when launchers have not been installed.

Activate the existing virtual environment before using the direct CLI. You do not need to reinstall dependencies every time; run `python -m pip install -r requirements.txt` again only when `requirements.txt` changes.

WSL/macOS/Linux:

```bash
source .venv/bin/activate
python ingest.py "https://youtu.be/VIDEO_ID" --no-note
```

Windows PowerShell, if Python is installed on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
python ingest.py "https://youtu.be/VIDEO_ID" --no-note
```

When no output config is set, files are written under `./output` relative to the current working directory:

- `output/transcripts/`
- `output/prompts/`
- `output/notes/` only when OpenAI note generation runs

Useful options:

```bash
python ingest.py "https://youtu.be/VIDEO_ID" --languages en,uk
python ingest.py "https://youtu.be/VIDEO_ID" --output-name my-video
python ingest.py "https://youtu.be/VIDEO_ID" --output-dir ./tmp-output
python ingest.py "https://youtu.be/VIDEO_ID" --env-file ./local.env
python ingest.py "https://youtu.be/VIDEO_ID" --export local
python ingest.py "https://youtu.be/VIDEO_ID" --output json
```

Transcript selection:

Normal YouTube fetching discovers available transcript tracks and chooses the best available track by origin and preferred language. Manual/author transcript quality wins over generated-track convenience, so a translated manual track may beat a generated track that already matches a preferred language. Selection priority is:

1. manual/author transcript in a preferred language;
2. manual/author transcript translated to a preferred language;
3. generated transcript in a preferred language;
4. generated transcript translated to a preferred language;
5. unknown-origin YouTube transcript track in a preferred language;
6. unknown-origin YouTube transcript track with API-provided translation to a preferred language.

Human output may include a concise line such as:

```text
Transcript selected: manual Spanish -> English
```

Manual transcript fallback:

```bash
python ingest.py "https://youtu.be/VIDEO_ID" --transcript-file ./manual-transcript.txt --no-note
```

`--transcript-file` reads UTF-8 transcript text from a local file instead of fetching captions from YouTube. The YouTube URL is still required because it remains the source metadata, video id source, and default output filename source. This mode bypasses YouTube discovery and selection and reports `transcript_file` metadata.

Expected result without OpenAI mode:

- a raw transcript text file in `output/transcripts/`
- a ready-to-paste GPT prompt in `output/prompts/`
- no markdown note in `output/notes/`

## Daily launcher setup

The editable installed CLI setup above is the recommended `v1.0.0` path. Repo-local launcher wrappers remain available for WSL/macOS/Linux shell compatibility:

```bash
bash ./scripts/install-launchers.sh
```

The wrappers install into `~/.local/bin`, call `./scripts/ynn-run` in this repo by absolute path, and change to the repository root before invoking `./ingest.py`. That keeps `.env` loading and output paths aligned with normal repo-local CLI usage. Because the wrappers point back to this repo by absolute path, they are not portable after the repository is deleted or moved.

## Installed CLI details

Editable package entrypoints run the packaged CLI implementation. The built-in prompt template is package-owned data, so installed commands do not require a repo-local `./prompts/comprehensive_note.md` file in the current working directory.

Output and config priority summary:

- output root priority is `--output-dir PATH`, then `YNN_OUTPUT_DIR`, then `./output` relative to the current working directory
- selected output roots write files under `OUTPUT_ROOT/transcripts/`, `OUTPUT_ROOT/prompts/`, and `OUTPUT_ROOT/notes/`
- config priority is explicit `--env-file PATH`, real process environment variables, cwd `./.env`, user config `~/.config/youtube-notion-notes/.env`, then built-in defaults
- user config fills missing values only; an explicit `--env-file PATH` must exist

Optional editable-install smoke verification:

```bash
YNN_RUN_EDITABLE_INSTALL_SMOKE=1 python -m unittest tests.test_editable_install_smoke
```

This smoke creates a temporary virtual environment and skips itself if local Python venv support is unavailable.

Optional regular-install smoke verification:

```bash
YNN_RUN_REGULAR_INSTALL_SMOKE=1 python -m unittest tests.test_regular_install_smoke
```

Examples:

```bash
ynn-prompt "https://youtu.be/VIDEO_ID" --output-dir ./tmp-output
YNN_OUTPUT_DIR=./tmp-output ynn-prompt "https://youtu.be/VIDEO_ID"
python ingest.py "https://youtu.be/VIDEO_ID" --no-note --output-dir ./tmp-output
ynn-notion "https://youtu.be/VIDEO_ID" --env-file ./notion.env
```

## Optional OpenAI mode

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

## Environment

Config is optional for local/manual prompt usage. The recommended installed CLI setup writes user config to `~/.config/youtube-notion-notes/.env`; a cwd `./.env`, process environment variables, and explicit `--env-file PATH` are also supported.

For portable installed usage, keep config in `ynn init` user config, process environment variables, or an explicit `--env-file PATH`. A repo-local `./.env` disappears with the repository checkout.

- `OPENAI_API_KEY`: optional API key for markdown note generation
- `OPENAI_MODEL`: optional model name, defaults to `gpt-4.1-mini`
- `YOUTUBE_TRANSCRIPT_LANGUAGES`: optional comma-separated language preference list, defaults to `en`
- `YNN_OUTPUT_DIR`: optional output root used when `--output-dir` is not provided
- `NOTION_API_KEY`: required only for Notion export and the manual Notion smoke test
- `NOTION_DATABASE_ID`: required only for Notion export and the manual Notion smoke test

`OPENAI_API_KEY` belongs only to optional OpenAI markdown note generation. It is not required for the Notion smoke test.

Config source priority is `--env-file PATH`, then real process environment variables, cwd `./.env`, user config `~/.config/youtube-notion-notes/.env`, and built-in defaults. An explicit `--env-file` path must exist.

## Optional Notion export

Default local behavior is unchanged. Notion export runs only when explicitly requested through `ynn-notion` or `--export notion`, and only after a markdown note has been generated and saved locally.

```bash
ynn-notion "https://youtu.be/VIDEO_ID"
python ingest.py "https://youtu.be/VIDEO_ID" --export notion
python ingest.py "https://youtu.be/VIDEO_ID" --export local
```

Set `OPENAI_API_KEY`, `NOTION_API_KEY`, and `NOTION_DATABASE_ID` through `ynn init`, `.env`, or another supported config source before using generated-note Notion export.

Required Notion database properties:

- `Name`: title
- `URL`: url
- `Tags`: multi_select
- `Status`: select
- `Source`: select
- `Created`: created_time

Recommended values are `Draft`, `Reviewed`, and `Archived` for `Status`, and `YouTube` for `Source`.

Markdown note metadata convention for export: the first H1 heading, formatted as `# Note title`, is the Notion page `Name`; tags should be written as `Tags: tag one, tag two` with comma-separated tags.

## JSON result output

For local automation and n8n integration, the CLI can accept structured JSON input and emit a machine-readable JSON result. Human-readable positional-URL behavior remains the default.

```bash
python ingest.py "https://youtu.be/VIDEO_ID" --output json
python ingest.py "https://youtu.be/VIDEO_ID" --export notion --output json
python ingest.py --input-json '{"url":"https://youtu.be/VIDEO_ID"}' --output json
python ingest.py --input-json '{"url":"https://youtu.be/VIDEO_ID","export":"notion"}' --output json
python ingest.py --input-json '{"url":"https://youtu.be/VIDEO_ID","transcript_file":"./manual-transcript.txt"}' --output json
python ingest.py --input-json-file payload.json --output json
printf '%s\n' '{"url":"https://youtu.be/VIDEO_ID"}' | python ingest.py --input-json-file - --output json
```

`./payload.json`

```json
{
  "url": "https://youtu.be/VIDEO_ID",
  "transcript_file": "./manual-transcript.txt",
  "export": "notion"
}
```

The `--input-json` or `--input-json-file` payload must be a JSON object with only these supported fields: a required `url` field, an optional `transcript_file` field, and an optional `export` field. `transcript_file` must be a string path to a UTF-8 transcript file and uses the same transcript-stage validation as `--transcript-file`. `export` accepts the same values as `--export`: `local` or `notion`. Unknown fields are rejected so automation typos do not get silently ignored.

Do not combine a positional URL with `--input-json` or `--input-json-file`. Do not combine `--input-json` with `--input-json-file`. Do not provide `export` in both JSON input and `--export`. When using JSON input, put `transcript_file` in the payload; the `--transcript-file` flag remains for positional URL mode.

In JSON output mode, stdout contains only JSON. On success, the payload includes `ok`, `url`, `export_mode`, local output paths when created, and Notion page details when export runs. Existing JSON fields remain valid.

When transcript selection metadata is known, success output also includes additive `transcript_selection` metadata with `origin`, `source_language`, `selected_language`, `requires_translation`, and `selection_reason`. For normal YouTube fetching, this describes the selected YouTube transcript track. For `--transcript-file` or JSON `transcript_file` input, it reports `origin: "transcript_file"` because local transcript-file input bypasses YouTube discovery and selection.

`notion_page_url` is included only when the Notion API response includes its canonical `url` field. On failure, including invalid JSON input, the payload includes `ok: false`, `stage`, and `error`.

For the first n8n smoke workflow contract, see `./docs/n8n-smoke-workflow.md`. It documents the manual n8n node chain for calling `python ingest.py --input-json-file - --output json`, passing JSON through stdin, and branching on `ok: true` / `ok: false`.

## Local developer shortcuts

The `make` targets are convenience commands for local development. They are not the main pipeline contract; the CLI examples above remain the canonical usage.

To use a repeated local sample URL, copy the template and set `YNN_SAMPLE_URL`:

```bash
cp .local.mk.example .local.mk
```

`./.local.mk`:

```make
YNN_SAMPLE_URL := https://youtu.be/VIDEO_ID
```

`./.local.mk` is local-only config and should not be committed. Keeping the sample URL there avoids manually editing placeholder `VIDEO_ID` values in repeated commands.

Run the test shortcut:

```bash
make test
```

Run the local ingest sample:

```bash
make ingest-sample
```

Run the Notion export sample:

```bash
make notion-sample
```

`make notion-sample` uses `--export notion`, so it requires the normal Notion/OpenAI prerequisites for a full generated-note export: a generated markdown note, `OPENAI_API_KEY`, `NOTION_API_KEY`, and `NOTION_DATABASE_ID`.

## Manual Notion smoke test

For a compact developer/debug smoke test, create one minimal properties-only page in the configured Notion database.

Set `NOTION_API_KEY` and `NOTION_DATABASE_ID` in `.env`, then run:

```bash
python -m youtube_notion_notes.services.notion
```

The page uses `Name: Notion smoke test`, `Source: YouTube`, `Status: Draft`, `Tags: smoke-test`, and the smoke-test URL. No markdown body blocks are appended yet.

## License

This repository is source-visible for portfolio and review purposes only.

The project is not open source. No permission is granted to use, copy, modify, redistribute, sublicense, or reuse the code without explicit written permission from the copyright holder.

See `./LICENSE.md` and `./THIRD_PARTY_NOTICES.md` for details.

## Limitations

- YouTube transcript fetching depends on available captions unless `--transcript-file` is used.
- Video titles are not fetched yet; output filenames use the video id unless `--output-name` is provided.
- OpenAI mode is optional and intentionally simple.
- Notion export requires a generated markdown note; prompt-only/manual mode does not export.
- No queueing or web UI exists.
