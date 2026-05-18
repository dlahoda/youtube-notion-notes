# YouTube to GPT to Notion Notes MVP

## Purpose

Keep this document as the canonical technical source of truth for the current project state, roadmap, slice boundaries, and durable project decisions.

This document should:

- record the current MVP state;
- separate Python pipeline logic from n8n orchestration;
- describe the pipeline as a small system, not an accidental script;
- call out risks and bottlenecks;
- keep Notion as final storage, not the center of logic;
- keep the LLM layer replaceable: OpenAI API, manual ChatGPT, or a future local model.

---

# 1. Current Project State

The project is a local Python pipeline that takes a YouTube link and creates a readable note that can be saved locally and optionally exported to Notion.

Current local usage:

```bash
python ingest.py "https://www.youtube.com/watch?v=..."
python ingest.py "https://www.youtube.com/watch?v=..." --export notion
```

Current roadmap:

- Milestone 1 is complete: local transcript and markdown note.
- Milestone 2 is complete and tagged `v0.2.0`: opt-in Notion export.
- Milestone 3 is complete and tagged `v0.3.0`: local CLI automation contract.
- Milestone 4 is complete and tagged `v0.4.0`: n8n integration contract and smoke workflow.
- Milestone 5 is next: pipeline core refactor.
- Milestone 6 is later: transcript fallback input.

---

# 2. MVP Boundaries

These boundaries keep the pipeline from growing into a larger product too early.

Outside the current local-first MVP:

- a perfect markdown editor;
- a custom StackEdit replacement;
- a full web app;
- a browser extension;
- a complex job queue;
- automatic handling for every possible YouTube edge case;
- a polished UI;
- a production-grade hosted workflow.

The current MVP answers one question:

> Can we reliably turn a YouTube link into a high-quality markdown note?

---

# 3. Pipeline

```text
YouTube URL
-> extract video_id
-> fetch transcript
-> clean transcript
-> generate note
-> save local markdown backup
-> optionally create Notion page
-> optionally append Notion blocks
```

## What Happens

The system takes one input URL and progressively turns it into a structured note.

## Why This Matters

Each step can be debugged independently. If transcript fetching fails, the Notion layer should not be involved. If note generation produces poor output, the YouTube extraction path should not need to change.

---

# 4. File Architecture

```text
youtube-notion-notes/
  ingest.py
  prompts/
    comprehensive_note.md
  services/
    pipeline.py
    transcript.py
    note_generator.py
    notion.py
    markdown_to_notion.py
    note_metadata.py
    notion_export.py
  scripts/
    n8n-ingest.sh
  docs/
    n8n-smoke-workflow.md
    n8n-smoke-workflow.json
  output/
    transcripts/
    prompts/
    notes/
  .env
  requirements.txt
```

## Module Responsibilities

### `./ingest.py`

Main CLI entry point.

Owns CLI argument parsing, input modes, output mode selection, environment loading, and user-facing process exit behavior.

Imports `run_pipeline` from `./services/pipeline.py`.

### `./services/pipeline.py`

Owns the current pipeline orchestration while preserving the existing CLI contract:

- transcript fetching;
- local transcript and prompt file writing;
- optional note generation;
- optional Notion export branching;
- JSON result shaping for pipeline success and pipeline failures.

### `./services/transcript.py`

Responsible only for YouTube URLs, video IDs, and transcript fetching.

### `./services/note_generator.py`

Responsible for turning a transcript into a note.

It should support multiple modes:

- OpenAI API;
- manual mode;
- future Ollama or local model mode.

### `./services/notion.py`

Responsible for creating Notion pages and appending blocks.

### `./services/markdown_to_notion.py`

Converts markdown into basic Notion blocks.

Supported markdown shapes are intentionally simple:

- headings;
- paragraphs;
- bullets;
- numbered lists;
- quotes;
- code blocks.

### `./services/note_metadata.py`

Extracts metadata from a markdown note for Notion export.

### `./services/notion_export.py`

Orchestrates Notion export on top of `./services/notion.py`, `./services/markdown_to_notion.py`, and metadata extraction.

### `./scripts/n8n-ingest.sh`

Small n8n-facing wrapper that calls `./ingest.py` through the JSON stdin/stdout contract and verifies that stdout is valid JSON.

---

# 5. Milestone 1: Local Note Without Notion

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

# 6. Milestone 2: Notion Export

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

# 7. Milestone 3: n8n Preparation

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

JSON input supports only:

- `url`;
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
```

The `--input-json` payload is a JSON object with:

- `url`: required YouTube URL string;
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

# 8. Milestone 4: n8n Integration Contract and Smoke Workflow

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

# 9. Milestone 5: Pipeline Core Refactor

## Status

In progress.

Slice 1 is complete: pipeline orchestration moved from `./ingest.py` to `./services/pipeline.py` without changing the CLI or JSON stdin/stdout contract.

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

Milestone 5 should make the internals easier to extend before adding new input modes such as transcript-file fallback.

## Slice 1: Extract Pipeline Orchestration

Status: complete.

Scope:

- add `./services/pipeline.py`;
- move pipeline-only constants, helpers, result shaping, and `run_pipeline` from `./ingest.py`;
- keep CLI parsing, JSON input handling, environment loading, and `main` in `./ingest.py`;
- update tests to patch `./services/pipeline.py` targets where pipeline dependencies are mocked.

Out of scope:

- no new CLI features;
- no transcript fallback;
- no long-video chunking;
- no HTTP server;
- no queue;
- no n8n workflow changes;
- no Notion behavior changes.

## Target Shape

- `./ingest.py` remains the CLI entry point.
- `./ingest.py` keeps CLI parsing and user-facing output mode selection.
- Pipeline orchestration moves into a dedicated service module.
- The JSON stdin/stdout contract stays unchanged.
- `./scripts/n8n-ingest.sh` stays unchanged unless required by a preserved contract.
- Notion logic stays inside Python.
- n8n remains orchestration-only.

## Non-Goals

- no new CLI features;
- no transcript fallback yet;
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

# 10. Milestone 6: Transcript Fallback Input

## Goal

Allow the pipeline to use a manually provided transcript when YouTube transcript fetching fails or is not desirable.

This supports the known transcript bottleneck: automatic YouTube captions can be missing, blocked, malformed, or unstable.

## Possible Shape

- accept transcript text from a local file;
- keep YouTube URL as source metadata;
- reuse the same prompt generation, optional note generation, local markdown output, and Notion export path.

## Non-Goals

- no Whisper or local transcription yet;
- no alternative transcript provider yet;
- no long-video chunking yet.

---

# 11. Future Options and Backlog

These items are intentionally outside Milestone 5. Transcript fallback input is already planned as Milestone 6; the rest is optional later backlog if the local MVP needs it.

## Known Limitations

- YouTube transcript fetching is the most fragile part. Automatic captions can be missing, blocked, malformed, or unstable.
- Long transcripts may not fit into one LLM request. Chunking and map-reduce summarization are not implemented.
- Notion is not a pure markdown editor. Markdown is converted into basic Notion blocks, and complex typography is intentionally deferred.
- OpenAI API billing is separate from a ChatGPT subscription. Manual mode remains the fallback when API usage is unavailable or unwanted.

## Current Design Decisions

- Support both manual GPT bridge mode and optional OpenAI API mode.
- Treat manual mode as a simple, durable fallback rather than a failure path.
- Keep future local model support possible, but do not implement it yet.
- Keep the note shape in `./prompts/comprehensive_note.md`: title, source URL, overview, key ideas, detailed notes, memorable phrasing, practical takeaways, and tags.
- Use Notion status values `Draft`, `Reviewed`, and `Archived`.

## Future Options

- long-video chunking and map-reduce note generation;
- constructing payloads through upstream n8n nodes instead of hardcoded smoke payloads;
- n8n notification or audit branches;
- scheduled n8n triggers;
- improved retry and reporting behavior;
- alternative transcript providers;
- Whisper or local transcription;
- hosted or remote execution model;
- optional HTTP wrapper if local command execution stops being enough.

---

# 12. Design Principle

The pipeline should be boring.

Boring is good here.

Less magic means fewer places where things break without explanation.

---

# 13. Repository Workflow

Canonical repository: `dlahoda/youtube-notion-notes`

Default branch: `main`.

Repository access rule:

- The repository is private.
- Use the GitHub connector/integration for repository access.
- Do not use web search to inspect repository contents.
- If GitHub connector access is unavailable, ask the user for a branch, PR, diff, or uploaded files instead of searching the web.

Working flow:

- implementation happens locally through Codex/VS Code;
- feature work is committed to feature branches;
- pushed branches or PRs are reviewed through GitHub;
- final integration uses squash merge into `main`;
- assistant must not create commits, branches, PRs, or merge changes unless explicitly asked.

---

# 14. Historical Setup Notes

The old Codex execution runbook was useful for bootstrapping Milestone 1 from an empty repository.

Current durable guidance:

- work one milestone or slice at a time;
- keep a git checkpoint before each large task;
- obey `./AGENTS.md` and this design document;
- keep changes small and reviewable;
- show diffs and verification commands after implementation;
- do not create commits, branches, PRs, or merges unless explicitly asked.

The original empty-repo setup prompt is historical context only; Milestones 1-4 are already complete.
