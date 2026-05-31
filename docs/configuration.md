# Configuration

Config is optional for local/manual prompt usage. The recommended installed CLI setup writes user config to `~/.config/youtube-notion-notes/.env`; a cwd `./.env`, process environment variables, and explicit `--env-file PATH` are also supported.

For portable installed usage, keep config in `ynn init` user config, process environment variables, or an explicit `--env-file PATH`. A repo-local `./.env` disappears with the repository checkout.

## Setup helper

The `ynn init --output-dir ~/ynn-output` command is the first-time setup helper.

`ynn init --output-dir PATH` creates or updates:

```text
~/.config/youtube-notion-notes/.env
```

During setup, `ynn init` can optionally collect transcript language preferences, `OPENAI_API_KEY`, `NOTION_API_KEY`, and `NOTION_DATABASE_ID`. Existing user config values are preserved by default. Empty prompt input skips that value.

## Config priority

Config source priority is:

1. explicit `--env-file PATH`;
2. real process environment variables;
3. cwd `./.env`;
4. user config `~/.config/youtube-notion-notes/.env`;
5. built-in defaults.

User config fills missing values only. An explicit `--env-file PATH` must exist.

## Environment variables

- `OPENAI_API_KEY`: optional API key for markdown note generation
- `OPENAI_MODEL`: optional model name, defaults to `gpt-4.1-mini`
- `YOUTUBE_TRANSCRIPT_LANGUAGES`: optional comma-separated language preference list, defaults to `en`
- `YNN_OUTPUT_DIR`: optional output root used when `--output-dir` is not provided
- `NOTION_API_KEY`: required only for Notion export and the manual Notion smoke test
- `NOTION_DATABASE_ID`: required only for Notion export and the manual Notion smoke test

`OPENAI_API_KEY` belongs only to optional OpenAI markdown note generation. It is not required for the Notion smoke test.

## Output root

Output root priority is `--output-dir PATH`, then `YNN_OUTPUT_DIR`, then `./output` relative to the current working directory.

Selected output roots write files under:

- `OUTPUT_ROOT/transcripts/`
- `OUTPUT_ROOT/prompts/`
- `OUTPUT_ROOT/notes/`

Examples:

```bash
ynn-prompt "https://youtu.be/VIDEO_ID" --output-dir ./tmp-output
YNN_OUTPUT_DIR=./tmp-output ynn-prompt "https://youtu.be/VIDEO_ID"
python ingest.py "https://youtu.be/VIDEO_ID" --no-note --output-dir ./tmp-output
ynn-notion "https://youtu.be/VIDEO_ID" --env-file ./notion.env
```
