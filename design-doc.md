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

The project is a Python pipeline that takes a YouTube link and creates a readable note that can be saved locally and optionally exported to Notion.

Current day-to-day command names are:

```bash
ynn "https://www.youtube.com/watch?v=..."
ynn-note "https://www.youtube.com/watch?v=..."
ynn-notion "https://www.youtube.com/watch?v=..."
ynn-prompt "https://www.youtube.com/watch?v=..."
```

For `v1.0.0`, editable installs expose these command names as console script entrypoints. Repo-local launcher scripts remain supported as thin wrappers over this repository. `./ingest.py` is still the underlying direct CLI contract for fallback use, tests, local development, n8n, and packaging work.

Current release state:

- Milestones 1-9 are complete and tagged through `v0.9.0`.
- `v1.0.0` packaging, numbered UX hardening, UX-6 transcript selection quality, docs truth sync, and CHANGELOG readiness are complete.
- UX-FINAL release/publication audit has not started.
- The public repository licensing gate remains deferred until final audit/publication steps.

Current `v1.0.0` packaging behavior:

- local editable installs expose the same `ynn`, `ynn-note`, `ynn-notion`, and `ynn-prompt` command names as the repo-local launchers;
- installed entrypoints use package modules under `./youtube_notion_notes/`;
- top-level `./ingest.py` and `./ynn_cli.py` remain compatibility wrappers for direct CLI, n8n, tests, and repo-local usage;
- the built-in prompt template is package-owned data under `./youtube_notion_notes/services/resources/`.

Current installed CLI UX contracts:

The installed CLI setup path is:

```text
install
-> init/config
-> use
```

`ynn init` is a setup helper that creates or updates the user config fallback without making it the only supported config path. Process environment variables, cwd `./.env`, explicit `--env-file PATH`, and manual user-config edits remain supported.

Runtime config priority:

1. explicit `--env-file PATH`;
2. real process environment variables;
3. cwd `./.env`;
4. user config `~/.config/youtube-notion-notes/.env`;
5. built-in defaults.

The user config file is a dotenv file at `~/.config/youtube-notion-notes/.env`. `ynn init --output-dir PATH` may store `YNN_OUTPUT_DIR` there, preserve existing values by default, create the configured output directory idempotently, and collect missing transcript-language, OpenAI, or Notion config values without calling those services.

Output root resolution remains explicit `--output-dir PATH`, then `YNN_OUTPUT_DIR`, then `./output` relative to cwd. Regular pipeline runs create `transcripts/`, `prompts/`, and `notes/` under the resolved output root as needed.

For generated-note Notion export, `--export notion` and `ynn-notion` fail before transcript fetching, OpenAI calls, or Notion calls when `OPENAI_API_KEY`, `NOTION_API_KEY`, or `NOTION_DATABASE_ID` is missing. Missing `OPENAI_API_KEY` remains a non-error for `ynn`, `ynn-note`, and `ynn-prompt`.

Current UX-6 transcript selection contract:

Normal YouTube transcript fetching inspects available transcript tracks and chooses the best available track by origin and quality before fetching transcript snippets. A narrow language-preference fetch fallback may remain for older `youtube-transcript-api` shapes where transcript discovery is unavailable.

Selection priority:

1. manual/author-provided transcript in preferred languages;
2. manual/author-provided transcript translated to a preferred language;
3. generated transcript in preferred languages;
4. generated transcript translated to a preferred language;
5. unknown-origin transcript in preferred languages;
6. unknown-origin transcript translated to a preferred language.

`--transcript-file` and JSON `transcript_file` input bypass YouTube track discovery and selection while preserving the original URL as source metadata. Human output can show one concise transcript selection line when the transcript source is known. JSON output keeps existing fields valid and adds `transcript_selection` metadata additively when known, including `origin: transcript_file` for transcript-file input.

UX-FINAL -- Public repository licensing gate: Not started.

- Before publishing the repository publicly for `v1.0.0`, use an All Rights Reserved / source-visible but not open-source licensing posture.
- Do not add MIT, Apache, BSD, GPL, AGPL, or any other open-source license unless that is explicitly decided later.
- Do not create `./LICENSE.md` until the public licensing posture and wording are intentionally chosen.
- Before publishing publicly, audit for committed secrets, generated output files, Notion IDs, private URLs, generated artifacts, and dependency licenses.

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

The `v0.9.0` MVP is repo-local. The launcher commands make that repo-local workflow comfortable for daily use. `v1.0.0` keeps those command names as installable package entrypoints and hardens the installed CLI setup path so daily use is predictable from any directory.

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
  pyproject.toml
  ingest.py
  ynn_cli.py
  youtube_notion_notes/
    __init__.py
    ingest.py
    ynn_cli.py
    services/
      __init__.py
      pipeline.py
      transcript.py
      note_generator.py
      resources/
        comprehensive_note.md
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

