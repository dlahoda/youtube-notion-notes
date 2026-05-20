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

Current day-to-day local usage goes through global launcher commands installed into the user's shell:

```bash
ynn "https://www.youtube.com/watch?v=..."
ynn-note "https://www.youtube.com/watch?v=..."
ynn-notion "https://www.youtube.com/watch?v=..."
ynn-prompt "https://www.youtube.com/watch?v=..."
```

These repo-local launchers remain thin wrappers over this repository. `./ingest.py` is still the underlying direct CLI contract for fallback use, tests, local development, n8n, and packaging work.

Current roadmap:

- Milestone 1 is complete: local transcript and markdown note.
- Milestone 2 is complete and tagged `v0.2.0`: opt-in Notion export.
- Milestone 3 is complete and tagged `v0.3.0`: local CLI automation contract.
- Milestone 4 is complete and tagged `v0.4.0`: n8n integration contract and smoke workflow.
- Milestone 5 is complete and tagged `v0.5.0`: pipeline core refactor.
- Milestone 6 is complete and tagged `v0.6.0`: transcript fallback input.
- Milestone 7 Slice 1 is complete and tagged `v0.7.0`: JSON transcript-file fallback input.
- Milestone 8 Slice 1 is complete and tagged `v0.8.0`: ingest CLI tests split by responsibility.
- Milestone 9 is complete and tagged `v0.9.0`: repo-local launcher usability closeout.
- `v1.0.0` Slice 1 is complete: minimal installable CLI packaging skeleton and console script entrypoints for local editable installs.
- `v1.0.0` Slice 2 is complete: runtime output/config path policy for repo-local and editable-installed CLI usage.
- `v1.0.0` Slice 3 is complete: package data and prompt template resource handling.
- `v1.0.0` Slice 4.2 is complete: service modules moved under `./youtube_notion_notes/services/` with internal service imports and service tests migrated.
- `v1.0.0` Slice 4.3 is complete: CLI implementation modules moved under `./youtube_notion_notes/` while top-level compatibility wrappers remain.
- `v1.0.0` Slice 4.4 is complete: package data handling for `comprehensive_note.md` was verified after the services move, including editable-install smoke coverage from a non-repo cwd.
- `v1.0.0` Slice 4.5 is complete: console script entrypoints point at package modules and transitional top-level `py-modules` packaging has been removed.
- `v1.0.0` UX-1 is complete: Notion export config preflight fails before transcript, prompt, note, or Notion work when required config is incomplete.
- `v1.0.0` UX hardening planning is active: the approved goal is to make installed CLI usage predictable after one setup path: install -> init/config -> use.
- `v1.0.0` UX-3 Slice 1 is complete: `ynn init --output-dir PATH` creates or updates the user config fallback, and runtime config loading follows the UX-2 source priority contract.
- `v1.0.0` UX-3 Slice 2 is complete: `ynn init --output-dir PATH` can optionally collect missing OpenAI and Notion config values interactively while preserving existing user config values.
- `v1.0.0` UX-3 transcript language follow-up is complete: `ynn init --output-dir PATH` can optionally append `YOUTUBE_TRANSCRIPT_LANGUAGES` to the user config while preserving runtime fallback to `en` when no language config is provided.
- `v1.0.0` UX-5 is complete: release readiness checks were manually run and passed.
- `v1.0.0` UX-6 Slice 1 is complete: transcript track discovery metadata can be listed internally without changing default transcript fetching behavior.
- `v1.0.0` UX-6 Slice 2 is complete: transcript track selection policy can choose from discovered metadata internally without changing default transcript fetching behavior.
- `v1.0.0` UX-6 Slice 2.1 is complete: unknown-origin transcript tracks are last-resort selection fallbacks after known manual and generated matches.
- `v1.0.0` UX-6 Slice 3 is complete: transcript selection runtime visibility and failure contracts are documented.
- `v1.0.0` UX-6 Slice 4 is complete: normal YouTube transcript fetching uses project-owned discovery and selection before fetching the selected track.
- `v1.0.0` UX-6 Slice 5 is complete: transcript selection metadata is visible in concise human output and additive JSON output.
- `v1.0.0` public repository release gate is deferred until numbered UX work is closed: publishing should use an All Rights Reserved / source-visible licensing posture unless a different license is explicitly decided later.

