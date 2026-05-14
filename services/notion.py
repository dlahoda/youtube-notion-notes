from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any


SMOKE_TEST_NAME = "Notion smoke test"
SMOKE_TEST_URL = "https://www.youtube.com/watch?v=notion-smoke-test"
SMOKE_TEST_SOURCE = "YouTube"
SMOKE_TEST_STATUS = "Draft"
SMOKE_TEST_TAGS = ["smoke-test"]


class NotionSmokeTestError(Exception):
    """Raised when the Notion smoke test cannot complete."""


def load_env_file(path: Path = Path(".env")) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise NotionSmokeTestError(f"{name} is required for the Notion smoke test.")
    return value


def smoke_test_properties() -> dict[str, Any]:
    return {
        "Name": {
            "title": [
                {
                    "text": {
                        "content": SMOKE_TEST_NAME,
                    },
                }
            ],
        },
        "URL": {
            "url": SMOKE_TEST_URL,
        },
        "Tags": {
            "multi_select": [{"name": tag} for tag in SMOKE_TEST_TAGS],
        },
        "Status": {
            "select": {
                "name": SMOKE_TEST_STATUS,
            },
        },
        "Source": {
            "select": {
                "name": SMOKE_TEST_SOURCE,
            },
        },
    }


def create_smoke_test_page() -> str:
    api_key = required_env("NOTION_API_KEY")
    database_id = required_env("NOTION_DATABASE_ID")

    try:
        from notion_client import Client
    except ImportError as exc:
        raise NotionSmokeTestError(
            "notion-client is not installed. Run: python -m pip install -r requirements.txt"
        ) from exc

    client = Client(auth=api_key)

    try:
        page = client.pages.create(
            parent={"database_id": database_id},
            properties=smoke_test_properties(),
        )
    except Exception as exc:
        raise NotionSmokeTestError(f"Notion page creation failed: {exc}") from exc

    page_id = page.get("id")
    if not page_id:
        raise NotionSmokeTestError("Notion page was created, but no page id was returned.")

    return str(page_id)


def main() -> int:
    load_env_file()

    try:
        page_id = create_smoke_test_page()
    except NotionSmokeTestError as exc:
        print(f"Notion smoke test failed: {exc}", file=sys.stderr)
        return 1

    print(f"Notion smoke test page created: {page_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