Compatibility wrapper for direct CLI usage.

Delegates to `youtube_notion_notes.ingest.main` so `python ./ingest.py ...`, n8n, tests, and repo-local launchers keep the existing direct CLI contract.

### `./ynn_cli.py`

Compatibility adapter for direct top-level import users and wrapper compatibility tests.

Re-exports the package launcher functions from `./youtube_notion_notes/ynn_cli.py`. Editable-install console scripts now point directly at `youtube_notion_notes.ynn_cli`.

### `./youtube_notion_notes/ingest.py`

Main CLI implementation module.

Owns CLI argument parsing, input modes, output mode selection, environment loading, and user-facing process exit behavior.

Imports `PipelineRequest` and `run_pipeline` from `./youtube_notion_notes/services/pipeline.py`.

### `./youtube_notion_notes/ynn_cli.py`

Thin installable CLI entrypoint implementation.

Owns only the `ynn`, `ynn-note`, `ynn-notion`, and `ynn-prompt` console script wrappers for local editable package installs. It appends the same mode flags as `./scripts/ynn-run` and delegates to `./youtube_notion_notes/ingest.py`.

### `./youtube_notion_notes/services/pipeline.py`

Owns the current pipeline orchestration while preserving the existing CLI contract:

- transcript fetching;
- local transcript and prompt file writing;
- optional note generation;
- optional Notion export branching;
- JSON result shaping for pipeline success and pipeline failures.

### `./youtube_notion_notes/services/transcript.py`

Responsible only for YouTube URLs, video IDs, and transcript fetching.

### `./youtube_notion_notes/services/note_generator.py`

Responsible for turning a transcript into a note.

Owns the default manual prompt template as package data at `./youtube_notion_notes/services/resources/comprehensive_note.md`, loaded through `importlib.resources` so installed/editable commands do not depend on the current working directory containing `./prompts/comprehensive_note.md`.

It should support multiple modes:

- OpenAI API;
- manual mode;
- future Ollama or local model mode.

### `./youtube_notion_notes/services/notion.py`

Responsible for creating Notion pages and appending blocks.

### `./youtube_notion_notes/services/markdown_to_notion.py`

Converts markdown into basic Notion blocks.

Supported markdown shapes are intentionally simple:

- headings;
- paragraphs;
- bullets;
- numbered lists;
- quotes;
- code blocks.

### `./youtube_notion_notes/services/note_metadata.py`

Extracts metadata from a markdown note for Notion export.

### `./youtube_notion_notes/services/notion_export.py`

Orchestrates Notion export on top of `./youtube_notion_notes/services/notion.py`, `./youtube_notion_notes/services/markdown_to_notion.py`, and metadata extraction.

### `./scripts/n8n-ingest.sh`

Small n8n-facing wrapper that calls `./ingest.py` through the JSON stdin/stdout contract and verifies that stdout is valid JSON.

### `./scripts/ynn-run`

Small repo-local launcher used by daily shell commands. It changes to the repository root before calling `./ingest.py`, uses `./.venv/bin/python` when present, and falls back to `python` otherwise.

### `./scripts/install-launchers.sh`

One-time local installer that creates `ynn`, `ynn-note`, `ynn-notion`, and `ynn-prompt` wrappers in `~/.local/bin`. These wrappers point back to the repo-local `./scripts/ynn-run` by absolute path.

---

# 5. Current CLI and Automation Contracts

These contracts are current behavior and should stay in `./design-doc.md` even when completed milestone history moves to archive docs.

## Platform Support Contract

For `v1.0.0`, WSL/Linux is the primary supported path. Windows via WSL is the recommended Windows path because it uses the same Linux-style setup and shell workflow. macOS is expected to work and likely supported, but should be smoke-tested separately before claiming strong support. Native Windows PowerShell is best-effort and partial: direct Python CLI usage and editable package console entrypoints may work when Python is installed on Windows, but repo-local shell launchers, bash wrappers, make-based workflows, and Unix-style environment examples are not the primary supported path.

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

These daily command names are part of local MVP usability. For `v1.0.0`, editable installs expose them as console script entrypoints:

```bash
ynn "https://www.youtube.com/watch?v=..."
ynn-note "https://www.youtube.com/watch?v=..."
ynn-notion "https://www.youtube.com/watch?v=..."
ynn-prompt "https://www.youtube.com/watch?v=..."
```

Repo-local launcher scripts remain supported as thin wrappers over the existing direct CLI contract.

Repo-local launcher behavior:

- `ynn` calls `python ./ingest.py "URL"`;
- `ynn-note` calls `python ./ingest.py "URL" --export local`;
- `ynn-notion` calls `python ./ingest.py "URL" --export notion`;
- `ynn-prompt` calls `python ./ingest.py "URL" --no-note`.