Completed `v1.0.0` packaging slices:

- Slice 1: minimal packaging skeleton and console script entrypoints. Complete.
- Slice 2: output/config path policy for installed CLI runtime behavior. Complete.
- Slice 3: package data and prompt template resource handling. Complete.
- Slice 4: proper package layout using the real import package `youtube_notion_notes`.
  Slice 4 replaces the temporary flat-repo packaging shape from Slice 1. Slice 4.2 moved service modules into `youtube_notion_notes.services`. Slice 4.3 moved CLI implementation modules into `youtube_notion_notes` while keeping top-level compatibility wrappers. Slice 4.4 verified package data handling for `comprehensive_note.md` after the services move. Slice 4.5 moved console scripts to `youtube_notion_notes.ynn_cli:*` and removed transitional top-level `py-modules` packaging.

Active `v1.0.0` UX hardening plan:

The approved UX milestone goal is to make the installed CLI predictable from any directory after one setup path:

```text
install
-> init/config
-> use
```

`ynn init` is included in `v1.0.0` scope. This section records both implemented behavior and remaining planned UX hardening work.

Milestone-level boundaries for UX hardening:

- no web UI;
- no new n8n behavior;
- no new Notion behavior beyond config validation needed for predictable Notion export;
- no runtime code, tests, or packaging config changes in the docs-only planning slice;
- no README restructure that presents future UX behavior as already implemented.

UX-1 -- Notion fail-fast: Complete.

- `--export notion` and `ynn-notion` should fail before transcript fetching, OpenAI calls, or Notion calls if required config is incomplete.
- For generated-note Notion export in the `v1.0.0` UX contract, `ynn-notion` requires `OPENAI_API_KEY`, `NOTION_API_KEY`, and `NOTION_DATABASE_ID`.
- Local and manual modes must not become strict.
- Missing `OPENAI_API_KEY` remains a non-error for `ynn`, `ynn-note`, and `ynn-prompt`.
- The implementation slice should keep human and JSON failure output clean and predictable.

UX-2 -- `ynn init` config contract design: Complete docs-only planning.

This UX-2 slice documented the planned config contract before UX-3 implementation.

Current behavior includes the UX-3 Slice 1 runtime config priority: the CLI can read an explicit `--env-file PATH`, real process environment variables, cwd `./.env`, the user config fallback at `~/.config/youtube-notion-notes/.env`, and built-in defaults.

UX-2/UX-3 config source priority:

1. explicit `--env-file PATH`;
2. real process environment variables;
3. cwd `./.env`;
4. user config `~/.config/youtube-notion-notes/.env`;
5. built-in defaults.

Priority semantics:

- explicit `--env-file PATH` is the highest-priority config source for that run;
- values loaded from an explicit `--env-file PATH` should override matching real process environment variables;
- real process environment variables should override cwd `./.env`, user config, and built-in defaults;
- cwd `./.env` should override user config and built-in defaults;
- user config is the installed CLI fallback created by `ynn init`;
- built-in defaults are used only when no higher-priority source provides a value.

User config file contract:

- the preferred user config path is `~/.config/youtube-notion-notes/.env`;
- the file is a plain dotenv text file;
- manual editing of this file is officially supported;
- no new config file format is introduced in this slice.

`ynn init` role:

- `ynn init` is a setup helper, not the only supported way to manage config;
- users may still use process environment variables, cwd `./.env`, explicit `--env-file PATH`, or manual edits to the user config file;
- `ynn init` should create or update the user config file so installed CLI usage is predictable from any directory.

Re-run and overwrite behavior:

- the first run should create `~/.config/youtube-notion-notes/.env` if it does not exist;
- re-running `ynn init` should not silently overwrite existing secret values;
- if the user config file already exists, `ynn init` should preserve existing values by default;
- a future implementation may support explicit overwrite or update behavior;
- silent destructive overwrite is out of scope.

Secrets:

- secrets are stored as plain text in the local user config file for the MVP;
- users should not commit this file;
- this is acceptable for the local MVP, but it is not a production secret-management story.

