# Changelog

All notable changes to this project will be documented in this file.

## v1.0.0 - 2026-06-01

### Added

- Added local package install support with console script entrypoints:
  `ynn`, `ynn-note`, `ynn-notion`, and `ynn-prompt`. Editable installs
  depend on the repository checkout; regular `python -m pip install .` is the
  portable local install path.
- Added the `ynn init` setup helper.
- Added user config fallback at `~/.config/youtube-notion-notes/.env`.
- Added optional `ynn init` prompts for transcript languages, OpenAI config,
  and Notion config.
- Added optional regular-install smoke verification.
- Added transcript selection metadata in human and JSON output.
- Added the All Rights Reserved / source-visible licensing notice.
- Added third-party dependency notices.

### Changed

- Packaged CLI modules under `./youtube_notion_notes/`.
- Moved service modules under `./youtube_notion_notes/services/`.
- Switched prompt template handling to package-owned resources.
- Updated output and config path policy for installed CLI use.
- Aligned README setup guidance around installed CLI usage.
- Focused `./design-doc.md` on current contracts and source-of-truth material;
  completed milestone and slice history now lives in
  `./docs/archive/milestone-history.md`.
- Normal YouTube transcript fetching now uses project-owned discovery and
  selection.

### Fixed / Hardened

- Notion export config preflight fails before transcript, prompt, note, or
  Notion work when required config is missing.
- Manual and author YouTube tracks are preferred over generated tracks.
- Translated manual tracks may beat generated preferred-language tracks by
  design.
- Unknown-origin YouTube tracks are last-resort fallbacks.
- `--transcript-file` bypasses YouTube discovery and selection.
- JSON output keeps existing fields valid and adds `transcript_selection`
  additively.

## v0.9.0

### Changed

- Closed out repo-local launcher usability for day-to-day CLI use.

## v0.8.0

### Changed

- Split ingest CLI tests by responsibility.

## v0.7.0

### Added

- Added JSON transcript-file fallback input.

## v0.6.0

### Added

- Added manual transcript-file fallback input.

## v0.5.0

### Changed

- Refactored the pipeline core into clearer responsibilities.

## v0.4.0

### Added

- Added the n8n integration contract and smoke workflow.

## v0.3.0

### Added

- Added the local CLI automation contract with JSON input and output.

## v0.2.0

### Added

- Added opt-in Notion export, its official Python client dependency, and the manual Notion smoke test.
- Documented the Notion export contract before the integration was added.

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