The launcher layer must not change pipeline behavior, the JSON input/output contract, or n8n behavior.

## Installed CLI Package Contract

Local editable installs expose the packaged CLI entrypoints:

```bash
python -m pip install -e .
```

The installed console script names match the repo-local launcher names:

```bash
ynn "https://www.youtube.com/watch?v=..."
ynn-note "https://www.youtube.com/watch?v=..."
ynn-notion "https://www.youtube.com/watch?v=..."
ynn-prompt "https://www.youtube.com/watch?v=..."
```

Installed entrypoint behavior:

- `ynn` delegates to the packaged ingest CLI implementation with `"URL"`;
- `ynn-note` delegates to the packaged ingest CLI implementation with `"URL" --export local`;
- `ynn-notion` delegates to the packaged ingest CLI implementation with `"URL" --export notion`;
- `ynn-prompt` delegates to the packaged ingest CLI implementation with `"URL" --no-note`.

`./ingest.py` remains the direct CLI contract, repo-local launcher scripts remain supported, and installed entrypoints must preserve pipeline behavior, JSON input/output contracts, n8n behavior, and Notion export behavior.

## Runtime Path Policy

Output policy:

- output root resolution order is explicit `--output-dir PATH`, then `YNN_OUTPUT_DIR`, then `./output` relative to the current working directory;
- `--output-dir PATH` wins over `YNN_OUTPUT_DIR`;
- if neither `--output-dir` nor `YNN_OUTPUT_DIR` is set, the compatibility default remains `./output` relative to the current working directory;
- when an output root is selected, transcript, prompt, and note files are written under `OUTPUT_ROOT/transcripts/`, `OUTPUT_ROOT/prompts/`, and `OUTPUT_ROOT/notes/`;
- output paths returned in JSON output mode reflect the actual filesystem paths used;
- `output_dir` is not part of the JSON input schema.

Note: For daily installed CLI usage, `YNN_OUTPUT_DIR` is the recommended persistent output root. The `./output` fallback exists for backward compatibility and simple local runs.

Env-file policy:

- runtime config priority is explicit `--env-file PATH`, then real process environment variables, then cwd `./.env`, then user config `~/.config/youtube-notion-notes/.env`, then built-in defaults;
- explicit `--env-file PATH` values override matching real process environment variables for that run;
- cwd `./.env` still participates below real process environment variables and above user config;
- user config fills missing values only;
- missing cwd `./.env` and missing user config do not fail;
- an explicit `--env-file PATH` must exist or the CLI returns a clean input error;
- `env_file` is not part of the JSON input schema.

## Prompt Template Resource Contract

Prompt template policy:

- the default prompt template lives at `./youtube_notion_notes/services/resources/comprehensive_note.md`;
- `./pyproject.toml` includes the markdown template as package data for `youtube_notion_notes.services`;
- `./youtube_notion_notes/services/note_generator.py` loads the default template with standard-library `importlib.resources`;
- `build_manual_prompt` still accepts an explicit template path for tests or future use;
- `./youtube_notion_notes/services/pipeline.py` uses the package-owned default template and no longer passes a cwd-relative `./prompts/comprehensive_note.md` path.

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
- Notion page details when Notion export runs;
- additive `transcript_selection` metadata when known.

`transcript_selection` includes:

- `origin`;
- `source_language`;
- `selected_language`;
- `requires_translation`;
- `selection_reason`.

`notion_page_url` comes from the Notion API page response `url` field and is included only when that field is present.

Failure output includes:

- `ok: false`;
- `stage`;
- `error`.

Current pipeline failure stages include `transcript`, `prompt_template`, and `notion_export`.
Input errors use the `input` stage.

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
- transcript-file input bypasses YouTube discovery and selection and reports `origin: transcript_file` in `transcript_selection`;
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
OPENAI_API_KEY=...
NOTION_API_KEY=...
NOTION_DATABASE_ID=...
```

For generated-note Notion export, `OPENAI_API_KEY` is required because Notion export depends on a generated markdown note. Missing `OPENAI_API_KEY` remains a non-error for local/manual modes.

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
- `./youtube_notion_notes/services/notion.py` allows empty tags so it can stay a small reusable Notion adapter.

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

Detailed completed milestone and slice history lives in `./docs/archive/milestone-history.md`. That archive is historical context only and is not current source of truth. Current release state is summarized in section 1.

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

Read `./docs/decisions.md` before changing pipeline ownership, automation boundaries, transcript acquisition boundaries, generation paths, Notion export shape, or transcript selection policy.

## Future Options

Backlog themes currently parked in `./docs/ideas.md` include:

- long-video handling;
- n8n orchestration improvements;
- transcript input and provider expansion;
- hosted, remote, or HTTP execution options;
- post-`v1.0.0` packaging polish if release review finds gaps.

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
