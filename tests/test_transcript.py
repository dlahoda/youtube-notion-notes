from __future__ import annotations

import sys
import types
import unittest
from dataclasses import dataclass
from unittest.mock import patch

from youtube_notion_notes.services.transcript import (
    TranscriptError,
    TranscriptSnippet,
    TranscriptTrack,
    TranscriptTranslationLanguage,
    fetch_transcript,
    list_transcript_tracks,
)


VIDEO_ID = "abc123def45"


@dataclass(frozen=True)
class FakeSnippet:
    start: float
    duration: float
    text: str


@dataclass(frozen=True)
class FakeTranslationLanguage:
    language_code: str
    language: str


class FakeTrack:
    def __init__(
        self,
        *,
        language_code: str,
        language: str,
        is_generated: bool,
        translation_languages: list[FakeTranslationLanguage] | None = None,
    ) -> None:
        self.language_code = language_code
        self.language = language
        self.is_generated = is_generated
        self.translation_languages = translation_languages or []

    @property
    def is_translatable(self) -> bool:
        return bool(self.translation_languages)


class TranscriptServiceTests(unittest.TestCase):
    def fake_youtube_module(self, api_class: type) -> types.ModuleType:
        fake_module = types.ModuleType("youtube_transcript_api")
        fake_module.YouTubeTranscriptApi = api_class
        return fake_module

    def test_fetch_transcript_keeps_current_language_based_api_behavior(self) -> None:
        calls = []

        class FakeYouTubeTranscriptApi:
            def fetch(self, video_id: str, *, languages: list[str]) -> list[FakeSnippet]:
                calls.append((video_id, languages))
                return [
                    FakeSnippet(start=0.0, duration=1.5, text="Hello\nworld"),
                    FakeSnippet(start=65.0, duration=2.0, text=" Next line "),
                ]

        with patch.dict(
            sys.modules,
            {"youtube_transcript_api": self.fake_youtube_module(FakeYouTubeTranscriptApi)},
        ):
            transcript = fetch_transcript(VIDEO_ID, ["uk", "en"])

        self.assertEqual(calls, [(VIDEO_ID, ["uk", "en"])])
        self.assertEqual(transcript.video_id, VIDEO_ID)
        self.assertEqual(
            transcript.snippets,
            [
                TranscriptSnippet(start=0.0, duration=1.5, text="Hello world"),
                TranscriptSnippet(start=65.0, duration=2.0, text="Next line"),
            ],
        )

    def test_list_transcript_tracks_normalizes_available_track_metadata(self) -> None:
        calls = []
        tracks = [
            FakeTrack(
                language_code="en",
                language="English",
                is_generated=False,
                translation_languages=[
                    FakeTranslationLanguage(language_code="uk", language="Ukrainian"),
                    FakeTranslationLanguage(language_code="de", language="German"),
                ],
            ),
            FakeTrack(
                language_code="es",
                language="Spanish (auto-generated)",
                is_generated=True,
            ),
        ]

        class FakeYouTubeTranscriptApi:
            def list(self, video_id: str) -> list[FakeTrack]:
                calls.append(video_id)
                return tracks

        with patch.dict(
            sys.modules,
            {"youtube_transcript_api": self.fake_youtube_module(FakeYouTubeTranscriptApi)},
        ):
            discovered = list_transcript_tracks(VIDEO_ID)

        self.assertEqual(calls, [VIDEO_ID])
        self.assertEqual(
            discovered,
            [
                TranscriptTrack(
                    language_code="en",
                    language_name="English",
                    is_generated=False,
                    is_translatable=True,
                    translation_languages=[
                        TranscriptTranslationLanguage(
                            language_code="uk",
                            language_name="Ukrainian",
                        ),
                        TranscriptTranslationLanguage(
                            language_code="de",
                            language_name="German",
                        ),
                    ],
                ),
                TranscriptTrack(
                    language_code="es",
                    language_name="Spanish (auto-generated)",
                    is_generated=True,
                    is_translatable=False,
                    translation_languages=[],
                ),
            ],
        )

    def test_list_transcript_tracks_accepts_mapping_like_metadata(self) -> None:
        class FakeYouTubeTranscriptApi:
            def list(self, video_id: str) -> list[dict[str, object]]:
                return [
                    {
                        "language_code": "fr",
                        "language": "French",
                        "is_generated": False,
                        "is_translatable": True,
                        "translation_languages": [
                            {"language_code": "en", "language": "English"},
                        ],
                    }
                ]

        with patch.dict(
            sys.modules,
            {"youtube_transcript_api": self.fake_youtube_module(FakeYouTubeTranscriptApi)},
        ):
            discovered = list_transcript_tracks(VIDEO_ID)

        self.assertEqual(
            discovered,
            [
                TranscriptTrack(
                    language_code="fr",
                    language_name="French",
                    is_generated=False,
                    is_translatable=True,
                    translation_languages=[
                        TranscriptTranslationLanguage(
                            language_code="en",
                            language_name="English",
                        ),
                    ],
                ),
            ],
        )

    def test_list_transcript_tracks_wraps_api_errors(self) -> None:
        class FakeYouTubeTranscriptApi:
            def list(self, video_id: str) -> list[FakeTrack]:
                raise RuntimeError("captions unavailable")

        with patch.dict(
            sys.modules,
            {"youtube_transcript_api": self.fake_youtube_module(FakeYouTubeTranscriptApi)},
        ):
            with self.assertRaisesRegex(
                TranscriptError,
                "Could not list transcript tracks for abc123def45: captions unavailable",
            ):
                list_transcript_tracks(VIDEO_ID)


if __name__ == "__main__":
    unittest.main()
