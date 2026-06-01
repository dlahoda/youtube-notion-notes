# v1.0.0-rc.1 Manual Smoke Results

## Run Summary

- RC version: `v1.0.0-rc.1`
- Date: `YYYY-MM-DD`
- Tester: `<name>`
- Environment: `<WSL/Linux distro, version, shell>`
- Python version: `<python --version>`
- Install mode: `<editable install / other>`
- Test video URL: `<https://youtu.be/VIDEO_ID>`
- Persistent output directory: `<absolute path, e.g. /path/to/repo/tmp/rc1-output-a>`
- Per-run relative output directory: `<./tmp/rc1-output-a or other, if used>`
- Notion test database: `<database name or id, or N/A>`
- OpenAI config available: `<yes/no>`
- Notion config available: `<yes/no>`
- User config path: `~/.config/youtube-notion-notes/.env`
- User config backed up before test: `<yes/no/N/A>`
- User config restored after test: `<yes/no/N/A>`
- Missing-config env file: `<./tmp/rc1-missing-config.env or N/A>`

## Scenario Checklist

| # | Scenario | Status | Notes |
| --- | --- | --- | --- |
| 1 | Install/config smoke | PASS | Editable install succeeded. Installed mise console scripts work when their bin dir is first on PATH; existing ~/.local/bin launchers otherwise shadow them. |
| 2 | Prompt-only happy path | PASS | Generated transcript and GPT prompt without OpenAI or Notion config; `find` warning was from smoke-check command argument order, not application behavior. |
| 3 | Local note happy path | PASS | Generated transcript, GPT prompt, and structured markdown note after installing editable OpenAI extra dependency. |
| 4 | Output root behavior | PASS | `YNN_OUTPUT_DIR` was used when no explicit output dir was provided; `--output-dir` correctly overrode it for a single run. |
| 5 | Transcript-file fallback | PASS | Local transcript fixture was used; output reported `Transcript selected: transcript file`, saved transcript contained fixture text, and prompt was generated. |
| 6 | Notion fail-fast | PASS | Missing OpenAI/Notion config produced a clean config error with non-zero exit before creating new output files. |
| 7 | Notion happy path | PASS / FAIL / BLOCKED / SKIPPED |  |
| 8 | JSON success | PASS / FAIL / BLOCKED / SKIPPED |  |
| 9 | JSON failure | PASS / FAIL / BLOCKED / SKIPPED |  |
| 10 | Optional repo-local launcher sanity | PASS / FAIL / BLOCKED / SKIPPED |  |
| 11 | Optional n8n wrapper sanity | PASS / FAIL / BLOCKED / SKIPPED |  |

Status key:

- `PASS`: tested and met pass criteria.
- `FAIL`: tested and did not meet pass criteria.
- `BLOCKED`: required credential, service, or environment prerequisite was unavailable.
- `SKIPPED`: intentionally not run because it is optional or outside this RC run.

## Per-Scenario Notes

### 1. Install/config smoke

- Status: `PASS`
- Commands run:
  - `python -m pip install -e .`
  - `ynn --help`
  - `ynn-prompt --help`
  - `ynn-note --help`
  - `ynn-notion --help`
  - `ynn init --output-dir /mnt/d/dev/youtube-notion-notes/tmp/rc1-output-a`
- Persisted `YNN_OUTPUT_DIR` value:
  - `/mnt/d/dev/youtube-notion-notes/tmp/rc1-output-a`
- User config backup path:
  - `./tmp/rc1-user-config-before-stage-1.env`
  - `./tmp/rc1-user-config-hidden-for-stage-1.env`
- User config restore needed: `no`
- Observed output:
  - Editable install completed successfully.
  - Installed console scripts resolved from `/home/denys/.local/share/mise/installs/python/3.13.13/bin/`.
  - `ynn init` completed and wrote config to `/home/denys/.config/youtube-notion-notes/.env`.
- Files/config checked:
  - `/mnt/d/dev/youtube-notion-notes/tmp/rc1-output-a`
  - `/home/denys/.config/youtube-notion-notes/.env`
- Issues:
  - Initial shell `PATH` resolved `ynn*` commands from `/home/denys/.local/bin`, not from the editable-install mise bin directory.
  - pip warned that `/home/denys/.local/share/mise/installs/python/3.13.13/bin` is not on `PATH`.

### 2. Prompt-only happy path

- Status: `PASS`
- Command run:
  - `ynn-prompt "https://youtu.be/KquM_52cAIE" --output-dir ./tmp/rc1-output-a`
- Transcript path:
  - `./tmp/rc1-output-a/transcripts/KquM_52cAIE.txt`
- Prompt path:
  - `./tmp/rc1-output-a/prompts/KquM_52cAIE_prompt.md`
- Issues:
  - None.


### 3. Local note happy path

- Status: `PASS`
- Command run:
  - `python -m pip install -e ".[openai]"`
  - `ynn-note "https://youtu.be/KquM_52cAIE" --output-dir ./tmp/rc1-output-a`
- Transcript path:
  - `./tmp/rc1-output-a/transcripts/KquM_52cAIE.txt`
- Prompt path:
  - `./tmp/rc1-output-a/prompts/KquM_52cAIE_prompt.md`
- Note path:
  - `./tmp/rc1-output-a/notes/KquM_52cAIE.md`
