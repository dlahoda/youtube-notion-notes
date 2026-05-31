# Development

## Local developer shortcuts

The `make` targets are convenience commands for local development. They are not the main pipeline contract; `./docs/usage.md` covers the normal CLI examples.

To use a repeated local sample URL, copy the template and set `YNN_SAMPLE_URL`:

```bash
cp .local.mk.example .local.mk
```

`./.local.mk`

```make
YNN_SAMPLE_URL := https://youtu.be/VIDEO_ID
```

`./.local.mk` is local-only config and should not be committed. Keeping the sample URL there avoids manually editing placeholder `VIDEO_ID` values in repeated commands.

Run the test shortcut:

```bash
make test
```

Run the local ingest sample:

```bash
make ingest-sample
```

Run the Notion export sample:

```bash
make notion-sample
```

`make notion-sample` uses `--export notion`, so it requires the normal Notion/OpenAI prerequisites for a full generated-note export: a generated markdown note, `OPENAI_API_KEY`, `NOTION_API_KEY`, and `NOTION_DATABASE_ID`.

## Install smoke tests

Optional editable-install smoke verification:

```bash
YNN_RUN_EDITABLE_INSTALL_SMOKE=1 python -m unittest tests.test_editable_install_smoke
```

This smoke creates a temporary virtual environment and skips itself if local Python venv support is unavailable.

Optional regular-install smoke verification:

```bash
YNN_RUN_REGULAR_INSTALL_SMOKE=1 python -m unittest tests.test_regular_install_smoke
```
