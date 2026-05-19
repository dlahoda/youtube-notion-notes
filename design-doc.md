# YouTube to GPT to Notion Notes MVP

## Purpose

Keep this document as the canonical technical source of truth for the current project state, active contracts, roadmap, slice boundaries, and project map.

This document should:

- record the current MVP state;
- separate Python pipeline logic from n8n orchestration;
- describe the pipeline as a small system, not an accidental script;
- call out risks and bottlenecks;
- keep Notion as final storage, not the center of logic;
- keep the LLM layer replaceable: OpenAI API, manual ChatGPT, or a future local model.
- point to durable project decisions that live in `./docs/decisions.md`.

## Project docs map

Default reading:
- ./design-doc.md — current source of truth, active contracts, current architecture, roadmap, and slice boundaries.
- ./AGENTS.md — repo-local rules for AI/Codex work.

Do not read every docs file by default. Start with ./design-doc.md and ./AGENTS.md, then open only the smallest supporting document needed for the current task.

Current decisions:
- ./docs/decisions.md — durable architecture decisions; read when changing contracts, module boundaries, integration shape, or project-level behavior.

Optional ideas:
- ./docs/ideas.md — future ideas and optional backlog items; not current scope unless explicitly promoted into ./design-doc.md.

Archive docs, if present under ./docs/archive/, are historical context only. Do not read them by default. They are not current source of truth.

Historical reference:
- ./docs/archive/milestone-history.md — completed milestone and slice detail only; not current source of truth.

---

# 1. Current Project State

The project is a repo-local Python pipeline that takes a YouTube link and creates a readable note that can be saved locally and optionally exported to Notion.

Current day-to-day local usage goes through global launcher commands installed into the user's shell:

```bash
ynn "https://www.youtube.com/watch?v=..."
ynn-note "https://www.youtube.com/watch?v=..."
ynn-notion "https://www.youtube.com/watch?v=..."
ynn-prompt "https://www.youtube.com/watch?v=..."
```

These launchers remain thin wrappers over this repository. `./ingest.py` is still the underlying direct CLI contract for fallback use, tests, local development, n8n, and any future packaging work.

Current roadmap:

- Milestone 1 is complete: local transcript and markdown note.
- Milestone 2 is complete and tagged `v0.2.0`: opt-in Notion export.
- Milestone 3 is complete and tagged `v0.3.0`: local CLI automation contract.
- Milestone 4 is complete and tagged `v0.4.0`: n8n integration contract and smoke workflow.
- Milestone 5 is complete and tagged `v0.5.0`: pipeline core refactor.
- Milestone 6 is complete and tagged `v0.6.0`: transcript fallback input.
- Milestone 7 Slice 1 is complete and tagged `v0.7.0`: JSON transcript-file fallback input.
- Milestone 8 Slice 1 is complete and tagged `v0.8.0`: ingest CLI tests split by responsibility.
- Milestone 9 is the current repo-local launcher usability closeout target and should be tagged `v0.9.0` when complete.
- A future installable CLI package is deferred to `v1.0.0`.

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

The current MVP is still repo-local. The launcher commands make that repo-local workflow comfortable for daily use, but they do not turn the project into an installable CLI package.

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
    ynn-run
    install-launchers.sh
  docs/
    decisions.md
    ideas.md
    n8n-smoke-workflow.md
    n8n-smoke-workflow.json
    archive/
      milestone-history.md
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

### `./scripts/ynn-run`

Small repo-local launcher used by daily shell commands. It changes to the repository root before calling `./ingest.py`, uses `./.venv/bin/python` when present, and falls back to `python` otherwise.

### `./scripts/install-launchers.sh`

One-time local installer that creates `ynn`, `ynn-note`, `ynn-notion`, and `ynn-prompt` wrappers in `~/.local/bin`. These wrappers point back to the repo-local `./scripts/ynn-run` by absolute path.

---

# 5. Current CLI and Automation Contracts

These contracts are current behavior and should stay in `./design-doc.md` even when completed milestone history moves to archive docs.

## Human CLI Usage

Default local usage accepts a YouTube URL and writes local transcript, prompt, and note outputs:

```bash
python ingest.py "https://www.youtube.com/watch?v=..."
```

Notion export is opt-in:

```bash
python ingest.py "https://www.youtube.com/watch?v=..." --export notion
```

Local-only mode can be explicit:

```bash
python ingest.py "https://www.youtube.com/watch?v=..." --export local
```

A local transcript file can be used when YouTube transcript fetching is unavailable or undesirable:

```bash
python ingest.py "https://www.youtube.com/watch?v=..." --transcript-file ./manual-transcript.txt
```

Daily local launcher commands are part of local MVP usability. They call back into this repository and remain thin wrappers over the existing direct CLI contract, not an installable package:

```bash
ynn "https://www.youtube.com/watch?v=..."
ynn-note "https://www.youtube.com/watch?v=..."
ynn-notion "https://www.youtube.com/watch?v=..."
ynn-prompt "https://www.youtube.com/watch?v=..."
```

Launcher behavior:

- `ynn` calls `python ./ingest.py "URL"`;
- `ynn-note` calls `python ./ingest.py "URL" --export local`;
- `ynn-notion` calls `python ./ingest.py "URL" --export notion`;
- `ynn-prompt` calls `python ./ingest.py "URL" --no-note`.

The launcher layer must not change pipeline behavior, the JSON input/output contract, or n8n behavior. A future installable CLI package remains a later `v1.0.0` target, not current MVP scope.

## JSON Input Contract

Automation callers may use structured JSON instead of a positional URL:

```bash
python ingest.py --input-json "{\"url\":\"https://www.youtube.com/watch?v=...\"}" --output json
python ingest.py --input-json-file payload.json --output json
python ingest.py --input-json-file - --output json
```

`--input-json-file -` reads the JSON payload from stdin.

The JSON payload is an object with only these supported fields:

- `url`: required YouTube URL string;
- `transcript_file`: optional UTF-8 local transcript file path string;
- `export`: optional export target, with the same accepted values as `--export`: `local` or `notion`.

Unknown JSON fields are rejected so automation typos do not get silently ignored.

Ambiguous input is rejected:

- positional URL plus `--input-json`;
- positional URL plus `--input-json-file`;
- `--input-json` plus `--input-json-file`;
- `export` inside any JSON payload plus `--export`.

## JSON Output Contract

JSON output mode can be combined with supported input and export modes:

```bash
python ingest.py "https://www.youtube.com/watch?v=..." --output json
python ingest.py "https://www.youtube.com/watch?v=..." --export notion --output json
```

In JSON output mode, stdout must contain only JSON, including for input errors.

Success output includes:

- `ok`;
- `url`;
- `export_mode`;
- created local output paths;
- Notion page details when Notion export runs.

`notion_page_url` comes from the Notion API page response `url` field and is included only when that field is present.

Failure output includes:

- `ok: false`;
- `stage`;
- `error`.

Input errors keep stdout JSON-only:

```json
{
  "ok": false,
  "stage": "input",
  "error": "..."
}
```

## `transcript_file` Support Summary

`transcript_file` is supported in both human CLI and JSON input paths.

Current behavior:

- `--transcript-file PATH` works with positional URL usage;
- JSON payloads may include `"transcript_file": "./manual-transcript.txt"`;
- the YouTube URL remains required and is kept as source metadata;
- the YouTube URL is still parsed for `video_id` and default output naming;
- transcript files are read as UTF-8 local files;
- missing, unreadable, empty, or whitespace-only transcript files fail during the transcript stage;
- non-whitespace transcript text is preserved unchanged;
- manual transcript text is written to `./output/transcripts/` using existing output naming behavior;
- prompt generation, optional OpenAI note generation, local markdown output, and Notion export reuse the same pipeline path.

Current boundaries:

- no URL-less transcript mode;
- no inline transcript text in JSON;
- no transcript from stdin;
- no `source_url`, `source_title`, or `source_type` metadata;
- no Whisper;
- no alternative transcript providers;
- no long-video chunking.

---

# 6. Current Notion Export Boundary

Notion export is optional and remains inside Python.

Supported export modes:

- `local`;
- `notion`.

Notion export can be selected through either CLI flags or JSON payloads:

```bash
python ingest.py "https://www.youtube.com/watch?v=..." --export notion
python ingest.py --input-json "{\"url\":\"https://www.youtube.com/watch?v=...\",\"export\":\"notion\"}" --output json
```

Required `.env` variables for Notion export:

```env
NOTION_API_KEY=...
NOTION_DATABASE_ID=...
```

`OPENAI_API_KEY` remains optional and belongs only to OpenAI note generation. It is not required for Notion export.

Required Notion database contract:

- `Name`: title;
- `URL`: YouTube link;
- `Tags`: multi-select;
- `Status`: select;
- `Source`: select;
- `Created`: created time.

Current Notion database details:

- `Status` uses a regular Notion `select` property, not Notion native Status;
- `Source` uses a regular Notion `select` property, not `rich_text`;
- `Tags` uses a `multi_select` property;
- `Created` is managed by Notion as `created_time` and should not be set manually by the client;
- recommended `Status` values are `Draft`, `Reviewed`, and `Archived`;
- recommended `Source` value for this pipeline is `YouTube`;
- `./services/notion.py` allows empty tags so it can stay a small reusable Notion adapter.

Markdown note metadata convention:

- the first Markdown H1 heading is treated as the note title;
- the note title must use `# Note title`;
- tags are read from a comma-separated `Tags:` line;
- spaces inside multi-word tags are preserved;
- the source URL is not parsed from markdown; it comes from the original CLI or JSON input.

