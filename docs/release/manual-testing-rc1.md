# v1.0.0-rc.1 Manual Smoke Plan

## Purpose

Provide a practical release-candidate smoke plan for `v1.0.0-rc.1`. This is release-maintenance documentation for a solo developer, not a full QA matrix.

## Scope

Primary platform:

- WSL/Linux.

Optional smoke only:

- macOS.

Core stages:

- installed CLI setup and config;
- prompt-only output without OpenAI or Notion;
- local note generation with OpenAI config;
- output root precedence;
- transcript-file fallback;
- Notion missing-config fail-fast;
- Notion happy path;
- JSON success and failure behavior.

## Out of Scope

- Native Windows PowerShell as a core RC blocker.
- Full command, option, install-mode, and platform matrix.
- Production n8n workflow validation.
- New Notion or n8n behavior.
- Runtime code or CLI behavior changes.
- Long-video chunking, Whisper, alternate transcript providers, web UI, queueing, or hosted execution.

## Test Data and Setup

Fill these in before starting:

- RC version: `v1.0.0-rc.1`
- Test date: `YYYY-MM-DD`
- Platform: `WSL/Linux`
- Python version: `python --version`
- Test video URL: `https://youtu.be/VIDEO_ID`
- Output root A: absolute path under the repo checkout, for example `$PWD/tmp/rc1-output-a` after `cd` to the repository root.
- Output root B: `./tmp/rc1-output-b`
- Explicit output root: `./tmp/rc1-output-explicit`
- Manual transcript file: `./tmp/rc1-manual-transcript.txt`
- Missing-config env file: `./tmp/rc1-missing-config.env`
- Notion test database: `<database name or id>`

Preflight:

- Use a non-production Notion database.
- Use a short public YouTube video with available captions.
- Keep generated files under temporary output roots.
- Do not commit secrets or generated output.
- Record or back up existing user config at `~/.config/youtube-notion-notes/.env`.
- `ynn init` may update `~/.config/youtube-notion-notes/.env`.
- Use absolute paths for `ynn init`; relative paths are okay for one-off explicit `--output-dir` smoke commands.
- For Stage 1, use a backed-up config without an existing `YNN_OUTPUT_DIR` if you need to verify the newly persisted value.
- Restore the original user config after the RC smoke if needed.

Suggested manual transcript fixture:

```text
This is a short local transcript fixture for v1.0.0-rc.1 manual testing.
It should bypass YouTube transcript discovery while still preserving the source URL.
```

## Ordered Stages

### 1. Install/config smoke

User journey covered:

- A developer installs the package in editable mode, confirms installed commands exist, and stores a persistent output root with `ynn init`.

Why it matters:

- `v1.0.0` depends on installed console scripts and user config working outside a repo-local launcher flow.

Steps:

```bash
python -m pip install -e .
ynn --help
ynn-prompt --help
ynn-note --help
ynn-notion --help
ynn init --output-dir "$PWD/tmp/rc1-output-a"
```

Check:

```bash
test -d "$PWD/tmp/rc1-output-a"
test -f ~/.config/youtube-notion-notes/.env
grep "^YNN_OUTPUT_DIR=$PWD/tmp/rc1-output-a$" ~/.config/youtube-notion-notes/.env
```

Expected result:

- Editable install completes.
- Installed command names are available.
- `ynn init --output-dir "$PWD/tmp/rc1-output-a"` creates the absolute output directory.
- User config can store an absolute `YNN_OUTPUT_DIR`.

Pass criteria:

- Installed command help checks run without command-not-found errors.
- User config exists and contains the configured absolute output root.
- The configured output directory exists.

Fail/blocker criteria:

- Editable install fails in a normal WSL/Linux environment.
- Any installed command is missing after install.
- `ynn init --output-dir` cannot create or persist the configured output root.

### 2. Prompt-only happy path

User journey covered:

- A user captures a transcript and prompt without OpenAI or Notion.

Why it matters:

- This is the minimal first successful path and should work without paid API setup.

Steps:

```bash
ynn-prompt "https://youtu.be/VIDEO_ID" --output-dir ./tmp/rc1-output-a
```

Expected result:

