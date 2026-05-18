
# YouTube → GPT → Notion Notes MVP

## ASK

Тримати цей документ як source of truth для поточного стану, roadmap, slice boundaries, і durable decisions проєкту.

## DO

-   Зафіксувати поточний стан MVP.
    
-   Відділити Python pipeline logic від n8n orchestration.
    
-   Описати пайплайн як систему, а не як випадковий скрипт.
    
-   Винести ризики й вузькі місця.
    
-   Тримати Notion як кінцевий storage, а не як центр логіки.
    
-   Залишити LLM-шар змінним: OpenAI API, manual ChatGPT, або локальна модель.
    

----------

# 1. Current project state

Проєкт зараз є локальним Python-пайплайном, який бере YouTube link і створює готову нотатку для читання та збереження.

Поточний локальний сценарій:

```bash
python ingest.py "https://www.youtube.com/watch?v=..."
python ingest.py "https://www.youtube.com/watch?v=..." --export notion

```

Поточний roadmap:

- Milestone 1 — complete: local transcript and markdown note.
- Milestone 2 — complete, tagged `v0.2.0`: opt-in Notion export.
- Milestone 3 — complete, tagged `v0.3.0`: local CLI automation contract.
- Milestone 4 — complete, tagged `v0.4.0`: n8n integration contract and smoke workflow.
- Milestone 5 — next: pipeline core refactor.
- Milestone 6 — later: transcript fallback input.

----------

# 2. MVP boundaries

Це важливо, щоб pipeline не розпух.

Поза поточним local-first MVP:

-   ідеальний markdown editor;
    
-   власний StackEdit;
    
-   повноцінний web app;
    
-   browser extension;
    
-   складну чергу задач;
    
-   автоматичну обробку всіх можливих YouTube edge cases;
    
-   красивий UI;
    
-   production-grade hosted workflow.
    

Поточний MVP відповідає на одне питання:

> Чи можемо ми стабільно перетворити YouTube link на якісний markdown-конспект?

----------

# 3. Пайплайн

```text
YouTube URL
→ extract video_id
→ fetch transcript
→ clean transcript
→ generate note
→ save local markdown backup
→ optionally create Notion page
→ optionally append Notion blocks

```

## Що відбувається

Система бере один вхідний URL і поступово перетворює його на структуровану нотатку.

## Чому це важливо

Кожен крок можна дебажити окремо. Якщо transcript зламався, ми не ліземо в Notion. Якщо GPT видав кашу, ми не чіпаємо YouTube-частину.

----------

# 4. Архітектура файлів

```text
youtube-notion-notes/
  ingest.py
  prompts/
    comprehensive_note.md
  services/
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

## Логіка модулів

### `ingest.py`

Головний entry point.

Поки що керує CLI, input modes, output modes, і частиною pipeline orchestration.

Milestone 5 має зробити цей файл тоншим без зміни поведінки.

### `services/transcript.py`

Відповідає тільки за YouTube URL, video_id і transcript.

### `services/note_generator.py`

Відповідає за перетворення transcript у конспект.

Має підтримувати різні режими:

-   OpenAI API;
    
-   manual mode;
    
-   future Ollama/local model.
    

### `services/notion.py`

Відповідає за створення сторінки в Notion і додавання блоків.

### `services/markdown_to_notion.py`

Перетворює markdown у базові Notion blocks.

Підтримує тільки прості речі:

-   headings;
    
-   paragraphs;
    
-   bullets;
    
-   numbered lists;
    
-   quotes;
    
-   code blocks.

### `services/note_metadata.py`

Витягує metadata з markdown note для Notion export.

### `services/notion_export.py`

Оркеструє Notion export поверх `./services/notion.py`, `./services/markdown_to_notion.py`, і metadata extraction.

### `./scripts/n8n-ingest.sh`

Малий wrapper для n8n, який викликає `./ingest.py` через JSON stdin/stdout contract і перевіряє, що stdout є валідним JSON.
    

----------

# 5. Milestone 1 — локальний конспект без Notion

## Status — complete

Ціль: довести, що transcript → note працює.

## Вхід

YouTube URL.

## Вихід

Два локальні файли:

```text
output/transcripts/video-title.txt
output/notes/video-title.md

```

## Кроки

1.  Прочитати URL з CLI.
    
2.  Дістати `video_id`.
    
3.  Витягнути transcript.
    
4.  Зберегти raw transcript.
    
5.  Прогнати transcript через note generator.
    
6.  Зберегти markdown note.
    

## Чому без Notion на цьому етапі

Notion додає окремий шар складності.

Цей milestone окремо довів, що “м’ясорубка” дає нормальний локальний конспект перед додаванням Notion.

----------

# 6. Milestone 2 — Notion export

## Status — complete

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

## Потрібні `.env` змінні

```env
NOTION_API_KEY=...
NOTION_DATABASE_ID=...

