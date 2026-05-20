from __future__ import annotations

import os
from pathlib import Path


USER_CONFIG_DIR = Path("~/.config/youtube-notion-notes")
USER_CONFIG_FILE = USER_CONFIG_DIR / ".env"


class ConfigFileError(Exception):
    pass


def user_config_path() -> Path:
    return USER_CONFIG_FILE.expanduser()


def parse_dotenv(path: Path, *, source_label: str = "env file") -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ConfigFileError(f"Unable to read {source_label} '{path}': {exc.strerror}.") from exc

    values: dict[str, str] = {}
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def read_optional_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return parse_dotenv(path)


def read_required_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        raise ConfigFileError(f"Unable to read --env-file '{path}': file does not exist.")
    return parse_dotenv(path, source_label="--env-file")


def load_runtime_config(
    *,
    explicit_env_file: Path | None = None,
    cwd_env_file: Path = Path(".env"),
    user_env_file: Path | None = None,
    include_user_config: bool = True,
) -> None:
    user_values = read_optional_dotenv(user_env_file or user_config_path()) if include_user_config else {}
    cwd_values = read_optional_dotenv(cwd_env_file)
    process_values = dict(os.environ)
    explicit_values = read_required_dotenv(explicit_env_file) if explicit_env_file else {}

    merged = {
        **user_values,
        **cwd_values,
        **process_values,
        **explicit_values,
    }
    os.environ.update(merged)