- Note quality/readability check:
  - Generated note is readable and structured.
  - Note contains H1 title, tags, summary, key ideas, practical takeaways, and open questions.
- Issues:
  - First attempt skipped markdown note generation because `OPENAI_API_KEY` was set but the optional `openai` package was not installed.
  - Resolved by installing the OpenAI extra in editable mode with `python -m pip install -e ".[openai]"` and rerunning the stage.

### 4. Output root behavior

- Status: `PASS`
- `YNN_OUTPUT_DIR` path:
  - `./tmp/rc1-output-b`
- Explicit `--output-dir` path:
  - `./tmp/rc1-output-explicit`
- Files found under `YNN_OUTPUT_DIR`:
  - `./tmp/rc1-output-b/transcripts/KquM_52cAIE.txt`
  - `./tmp/rc1-output-b/prompts/KquM_52cAIE_prompt.md`
- Files found under explicit output dir:
  - `./tmp/rc1-output-explicit/transcripts/KquM_52cAIE.txt`
  - `./tmp/rc1-output-explicit/prompts/KquM_52cAIE_prompt.md`
- Issues:
  - None.

### 5. Transcript-file fallback

- Status: `PASS`
- Command run:
  - `python ingest.py "https://youtu.be/KquM_52cAIE" --transcript-file ./tmp/rc1-manual-transcript.txt --no-note --output-dir ./tmp/rc1-output-a`
- Transcript fixture path:
  - `./tmp/rc1-manual-transcript.txt`
- Saved transcript path:
  - `./tmp/rc1-output-a/transcripts/KquM_52cAIE.txt`
- Evidence local fixture text was used:
  - Human output reported `Transcript selected: transcript file`.
  - `grep` found `This is a local transcript fixture for rc1.` in `./tmp/rc1-output-a/transcripts/KquM_52cAIE.txt`.
- Issues:
  - None.

### 6. Notion fail-fast

- Status: `PASS`
- Command run:
  - `ynn-notion "https://youtu.be/KquM_52cAIE" --env-file ./tmp/rc1-missing-config.env --output-dir ./tmp/rc1-output-a`
- Missing-config env file used:
  - `./tmp/rc1-missing-config.env`
- Missing config tested:
  - `OPENAI_API_KEY`
  - `NOTION_API_KEY`
  - `NOTION_DATABASE_ID`
- Observed error:
  - `Notion export config error: missing required config: OPENAI_API_KEY, NOTION_API_KEY, NOTION_DATABASE_ID.`
  - `exit_code=1`
- Evidence no transcript/OpenAI/Notion work happened:
  - No traceback was printed.
  - No transcript selection or output-save messages were printed.
  - `find ./tmp/rc1-output-a -type f -newer ./tmp/rc1-stage6-before -print` produced no new files.
- Issues:
  - None.

### 7. Notion happy path

- Status: `PASS / FAIL / BLOCKED / SKIPPED`
- Command run:
  - `ynn-notion "<url>" --output-dir <path>`
- Local note path:
- Notion page URL:
- Properties checked:
  - `Name`:
  - `URL`:
  - `Tags`:
  - `Status`:
  - `Source`:
  - `Created`:
- Body blocks present: `yes/no`
- Issues:

### 8. JSON success

- Status: `PASS / FAIL / BLOCKED / SKIPPED`
- Command run:
  - `python ingest.py "<url>" --no-note --output json --output-dir <path>`
- JSON output file:
- `python -m json.tool` result:
- Fields checked:
  - `ok`:
  - `url`:
  - `export_mode`:
  - output paths:
  - Notion fields only when applicable:
- Issues:

### 9. JSON failure

- Status: `PASS / FAIL / BLOCKED / SKIPPED`
- Command run:
  - `python ingest.py --input-json '{"url":"<url>","unexpected":true}' --output json`
- JSON output file:
- `python -m json.tool` result:
- Fields checked:
  - `ok`:
  - `stage`:
  - `error`:
- Issues:

### 10. Optional repo-local launcher sanity

- Status: `PASS / FAIL / BLOCKED / SKIPPED`
- Commands run:
  - `bash ./scripts/install-launchers.sh`
  - `ynn-prompt "<url>" --output-dir <path>`
- Transcript path:
- Prompt path:
- Issues:

### 11. Optional n8n wrapper sanity

- Status: `PASS / FAIL / BLOCKED / SKIPPED`
- Success command:
  - `printf '%s\n' '{"url":"<url>"}' | ./scripts/n8n-ingest.sh`
- Success JSON output file:
- Failure command:
  - `printf '%s\n' '{"url":"<url>","unexpected":true}' | ./scripts/n8n-ingest.sh`
- Failure JSON output file:
- `python -m json.tool` results:
- Issues:

## Final RC Decision

- Decision: `PASS / FAIL / BLOCKED`
- Decision date: `YYYY-MM-DD`
- Summary:
- Required follow-up before release:
- Follow-up can wait until after release:

## Known Not-Tested Areas

- Native Windows PowerShell workflow.
- Full macOS matrix.
- Full command/option/install-mode matrix.
- Production n8n workflow.
- Long videos that exceed one LLM request.
- Videos without transcripts beyond transcript-file fallback.
- Alternate transcript providers, Whisper, inline transcript JSON, transcript from stdin, or URL-less transcript mode.
- Complex markdown-to-Notion formatting beyond documented basic block shapes.