```

`OPENAI_API_KEY` залишається optional і належить тільки до OpenAI note generation. Він не потрібен для Notion export.

## Поля Notion database

Обов'язковий контракт database:

-   `Name` — title;

-   `URL` — YouTube link;

-   `Tags` — multi-select;

-   `Status` — select;

-   `Source` — select;

-   `Created` — created time.

Рекомендовані `Status` values:

-   `Draft`;

-   `Reviewed`;

-   `Archived`.

Рекомендований `Source` value для цього pipeline:

-   `YouTube`.

## Notion property decisions

- `Status` uses a regular Notion `select` property, not Notion's native Status property.
- `Source` uses a regular Notion `select` property, not `rich_text`.
- `Tags` uses a `multi_select` property.
- `./services/notion.py` allows empty tags so it can stay a small reusable Notion adapter.
- Higher-level pipeline/export code may require tags for YouTube notes later.
- `Created` is managed by Notion as `created_time` and should not be set manually by the client.

## CLI shape

Notion export має бути opt-in:

```bash
python ingest.py "URL" --export notion

```

Local-only режим може бути явним:

```bash
python ingest.py "URL" --export local

```


## Body сторінки

Конспект вставляється в тіло сторінки як Notion blocks.

## Markdown note metadata convention

-   The first Markdown H1 heading is treated as the note title.
-   The note title must use `# Note title`.
-   Tags are read from a comma-separated `Tags:` line.
-   Spaces inside multi-word tags are preserved.
-   The source URL is not parsed from markdown; it comes from the original CLI input.

----------

# 7. Milestone 3 — підготовка до n8n

Ціль: зробити так, щоб Python-логіку можна було викликати з n8n.

## Status — complete

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

## CLI result contract

First small slice: keep the existing human-readable CLI as the default, and add opt-in machine-readable output for automation:

```bash
python ingest.py "URL" --output json
python ingest.py "URL" --export notion --output json

```

In JSON output mode, stdout must contain only JSON. Success output includes `ok`, `url`, `export_mode`, created local paths, and Notion page details when export runs. `notion_page_url` comes from the Notion API page response `url` field and is included only when that field is present. Failure output includes `ok: false`, `stage`, and `error`.

## CLI JSON input contract

Second small slice: allow automation callers to pass a structured JSON payload instead of a positional URL:

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

Third small slice: allow the same JSON payload contract to come from a file or stdin, so automation callers do not need fragile inline JSON shell quoting:

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

## Чому це важливо

n8n тоді буде оркестратором, а не місцем, де живе вся складна логіка.

Це зменшує біль підтримки.

----------

# 8. Milestone 4 — n8n integration contract and smoke workflow

Goal: define how n8n will call the existing local Python CLI without adding an HTTP server or queue.

Preferred integration shape:

Validated decision: n8n should call `./ingest.py` directly through the JSON stdin/stdout contract. Exact direct stdin UI wiring remains unnecessary for now because a shell pipe wrapper works and preserves the same Python contract.

- n8n uses an Execute Command-style node.
- n8n passes a JSON payload to `python ./ingest.py --input-json-file - --output json`.
- Python reads JSON from stdin.
- Python writes machine-readable JSON to stdout only.
- n8n branches on `ok: true` / `ok: false`.
- n8n does not depend on `./Makefile` targets.
- `./Makefile` remains a local developer convenience only.

Non-goals:

- no HTTP server;
- no queue;
- no new dependencies;
- no Notion logic inside n8n;
- no duplicated pipeline logic in n8n.

## Slice 1 — n8n smoke workflow contract

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

## Slice 2 — real local n8n smoke test

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
- `./Makefile` remains local dev convenience only;
- direct `./ingest.py` JSON stdin/stdout remains the integration boundary;
- exact direct stdin UI wiring remains unnecessary for now because the shell pipe wrapper works;
- if `./ingest.py` emits valid JSON with `ok: false` but exits non-zero, the n8n-side shell wrapper may normalize the shell exit code so the workflow can branch on parsed JSON `ok`;
- invalid or missing stdout JSON should still be treated as a workflow error, because broad `|| true` can mask infrastructure failures.

## Slice 3 — small n8n shell wrapper

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

## Slice 4 — exported minimal n8n smoke workflow template

Status: complete.

Scope:

- add sanitized `./docs/n8n-smoke-workflow.json` template;
- keep the workflow minimal: Manual Trigger, Execute Command, Code, IF;
- use `sh ./scripts/n8n-ingest.sh` through a placeholder repository path;
- keep `./ingest.py` JSON stdin/stdout as the integration boundary;
- avoid runtime Python changes;
- avoid secrets, Notion API keys, database IDs, and personal local paths;
- keep the template as manual smoke workflow documentation, not production automation.

## Milestone 4 status

Milestone 4 is complete enough for the local MVP and tagged `v0.4.0`.

The project now has:

- a validated JSON stdin/stdout integration contract between n8n and `./ingest.py`;
- a real local n8n smoke test;
- a small n8n-facing shell wrapper;
- a sanitized exported smoke workflow template;
- a clear separation between orchestration in n8n and pipeline logic in Python.

The current design intentionally stays local-first and avoids additional infrastructure such as HTTP services, queues, or external workflow state.

Future n8n expansion is optional backlog work, not part of the Milestone 4 MVP boundary.

----------

# 9. Milestone 5 — pipeline core refactor

Goal: move pipeline orchestration out of ./ingest.py while preserving existing behavior.

The current CLI works, but ./ingest.py now owns too many responsibilities:

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

Target shape:

- ./ingest.py remains the CLI entry point;
- ./ingest.py keeps CLI parsing and user-facing output mode selection;
- pipeline orchestration moves into a dedicated service module;
- the JSON stdin/stdout contract stays unchanged;
- ./scripts/n8n-ingest.sh stays unchanged unless required by a preserved contract;
- Notion logic stays inside Python;
- n8n remains orchestration-only.

Non-goals:

- no new CLI features;
- no transcript fallback yet;
- no long-video chunking;
- no HTTP server;
- no queue;
- no n8n workflow expansion;
- no Notion behavior changes.

Success criteria:

- existing tests pass;
- local CLI behavior is unchanged;
- JSON output shape is unchanged;
- n8n wrapper behavior is unchanged;
- Notion export still works through the existing export path;
- ./ingest.py becomes thinner and easier to read.

----------

# 10. Milestone 6 — transcript fallback input

Goal: allow the pipeline to use a manually provided transcript when YouTube transcript fetching fails or is not desirable.

This supports the known transcript bottleneck: automatic YouTube captions can be missing, blocked, malformed, or unstable.

Possible shape:

- accept transcript text from a local file;
- keep YouTube URL as source metadata;
- reuse the same prompt generation, optional note generation, local markdown output, and Notion export path.

Non-goals:

- no Whisper/local transcription yet;
- no alternative transcript provider yet;
- no long-video chunking yet.

----------

# 11. Future options / backlog

These items are intentionally outside Milestone 5. Transcript fallback input is already planned as Milestone 6; the rest is optional later backlog if the local MVP needs it.

Known limitations:

- YouTube transcript fetching is the most fragile part. Automatic captions can be missing, blocked, malformed, or unstable.
- Long transcripts may not fit into one LLM request. Chunking and map-reduce summarization are not implemented.
- Notion is not a pure markdown editor. Markdown is converted into basic Notion blocks, and complex typography is intentionally deferred.
- OpenAI API billing is separate from a ChatGPT subscription. Manual mode remains the fallback when API usage is unavailable or unwanted.

Current design decisions:

- Support both manual GPT bridge mode and optional OpenAI API mode.
- Treat manual mode as a simple, durable fallback rather than a failure path.
- Keep future local model support possible, but do not implement it yet.
- Keep the note shape in `./prompts/comprehensive_note.md`: title, source URL, overview, key ideas, detailed notes, memorable phrasing, practical takeaways, and tags.
- Use Notion status values `Draft`, `Reviewed`, and `Archived`.

Future options:

- long-video chunking and map-reduce note generation;
- constructing payloads through upstream n8n nodes instead of hardcoded smoke payloads;
- n8n notification or audit branches;
- scheduled n8n triggers;
- improved retry and reporting behavior;
- alternative transcript providers;
- Whisper or local transcription;
- hosted or remote execution model;
- optional HTTP wrapper if local command execution stops being enough.

----------

# 12. Принцип дизайну

Пайплайн має бути нудний.

Нудний тут добре.

Менше магії означає менше місць, де все ламається без пояснень.

----------

# 13. Repository workflow

Canonical repository: dlahoda/youtube-notion-notes

Default branch: main.

Repository access rule:

- The repository is private.
- Use the GitHub connector/integration for repository access.
- Do not use web search to inspect repository contents.
- If GitHub connector access is unavailable, ask the user for a branch, PR, diff, or uploaded files instead of searching the web.

Working flow:

- implementation happens locally through Codex/VS Code;
- feature work is committed to feature branches;
- pushed branches or PRs are reviewed through GitHub;
- final integration uses squash merge into main;
- assistant must not create commits, branches, PRs, or merge changes unless explicitly asked.

----------

# 14. Historical setup notes

The old Codex execution runbook was useful for bootstrapping Milestone 1 from an empty repository.

Current durable guidance:

- work one milestone or slice at a time;
- keep a git checkpoint before each large task;
- obey `./AGENTS.md` and this design document;
- keep changes small and reviewable;
- show diffs and verification commands after implementation;
- do not create commits, branches, PRs, or merges unless explicitly asked.

The original empty-repo setup prompt is historical context only; Milestones 1-4 are already complete.
