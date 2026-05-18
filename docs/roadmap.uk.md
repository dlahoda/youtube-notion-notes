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

## Milestone 5: pipeline core refactor

Наступний крок: зробити `./ingest.py` тоншим.

Поточна поведінка має залишитися тією самою: CLI, JSON-контракт, локальний output, Notion export і n8n wrapper не повинні змінити зовнішню форму. Внутрішня orchestration-логіка має переїхати з `./ingest.py` у окремий Python service module.

Це підготує код до наступних input modes без додавання нових CLI-фіч у цьому milestone.

## Milestone 6: transcript fallback input

Після refactor планується fallback для випадків, коли YouTube transcript недоступний або його не хочеться брати автоматично.

Очікувана ідея: користувач дає transcript із локального файлу, а пайплайн далі використовує той самий шлях генерації нотатки, локального збереження та опційного Notion export.

Whisper, альтернативні transcript providers і long-video chunking поки не входять у цей milestone.

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
