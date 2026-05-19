# YouTube Notion Notes

Repo-local Python CLI that turns one YouTube URL into a local transcript and a ready-to-paste GPT prompt. If OpenAI API config is present, it can also generate a markdown note.

Notion export is opt-in after a markdown note is generated locally. Production n8n automation and web UI are intentionally not implemented.

## One-time setup: WSL/macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

## One-time setup: Windows PowerShell, only if Python is installed on Windows

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
Copy-Item .env.example .env
```

## Default daily usage

Default day-to-day usage is through thin launcher commands installed into your shell. They work from any terminal directory, but they still call back into this local repository.

```bash
ynn "https://youtu.be/VIDEO_ID"
ynn-note "https://youtu.be/VIDEO_ID"
ynn-notion "https://youtu.be/VIDEO_ID"
ynn-prompt "https://youtu.be/VIDEO_ID"
```

Launcher behavior:

- `ynn` runs the current default CLI behavior: `python ./ingest.py "URL"`
- `ynn-note` explicitly runs local note mode: `python ./ingest.py "URL" --export local`
- `ynn-notion` runs Notion export mode: `python ./ingest.py "URL" --export notion`
- `ynn-prompt` runs prompt-only/manual-safe mode: `python ./ingest.py "URL" --no-note`

These names can come from either the repo-local launcher setup or the local editable package install below. The repo-local launcher workflow remains supported.

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

When no output override is set, files are written under `./output` relative to the current working directory:

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

Manual transcript fallback:

```bash
python ingest.py "https://youtu.be/VIDEO_ID" --transcript-file ./manual-transcript.txt --no-note
```

`--transcript-file` reads UTF-8 transcript text from a local file instead of fetching captions from YouTube. The YouTube URL is still required because it remains the source metadata, video id source, and default output filename source.

Expected result without OpenAI mode:

- a raw transcript text file in `output/transcripts/`
- a ready-to-paste GPT prompt in `output/prompts/`
- no markdown note in `output/notes/`

## Daily launcher setup

This launcher setup is for WSL/macOS/Linux shell usage.

For daily local usage, install thin launcher commands into `~/.local/bin`:

```bash
bash ./scripts/install-launchers.sh
```

The installed wrappers call `./scripts/ynn-run` in this repo by absolute path. `./scripts/ynn-run` changes to the repository root before invoking `./ingest.py`, so `.env` loading and output paths keep matching normal repo-local CLI usage.

## Installable CLI package

For local package-development usage, install the repository in editable mode:

```bash
python -m pip install -e .
```

This installs the same command names:

```bash
ynn "https://youtu.be/VIDEO_ID"
ynn-note "https://youtu.be/VIDEO_ID"
ynn-notion "https://youtu.be/VIDEO_ID"
ynn-prompt "https://youtu.be/VIDEO_ID"
```

The editable package entrypoints delegate to the existing `./ingest.py` CLI behavior. Installed commands use the current working directory for default `.env`, fallback `./output/`, and `./prompts/comprehensive_note.md`; `--env-file`, `--output-dir`, and `YNN_OUTPUT_DIR` can make runtime paths explicit for a run.

Runtime path policy:

- output root resolution order is `--output-dir PATH`, then `YNN_OUTPUT_DIR`, then `./output` relative to the current working directory
- selected output roots write files under `OUTPUT_ROOT/transcripts/`, `OUTPUT_ROOT/prompts/`, and `OUTPUT_ROOT/notes/`
- default env loading uses optional `./.env` relative to the current working directory when it exists
- `--env-file PATH` loads that env file instead, and the explicit file must exist

For daily installed CLI usage, set `YNN_OUTPUT_DIR` to avoid creating `./output` in whichever directory the command was run from.

Examples:

```bash
ynn-prompt "https://youtu.be/VIDEO_ID" --output-dir ./tmp-output
YNN_OUTPUT_DIR=./tmp-output ynn-prompt "https://youtu.be/VIDEO_ID"
python ingest.py "https://youtu.be/VIDEO_ID" --no-note --output-dir ./tmp-output
ynn-notion "https://youtu.be/VIDEO_ID" --env-file ./notion.env
```

Current Slice 2 limitation: installed commands may still depend on `./prompts/comprehensive_note.md` being available from the current working directory. Package-resource handling for the prompt template is planned for Slice 3.

## Optional OpenAI mode

OpenAI mode is not required for `ynn-prompt`, `--no-note`, transcript capture, or prompt generation. Install it only if you want `ynn`, `ynn-note`, or direct `python ingest.py` usage to generate markdown notes automatically, then set `OPENAI_API_KEY` in `.env`.

WSL/macOS/Linux:

```bash
python -m pip install -r requirements-openai.txt
```

Windows PowerShell, only if Python is installed on Windows:

```powershell
py -m pip install -r requirements-openai.txt
```

## Environment

`.env` is optional for local/manual usage.

- `OPENAI_API_KEY`: optional API key for markdown note generation
- `OPENAI_MODEL`: optional model name, defaults to `gpt-4.1-mini`
- `YOUTUBE_TRANSCRIPT_LANGUAGES`: optional comma-separated language preference list, defaults to `en`
- `YNN_OUTPUT_DIR`: optional output root used when `--output-dir` is not provided
- `NOTION_API_KEY`: required only for Notion export and the manual Notion smoke test
- `NOTION_DATABASE_ID`: required only for Notion export and the manual Notion smoke test

`OPENAI_API_KEY` belongs only to optional OpenAI markdown note generation. It is not required for the Notion smoke test.

By default, the CLI loads `./.env` from the current working directory when it exists and continues when it does not. Use `--env-file PATH` to load a different env file for that run; an explicit `--env-file` path must exist. Values in the env file do not override environment variables that are already set.

## Optional Notion export

Default local behavior is unchanged. Notion export runs only when explicitly requested through `ynn-notion` or `--export notion`, and only after the markdown note has been generated and saved locally.

```bash
python ingest.py "https://youtu.be/VIDEO_ID" --export notion
```

Set `NOTION_API_KEY` and `NOTION_DATABASE_ID` in `.env` before using `--export notion`.

## JSON result output

For future automation, the CLI can accept structured JSON input and emit a machine-readable JSON result. Human-readable positional-URL behavior remains the default.

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

In JSON output mode, stdout contains only JSON. On success, the payload includes `ok`, `url`, `export_mode`, local output paths when created, and Notion page details when export runs. `notion_page_url` is included only when the Notion API response includes its canonical `url` field. On failure, including invalid JSON input, the payload includes `ok: false`, `stage`, and `error`.

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

The smoke test is opt-in and does not change the default local CLI behavior. It creates one minimal page in the configured Notion database using properties only.

Set `NOTION_API_KEY` and `NOTION_DATABASE_ID` in `.env`, then run:

```bash
python -m services.notion
```

The created page uses:

- `Name`: `Notion smoke test`
- `URL`: `https://www.youtube.com/watch?v=notion-smoke-test`
- `Source`: `YouTube`
- `Status`: `Draft`
- `Tags`: `smoke-test`

No markdown body blocks are appended yet.

## Notion export contract

Notion export is available as an opt-in CLI mode. The existing local/manual behavior remains the default.

Required Notion database properties:

- `Name`: title
- `URL`: url
- `Tags`: multi_select
- `Status`: select
- `Source`: select
- `Created`: created_time

Recommended `Status` values:

- `Draft`
- `Reviewed`
- `Archived`

Recommended `Source` value for this pipeline:

- `YouTube`

CLI shape:

```bash
python ingest.py "https://youtu.be/VIDEO_ID" --export notion
python ingest.py "https://youtu.be/VIDEO_ID" --export local
```

Markdown note metadata convention for export: the first H1 heading, formatted as `# Note title`, is the Notion page `Name`; tags should be written as `Tags: tag one, tag two` with comma-separated tags.

## Limitations

- YouTube transcript fetching depends on available captions unless `--transcript-file` is used.
- Video titles are not fetched yet; output filenames use the video id unless `--output-name` is provided.
- OpenAI mode is optional and intentionally simple.
- Notion export requires a generated markdown note; prompt-only/manual mode does not export.
- Installed commands still depend on `./prompts/comprehensive_note.md` being available from the current working directory until package-resource handling is added.
- No queueing or web UI exists in this milestone.
