# Troubleshooting

## Install and command setup

Editable package console scripts depend on the repository checkout path used by `python -m pip install -e .`. Do not delete or move that checkout if you want those installed console scripts to keep working. Use `python -m pip install .` when you want console scripts copied into the environment without depending on this checkout after installation.

Repo-local launcher wrappers also point back to this repository by absolute path. They are not portable after the repository is deleted or moved.

If `ynn init --output-dir PATH` reports a transcript or YouTube URL error, check `command -v ynn`. A stale `~/.local/bin/ynn` can appear before an editable-install console script on `PATH`; reinstall the repo-local wrappers with `bash ./scripts/install-launchers.sh`, remove the stale launcher, or put the editable-install environment earlier on `PATH`.

## Config lookup

Config is optional for local/manual prompt usage. Config source priority is explicit `--env-file PATH`, real process environment variables, cwd `./.env`, user config `~/.config/youtube-notion-notes/.env`, and built-in defaults.

An explicit `--env-file PATH` must exist. For portable installed usage, keep config in `ynn init` user config, process environment variables, or an explicit `--env-file PATH`.

## Transcript fetching

YouTube transcript fetching depends on available captions unless `--transcript-file` is used.

```bash
python ingest.py "https://youtu.be/VIDEO_ID" --transcript-file ./manual-transcript.txt --no-note
```

`--transcript-file` reads UTF-8 transcript text from a local file instead of fetching captions from YouTube. The YouTube URL is still required because it remains the source metadata, video id source, and default output filename source.

## OpenAI note generation

OpenAI mode is not required for `ynn-prompt`, `--no-note`, transcript capture, or prompt generation.

If you expect automatic markdown note generation from `ynn`, `ynn-note`, or direct `python ingest.py` usage, install the optional OpenAI dependency path for your setup and set `OPENAI_API_KEY` through `ynn init`, `.env`, or another supported config source.

## Notion export

Notion export runs only when explicitly requested through `ynn-notion` or `--export notion`, and only after a markdown note has been generated and saved locally.

Generated-note Notion export needs `OPENAI_API_KEY`, `NOTION_API_KEY`, and `NOTION_DATABASE_ID`. It also expects the required Notion database properties documented in `./docs/notion-setup.md`.

## Output locations

Output root priority is `--output-dir PATH`, then `YNN_OUTPUT_DIR`, then `./output` relative to the current working directory.

When no output config is set, the direct CLI writes transcript and prompt files under the current working directory's `./output`. Markdown notes appear under `./output/notes/` only when OpenAI note generation runs.
