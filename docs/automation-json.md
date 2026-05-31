# Automation JSON

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

## JSON input

The `--input-json` or `--input-json-file` payload must be a JSON object with only these supported fields: a required `url` field, an optional `transcript_file` field, and an optional `export` field. `transcript_file` must be a string path to a UTF-8 transcript file and uses the same transcript-stage validation as `--transcript-file`. `export` accepts the same values as `--export`: `local` or `notion`. `local` is the explicit form of the default local pipeline behavior and does not perform a separate export step; `notion` is the external export mode. Unknown fields are rejected so automation typos do not get silently ignored.

Do not combine a positional URL with `--input-json` or `--input-json-file`. Do not combine `--input-json` with `--input-json-file`. Do not provide `export` in both JSON input and `--export`. When using JSON input, put `transcript_file` in the payload; the `--transcript-file` flag remains for positional URL mode.

## JSON output

In JSON output mode, stdout contains only JSON. On success, the payload includes `ok`, `url`, `export_mode`, local output paths when created, and Notion page details when export runs. Existing JSON fields remain valid.

When transcript selection metadata is known, success output also includes additive `transcript_selection` metadata with `origin`, `source_language`, `selected_language`, `requires_translation`, and `selection_reason`. For normal YouTube fetching, this describes the selected YouTube transcript track. For `--transcript-file` or JSON `transcript_file` input, it reports `origin: "transcript_file"` because local transcript-file input bypasses YouTube discovery and selection.

`notion_page_url` is included only when the Notion API response includes its canonical `url` field.

## Failure shape

On failure, including invalid JSON input, the payload includes `ok: false`, `stage`, and `error`.

## n8n contract

For the first n8n smoke workflow contract, see [./docs/n8n-smoke-workflow.md](./n8n-smoke-workflow.md). It documents the manual n8n node chain for calling `python ingest.py --input-json-file - --output json`, passing JSON through stdin, and branching on `ok: true` / `ok: false`.
