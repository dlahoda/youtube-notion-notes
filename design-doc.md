
# YouTube → GPT → Notion Notes MVP

## ASK

Ти хочеш перенести проєкт із простого чату в робочий документ, бо тут уже з’являється дизайн пайплайну, архітектура, рішення по API, майбутній n8n і місце для поступових правок.

## DO

-   Зафіксувати ціль MVP.
    
-   Відділити першу локальну Python-версію від майбутнього n8n.
    
-   Описати пайплайн як систему, а не як випадковий скрипт.
    
-   Винести ризики й вузькі місця.
    
-   Тримати Notion як кінцевий storage, а не як центр логіки.
    
-   Залишити LLM-шар змінним: OpenAI API, manual ChatGPT, або локальна модель.
    

----------

# 1. Ціль MVP

Зробити локальний Python-пайплайн, який бере YouTube link і створює готову нотатку для читання та збереження.

Бажаний фінальний сценарій:

```bash
python ingest.py "https://www.youtube.com/watch?v=..."

```

Результат:

-   transcript витягнуто;
    
-   конспект згенеровано;
    
-   markdown backup збережено локально;
    
-   Notion page створено в конкретній database;
    
-   title, URL, tags, status і body заповнені.
    

----------

# 2. Не-цілі на старті

Це важливо, щоб MVP не розпух.

Поки що НЕ робимо:

-   ідеальний markdown editor;
    
-   власний StackEdit;
    
-   повноцінний web app;
    
-   browser extension;
    
-   складну чергу задач;
    
-   автоматичну обробку всіх можливих YouTube edge cases;
    
-   красивий UI;
    
-   n8n workflow на першому етапі.
    

Перший етап має відповідати на одне питання:

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
→ create Notion page
→ append Notion blocks

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
  config.py
  prompts/
    comprehensive_note.md
  services/
    transcript.py
    note_generator.py
    notion.py
    markdown_to_notion.py
  output/
    transcripts/
    notes/
  .env
  requirements.txt

```

## Логіка модулів

### `ingest.py`

Головний entry point.

Керує пайплайном, але не містить усю бізнес-логіку всередині себе.

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

На старті підтримує тільки прості речі:

-   headings;
    
-   paragraphs;
    
-   bullets;
    
-   numbered lists;
    
-   quotes;
    
-   code blocks.
    

----------

# 5. Milestone 1 — локальний конспект без Notion

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

Спершу треба переконатися, що “м’ясорубка” дає нормальний конспект.

----------

# 6. Milestone 2 — Notion export

## Planning checkpoint — Notion export contract

Ціль поточного planning checkpoint: зафіксувати контракт для майбутнього Notion export без реалізації інтеграції.

На цьому етапі НЕ робимо:

-   `services/notion.py`;

-   `services/markdown_to_notion.py`;

-   Notion SDK dependency;

-   Notion API calls;

-   n8n workflow;

-   web UI.

## Status — complete

Milestone 2 is implemented and smoke-tested.

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

`OPENAI_API_KEY` залишається optional і належить тільки до OpenAI note generation. Він не потрібен для future Notion export.

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

Local-only режим може бути явним, якщо це добре ляже в CLI:

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

Milestone 3's local CLI automation contract is complete.

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

n8n orchestration and any HTTP wrapper are not implemented yet. They belong to later work, after this local CLI contract.

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

Later possible HTTP wrapper mode, not implemented yet:

```text
POST /ingest
{
  "url": "https://www.youtube.com/watch?v=..."
}

```

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

Milestone 4 is complete enough for the local MVP.

The project now has:

- a validated JSON stdin/stdout integration contract between n8n and `./ingest.py`;
- a real local n8n smoke test;
- a small n8n-facing shell wrapper;
- a sanitized exported smoke workflow template;
- a clear separation between orchestration in n8n and pipeline logic in Python.

The current design intentionally stays local-first and avoids additional infrastructure such as HTTP services, queues, or external workflow state.

Remaining future work is optional and belongs to later milestones or experiments, not to the Milestone 4 MVP boundary.

## Possible future extensions

Possible future extensions may include:

- constructing payloads through upstream n8n nodes instead of hardcoded smoke payloads;
- notification or audit branches in n8n;
- scheduled or automatic triggers;
- improved retry/reporting behavior;
- alternative transcript providers;
- hosted or remote execution models.

These are intentionally outside the current local MVP scope.

----------

# 9. Вузькі місця

## 1. YouTube transcript

Найкрихкіша частина.

Автоматичні субтитри можуть бути відсутні, закриті, дивно розмічені або зламані через зміни YouTube.

Fallback:

-   manual paste transcript;
    
-   інший transcript provider;
    
-   whisper/local transcription у майбутньому.
    

## 2. Довгі відео

Довгі transcript можуть не влазити в один LLM-запит.

Fallback:

-   chunking;
    
-   map-reduce summary;
    
-   спершу short MVP для відео до певної довжини.
    

## 3. Markdown → Notion

Notion не є markdown editor у чистому вигляді.

Треба конвертувати markdown у blocks.

Fallback:

-   на старті вставляти простішу структуру;
    
-   складну типографіку відкласти.
    

## 4. API billing

OpenAI API окремий від ChatGPT subscription.

Fallback:

-   manual mode;
    
-   локальна модель;
    
-   cheap model для першого проходу;
    
-   GPT тільки для фінального polish.
    

----------

# 10. Пропонований перший режим: manual-safe MVP

Щоб не впертися в оплату API відразу, можна зробити два режими.

## Mode A — full auto

```text
transcript → OpenAI API → markdown note

