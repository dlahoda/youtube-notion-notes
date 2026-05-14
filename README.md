# YouTube Notion Notes

Small Python CLI for Milestone 1: turn one YouTube URL into a local transcript and a ready-to-paste GPT prompt. If OpenAI API config is present, it can also generate a markdown note.

Notion export, n8n workflows, and web UI are intentionally not implemented yet.

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

`.env` is optional for Milestone 1.

- `OPENAI_API_KEY`: optional API key for markdown note generation
- `OPENAI_MODEL`: optional model name, defaults to `gpt-4.1-mini`
- `YOUTUBE_TRANSCRIPT_LANGUAGES`: optional comma-separated language preference list, defaults to `en`
- `NOTION_API_KEY`: future Notion export API key, not used by the current CLI
- `NOTION_DATABASE_ID`: future Notion export database id, not used by the current CLI

`OPENAI_API_KEY` belongs only to optional OpenAI markdown note generation. It is not required for future Notion export.

## Future Notion export contract

Notion export is planned but intentionally not implemented yet. The existing local/manual behavior remains the default.

Required future Notion database properties:

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

Proposed future CLI shape:

```bash
python ingest.py "https://youtu.be/VIDEO_ID" --export notion
python ingest.py "https://youtu.be/VIDEO_ID" --export local
```

The `--export` flag is documented as a future shape only and is not available in the current CLI.

## Limitations

- Only videos with available YouTube transcripts/captions are supported.
- Video titles are not fetched yet; output filenames use the video id unless `--output-name` is provided.
- OpenAI mode is optional and intentionally simple.
- No Notion export, n8n integration, queueing, or web UI exists in this milestone.
