# Future Ideas and Optional Backlog

This document parks future ideas and optional backlog items that are not current scope.

Items here are not active contracts, not implementation instructions, and not part of current product or CLI behavior. Promote an item into `./design-doc.md` before treating it as scoped work.

Durable architecture decisions still live in `./docs/decisions.md`.

---

# Ideas

## Long Video Handling

- Add long-video chunking and map-reduce note generation for transcripts that do not fit into one LLM request.

## n8n Orchestration

- Construct payloads through upstream n8n nodes instead of relying only on hardcoded smoke payloads.
- Add n8n notification or audit branches.
- Add scheduled n8n triggers.
- Improve retry and reporting behavior.

## Transcript Sources and Input Modes

- Add broader transcript input modes.
- Add alternative transcript providers.
- Add Whisper or local transcription.

## Execution Model

- Explore a hosted or remote execution model.
- Add an optional HTTP wrapper if local command execution stops being enough.
- Package the CLI as an installable command for a future `v1.0.0`; this is not part of the repo-local launcher usability closeout for `v0.9.0`.