- Transcript output is created under `./tmp/rc1-output-a/transcripts/`.
- Prompt output is created under `./tmp/rc1-output-a/prompts/`.
- No markdown note is required.

Pass criteria:

- Transcript and prompt files exist and are non-empty.
- No OpenAI or Notion config is required.

Fail/blocker criteria:

- `ynn-prompt` requires OpenAI or Notion config.
- No transcript or prompt file is created for a video with available captions.
- Output is written outside the selected output root.

### 3. Local note happy path

User journey covered:

- A user generates a local markdown note with OpenAI config.

Why it matters:

- Local note generation is the main value path before optional Notion export.

Setup:

- Configure `OPENAI_API_KEY` through `ynn init`, process environment, cwd `./.env`, or explicit `--env-file`.
- Install optional OpenAI support if needed:

```bash
python -m pip install ".[openai]"
```

Steps:

```bash
ynn-note "https://youtu.be/VIDEO_ID" --output-dir ./tmp/rc1-output-a
```

Alternative:

```bash
ynn "https://youtu.be/VIDEO_ID" --output-dir ./tmp/rc1-output-a
```

Expected result:

- Transcript, prompt, and markdown note outputs are created.
- The markdown note is readable and structured.

Pass criteria:

- Files exist under `./tmp/rc1-output-a/transcripts/`, `./tmp/rc1-output-a/prompts/`, and `./tmp/rc1-output-a/notes/`.
- The note contains a clear H1 and organized markdown sections.

Fail/blocker criteria:

- OpenAI-configured local note generation fails for a normal short captioned video.
- The note is empty, unreadable, or saved outside `./tmp/rc1-output-a/notes/`.

### 4. Output root behavior

User journey covered:

- A user has `YNN_OUTPUT_DIR`, then overrides it for one run with `--output-dir`.

Why it matters:

- Output location predictability is central to installed CLI daily use and automation.

Steps:

```bash
YNN_OUTPUT_DIR=./tmp/rc1-output-b ynn-prompt "https://youtu.be/VIDEO_ID"
YNN_OUTPUT_DIR=./tmp/rc1-output-b ynn-prompt "https://youtu.be/VIDEO_ID" --output-dir ./tmp/rc1-output-explicit
```

Expected result:

- First run writes under `./tmp/rc1-output-b/transcripts/` and `./tmp/rc1-output-b/prompts/`.
- Second run writes under `./tmp/rc1-output-explicit/transcripts/` and `./tmp/rc1-output-explicit/prompts/`.
- `--output-dir` wins over `YNN_OUTPUT_DIR`.

Pass criteria:

- Files appear under the expected `transcripts/`, `prompts/`, and, when applicable, `notes/` directories.
- Explicit `--output-dir` output is not written to `YNN_OUTPUT_DIR`.

Fail/blocker criteria:

- `YNN_OUTPUT_DIR` is ignored when no `--output-dir` is provided.
- `--output-dir` does not override `YNN_OUTPUT_DIR`.
- Output subdirectory names are inconsistent with the documented contract.

### 5. Transcript-file fallback

User journey covered:

- A user provides a local UTF-8 transcript file when YouTube transcript fetching is unavailable or undesirable.

Why it matters:

- YouTube transcript fetching is the most fragile part of the system.

Setup:

```bash
mkdir -p ./tmp
printf '%s\n' 'This is a local transcript fixture for rc1.' > ./tmp/rc1-manual-transcript.txt
```

Steps:

```bash
python ingest.py "https://youtu.be/VIDEO_ID" --transcript-file ./tmp/rc1-manual-transcript.txt --no-note --output-dir ./tmp/rc1-output-a
```

Expected result:

- The local UTF-8 transcript file is used.
- YouTube transcript discovery is bypassed.
- Source URL remains required and preserved as source metadata.
- Transcript and prompt outputs are created.

Pass criteria:

- Saved transcript includes the fixture text.
- Human output or JSON metadata, when checked, indicates transcript-file input.
- Running without a URL is still rejected.

Fail/blocker criteria:

- The command attempts normal YouTube transcript discovery despite `--transcript-file`.
- The source URL becomes optional.
- A valid UTF-8 transcript fixture cannot produce transcript and prompt outputs.