The note body is inserted into the Notion page as basic Notion blocks. Supported markdown shapes are intentionally simple: headings, paragraphs, bullets, numbered lists, quotes, and code blocks.

n8n must not duplicate Notion export logic. n8n stays orchestration-only and calls the Python CLI boundary.

---

# 7. Current n8n Orchestration Boundary

n8n calls `./ingest.py` through the JSON stdin/stdout contract. It should orchestrate, branch, and notify; it should not contain transcript fetching, note generation, markdown conversion, or Notion export logic.

Preferred local integration:

- n8n uses an Execute Command-style node;
- n8n passes a JSON payload to `python ./ingest.py --input-json-file - --output json`;
- Python reads JSON from stdin;
- Python writes machine-readable JSON to stdout only;
- n8n parses stdout JSON and branches on `ok: true` / `ok: false`;
- n8n does not depend on `./Makefile` targets;
- `./Makefile` remains a local developer convenience only.

Current wrapper boundary:

- `./scripts/n8n-ingest.sh` is the small n8n-facing shell wrapper;
- the wrapper calls `./ingest.py` through `--input-json-file - --output json`;
- the wrapper validates that stdout is JSON before returning it to n8n;
- the wrapper allows n8n to continue when `./ingest.py` emits valid JSON with `ok: false`;
- missing or invalid stdout JSON is treated as a workflow error.

Current non-goals:

- no HTTP server;
- no queue;
- no new dependencies;
- no Notion logic inside n8n;
- no duplicated pipeline logic in n8n.

Optional future n8n expansion belongs in backlog unless local command execution stops being enough.

---

# 8. Completed Milestone Summary

Detailed completed milestone and slice history lives in `./docs/archive/milestone-history.md`. That archive is historical context only and is not current source of truth.

Completed milestones:

- Milestone 1: Local note without Notion — complete. The pipeline can turn a YouTube URL into local transcript and markdown note outputs.
- Milestone 2: Notion export — complete and tagged `v0.2.0`. Notion export is opt-in and handled inside Python.
- Milestone 3: n8n preparation — complete and tagged `v0.3.0`. The CLI supports JSON input/output contracts for automation.
- Milestone 4: n8n integration contract and smoke workflow — complete and tagged `v0.4.0`. n8n integration is local-first through JSON stdin/stdout and a small wrapper.
- Milestone 5: Pipeline core refactor — complete and tagged `v0.5.0`. Pipeline orchestration lives in `./services/pipeline.py` behind `PipelineRequest`.
- Milestone 6: Transcript fallback input — complete and tagged `v0.6.0`. Human CLI usage supports local UTF-8 transcript files.
- Milestone 7: JSON transcript fallback input — Slice 1 complete and tagged `v0.7.0`. JSON input supports the same local transcript-file fallback.
- Milestone 8: Test suite maintenance — Slice 1 complete and tagged `v0.8.0`. Ingest CLI tests are split by responsibility without runtime behavior changes.

Current closeout target:

- Milestone 9: Repo-local launcher usability closeout — active docs-only closeout target for `v0.9.0`. This milestone recognizes that day-to-day MVP usage now works through `ynn`, `ynn-note`, `ynn-notion`, and `ynn-prompt` while the project remains repo-local and `./ingest.py` remains the underlying CLI contract.

---

# 9. Future Options and Backlog

Future ideas and optional backlog items live in `./docs/ideas.md`.

Those ideas are not current scope, active contracts, or implementation instructions unless they are explicitly promoted back into `./design-doc.md`.

## Known Limitations

- YouTube transcript fetching is the most fragile part. Automatic captions can be missing, blocked, malformed, or unstable, so Milestone 6 added an explicit local transcript file fallback.
- Long transcripts may not fit into one LLM request. Chunking and map-reduce summarization are not implemented.
- Notion is not a pure markdown editor. Markdown is converted into basic Notion blocks, and complex typography is intentionally deferred.
- OpenAI API billing is separate from a ChatGPT subscription. Manual mode remains the fallback when API usage is unavailable or unwanted.

## Current Design Decisions

Durable project decisions live in `./docs/decisions.md`.

Current summary:

- Python owns pipeline logic; n8n orchestrates only.
- JSON stdin/stdout is the current automation boundary.
- Notion export stays inside Python.
- Manual transcript-file input still requires a source YouTube URL.
- Manual GPT bridge mode remains a durable fallback.
- Future local model support remains possible but is not implemented yet.
- Markdown-to-Notion conversion stays intentionally simple.

## Future Options

Backlog themes currently parked in `./docs/ideas.md` include:

- long-video handling;
- n8n orchestration improvements;
- transcript input and provider expansion;
- hosted, remote, or HTTP execution options;
- installable CLI packaging for a future `v1.0.0`.

---

# 10. Design Principle

The pipeline should be boring.

Boring is good here.

Less magic means fewer places where things break without explanation.

---

# 11. Repository Workflow

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
