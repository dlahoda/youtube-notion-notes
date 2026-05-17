# n8n Smoke Workflow

This document describes the first small n8n smoke workflow for the YouTube Notion Notes pipeline.

The goal is to prove that n8n can call the existing local Python CLI, pass one JSON payload through stdin, receive JSON-only stdout, and branch on the result. This is a contract and manual build guide only; it is not an exported n8n workflow.

## Goal

Build a minimal n8n workflow that:

- receives or defines one YouTube URL;
- sends a small JSON object to the local CLI through stdin;
- runs the canonical command:

```bash
python ingest.py --input-json-file - --output json
```

- parses the CLI stdout as JSON;
- follows the success path when `ok` is `true`;
- follows the failure path when `ok` is `false`.

The smoke workflow should prove the handoff between n8n and `./ingest.py`. It should not duplicate transcript fetching, note generation, markdown conversion, or Notion export logic.

## Minimal n8n node chain

Build the first workflow manually with a small node chain:

1. Manual Trigger
2. Set or Edit Fields node that creates the input payload
3. Execute Command node that runs `python ingest.py --input-json-file - --output json`
4. JSON parsing step for stdout
5. IF node that checks `ok`
6. Success branch for `ok: true`
7. Failure branch for `ok: false`

The exact n8n node names may vary by version, but the workflow should stay this small. Do not create a real exported workflow JSON in this slice.

## Command Contract

Canonical command:

```bash
python ingest.py --input-json-file - --output json
```

Contract:

- `--input-json-file -` means `./ingest.py` reads the request JSON from stdin.
- `--output json` means stdout must contain only one JSON result object.
- n8n should pass the JSON payload to stdin, not as shell-escaped inline JSON.
- n8n should parse stdout as JSON before branching.

### n8n stdin verification note

The Python CLI contract is already settled, but the exact n8n wiring still needs to be verified in the UI.

During the first real n8n smoke test, confirm whether the Execute Command-style node can pass the JSON payload directly to stdin.

If direct stdin input is not supported or is awkward in the installed n8n version, keep the Python CLI contract unchanged and adjust only the n8n-side wrapper. For example, the workflow may use a small shell pipe or temporary payload file, as long as `./ingest.py` is still called through the supported JSON input contract and stdout remains JSON-only.

Run the command from the repository root so relative output paths are created under this project.

## JSON Payload Sent To Stdin

Minimal local/manual payload:

```json
{
  "url": "https://youtu.be/VIDEO_ID"
}
```

Optional Notion export payload:

```json
{
  "url": "https://youtu.be/VIDEO_ID",
  "export": "notion"
}
```

Supported fields:

- `url`: required YouTube URL string.
- `export`: optional export target. Supported values are `local` and `notion`.

Unknown fields should be treated as input errors by `./ingest.py`. Keep the n8n payload small so typos fail visibly.

## Expected JSON-Only Stdout

On success, stdout contains a JSON object with `ok: true` and result metadata such as the source URL, export mode, and created local output paths. When Notion export runs, the result may also include Notion page details.

Success shape:

```json
{
  "ok": true,
  "url": "https://youtu.be/VIDEO_ID",
  "export_mode": "local"
}
```

On failure, stdout contains a JSON object with `ok: false`, `stage`, and `error`.

Failure shape:

```json
{
  "ok": false,
  "stage": "input",
  "error": "..."
}
```

In JSON output mode, n8n should rely only on stdout JSON. Human-readable logs, prompts, and diagnostics must not be mixed into stdout.

## Branching In n8n

After parsing stdout as JSON:

- if `ok` is `true`, route to the success branch;
- if `ok` is `false`, route to the failure branch;
- the success branch may record the created local file paths or Notion page URL when present;
- the failure branch should preserve `stage` and `error` for review.

Do not infer success from process exit code alone. The workflow contract is the parsed JSON result.

## What Belongs In n8n

n8n should own orchestration only:

- receive or schedule the trigger;
- construct the small JSON payload;
- call the local CLI;
- parse stdout JSON;
- branch on `ok`;
- send notifications or record a workflow-level audit event later, if needed.

## What Must Stay Inside Python

Python remains the source of truth for pipeline behavior:

- YouTube URL validation and transcript fetching;
- transcript and prompt file creation;
- OpenAI note generation;
- markdown note metadata parsing;
- markdown-to-Notion conversion;
- Notion export;
- error staging and JSON result formatting.

Do not put Notion logic inside n8n. Do not duplicate pipeline logic in n8n.

## Manual Verification

From the repository root, verify the CLI contract before building the n8n workflow:

```bash
printf '%s\n' '{"url":"https://youtu.be/VIDEO_ID"}' | python ingest.py --input-json-file - --output json
```

For Notion export, after the normal OpenAI and Notion environment variables are configured:

```bash
printf '%s\n' '{"url":"https://youtu.be/VIDEO_ID","export":"notion"}' | python ingest.py --input-json-file - --output json
```

Manual review checklist:

- stdout is valid JSON and contains no human-readable text outside the JSON object;
- successful runs include `ok: true`;
- failed runs include `ok: false`, `stage`, and `error`;
- local/manual behavior still works without n8n;
- Notion export remains opt-in with `"export": "notion"`;
- no secrets are placed in the n8n workflow definition or committed files.

## Known Limitations

- This document is a manual workflow contract, not an exported n8n workflow JSON.
- The workflow assumes n8n can run a local command in the project environment.
- The workflow assumes dependencies are already installed for `./ingest.py`.
- Videos still require available YouTube transcripts or captions.
- OpenAI note generation remains optional and requires OpenAI configuration.
- Notion export remains opt-in and requires Notion configuration.
- There is no HTTP server, queue, or retry system in this slice.
