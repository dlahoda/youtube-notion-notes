# Milestone History

This file is historical context only. It is not the current source of truth for project contracts, architecture, roadmap, or active slice boundaries.

For current guidance, read `./design-doc.md` first, then `./AGENTS.md`.

---

# Detailed Completed Milestone History

The sections below were moved out of `./design-doc.md` during the docs-only decomposition slice that kept `./design-doc.md` focused on current contracts and project map.

---

# Milestone 1: Local Note Without Notion

## Status

Complete.

## Goal

Prove that transcript to note works.

## Input

YouTube URL.

## Output

Two local files:

```text
output/transcripts/video-title.txt
output/notes/video-title.md
```

## Steps

1. Read the URL from the CLI.
2. Extract `video_id`.
3. Fetch the transcript.
4. Save the raw transcript.
5. Run the transcript through the note generator.
6. Save the markdown note.

## Why Notion Was Excluded

Notion adds a separate layer of complexity.

This milestone separately proved that the pipeline can produce a useful local note before adding Notion.

---

# Milestone 2: Notion Export

## Status

Complete.

Milestone 2 is implemented, smoke-tested, and tagged `v0.2.0`.

End-to-end smoke test passed:

- `python ingest.py "YOUTUBE_URL" --export notion` successfully generated a markdown note and created a Notion page.
- The Notion page received title, URL, tags, status, source, and converted markdown body blocks.
- Default local/manual behavior remains unchanged when `--export notion` is omitted.

Implemented pieces:

- reusable Notion page creator in `./services/notion.py`;
- markdown-to-Notion-blocks converter in `./services/markdown_to_notion.py`;
- markdown note metadata extraction in `./services/note_metadata.py`;
- internal Notion export orchestration in `./services/notion_export.py`;
- opt-in CLI export via `--export notion` in `./ingest.py`.

## Required `.env` Variables

```env
NOTION_API_KEY=...
NOTION_DATABASE_ID=...
```

`OPENAI_API_KEY` remains optional and belongs only to OpenAI note generation. It is not required for Notion export.

## Notion Database Properties

Required database contract:

- `Name`: title;
- `URL`: YouTube link;
- `Tags`: multi-select;
- `Status`: select;
- `Source`: select;
- `Created`: created time.

Recommended `Status` values:

- `Draft`;
- `Reviewed`;
- `Archived`.

Recommended `Source` value for this pipeline:

- `YouTube`.

## Notion Property Decisions

- `Status` uses a regular Notion `select` property, not Notion's native Status property.
- `Source` uses a regular Notion `select` property, not `rich_text`.
- `Tags` uses a `multi_select` property.
- `./services/notion.py` allows empty tags so it can stay a small reusable Notion adapter.
- Higher-level pipeline or export code may require tags for YouTube notes later.
- `Created` is managed by Notion as `created_time` and should not be set manually by the client.

## CLI Shape

Notion export is opt-in:

```bash
python ingest.py "URL" --export notion
```

Local-only mode can be explicit:

```bash
python ingest.py "URL" --export local
```

## Page Body

The note is inserted into the Notion page body as Notion blocks.

## Markdown Note Metadata Convention

- The first Markdown H1 heading is treated as the note title.
- The note title must use `# Note title`.
- Tags are read from a comma-separated `Tags:` line.
- Spaces inside multi-word tags are preserved.
- The source URL is not parsed from markdown; it comes from the original CLI input.

---

# Milestone 3: n8n Preparation

## Goal

Make the Python logic callable from n8n.

## Status

Complete.

Milestone 3's local CLI automation contract is complete and tagged `v0.3.0`.

Supported current CLI input modes:

- positional URL;
- `--input-json`;
- `--input-json-file payload.json`;
- `--input-json-file -` for stdin.

Supported current export modes:

- `local`;
- `notion`.

JSON output mode can be combined with supported input and export modes.

JSON output mode keeps stdout JSON-only, including for input errors.

Current JSON input supports only:

- `url`;
- `transcript_file`;
- `export`.

Unknown JSON fields are rejected so automation typos do not get silently ignored.

n8n orchestration was validated in Milestone 4. Any HTTP wrapper remains optional future work.

## CLI Result Contract

The first small slice kept the existing human-readable CLI as the default and added opt-in machine-readable output for automation:

```bash
python ingest.py "URL" --output json
python ingest.py "URL" --export notion --output json
```

In JSON output mode, stdout must contain only JSON. Success output includes `ok`, `url`, `export_mode`, created local paths, and Notion page details when export runs. `notion_page_url` comes from the Notion API page response `url` field and is included only when that field is present. Failure output includes `ok: false`, `stage`, and `error`.

## CLI JSON Input Contract

The second small slice allowed automation callers to pass a structured JSON payload instead of a positional URL:

```bash
python ingest.py --input-json '{"url":"https://www.youtube.com/watch?v=..."}' --output json
python ingest.py --input-json '{"url":"https://www.youtube.com/watch?v=...","export":"notion"}' --output json
python ingest.py --input-json '{"url":"https://www.youtube.com/watch?v=...","transcript_file":"./manual-transcript.txt"}' --output json
```

The `--input-json` payload is a JSON object with:

- `url`: required YouTube URL string;
- `transcript_file`: optional UTF-8 local transcript file path string;
- `export`: optional export target, with the same accepted values as `--export`: `local` or `notion`.

Unknown fields are rejected so automation typos do not get silently ignored.

Ambiguous input is rejected:

- positional URL plus `--input-json`;
- `export` inside `--input-json` plus `--export`.

The third small slice allowed the same JSON payload contract to come from a file or stdin, so automation callers do not need fragile inline JSON shell quoting:

```bash
python ingest.py --input-json-file payload.json --output json
python ingest.py --input-json-file - --output json
```

`--input-json-file -` reads the payload from stdin. The payload still uses the same fields:

- `url`: required YouTube URL string;
- `transcript_file`: optional UTF-8 local transcript file path string;
- `export`: optional export target, with the same accepted values as `--export`: `local` or `notion`.

Unknown fields are rejected for file and stdin payloads too.

Additional ambiguous input is rejected:

- positional URL plus `--input-json-file`;
- `--input-json` plus `--input-json-file`;
- `export` inside any JSON payload plus `--export`.

JSON output mode keeps stdout JSON-only for input errors:

```json
{
  "ok": false,
  "stage": "input",
  "error": "..."
}
```

An HTTP wrapper is intentionally not part of the current local-first design. Keep it in the future backlog unless local command execution stops being enough.

## Why This Matters

n8n should be the orchestrator, not the place where complex pipeline logic lives.

That reduces maintenance cost and keeps the core behavior testable in Python.

---

# Milestone 4: n8n Integration Contract and Smoke Workflow

## Goal

Define how n8n calls the existing local Python CLI without adding an HTTP server or queue.

## Preferred Integration Shape

Validated decision: n8n should call `./ingest.py` directly through the JSON stdin/stdout contract. Exact direct stdin UI wiring remains unnecessary for now because a shell pipe wrapper works and preserves the same Python contract.

- n8n uses an Execute Command-style node.
- n8n passes a JSON payload to `python ./ingest.py --input-json-file - --output json`.
- Python reads JSON from stdin.
- Python writes machine-readable JSON to stdout only.
- n8n branches on `ok: true` / `ok: false`.
- n8n does not depend on `./Makefile` targets.
- `./Makefile` remains a local developer convenience only.

## Non-Goals

- no HTTP server;
- no queue;
- no new dependencies;
- no Notion logic inside n8n;
- no duplicated pipeline logic in n8n.

## Slice 1: n8n Smoke Workflow Contract

Status: documentation-only planning slice.

Scope:

