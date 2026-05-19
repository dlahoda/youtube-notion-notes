from __future__ import annotations

from dataclasses import dataclass
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


class NotionPageCreationError(Exception):
    """Raised when a Notion page cannot be created."""


@dataclass(frozen=True)
class NotionPage:
    id: str
    url: str | None = None


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
        raise NotionPageCreationError(f"{name} is required for Notion page creation.")
    return value


def _page_properties(
    *,
    title: str,
    url: str,
    tags: list[str] | None,
    status: str,
    source: str,
) -> dict[str, Any]:
    return {
        "Name": {
            "title": [
                {
                    "text": {
                        "content": title,
                    },
                }
            ],
        },
        "URL": {
            "url": url,
        },
        "Tags": {
            "multi_select": [{"name": tag} for tag in tags or []],
        },
        "Status": {
            "select": {
                "name": status,
            },
        },
        "Source": {
            "select": {
                "name": source,
            },
        },
    }


def create_notion_page(
    *,
    title: str,
    url: str,
    tags: list[str] | None = None,
    status: str = "Draft",
    source: str = "YouTube",
    children: list[dict] | None = None,
) -> NotionPage:
    title = title.strip()
    url = url.strip()
    status = status.strip()
    source = source.strip()
    clean_tags = [tag.strip() for tag in tags or [] if tag.strip()]

    if not title:
        raise NotionPageCreationError("title is required.")
    if not url:
        raise NotionPageCreationError("url is required.")
    if not status:
        raise NotionPageCreationError("status is required.")
    if not source:
        raise NotionPageCreationError("source is required.")

    api_key = required_env("NOTION_API_KEY")
    database_id = required_env("NOTION_DATABASE_ID")

    try:
        from notion_client import Client
    except ImportError as exc:
        raise NotionPageCreationError(
            "notion-client is not installed. Run: python -m pip install -r requirements.txt"
        ) from exc

    client = Client(auth=api_key)

    try:
        page_payload: dict[str, Any] = {
            "parent": {"database_id": database_id},
            "properties": _page_properties(
                title=title,
                url=url,
                tags=clean_tags,
                status=status,
                source=source,
            ),
        }
        if children:
            page_payload["children"] = children

        page = client.pages.create(
            **page_payload,
        )
    except Exception as exc:
        raise NotionPageCreationError(f"Notion page creation failed: {exc}") from exc

    page_id = page.get("id")
    if not page_id:
        raise NotionPageCreationError("Notion page was created, but no page id was returned.")

    page_url = page.get("url")
    return NotionPage(
        id=str(page_id),
        url=str(page_url) if page_url else None,
    )


def create_smoke_test_page() -> str:
    try:
        page = create_notion_page(
            title=SMOKE_TEST_NAME,
            url=SMOKE_TEST_URL,
            tags=SMOKE_TEST_TAGS,
            status=SMOKE_TEST_STATUS,
            source=SMOKE_TEST_SOURCE,
        )
        return page.id
    except NotionPageCreationError as exc:
        raise NotionSmokeTestError(str(exc)) from exc


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
