# YouTube Notion Notes

Small Python CLI for Milestone 1: turn one YouTube URL into a local transcript and a ready-to-paste GPT prompt. If OpenAI API config is present, it can also generate a markdown note.

Notion export, n8n workflows, and web UI are intentionally not implemented yet.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
cp .env.example .env
```

The CLI works without editing `.env`. To enable automatic markdown note generation, set `OPENAI_API_KEY` in `.env`.

## Usage

```bash
python3 ingest.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

By default, files are written to:

- `output/transcripts/`
- `output/prompts/`
- `output/notes/` only when OpenAI note generation runs

Useful options:

```bash
python3 ingest.py "https://youtu.be/VIDEO_ID" --languages en,uk
python3 ingest.py "https://youtu.be/VIDEO_ID" --no-note
python3 ingest.py "https://youtu.be/VIDEO_ID" --output-name my-video
```

## Manual Testing

Run the CLI with any YouTube video that has captions:

```bash
python3 ingest.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

Expected result without an OpenAI key:

- a raw transcript text file in `output/transcripts/`
- a ready-to-paste GPT prompt in `output/prompts/`
- no markdown note in `output/notes/`

## Environment

`.env` is optional for Milestone 1.

- `OPENAI_API_KEY`: optional API key for markdown note generation
- `OPENAI_MODEL`: optional model name, defaults to `gpt-4.1-mini`
- `YOUTUBE_TRANSCRIPT_LANGUAGES`: optional comma-separated language preference list, defaults to `en`

## Limitations

- Only videos with available YouTube transcripts/captions are supported.
- Video titles are not fetched yet; output filenames use the video id unless `--output-name` is provided.
- OpenAI mode is optional and intentionally simple.
- No Notion export, n8n integration, queueing, or web UI exists in this milestone.
