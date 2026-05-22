# Durable Project Decisions

This document records durable architecture and product decisions for the project.

Read this when changing contracts, module boundaries, integration shape, or project-level behavior. Keep milestone status and active backlog planning in `./design-doc.md`. Keep completed slice history in `./docs/archive/*`.

---

# 1. Pipeline Ownership

Python owns pipeline logic. n8n orchestrates only.

`./ingest.py` and the Python service modules are responsible for:

- YouTube URL parsing and transcript fetching;
- transcript-file fallback handling;
- prompt and note generation;
- local file output;
- Notion export;
- JSON success and failure response shaping.

n8n may call the CLI, pass structured input, branch on results, and notify. It must not duplicate transcript fetching, note generation, markdown conversion, or Notion export logic.

Notion is final storage for exported notes, not the center of application logic.

---

# 2. Automation Boundary

JSON stdin/stdout is the current automation boundary.

The local automation shape is:

```bash
python ./ingest.py --input-json-file - --output json
```

Automation callers pass a JSON payload on stdin. Python writes machine-readable JSON to stdout only, including for input errors.

No HTTP server or queue should be added unless local command execution stops being enough.

`./scripts/n8n-ingest.sh` remains a small n8n-facing wrapper around the same JSON stdin/stdout contract. `./Makefile` remains a local developer convenience and is not part of the n8n contract.

---

# 3. Transcript Fallback Input

Manual transcript-file input still requires a source YouTube URL.

The source YouTube URL remains required because it is used for source metadata, `video_id` parsing, and default output naming. Manual transcript text is an alternate transcript source, not a replacement for source identity.

There is no URL-less transcript mode yet.

Current transcript input boundaries:

- no inline transcript text in JSON;
- no transcript from stdin;
- no `source_url`, `source_title`, or `source_type` metadata;
- no Whisper;
- no alternative transcript providers;
- no long-video chunking.

---

# 4. LLM Generation

The LLM layer should stay replaceable.

Supported generation paths include manual GPT bridge mode and optional OpenAI API mode. Manual GPT bridge mode is a durable fallback, not a failure path.

Future local model support should remain possible, but should not be implemented until explicitly scoped.

The note shape stays in the built-in prompt template at `./services/resources/comprehensive_note.md`: title, source URL, overview, key ideas, detailed notes, memorable phrasing, practical takeaways, and tags.

---

# 5. Notion Export

Notion export stays inside Python.

n8n must not contain Notion export logic. Python owns Notion page creation, markdown-to-Notion conversion, metadata extraction, and Notion API calls.

Notion database properties:

- `Name`: title;
- `URL`: YouTube link;
- `Tags`: multi-select;
- `Status`: regular select, not Notion native Status;
- `Source`: regular select, not `rich_text`;
- `Created`: created time managed by Notion.

Recommended `Status` values are `Draft`, `Reviewed`, and `Archived`.

The recommended `Source` value for this pipeline is `YouTube`.

`./services/notion.py` allows empty tags so it can stay a small reusable Notion adapter.

Markdown note metadata convention:

- the first Markdown H1 heading is treated as the note title;
- the note title must use `# Note title`;
- tags are read from a comma-separated `Tags:` line;
- spaces inside multi-word tags are preserved;
- the source URL is not parsed from markdown; it comes from the original CLI or JSON input.

Markdown-to-Notion conversion is intentionally simple. Supported markdown shapes are headings, paragraphs, bullets, numbered lists, quotes, and code blocks.

---

# 6. Transcript Selection Quality

Normal YouTube transcript fetching prefers manual/author transcript quality over generated transcript convenience.

Project-owned discovery and selection prioritize tracks in this order:

1. manual/author transcript in a preferred language;
2. manual/author transcript translated to a preferred language;
3. generated transcript in a preferred language;
4. generated transcript translated to a preferred language;
5. unknown-origin YouTube transcript track in a preferred language;
6. unknown-origin YouTube transcript track with API-provided translation to a preferred language.

A manual/author transcript that requires translation may beat a generated transcript that already matches a preferred language by design. Unknown-origin track are last-resort fallbacks after known manual and generated matches.

Manual transcript-file input bypasses YouTube transcript discovery and selection.

---

# 7. Design Principle

The pipeline should be boring.

Less magic means fewer places where things break without explanation.
