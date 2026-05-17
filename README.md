# YouTube Notion Notes

Small Python CLI that turns one YouTube URL into a local transcript and a ready-to-paste GPT prompt. If OpenAI API config is present, it can also generate a markdown note.

Notion export is opt-in after a markdown note is generated locally. n8n workflows and web UI are intentionally not implemented.

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

## Run after setup

For normal usage, activate the existing virtual environment and run the CLI. You do not need to reinstall dependencies every time; run `python -m pip install -r requirements.txt` again only when `requirements.txt` changes.

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

By default, files are written to:

- `output/transcripts/`
- `output/prompts/`
- `output/notes/` only when OpenAI note generation runs

Useful options:

```bash
python ingest.py "https://youtu.be/VIDEO_ID" --languages en,uk
python ingest.py "https://youtu.be/VIDEO_ID" --output-name my-video
python ingest.py "https://youtu.be/VIDEO_ID" --export local
python ingest.py "https://youtu.be/VIDEO_ID" --output json
```

Expected result without OpenAI mode:

- a raw transcript text file in `output/transcripts/`
- a ready-to-paste GPT prompt in `output/prompts/`
- no markdown note in `output/notes/`

## Optional OpenAI mode

OpenAI mode is not required for manual-safe mode. Install it only if you want the CLI to generate markdown notes automatically, then set `OPENAI_API_KEY` in `.env`.

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
- `NOTION_API_KEY`: required only for Notion export and the manual Notion smoke test
- `NOTION_DATABASE_ID`: required only for Notion export and the manual Notion smoke test

`OPENAI_API_KEY` belongs only to optional OpenAI markdown note generation. It is not required for the Notion smoke test.

## Optional Notion export

Default local behavior is unchanged. Notion export runs only when explicitly requested, and only after the markdown note has been generated and saved locally.

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
python ingest.py --input-json-file payload.json --output json
printf '%s\n' '{"url":"https://youtu.be/VIDEO_ID"}' | python ingest.py --input-json-file - --output json
```

`./payload.json`

```json
{
  "url": "https://youtu.be/VIDEO_ID",
  "export": "notion"
}
```

The `--input-json` or `--input-json-file` payload must be a JSON object with only two supported fields: a required `url` field and an optional `export` field. `export` accepts the same values as `--export`: `local` or `notion`. Unknown fields are rejected so automation typos do not get silently ignored.

Do not combine a positional URL with `--input-json` or `--input-json-file`. Do not combine `--input-json` with `--input-json-file`. Do not provide `export` in both JSON input and `--export`.

In JSON output mode, stdout contains only JSON. On success, the payload includes `ok`, `url`, `export_mode`, local output paths when created, and Notion page details when export runs. `notion_page_url` is included only when the Notion API response includes its canonical `url` field. On failure, including invalid JSON input, the payload includes `ok: false`, `stage`, and `error`.

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

- Only videos with available YouTube transcripts/captions are supported.
- Video titles are not fetched yet; output filenames use the video id unless `--output-name` is provided.
- OpenAI mode is optional and intentionally simple.
- Notion export requires a generated markdown note; prompt-only/manual mode does not export.
- No n8n integration, queueing, or web UI exists in this milestone.
