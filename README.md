# YouTube Notion Notes

Python CLI that turns one YouTube URL into a local transcript and a ready-to-paste ChatGPT prompt. If OpenAI API config is present, it can also generate a markdown note. Notion export is opt-in after a markdown note is generated locally.

Production n8n automation and web UI are intentionally not implemented.

## Platform support

WSL/Linux is the primary supported path. On Windows, WSL is recommended because it uses the same Linux-style setup, launcher, environment, and shell workflow.

macOS is expected to work, but should be smoke-tested separately before claiming strong support.

Native Windows PowerShell support is best-effort and partial. Direct Python CLI usage and editable package console entrypoints may work when Python is installed on Windows. Repo-local shell launchers, bash wrappers, make-based developer shortcuts, and Unix-style environment examples are not the primary supported path on native Windows.

## Recommended quickstart

Requires Python 3.10+.
Using a virtual environment is recommended, especially on Linux/WSL systems with externally managed Python environments.

From the repository root, use the installed CLI flow:

```bash
python -m pip install -e .
ynn init --output-dir ~/ynn-output
ynn-prompt "https://youtu.be/VIDEO_ID"
```

The minimal first successful path stops at `ynn-prompt`.

`ynn-note` is optional and needs OpenAI config for automatic markdown note generation. `ynn-notion` is optional and needs OpenAI plus Notion config.

## Command requirements

| Command | What it does | OpenAI required? | Notion required? |
| --- | --- | --- | --- |
| `ynn-prompt` | Builds the transcript and ChatGPT-ready prompt, then stops. It does not call OpenAI and does not create a Notion page. | No | No |
| `ynn` | Runs the default local pipeline and can create a generated markdown note when OpenAI config is available. | Only for automatic markdown note generation | No |
| `ynn-note` | Runs local note mode and can create a generated markdown note when OpenAI config is available. | Only for automatic markdown note generation | No |
| `ynn-notion` | Generates a markdown note locally, then exports it to Notion. | Yes | Yes: `NOTION_API_KEY` and `NOTION_DATABASE_ID` |

## Docs

- [Installation](./docs/installation.md)
- [Configuration](./docs/configuration.md)
- [Usage](./docs/usage.md)
- [Notion setup](./docs/notion-setup.md)
- [Automation JSON](./docs/automation-json.md)
- [Development](./docs/development.md)
- [Troubleshooting](./docs/troubleshooting.md)

## License

This repository is source-visible for portfolio and review purposes only.

The project is not open source. No permission is granted to use, copy, modify, redistribute, sublicense, or reuse the code without explicit written permission from the copyright holder.

See `./LICENSE.md` and `./THIRD_PARTY_NOTICES.md` for details.

## Limitations

- YouTube transcript fetching depends on available captions unless `--transcript-file` is used.
- Video titles are not fetched yet; output filenames use the video id unless `--output-name` is provided.
- OpenAI mode is optional and intentionally simple.
- Notion export requires a generated markdown note; prompt-only/manual mode does not export.
- No queueing or web UI exists.