Output directory config contract:

- `YNN_OUTPUT_DIR` may be stored in the user config file;
- explicit `--output-dir PATH` remains the highest-priority output directory override;
- process environment `YNN_OUTPUT_DIR` remains above config-file fallback behavior unless the command uses an explicit `--env-file PATH`, which intentionally overrides matching process environment values according to the UX-2 config priority contract;
- default output remains `./output` relative to cwd when no output setting is provided;
- `ynn init` may create the configured output directory when the user chooses or accepts an output path;
- output directory creation should be idempotent, preserving existing directories;
- `ynn init` must not delete, clean, or move existing output files;
- parent directory creation is allowed for the selected output path;
- regular pipeline runs keep creating `transcripts/`, `prompts/`, and `notes/` under the resolved output root as needed.

UX-2 boundaries:

- no implementation;
- no runtime code changes;
- no test changes;
- no packaging config changes;
- no README restructure;
- no n8n behavior changes;
- no Notion behavior changes beyond documenting config requirements already introduced by UX-1;
- no new config file format beyond dotenv.

UX-3 -- `ynn init` implementation: Active; Slices 1, 2, and transcript language follow-up complete.

- Add an installed CLI setup command only after the config contract is documented.
- The desired installed CLI flow is:

```bash
python -m pip install -e .
ynn init --output-dir ~/ynn-output
ynn-prompt "https://www.youtube.com/watch?v=..."
ynn-note "https://www.youtube.com/watch?v=..."
ynn-notion "https://www.youtube.com/watch?v=..."
```

UX-3 Slice 1:

- `ynn init --output-dir PATH` creates or updates `~/.config/youtube-notion-notes/.env`;
- existing user config values are preserved by default;
- `YNN_OUTPUT_DIR` is added only when it is not already present;
- `~` in the provided output path is expanded before writing;
- the configured output directory is created idempotently;
- runtime config loading follows the UX-2 priority contract.

UX-3 Slice 2:

- after configuring the output directory, `ynn init --output-dir PATH` prompts for optional `OPENAI_API_KEY`, `NOTION_API_KEY`, and `NOTION_DATABASE_ID`;
- empty prompt input skips that value;
- existing user config values are preserved by default and are not duplicated;
- missing provided values are appended to the existing dotenv file;
- API key prompts use hidden input;
- manual editing of the user config dotenv file remains supported;
- runtime config priority remains unchanged;
- `ynn init` does not call OpenAI or Notion and does not validate keys.

UX-3 transcript language follow-up:

- `ynn init --output-dir PATH` prompts for optional transcript language preferences as `YOUTUBE_TRANSCRIPT_LANGUAGES`;
- the prompt makes the runtime default clear as `Transcript languages [en]: `;
- empty prompt input skips writing `YOUTUBE_TRANSCRIPT_LANGUAGES`;
- existing `YOUTUBE_TRANSCRIPT_LANGUAGES` values are preserved and not duplicated;
- runtime fallback remains `en` when no language config is provided;
- runtime config priority and pipeline behavior remain unchanged.

UX-4 -- README command/setup contract:

- After UX-1 and UX-3 behavior exists, restructure `./README.md` around what this does, platform support, recommended installed CLI setup, first run, daily commands, command requirements and expected outcomes, repo-local/developer/fallback usage, automation/n8n notes, and limitations.
- Add a command requirements table.
- Explain `ynn-prompt` clearly: it builds the ChatGPT-ready prompt file and stops. It does not call OpenAI and does not create a Notion page.
- Do not restructure `./README.md` as if the UX work is already implemented before the corresponding runtime behavior exists.

UX-5 -- Release readiness check: Complete.

The following release readiness checks were manually run and passed:

- `make test`;
- editable-install smoke test;
- manual `ynn-prompt` smoke;
- manual `ynn-notion` config failure smoke.

UX-6 -- Transcript selection quality: Active; Slices 1, 2, 2.1, 3, 4, and 5 complete.

