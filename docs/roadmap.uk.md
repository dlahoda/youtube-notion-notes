# Дорожня карта YouTube to Notion Notes

`./design-doc.md` є канонічним технічним джерелом правди для проєкту. Цей файл лише коротко пояснює roadmap українською для швидкого людського читання. Якщо між документами виникає різниця, пріоритет має `./design-doc.md`.

## Що робить проєкт

Проєкт перетворює YouTube-посилання на локальний transcript і markdown-конспект. За бажанням цей конспект можна експортувати в Notion.

Основний сценарій залишається локальним і простим:

1. взяти YouTube URL;
2. отримати transcript;
3. згенерувати markdown-нотатку;
4. зберегти локальні файли;
5. опційно створити сторінку в Notion.

## Принципи

- Пайплайн має бути нудний, простий і передбачуваний.
- Python володіє логікою пайплайна.
- n8n лише оркеструє запуск і гілкування.
- Notion є сховищем результату, а не центром логіки.
- Ручний ChatGPT-режим лишається нормальним fallback, не аварійним шляхом.
- Нові залежності й інфраструктура додаються тільки коли вони справді потрібні.

## Що вже зроблено

Milestone 1 завершено: CLI може взяти YouTube URL, отримати transcript і створити локальний markdown-конспект.

Milestone 2 завершено і позначено тегом `v0.2.0`: додано opt-in експорт у Notion через `--export notion`.

Milestone 3 завершено і позначено тегом `v0.3.0`: CLI отримав контракт для автоматизації через JSON input/output.

Milestone 4 завершено і позначено тегом `v0.4.0`: перевірено локальний n8n smoke workflow, додано wrapper `./scripts/n8n-ingest.sh` і шаблон workflow. n8n не містить бізнес-логіки пайплайна.

Milestone 5 завершено і позначено тегом `v0.5.0`: orchestration-логіку винесено з `./ingest.py` у `./services/pipeline.py`, а CLI та JSON-контракт лишилися стабільними.

Milestone 6 завершено і позначено тегом `v0.6.0`: додано fallback input із локального transcript-файлу.

## Milestone 5: pipeline core refactor

Milestone завершено: `./ingest.py` став тоншим, а orchestration-логіка пайплайна живе в `./services/pipeline.py`.

Зовнішня поведінка збережена: CLI, JSON-контракт, локальний output, Notion export і n8n wrapper не змінили форму.

Цей refactor підготував код до наступних input modes без додавання нових CLI-фіч у Milestone 5.

## Milestone 6: transcript fallback input

Milestone завершено: додано `--transcript-file` для fallback-сценарію, коли YouTube transcript недоступний або його не хочеться брати автоматично.

Режим працює для звичайного CLI з positional YouTube URL. YouTube URL досі обовʼязковий і лишається source metadata, а transcript читається з локального UTF-8 файлу.

Empty або whitespace-only transcript files відхиляються на transcript stage до запису transcript, prompt, note або Notion output files. Якщо файл має non-whitespace content, transcript text зберігається без змін.

JSON/n8n transcript input, URL-less transcript mode, Whisper, alternative transcript providers і long-video chunking не входили в Milestone 6.

## Milestone 7: next slice TBD

Наступний milestone ще не вибрано. Майбутні варіанти лишаються в backlog.

## Майбутній backlog

Це не поточна робота:

- chunking для довгих відео;
- map-reduce note generation;
- альтернативні transcript providers;
- Whisper або локальна транскрипція;
- scheduled n8n flows;
- notification або audit branches у n8n;
- hosted execution;
- HTTP wrapper, якщо локального command execution колись стане недостатньо.

Поки що головна ціль проста: стабільний локальний Python pipeline, який робить якісний markdown-конспект із YouTube URL і може зберегти результат у Notion.
