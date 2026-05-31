# Usage

## Installed commands

The installed CLI setup path makes these command names available:

```bash
ynn "https://youtu.be/VIDEO_ID"
ynn-note "https://youtu.be/VIDEO_ID"
ynn-notion "https://youtu.be/VIDEO_ID"
ynn-prompt "https://youtu.be/VIDEO_ID"
```

| Command | What it does | OpenAI required? | Notion required? |
| --- | --- | --- | --- |
| `ynn-prompt` | Builds the transcript and ChatGPT-ready prompt, then stops. It does not call OpenAI and does not create a Notion page. | No | No |
| `ynn` | Runs the default local pipeline and can create a generated markdown note when OpenAI config is available. | Only for automatic markdown note generation | No |
| `ynn-note` | Runs local note mode and can create a generated markdown note when OpenAI config is available. | Only for automatic markdown note generation | No |
| `ynn-notion` | Generates a markdown note locally, then exports it to Notion. | Yes | Yes: `NOTION_API_KEY` and `NOTION_DATABASE_ID` |

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

Expected result without OpenAI mode:

- a raw transcript text file in `output/transcripts/`
- a ready-to-paste GPT prompt in `output/prompts/`
- no markdown note in `output/notes/`

## Useful options

```bash
python ingest.py "https://youtu.be/VIDEO_ID" --languages en,uk
python ingest.py "https://youtu.be/VIDEO_ID" --output-name my-video
python ingest.py "https://youtu.be/VIDEO_ID" --output-dir ./tmp-output
python ingest.py "https://youtu.be/VIDEO_ID" --env-file ./local.env
python ingest.py "https://youtu.be/VIDEO_ID" --export local
python ingest.py "https://youtu.be/VIDEO_ID" --output json
```

Default local behavior is unchanged. `--export local` is the explicit form of that default behavior; it does not perform a separate export step. It writes the normal local outputs: transcript, prompt, and a markdown note only when note generation is available.

Notion export runs only when explicitly requested through `ynn-notion` or `--export notion`, and only after a markdown note has been generated and saved locally.

```bash
ynn-notion "https://youtu.be/VIDEO_ID"
python ingest.py "https://youtu.be/VIDEO_ID" --export notion
python ingest.py "https://youtu.be/VIDEO_ID" --export local
```

## Transcript selection

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

## Manual transcript fallback

```bash
python ingest.py "https://youtu.be/VIDEO_ID" --transcript-file ./manual-transcript.txt --no-note
```

`--transcript-file` reads UTF-8 transcript text from a local file instead of fetching captions from YouTube. The YouTube URL is still required because it remains the source metadata, video id source, and default output filename source. This mode bypasses YouTube discovery and selection and reports `transcript_file` metadata.