- add `./docs/n8n-smoke-workflow.md` as the manual build guide for the first n8n smoke workflow;
- document the minimal node chain: manual trigger, execute command, stdout JSON parsing, and `ok` branch;
- record the canonical command: `python ingest.py --input-json-file - --output json`;
- document the stdin JSON payload shape with required `url` and optional `export`;
- confirm that stdout is JSON-only and n8n branches on `ok: true` / `ok: false`;
- keep pipeline logic, Notion export, error staging, and JSON result formatting inside Python;
- verify during the first real n8n UI smoke test whether the Execute Command-style node can pass JSON directly to stdin.

Out of scope:

- no runtime Python behavior changes;
- no dependency changes;
- no HTTP server;
- no queue;
- no Notion logic inside n8n;
- no duplicated transcript, note generation, markdown conversion, or Notion export logic in n8n;
- exported n8n workflow JSON belongs to a later slice.

## Slice 2: Real Local n8n Smoke Test

Status: complete.

Validated with n8n 2.20.9:

- local n8n can run the Execute Command node when started with `NODES_EXCLUDE='[]' npx n8n`;
- Execute Command can run a local command from the workflow;
- n8n can call `./ingest.py` through stdin JSON and stdout JSON;
- a Code node can parse stdout with `JSON.parse($json.stdout)`;
- an IF node can branch on `ok === true`;
- success payloads route to the success branch;
- failure payloads with `ok: false` route to the false branch after parsing.

Durable decisions:

- n8n should not depend on `./Makefile`;
- `./Makefile` remains local developer convenience only;
- direct `./ingest.py` JSON stdin/stdout remains the integration boundary;
- exact direct stdin UI wiring remains unnecessary for now because the shell pipe wrapper works;
- if `./ingest.py` emits valid JSON with `ok: false` but exits non-zero, the n8n-side shell wrapper may normalize the shell exit code so the workflow can branch on parsed JSON `ok`;
- invalid or missing stdout JSON should still be treated as a workflow error, because broad `|| true` can mask infrastructure failures.

## Slice 3: Small n8n Shell Wrapper

Status: complete.

Scope:

- add `./scripts/n8n-ingest.sh` as the small n8n-facing shell wrapper;
- keep `./ingest.py` as the integration boundary through `--input-json-file - --output json`;
- let n8n use `cd /path/to/youtube-notion-notes && sh ./scripts/n8n-ingest.sh`;
- keep `./Makefile` as local developer convenience only;
- validate that `./ingest.py` stdout is JSON before returning it to n8n;
- allow n8n to continue when `./ingest.py` emits valid JSON with `ok: false`;
- fail the wrapper when stdout is missing or invalid JSON.

Out of scope remains unchanged:

- no runtime Python behavior changes;
- no dependency changes;
- no HTTP server;
- no queue;
- no Notion logic inside n8n;
- no duplicated pipeline logic in n8n;
- exported n8n workflow JSON belongs to a later slice.

## Slice 4: Exported Minimal n8n Smoke Workflow Template

Status: complete.

Scope:

- add sanitized `./docs/n8n-smoke-workflow.json` template;
- keep the workflow minimal: Manual Trigger, Execute Command, Code, IF;
- use `sh ./scripts/n8n-ingest.sh` through a placeholder repository path;
- keep `./ingest.py` JSON stdin/stdout as the integration boundary;
- avoid runtime Python changes;
- avoid secrets, Notion API keys, database IDs, and personal local paths;
- keep the template as manual smoke workflow documentation, not production automation.

## Milestone 4 Status

Milestone 4 is complete enough for the local MVP and tagged `v0.4.0`.

The project now has:

- a validated JSON stdin/stdout integration contract between n8n and `./ingest.py`;
- a real local n8n smoke test;
- a small n8n-facing shell wrapper;
- a sanitized exported smoke workflow template;
- a clear separation between orchestration in n8n and pipeline logic in Python.

The current design intentionally stays local-first and avoids additional infrastructure such as HTTP services, queues, or external workflow state.

Future n8n expansion is optional backlog work, not part of the Milestone 4 MVP boundary.

---

# Milestone 5: Pipeline Core Refactor

