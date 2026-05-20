from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from youtube_notion_notes.config import ConfigFileError, parse_dotenv, user_config_path
from youtube_notion_notes.services.pipeline import OUTPUT_DIR_ENV_VAR


OPTIONAL_CONFIG_PROMPTS = (
    ("OPENAI_API_KEY", "OpenAI API key (optional, empty to skip): ", True),
    ("NOTION_API_KEY", "Notion API key (optional, empty to skip): ", True),
    ("NOTION_DATABASE_ID", "Notion database ID (optional, empty to skip): ", False),
)


class InitArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = InitArgumentParser(description="Create or update youtube-notion-notes user config.")
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Persistent output root for transcript, prompt, and note files.",
    )
    return parser.parse_args(argv)


def append_env_value(path: Path, key: str, value: str) -> None:
    if path.exists():
        existing_text = path.read_text(encoding="utf-8")
        separator = "" if not existing_text or existing_text.endswith("\n") else "\n"
        path.write_text(f"{existing_text}{separator}{key}={value}\n", encoding="utf-8")
        return

    path.write_text(f"{key}={value}\n", encoding="utf-8")


def init_output_dir(output_dir: str, *, config_path: Path | None = None) -> Path:
    path = config_path or user_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    requested_output_dir = Path(output_dir).expanduser()
    existing_values = parse_dotenv(path) if path.exists() else {}
    configured_output_dir = requested_output_dir

    if OUTPUT_DIR_ENV_VAR in existing_values:
        configured_output_dir = Path(existing_values[OUTPUT_DIR_ENV_VAR]).expanduser()
    else:
        append_env_value(path, OUTPUT_DIR_ENV_VAR, str(requested_output_dir))

    configured_output_dir.mkdir(parents=True, exist_ok=True)
    return path


def init_optional_config(config_path: Path) -> None:
    existing_values = parse_dotenv(config_path) if config_path.exists() else {}

    for key, prompt, is_secret in OPTIONAL_CONFIG_PROMPTS:
        if key in existing_values:
            print(f"{key} already configured; leaving existing value unchanged.")
            continue

        value = getpass.getpass(prompt).strip() if is_secret else input(prompt).strip()
        if not value:
            continue

        append_env_value(config_path, key, value)
        existing_values[key] = value


def init_user_config(output_dir: str, *, config_path: Path | None = None) -> Path:
    path = init_output_dir(output_dir, config_path=config_path)
    init_optional_config(path)
    return path


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        config_path = init_user_config(args.output_dir)
    except ValueError as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2
    except (ConfigFileError, OSError) as exc:
        print(f"Init error: {exc}", file=sys.stderr)
        return 1

    print(f"Config ready: {config_path}")
    return 0
