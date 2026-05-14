# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

### Planning

- Documented the future Notion export contract without implementing the integration.

## v0.1.0 - 2026-05-14

### Added

- Added local Python CLI entry point in `./ingest.py`.
- Added YouTube transcript extraction in `./services/transcript.py`.
- Added ready-to-paste GPT prompt generation.
- Added local transcript output in `./output/transcripts/`.
- Added local prompt output in `./output/prompts/`.
- Added optional OpenAI markdown note generation in `./services/note_generator.py`.
- Added manual-safe setup instructions in `./README.md`.

### Not included

- No Notion export.
- No n8n workflow.
- No web UI.