```

## Mode B — manual GPT bridge

```text
transcript → ready prompt file → user pastes into ChatGPT → saves result manually or through script

```

Це не ідеальна автоматизація, але дає backup-режим без API billing.

----------

# 11. Наступний практичний крок

Зробити Milestone 1.

Мінімальний результат:

-   `requirements.txt`;
    
-   `.env.example`;
    
-   `ingest.py`;
    
-   `services/transcript.py`;
    
-   `services/note_generator.py`;
    
-   `prompts/comprehensive_note.md`;
    
-   локальний markdown output.
    

Після цього можна додавати Notion.

----------

# 12. Відкриті рішення

## LLM mode для першої версії

Варіанти:

1.  OpenAI API одразу.
    
2.  Manual ChatGPT bridge спочатку.
    
3.  Підтримати обидва режими з самого початку.
    

Рекомендація: підтримати обидва, але зробити manual mode простим fallback.

## Формат конспекту

Можна взяти наявний стиль з твого “Comprehensive Note” чату.

Бажаний output:

-   title;
    
-   source URL;
    
-   short overview;
    
-   key ideas;
    
-   detailed notes;
    
-   quotes or memorable phrasing;
    
-   practical takeaways;
    
-   tags.
    

## Notion page status

Рекомендація:

-   `Draft` — створено автоматом, ще не читав;
    
-   `Reviewed` — прочитав і підчистив;
    
-   `Archived` — залишив для історії.
    

----------

# 13. Принцип дизайну

Пайплайн має бути нудний.

Нудний тут добре.

Менше магії означає менше місць, де все ламається без пояснень.

----------
# 14. Repository workflow

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

# 15. Codex execution runbook

## Мета

Провести першу реалізацію через Codex маленькими контрольованими кроками.

Codex не має будувати весь проєкт одразу.

Він має робити один milestone за раз.

----------

## Step 0 — створити репозиторій

Почати з порожньої папки:

```bash
mkdir youtube-notion-notes
cd youtube-notion-notes
git init

```

Перший commit може бути порожній або тільки з README.

Головна ідея: перед кожним великим Codex-завданням мати git checkpoint.

----------

## Step 1 — додати `AGENTS.md`

`AGENTS.md` — це інструкції для Codex у межах конкретної репи.

Мінімальний зміст:

```md
# AGENTS.md

## Project goal

Build a small Python CLI tool that turns a YouTube URL into a local transcript and a markdown note.

Later milestones may export to Notion and be wrapped by n8n, but do not implement those unless explicitly requested.

## Current milestone

Implement Milestone 1 only:

- parse a YouTube URL;
- fetch a transcript;
- save raw transcript locally;
- create a ready-to-paste GPT prompt;
- optionally generate a markdown note if OpenAI API config is present.

## Engineering rules

- Keep changes small and reviewable.
- Prefer boring, simple Python.
- Do not add a web UI.
- Do not implement Notion yet.
- Do not implement n8n yet.
- Do not add unnecessary dependencies.
- Keep secrets out of git.
- Use `.env.example` for required environment variables.
- Add README instructions for setup and usage.

## Verification

After changes, explain:

- what files were created or changed;
- how to install dependencies;
- how to run the CLI;
- how to test it manually with one YouTube URL;
- what limitations remain.

```

----------

## Step 2 — перший Codex prompt

Дати Codex вузьке завдання:

```text
Read AGENTS.md and implement Milestone 1 only.

Create the initial Python CLI project structure.

Requirements:
- `ingest.py` is the CLI entry point.
- `services/transcript.py` handles YouTube URL parsing and transcript fetching.
- `services/note_generator.py` supports manual mode and optional OpenAI mode.
- `prompts/comprehensive_note.md` contains the note-generation prompt template.
- `requirements.txt`, `.env.example`, and `README.md` are included.
- Raw transcript files are saved to `output/transcripts/`.
- Ready-to-paste GPT prompt files are saved to `output/prompts/`.
- Markdown notes are saved to `output/notes/` only when note generation is available.

Constraints:
- Do not implement Notion.
- Do not implement n8n.
- Do not add a web UI.
- Keep dependencies minimal.
- Add basic error handling.

After implementing, show me the diff and the exact commands to verify it.

```

----------

## Step 3 — review before accepting

Before accepting Codex changes, check:

-   Does it obey the milestone boundary?
    
-   Did it avoid Notion/n8n?
    
-   Did it avoid secrets in git?
    
-   Does README show exact commands?
    
-   Can the CLI run with no OpenAI API key?
    
-   Are output folders ignored or safe?
    

----------

## Step 4 — git checkpoint

After the first working version:

```bash
git status
git add .
git commit -m "Implement local transcript MVP"

```

Only after this checkpoint should the project move toward Notion export.
