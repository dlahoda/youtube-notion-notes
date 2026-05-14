
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

Існуюча локальна/manual поведінка залишається default.

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

## Future CLI shape

Notion export має бути opt-in:

```bash
python ingest.py "URL" --export notion

```

Local-only режим може бути явним, якщо це добре ляже в CLI:

```bash
python ingest.py "URL" --export local

```

На planning milestone цей flag тільки документується. Його не треба реалізовувати, поки немає Notion export implementation.


## Body сторінки

Конспект вставляється в тіло сторінки як Notion blocks.

----------

# 7. Milestone 3 — підготовка до n8n

Ціль: зробити так, щоб Python-логіку можна було викликати з n8n.

Можливі режими:

```bash
python ingest.py "URL"

```

або:

```bash
python ingest.py --json '{"url":"..."}'

```

або маленький локальний HTTP wrapper:

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

# 8. Вузькі місця

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

# 9. Пропонований перший режим: manual-safe MVP

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

# 10. Наступний практичний крок

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

# 11. Відкриті рішення

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

# 12. Принцип дизайну

Пайплайн має бути нудний.

Нудний тут добре.

Менше магії означає менше місць, де все ламається без пояснень.

----------

# 13. Codex execution runbook

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