### 6. Notion fail-fast

User journey covered:

- A user requests Notion export without required OpenAI or Notion config.

Why it matters:

- Notion export should fail cleanly before transcript fetching, OpenAI calls, or Notion calls when required config is missing.

Setup:

- Do not rely only on `env -u ...`. It removes process environment values, but it does not hide values loaded from cwd `./.env` or user config at `~/.config/youtube-notion-notes/.env`.
- Use an explicit temporary env file with blank required values so this test overrides process environment, cwd `./.env`, and user config:

```bash
mkdir -p ./tmp
printf '%s\n' \
  'OPENAI_API_KEY=' \
  'NOTION_API_KEY=' \
  'NOTION_DATABASE_ID=' \
  > ./tmp/rc1-missing-config.env
```

Steps:

```bash
ynn-notion "https://youtu.be/VIDEO_ID" --env-file ./tmp/rc1-missing-config.env --output-dir ./tmp/rc1-output-a
```

Alternative:

```bash
python ingest.py "https://youtu.be/VIDEO_ID" --export notion --env-file ./tmp/rc1-missing-config.env --output-dir ./tmp/rc1-output-a
```

Expected result:

- Command exits with a clean configuration/input error.
- No transcript fetching, OpenAI call, or Notion call is needed.
- No new transcript, prompt, note, or Notion page is created for this failing run.

Pass criteria:

- Error clearly names missing required config.
- Failure happens before any new output files or external calls for the run.

Fail/blocker criteria:

- Notion export begins transcript fetching or calls OpenAI/Notion before required config is present.
- Error is a traceback or otherwise unclear for a normal missing-config case.

### 7. Notion happy path

User journey covered:

- A configured user generates a local note and exports it to Notion.

Why it matters:

- Notion export is opt-in, but it is the full external integration path for the release.

Setup:

- Configure `OPENAI_API_KEY`, `NOTION_API_KEY`, and `NOTION_DATABASE_ID`.
- Use a Notion test database with required properties:
  - `Name`: title
  - `URL`: url
  - `Tags`: multi_select
  - `Status`: select
  - `Source`: select
  - `Created`: created_time

Steps:

```bash
ynn-notion "https://youtu.be/VIDEO_ID" --output-dir ./tmp/rc1-output-a
```

Expected result:

- Transcript, prompt, and markdown note are saved locally.
- A Notion page is created.
- Required properties are populated.
- Body blocks are present.

Pass criteria:

- Local markdown note exists under `./tmp/rc1-output-a/notes/`.
- Notion page has the expected source URL.
- `Status` is `Draft`.
- `Source` is `YouTube`.
- Tags are present when note metadata contains a `Tags:` line.
- Page body contains converted note content.

Fail/blocker criteria:

- Notion page is created without a local markdown note.
- Required Notion properties are not populated.
- Body blocks are missing for a generated note.
- Export fails against a database that matches the documented property contract.

### 8. JSON success

User journey covered:

- Automation receives valid JSON for a successful pipeline run.

Why it matters:

- n8n and other automation callers require stdout to contain only machine-readable JSON.

Steps:

```bash
python ingest.py "https://youtu.be/VIDEO_ID" --no-note --output json --output-dir ./tmp/rc1-output-a > ./tmp/rc1-success.json
python -m json.tool ./tmp/rc1-success.json
```

Optional Notion JSON success, if Notion happy path is configured:

```bash
python ingest.py "https://youtu.be/VIDEO_ID" --export notion --output json --output-dir ./tmp/rc1-output-a > ./tmp/rc1-notion-success.json
python -m json.tool ./tmp/rc1-notion-success.json
```

Expected result:

- stdout contains only valid JSON.
- Success JSON includes `ok`, `url`, `export_mode`, and created output paths.
- Notion details are included only when Notion export runs.

Pass criteria:

- `python -m json.tool` succeeds.
- `ok` is `true`.
- `url` matches the test URL.
- `export_mode` matches the requested mode.
- Output path fields point to files that exist.

Fail/blocker criteria:

- stdout contains human text mixed with JSON.
- Success JSON omits core fields.
- JSON output paths do not match actual filesystem output.