- Current normal YouTube transcript fetching inspects available transcript tracks and chooses the best available track by origin and quality before fetching transcript snippets.
- A narrow language-preference fetch fallback may remain only for older `youtube-transcript-api` shapes where transcript discovery is not available.
- Slice 1 adds only the internal transcript track discovery contract.
- Slice 1 keeps `fetch_transcript(video_id, languages)` behavior unchanged.
- Slice 1 adds project-owned transcript track metadata structures near `./youtube_notion_notes/services/transcript.py`.
- Slice 1 can list available transcript tracks through `youtube-transcript-api` and normalize available language code, language name, generated/manual status, translatability, and translation language metadata.
- Slice 1 does not add CLI flags, JSON output fields, README instructions, Notion behavior, n8n behavior, or automatic best-track selection.
- Slice 2 adds only the internal transcript track selection policy.
- Slice 2 keeps `fetch_transcript(video_id, languages)` behavior unchanged.
- Slice 2 can choose from discovered `TranscriptTrack` metadata by origin, direct language match, translation language match, and preferred language order.
- Slice 2 returns the selected track plus selection metadata, or no selection when no track matches the policy.
- Slice 2 does not connect selection to CLI flags, JSON output, README instructions, Notion behavior, n8n behavior, or automatic best-track fetching.
- Slice 2.1 makes unknown-origin tracks a last-resort fallback instead of ignoring them completely.
- Slice 2.1 keeps unknown-origin tracks lower priority than known manual or generated tracks.
- Current internal selection priority:
  1. manual/author-provided transcript in preferred languages;
  2. manual/author-provided transcript translated to a preferred language;
  3. generated transcript in preferred languages;
  4. generated transcript translated to a preferred language;
  5. unknown-origin transcript in preferred languages;
  6. unknown-origin transcript translated to a preferred language.
- Original spoken language detection is future best-effort only.
- Do not require YouTube Data API, OAuth, `captions.list`, or quota-dependent behavior for `v1.0.0`.
- Slice 4 connects discovery and selection metadata to normal runtime YouTube transcript fetching.
- Slice 4 keeps `--transcript-file` behavior as a bypass of YouTube track discovery and selection.
- Slice 4 keeps the existing transcript object shape for downstream prompt and note generation.
- Slice 5 exposes project-owned transcript selection metadata without changing selection priority or adding CLI flags.
- Slice 5 adds concise human output when the transcript source is known.
- Slice 5 adds an additive JSON result field named `transcript_selection`.
- Slice 5 keeps existing JSON fields valid and keeps `--transcript-file` as a bypass of YouTube discovery and selection.

UX-6 Slice 3 -- Transcript selection runtime visibility contract: Complete docs-only.

This slice defined the runtime visibility contract before connecting the UX-6 selection policy to transcript fetching.

Historical behavior before Slice 4:

- runtime transcript fetching remains unchanged;
- discovery and selection metadata are not yet connected to CLI fetching;
- no new human output line or JSON metadata field exists yet.

Human output visibility contract:

- when runtime selection is later connected, human CLI output should show one short transcript selection line;
- the line should be concise and useful for debugging;
- example shape: `Transcript selected: manual Spanish -> English`;
- the line should not be noisy during normal successful runs;
- the line should not expose low-level `youtube-transcript-api` object names, exception classes, or other library internals.

JSON output metadata contract:

- JSON changes must be additive only so existing automation and n8n consumers keep working;
- existing JSON fields must remain valid;
- add one compact metadata field, preferably `transcript_selection`;
- `transcript_selection` should include enough information to debug runtime selection:
  - `origin`: `manual`, `generated`, `unknown`, or `transcript_file`;
  - `source_language`;
  - `selected_language`;
  - `requires_translation`;
  - `selection_reason`.

Failure behavior contract:

- if transcript track discovery fails during future runtime selection, fail cleanly in the transcript stage;
- if discovery succeeds but no track matches the policy, fail cleanly in the transcript stage;
- when available, no-match errors should include available language codes without dumping raw library internals;
- human output should stay short and actionable;
- JSON failure output should stay structured and keep the existing failure envelope valid;
- Notion export and note generation must not be responsible for transcript selection failures.

`--transcript-file` behavior:

- manual transcript-file mode should bypass YouTube track discovery and selection;
- transcript-file metadata should use `origin: transcript_file`;
- transcript-file mode should preserve the original URL as source metadata for prompt and note generation.

Slice 3 boundaries:

- docs-only;
- no runtime fetching behavior change;
- no code changes;
- no test changes;
- no CLI flags;
- no README changes that present future behavior as current;
- no Notion or n8n behavior changes;
- no open-source licensing changes;
- runtime wiring happened in UX-6 Slice 4.

UX-FINAL -- Public repository licensing gate: Deferred until numbered UX items are closed.

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

The `v0.9.0` MVP is repo-local. The launcher commands make that repo-local workflow comfortable for daily use. `v1.0.0` began by turning the same command names into installable package entrypoints through small slices, then hardens the installed CLI setup path so daily use is predictable from any directory.

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

Daily local launcher commands are part of local MVP usability. They call back into this repository and remain thin wrappers over the existing direct CLI contract:

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

The launcher layer must not change pipeline behavior, the JSON input/output contract, or n8n behavior.

## Installable CLI Package Slice 1

`v1.0.0` Slice 1 added a minimal Python packaging layer for local editable installs:

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

Slice 1 boundaries:

- `./ingest.py` remains the direct CLI contract;
- repo-local launcher scripts remain supported;
- no pipeline behavior changes;
- no JSON input/output changes;
- no n8n behavior changes;
- no Notion export behavior changes;
- no output directory policy changes;
- no `.env` loading policy changes;
- no prompt template package-resource handling;
- no `src/` layout or full package refactor.

## Runtime Path Policy Slice 2

`v1.0.0` Slice 2 made output and env-file behavior explicit for both repo-local CLI usage and editable-installed console script usage, without changing pipeline behavior.

Output policy:

- output root resolution order is explicit `--output-dir PATH`, then `YNN_OUTPUT_DIR`, then `./output` relative to the current working directory;
- `--output-dir PATH` wins over `YNN_OUTPUT_DIR`;
- if neither `--output-dir` nor `YNN_OUTPUT_DIR` is set, the compatibility default remains `./output` relative to the current working directory;
- when an output root is selected, transcript, prompt, and note files are written under `OUTPUT_ROOT/transcripts/`, `OUTPUT_ROOT/prompts/`, and `OUTPUT_ROOT/notes/`;
- output paths returned in JSON output mode reflect the actual filesystem paths used;
- `output_dir` is not part of the JSON input schema in this slice.

Note: For daily installed CLI usage, `YNN_OUTPUT_DIR` is the recommended persistent output root. The `./output` fallback exists for backward compatibility and simple local runs.

Env-file policy:

- runtime config priority is explicit `--env-file PATH`, then real process environment variables, then cwd `./.env`, then user config `~/.config/youtube-notion-notes/.env`, then built-in defaults;
- explicit `--env-file PATH` values override matching real process environment variables for that run;
- cwd `./.env` still participates below real process environment variables and above user config;
- user config fills missing values only;
- missing cwd `./.env` and missing user config do not fail;
- an explicit `--env-file PATH` must exist or the CLI returns a clean input error;
- `env_file` is not part of the JSON input schema in this slice.

Slice 2 boundaries:

- no JSON input/output schema changes;
- no n8n behavior changes;
- no Notion export behavior changes;
- no transcript fetching behavior changes;
- no note generation behavior changes;
- no `src/` layout or package refactor.

## Package Data Prompt Template Slice 3

`v1.0.0` Slice 3 moved the built-in manual prompt template into package-owned data while preserving the existing CLI behavior and output contracts.

Prompt template policy:

- the default prompt template lives at `./youtube_notion_notes/services/resources/comprehensive_note.md`;
- `./pyproject.toml` includes the markdown template as package data for `youtube_notion_notes.services`;
- `./youtube_notion_notes/services/note_generator.py` loads the default template with standard-library `importlib.resources`;
- `build_manual_prompt` still accepts an explicit template path for tests or future use;
- `./youtube_notion_notes/services/pipeline.py` uses the package-owned default template and no longer passes a cwd-relative `./prompts/comprehensive_note.md` path.

Slice 3 boundaries:

- no CLI behavior changes;
- no JSON input/output schema changes;
- no n8n behavior changes;
- no Notion export behavior changes;
- no output directory or env-file behavior changes;
- no custom prompt selection, prompt profiles, prompt env vars, or prompt CLI flag;
- no `src/` layout or package refactor.

## Package Layout Planning Slice 4.1

`v1.0.0` Slice 4.1 is a docs-only planning slice for replacing the transitional flat-repo packaging shape with a real package layout. It must not move files, change imports, update runtime behavior, or change `./pyproject.toml` entrypoints.

Target package layout:

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
  tests/
```

Target import map:

- `./ingest.py` becomes a compatibility wrapper around `youtube_notion_notes.ingest.main`;
- `./ynn_cli.py` becomes a compatibility adapter around `youtube_notion_notes.ynn_cli`;
- `./services/pipeline.py` moves to `./youtube_notion_notes/services/pipeline.py`;
- `./services/note_generator.py` moves to `./youtube_notion_notes/services/note_generator.py`;
- all internal imports move from `services.*` to `youtube_notion_notes.services.*`;
- the lazy Notion export import inside pipeline moves from `services.notion_export` to `youtube_notion_notes.services.notion_export`;
- console scripts point to `youtube_notion_notes.ynn_cli:*`;
- tests that exercise real package modules should import `youtube_notion_notes.*`, not only the top-level wrappers.

Compatibility policy for `./ingest.py`:

- `./ingest.py` remains the long-term compatibility wrapper for direct CLI, n8n, tests, local fallback usage, and existing repo-local launchers;
- `python ./ingest.py ...` must preserve the current human CLI behavior, JSON input/output contract, output-dir policy, env-file policy, transcript-file behavior, and Notion behavior;
- after the package move, real CLI implementation should live in `./youtube_notion_notes/ingest.py`, with `./ingest.py` delegating without adding behavior;
- do not create a long-term top-level `services` compatibility package to support old internal imports.

Compatibility policy for `./ynn_cli.py`:

- top-level `./ynn_cli.py` is a migration compatibility adapter for the current editable install entrypoints and tests;
- after console script entrypoints point to `youtube_notion_notes.ynn_cli`, all real wrapper behavior should live in `./youtube_notion_notes/ynn_cli.py`;
- direct behavior of `ynn`, `ynn-note`, `ynn-notion`, and `ynn-prompt` must stay unchanged while the adapter exists;
- `./ynn_cli.py` is not the long-term implementation module once package entrypoints have migrated.

n8n wrapper compatibility policy:

- `./scripts/n8n-ingest.sh` should keep calling `python ./ingest.py --input-json-file - --output json` unless there is a separately justified reason to change it;
- the wrapper must continue to accept JSON on stdin, return valid JSON on stdout, validate stdout JSON, and allow valid `ok: false` CLI results to reach n8n;
- n8n must continue to depend on the Python CLI boundary, not on package internals.

Import migration strategy:

- migrate internal imports fully to `youtube_notion_notes.services.*`;
- avoid dual import paths inside runtime code;
- move tests in the same slice as their corresponding runtime module so mocks and patches target the active import path;
- keep wrapper-focused tests small and explicit so they prove compatibility without accidentally becoming the only coverage;
- add or adjust package-module tests so failures in `youtube_notion_notes.ingest`, `youtube_notion_notes.ynn_cli`, and `youtube_notion_notes.services.*` are visible even if top-level wrappers still work.

Package data strategy after moving services:

- move the built-in template from `./services/resources/comprehensive_note.md` to `./youtube_notion_notes/services/resources/comprehensive_note.md`;
- keep the default template loaded through `importlib.resources`, not cwd-relative paths;
- update the moved note generator module after the move to read from package `youtube_notion_notes.services`;
- update `./pyproject.toml` package data from `services = ["resources/*.md"]` to package data for `youtube_notion_notes.services`;
- keep explicit `template_path` support in `build_manual_prompt` for tests and future use;
- preserve installed and editable package behavior when the current working directory does not contain prompt files.

Proposed Slice 4.2-4.5 boundaries:

- Slice 4.2: create ./youtube_notion_notes/ package skeleton and move ./services/ into ./youtube_notion_notes/services/, migrate internal service imports and service tests. Complete.
- Slice 4.3: move CLI implementation into ./youtube_notion_notes/ingest.py and ./youtube_notion_notes/ynn_cli.py while keeping top-level ./ingest.py and ./ynn_cli.py as wrappers. Complete.
- Slice 4.4: verify package data handling for comprehensive_note.md after the services move, clean up any remaining transitional package-data assumptions, and smoke-test editable install from a non-repo cwd. Complete.
- Slice 4.5: update console script entrypoints, clean py-modules/packages transitional packaging, and update editable-install smoke docs. Complete.

Affected tests:

- `./tests/test_ingest_cli.py`, `./tests/test_pipeline.py`, `./tests/test_note_generator.py`, `./tests/test_notion_export.py`, `./tests/test_notion.py`, `./tests/test_markdown_to_notion.py`, and `./tests/test_note_metadata.py` now import and patch `youtube_notion_notes.services.*`.
- `./tests/test_ingest_input.py` imports `youtube_notion_notes.ingest` for real CLI module coverage and imports `PipelineRequest` from `youtube_notion_notes.services.pipeline`.
- `./tests/test_ynn_cli.py` imports `youtube_notion_notes.ynn_cli` for real launcher adapter coverage.
- `./tests/test_cli_wrappers.py` keeps small compatibility checks for top-level `./ingest.py` and `./ynn_cli.py`.

Risks and guardrails:

- Tests may accidentally keep testing top-level wrappers instead of the real package modules after CLI code moves.
- Tests that patch `sys.modules` or fake `services.notion_export` must migrate to the new `youtube_notion_notes.services.*` module paths.
- The built-in prompt template must remain package data after moving from `./services/resources/comprehensive_note.md` to `./youtube_notion_notes/services/resources/comprehensive_note.md`.
- `./scripts/n8n-ingest.sh` should keep calling `python ./ingest.py --input-json-file - --output json` unless there is a separately justified reason to change it.
- Do not create a long-term top-level `services` compatibility package. Migrate internal imports fully.
- `./ingest.py` remains the long-term compatibility wrapper for direct CLI, n8n, tests, and local fallback usage.
- `./pyproject.toml` changes should land only in implementation slices, not in Slice 4.1.
- Package layout work must preserve direct CLI behavior, JSON input/output contracts, n8n wrapper behavior, Notion behavior, output-dir policy, env-file policy, and prompt template package-data behavior.

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
- Milestone 5: Pipeline core refactor — complete and tagged `v0.5.0`. Pipeline orchestration lives in `./youtube_notion_notes/services/pipeline.py` behind `PipelineRequest`.
- Milestone 6: Transcript fallback input — complete and tagged `v0.6.0`. Human CLI usage supports local UTF-8 transcript files.
- Milestone 7: JSON transcript fallback input — Slice 1 complete and tagged `v0.7.0`. JSON input supports the same local transcript-file fallback.
- Milestone 8: Test suite maintenance — Slice 1 complete and tagged `v0.8.0`. Ingest CLI tests are split by responsibility without runtime behavior changes.
- Milestone 9: Repo-local launcher usability closeout — complete and tagged `v0.9.0`. Day-to-day MVP usage works through `ynn`, `ynn-note`, `ynn-notion`, and `ynn-prompt` while `./ingest.py` remains the underlying CLI contract.
- `v1.0.0` Slice 1: minimal installable CLI packaging entrypoints for local editable installs — complete.
- `v1.0.0` Slice 2: runtime output/config path policy for repo-local and editable-installed CLI usage — complete.
- `v1.0.0` Slice 3: package data and prompt template resource handling — complete.
- `v1.0.0` Slice 4.2: service package move into `youtube_notion_notes.services` — complete.
- `v1.0.0` Slice 4.3: CLI package module move into `youtube_notion_notes.ingest` and `youtube_notion_notes.ynn_cli` — complete.
- `v1.0.0` Slice 4.4: package data verification after the services move — complete.
- `v1.0.0` Slice 4.5: package console script entrypoint cleanup — complete.

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