## Status

Complete.

Milestone 5 is complete enough for the local MVP. Pipeline orchestration now lives in `./services/pipeline.py`, the pipeline accepts `PipelineRequest` instead of `argparse.Namespace`, and focused service-level tests cover the pipeline boundary.

Slice 1 is complete: pipeline orchestration moved from `./ingest.py` to `./services/pipeline.py` without changing the CLI or JSON stdin/stdout contract.

Slice 2 is complete: `./services/pipeline.py` now accepts a small internal `PipelineRequest` object instead of `argparse.Namespace`, while `./ingest.py` keeps CLI parsing and JSON input handling.

Slice 3 is complete: focused service-level tests now cover `./services/pipeline.py` directly through `PipelineRequest` and `run_pipeline`.

## Goal

Move pipeline orchestration out of `./ingest.py` while preserving existing behavior.

Before this milestone, `./ingest.py` owned too many responsibilities:

- CLI argument parsing;
- JSON input handling;
- environment loading;
- pipeline orchestration;
- local file writing;
- note generation branching;
- Notion export branching;
- JSON result shaping;
- error staging.

Milestone 5 made the internals easier to extend before adding new input modes such as transcript-file fallback.

## Slice 1: Extract Pipeline Orchestration

Status: complete.

Scope:

- add `./services/pipeline.py`;
- move pipeline-only constants, helpers, result shaping, and `run_pipeline` from `./ingest.py`;
- keep CLI parsing, JSON input handling, environment loading, and `main` in `./ingest.py`;
- update tests to patch `./services/pipeline.py` targets where pipeline dependencies are mocked.

## Slice 2: Introduce PipelineRequest Contract

Status: complete.

Scope:

- add a small `PipelineRequest` dataclass in `./services/pipeline.py`;
- change `run_pipeline` to accept `PipelineRequest` instead of `argparse.Namespace`;
- keep CLI parsing, JSON input handling, and conversion into `PipelineRequest` in `./ingest.py`;
- keep result JSON keys, human-readable output, and n8n wrapper behavior unchanged.

## Slice 3: Add Focused Pipeline Service Tests

Status: complete.

Scope:

- add `./tests/test_pipeline.py`;
- test `./services/pipeline.py` directly through `PipelineRequest` and `run_pipeline`;
- mock transcript parsing/fetching, manual prompt construction, optional note generation, and Notion export at the `./services/pipeline.py` boundary;
- use temporary output roots by patching `TRANSCRIPT_DIR`, `PROMPT_DIR`, and `NOTES_DIR`;
- cover manual/local fallback, Notion export rejection without a generated note, local generated-note output, and Notion export result details.

## Target Shape

- `./ingest.py` remains the CLI entry point.
- `./ingest.py` keeps CLI parsing and user-facing output mode selection.
- Pipeline orchestration lives in a dedicated service module.
- `./services/pipeline.py` accepts a pipeline-specific request object, not raw CLI parser state.
- The JSON stdin/stdout contract stays unchanged.
- `./scripts/n8n-ingest.sh` stays unchanged unless required by a preserved contract.
- Notion logic stays inside Python.
- n8n remains orchestration-only.

## Non-Goals

- no new CLI features;
- no transcript fallback in Milestone 5;
- no long-video chunking;
- no HTTP server;
- no queue;
- no n8n workflow expansion;
- no Notion behavior changes.

## Success Criteria

- existing tests pass;
- local CLI behavior is unchanged;
- JSON output shape is unchanged;
- n8n wrapper behavior is unchanged;
- Notion export still works through the existing export path;
- `./ingest.py` becomes thinner and easier to read.

---

# Milestone 6: Transcript Fallback Input

## Status

Milestone 6 is complete for the local MVP and tagged `v0.6.0`.

## Goal

Allow the pipeline to use a manually provided transcript when YouTube transcript fetching fails or is not desirable.

This supports the known transcript bottleneck: automatic YouTube captions can be missing, blocked, malformed, or unstable.

