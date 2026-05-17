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
3. Execute Command node that calls `./ingest.py` directly through the JSON stdin/stdout contract
4. Code node that parses stdout with `JSON.parse`
5. IF node that checks `ok`
6. Success branch for `ok: true`
7. Failure branch for `ok: false`

The exact n8n node names may vary by version, but the workflow should stay this small. Do not create a real exported workflow JSON in this slice.

## Real Smoke Test Result

Validated with n8n 2.20.9:

- The Execute Command node exists, but it was excluded/hidden by default in this local n8n setup.
- Starting n8n with `NODES_EXCLUDE='[]' npx n8n` made Execute Command available.
- Execute Command successfully ran a local command from the workflow.
- The command returned stdout containing JSON from `./ingest.py`.
- A Code node successfully parsed stdout with `JSON.parse($json.stdout)`.
- An IF node successfully branched on `ok === true` for success.
- A failure payload produced `ok: false` and routed to the false branch after parsing.
- Using `make n8n-json-bad-sample` caused n8n to fail early because `make` propagated the non-zero process exit before the workflow could branch on parsed JSON.

Decisions from the smoke test:

- n8n should call `./ingest.py` directly through the JSON stdin/stdout contract.
- n8n should not depend on `./Makefile` targets as the automation contract.
- `./Makefile` remains only a local developer convenience.
- If `./ingest.py` emits valid JSON with `ok: false` but exits non-zero, the n8n-side shell wrapper may normalize the shell exit code so the workflow can branch on parsed JSON `ok`.
- Broad `|| true` can mask infrastructure failures, so invalid or missing stdout JSON should still be treated as a workflow error.

## Command Contract

Canonical command:

```bash
python ingest.py --input-json-file - --output json
```

Contract:

- `--input-json-file -` means `./ingest.py` reads the request JSON from stdin.
- `--output json` means stdout must contain only one JSON result object.
- n8n should use the JSON stdin/stdout contract rather than `./Makefile` targets.
- n8n should parse stdout as JSON before branching.

### Recommended Execute Command

Run the command from the repository root so relative output paths are created under this project. In n8n, use the real repository path:

```bash
cd /path/to/youtube-notion-notes && (printf '%s\n' '{"url":"https://youtu.be/VIDEO_ID"}' | python ./ingest.py --input-json-file - --output json || true)
```

The wrapper exists because n8n Execute Command can fail the node on a non-zero process exit before later Code and IF nodes can parse stdout and branch on `ok`.

Keep the wrapper narrow:

- use it only around the direct `./ingest.py` JSON contract;
- parse stdout as JSON in the next node;
- treat invalid or missing stdout JSON as a workflow error;
- do not use `./Makefile` targets as the automation interface.

Direct stdin UI wiring remains unnecessary for now because the shell pipe wrapper validates the same Python contract.

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

Use a Code node to parse the Execute Command stdout:

```javascript
const raw = $json.stdout;
return [{ json: JSON.parse(raw) }];
```

Then use an IF node condition:

```text
{{ $json.ok === true }}
```

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

Do not store secrets in the workflow definition. Keep API keys and database IDs in the local environment used by `./ingest.py`.

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
- n8n parses stdout with a Code node before the IF node;
- the IF node branches with `{{ $json.ok === true }}`;
- workflow errors still surface when stdout is missing or not valid JSON;
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