### 9. JSON failure

User journey covered:

- Automation receives valid JSON for input errors.

Why it matters:

- n8n branches on structured failure and should not scrape human error text.

Steps:

```bash
python ingest.py --input-json '{"url":"https://youtu.be/VIDEO_ID","unexpected":true}' --output json > ./tmp/rc1-failure.json
python -m json.tool ./tmp/rc1-failure.json
```

Expected result:

- stdout contains only valid JSON.
- Failure JSON includes `ok: false`, `stage`, and `error`.
- Input errors use `stage: "input"`.

Pass criteria:

- `python -m json.tool` succeeds.
- `ok` is `false`.
- `stage` and `error` are present.
- No human text is mixed into stdout.

Fail/blocker criteria:

- Invalid input emits non-JSON stdout in JSON mode.
- Failure JSON omits `stage` or `error`.
- Unknown JSON fields are silently accepted.

## Minimum RC Blocker Suite

These scenarios must pass on WSL/Linux before tagging or promoting `v1.0.0-rc.1`:

- Stage 1: Install/config smoke.
- Stage 2: Prompt-only happy path.
- Stage 3: Local note happy path, if OpenAI credentials are available for release testing.
- Stage 4: Output root behavior.
- Stage 5: Transcript-file fallback.
- Stage 6: Notion fail-fast.
- Stage 7: Notion happy path, if Notion and OpenAI credentials are available for release testing.
- Stage 8: JSON success.
- Stage 9: JSON failure.

If OpenAI or Notion credentials are unavailable, mark affected stages `BLOCKED`, not `PASS`.

## Optional Sanity Checks

### 10. Repo-local launcher sanity

User journey covered:

- Existing repo-local launcher wrappers still route to the direct CLI path.

Why it matters:

- Repo-local wrappers remain supported, but should not duplicate the installed CLI matrix.

Steps:

```bash
bash ./scripts/install-launchers.sh
ynn-prompt "https://youtu.be/VIDEO_ID" --output-dir ./tmp/rc1-output-a
```

Expected result:

- One prompt-only run succeeds through the repo-local launcher wrapper.

Pass criteria:

- Transcript and prompt files are created under the selected output root.

Fail/blocker criteria:

- Repo-local wrapper installation or one prompt-only wrapper run fails on WSL/Linux.

### 11. n8n wrapper sanity

User journey covered:

- The shell wrapper used by n8n returns valid JSON for one success and one automation-safe failure.

Why it matters:

- The wrapper is part of the n8n integration contract, but this plan should not validate a full production n8n workflow.

Success steps:

```bash
printf '%s\n' '{"url":"https://youtu.be/VIDEO_ID"}' | ./scripts/n8n-ingest.sh > ./tmp/rc1-n8n-success.json
python -m json.tool ./tmp/rc1-n8n-success.json
```

Failure steps:

```bash
printf '%s\n' '{"url":"https://youtu.be/VIDEO_ID","unexpected":true}' | ./scripts/n8n-ingest.sh > ./tmp/rc1-n8n-failure.json
python -m json.tool ./tmp/rc1-n8n-failure.json
```

Expected result:

- Success output is valid JSON with `ok: true`.
- Failure output is valid JSON with `ok: false`.

Pass criteria:

- Both wrapper outputs parse as JSON.
- Failure is an automation-safe `ok: false` payload, not wrapper noise.

Fail/blocker criteria:

- Wrapper emits non-JSON stdout for valid CLI JSON output.
- Wrapper turns a valid `ok: false` payload into an unparseable workflow error.

## Known Not-Tested / Not Blockers

- Native Windows PowerShell workflow.
- Full macOS matrix.
- Every combination of `ynn`, `ynn-note`, `ynn-notion`, `ynn-prompt`, and direct `python ingest.py`.
- Production n8n workflow behavior.
- Long videos that exceed one LLM request.
- Videos without transcripts except where transcript-file fallback is tested.
- Alternate transcript providers, Whisper, inline transcript JSON, transcript from stdin, or URL-less transcript mode.
- Complex markdown-to-Notion formatting beyond the documented basic block shapes.