## Implemented Shape

- accept transcript text from a local file;
- keep YouTube URL as source metadata;
- reuse the same prompt generation, optional note generation, local markdown output, and Notion export path.

## Slice 1: Explicit Local Transcript File Input for Normal CLI Path

Status: complete.

Scope:

- add `--transcript-file PATH` to `./ingest.py` for positional-URL CLI usage;
- keep the positional YouTube URL required when using `--transcript-file`;
- keep the YouTube URL as source metadata;
- still parse the YouTube URL to get `video_id` and default output naming;
- when `--transcript-file` is provided, read UTF-8 transcript text from that file instead of calling YouTube transcript fetching;
- write the manual transcript text to `./output/transcripts/` using the existing output naming behavior;
- build the GPT prompt with the same prompt template and the original YouTube URL;
- reuse existing optional OpenAI note generation, local markdown output, and Notion export behavior.

Historical out of scope for this slice:

- no changes to the JSON input payload contract in Milestone 6 Slice 1;
- no `transcript_file` field in `--input-json` or `--input-json-file` until the later Milestone 7 JSON contract extension;
- no changes to `./scripts/n8n-ingest.sh`;
- no URL-less transcript-to-note mode;
- no `--source-url`, `--source-title`, or `--source-type`;
- no Whisper, alternative transcript provider, or long-video chunking.

## Slice 2: Empty Manual Transcript File Validation

Status: complete.

Scope:

- reject `--transcript-file` input when the file is empty or contains only whitespace;
- fail during the transcript stage before writing transcript, prompt, note, or Notion output files;
- preserve existing behavior for missing or unreadable transcript files;
- preserve transcript text unchanged when the file contains non-whitespace content.

Historical out of scope for this slice:

- no JSON input payload contract changes in Milestone 6 Slice 2;
- no `./scripts/n8n-ingest.sh` changes;
- no URL-less transcript-to-note mode;
- no new source metadata options.

## Non-Goals

- no Whisper or local transcription;
- no alternative transcript provider;
- no long-video chunking.

---

# Milestone 7: JSON Transcript Fallback Input

## Status

Milestone 7 Slice 1 is complete for the local MVP.

## Goal

Allow automation callers to use the existing manual transcript-file fallback through the JSON input contract.

This keeps n8n and other automation paths aligned with the normal positional CLI path without adding new transcript sources or changing the pipeline core.

## Slice 1: Allow `transcript_file` in JSON Input

Status: complete.

Scope:

- add `transcript_file` as an optional supported field for `--input-json`;
- add `transcript_file` as an optional supported field for `--input-json-file`, including stdin via `--input-json-file -`;
- keep `url` required in every JSON payload;
- require `transcript_file` to be a string when provided;
- keep rejecting unknown JSON fields;
- pass JSON `transcript_file` into `PipelineRequest.transcript_file`;
- reuse existing transcript-stage file reading and validation in `./services/pipeline.py`;
- preserve JSON stdout-only behavior;
- keep existing positional URL plus `--transcript-file` behavior unchanged;
- keep `./scripts/n8n-ingest.sh` unchanged.

Supported JSON shape:

```json
{
  "url": "https://youtu.be/VIDEO_ID",
  "transcript_file": "./manual-transcript.txt",
  "export": "local"
}
```

Out of scope:

- no URL-less transcript mode;
- no inline transcript text in JSON;
- no transcript from stdin;
- no `source_url`, `source_title`, or `source_type` metadata;
- no Whisper;
- no alternative transcript providers;
- no long-video chunking;
- no n8n workflow changes;
- no HTTP wrapper;
- no new dependencies.

## Non-Goals

- do not expand the n8n workflow contract beyond the existing JSON stdin/stdout boundary;
- do not add new transcript acquisition behavior beyond local UTF-8 transcript files;
- do not change Notion export behavior.

---

# Milestone 8: Test Suite Maintenance

## Status

Milestone 8 Slice 1 is complete.

## Goal

