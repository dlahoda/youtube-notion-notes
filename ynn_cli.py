from __future__ import annotations

import sys

import ingest


def run_with_appended_args(extra_args: list[str] | None = None) -> int:
    original_argv = sys.argv[:]
    sys.argv = [*original_argv, *(extra_args or [])]
    try:
        return ingest.main()
    finally:
        sys.argv = original_argv


def main() -> int:
    return run_with_appended_args()


def main_note() -> int:
    return run_with_appended_args(["--export", "local"])


def main_notion() -> int:
    return run_with_appended_args(["--export", "notion"])


def main_prompt() -> int:
    return run_with_appended_args(["--no-note"])
