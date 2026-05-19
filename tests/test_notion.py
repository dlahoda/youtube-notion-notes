from __future__ import annotations

import os
import sys
import types
import unittest
from unittest.mock import Mock, patch

from youtube_notion_notes.services.notion import create_notion_page


class NotionTests(unittest.TestCase):
    def test_create_notion_page_passes_children_and_properties_to_client(self) -> None:
        children = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "Body"},
                        }
                    ],
                },
            }
        ]
        fake_client = Mock()
        fake_client.pages.create.return_value = {
            "id": "fake-page-id",
            "url": "https://www.notion.so/Real-Canonical-Url-From-Api",
            "public_url": "https://published.example/not-used",
        }
        client_class = Mock(return_value=fake_client)
        fake_notion_client_module = types.SimpleNamespace(Client=client_class)

        with (
            patch.dict(
                os.environ,
                {
                    "NOTION_API_KEY": "secret",
                    "NOTION_DATABASE_ID": "database-123",
                },
            ),
            patch.dict(sys.modules, {"notion_client": fake_notion_client_module}),
        ):
            page = create_notion_page(
                title="Video Note",
                url="https://youtu.be/example",
                tags=["python", "note taking"],
                status="Draft",
                source="YouTube",
                children=children,
            )

        self.assertEqual(page.id, "fake-page-id")
        self.assertEqual(page.url, "https://www.notion.so/Real-Canonical-Url-From-Api")
        self.assertNotEqual(page.url, "https://published.example/not-used")
        client_class.assert_called_once_with(auth="secret")
        fake_client.pages.create.assert_called_once()

        call_kwargs = fake_client.pages.create.call_args.kwargs
        self.assertEqual(call_kwargs["parent"], {"database_id": "database-123"})
        self.assertEqual(call_kwargs["children"], children)

        properties = call_kwargs["properties"]
        self.assertEqual(properties["Name"]["title"][0]["text"]["content"], "Video Note")
        self.assertEqual(properties["URL"]["url"], "https://youtu.be/example")
        self.assertEqual(
            properties["Tags"]["multi_select"],
            [{"name": "python"}, {"name": "note taking"}],
        )
        self.assertEqual(properties["Status"]["select"]["name"], "Draft")
        self.assertEqual(properties["Source"]["select"]["name"], "YouTube")


if __name__ == "__main__":
    unittest.main()