Keep the test suite easy to read as the CLI contract grows, without changing runtime behavior.

## Slice 1: Split Ingest CLI Tests by Responsibility

Status: complete.

Scope:

- split the former `./tests/test_ingest.py` coverage into focused ingest test modules;
- add `./tests/test_ingest_input.py` for JSON input parsing, input validation, ambiguity checks, transcript-file input mapping, and `PipelineRequest` mapping with `run_pipeline` mocked directly;
- add `./tests/test_ingest_cli.py` for broader `ingest.main()` CLI behavior with pipeline dependencies mocked;
- keep `./tests/test_pipeline.py` focused on service-level pipeline behavior;
- preserve existing ingest behavior coverage without changing `./ingest.py`, `./services/pipeline.py`, or `./scripts/n8n-ingest.sh`.

Out of scope:

- no runtime refactor;
- no pytest migration;
- no new dependencies;
- no Notion behavior changes;
- no n8n behavior changes;
- no design-doc decomposition.

---

# Milestone 9: Repo-local Launcher Usability Closeout

## Status

Complete and tagged `v0.9.0`.

## Goal

Make day-to-day repo-local MVP usage comfortable through `ynn`, `ynn-note`, `ynn-notion`, and `ynn-prompt`.

## Summary

- repo-local launchers call back into this repository as thin wrappers;
- `./ingest.py` remains the underlying direct CLI contract for fallback use, tests, local development, n8n, and packaging work;
- launcher usability was a repo-local closeout before `v1.0.0` installable CLI packaging;
- `v1.0.0` later kept the same command names as editable-install console script entrypoints.

---

# v1.0.0 Packaging Slices

## Status

Complete before the numbered UX hardening work.

## Slice Summary

- Slice 1 added the minimal editable-install packaging skeleton and the `ynn`, `ynn-note`, `ynn-notion`, and `ynn-prompt` console script entrypoints.
- Slice 2 defined runtime output and config-path policy for repo-local and editable-installed CLI usage.
- Slice 3 moved the built-in prompt template into package-owned resources.
- Slice 4 replaced the transitional flat-repo packaging shape with the `youtube_notion_notes` package: Slice 4.2 moved service modules, Slice 4.3 moved CLI implementation modules while keeping top-level compatibility wrappers, Slice 4.4 verified prompt template package data after the services move, and Slice 4.5 moved console scripts to package modules and removed transitional top-level `py-modules` packaging.

---

# v1.0.0 Numbered UX Hardening

## Status

Complete before the separate UX-FINAL release/publication audit.

## Slice Summary

- UX-1 added the Notion export config preflight before transcript, note-generation, or Notion work for generated-note export.
- UX-2 documented the installed CLI config contract, including the `ynn init` role and runtime config priority, before implementation.
- UX-3 implemented `ynn init` user-config and output-directory setup, then added optional prompts for missing OpenAI and Notion config values and transcript language preferences.
- UX-4 aligned user-facing setup and command guidance to the installed CLI flow.
- UX-5 recorded release-readiness verification before UX-6 transcript selection quality work.

---

# v1.0.0 UX-6: Transcript Selection Quality

## Status

UX-6 is complete before the separate UX-FINAL release/publication audit.

## Completion Note

- normal YouTube transcript fetching uses project-owned discovery and selection before fetching the chosen track;
- selection prefers known manual/author tracks over generated tracks, including translated manual tracks before generated preferred-language tracks;
- unknown-origin tracks remain last-resort fallbacks;
- transcript-file input bypasses YouTube discovery and selection;
- JSON success output may include additive `transcript_selection` metadata.

## Slice Summary

- Early slices added project-owned transcript track discovery metadata and selection policy, including unknown-origin tracks as last-resort fallbacks.
- Runtime slices connected discovery and selection to normal YouTube transcript fetching and exposed concise human selection output plus additive JSON selection metadata.
- Closeout aligned current docs with the completed transcript selection behavior before the separate UX-FINAL release/publication audit.
