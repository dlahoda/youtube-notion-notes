# Notion Setup

## Optional Notion export

Default local behavior is unchanged. Notion export runs only when explicitly requested through `ynn-notion` or `--export notion`, and only after a markdown note has been generated and saved locally.

```bash
ynn-notion "https://youtu.be/VIDEO_ID"
python ingest.py "https://youtu.be/VIDEO_ID" --export notion
python ingest.py "https://youtu.be/VIDEO_ID" --export local
```

Set `OPENAI_API_KEY`, `NOTION_API_KEY`, and `NOTION_DATABASE_ID` through `ynn init`, `.env`, or another supported config source before using generated-note Notion export.

## Database properties

Required Notion database properties:

- `Name`: title
- `URL`: url
- `Tags`: multi_select
- `Status`: select
- `Source`: select
- `Created`: created_time

Recommended values are `Draft`, `Reviewed`, and `Archived` for `Status`, and `YouTube` for `Source`.

## Markdown metadata convention

Markdown note metadata convention for export: the first H1 heading, formatted as `# Note title`, is the Notion page `Name`; tags should be written as `Tags: tag one, tag two` with comma-separated tags.

## Manual Notion smoke test

For a compact developer/debug smoke test, create one minimal properties-only page in the configured Notion database.

Set `NOTION_API_KEY` and `NOTION_DATABASE_ID` in `.env`, then run:

```bash
python -m youtube_notion_notes.services.notion
```

The page uses `Name: Notion smoke test`, `Source: YouTube`, `Status: Draft`, `Tags: smoke-test`, and the smoke-test URL. No markdown body blocks are appended yet.
