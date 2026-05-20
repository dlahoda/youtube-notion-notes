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
    select_transcript_track,
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

    def track(
        self,
        language_code: str,
        *,
        is_generated: bool | None,
        translations: list[str] | None = None,
    ) -> TranscriptTrack:
        return TranscriptTrack(
            language_code=language_code,
            language_name=None,
            is_generated=is_generated,
            is_translatable=bool(translations),
            translation_languages=[
                TranscriptTranslationLanguage(
                    language_code=translation,
                    language_name=None,
                )
                for translation in translations or []
            ],
        )

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

    def test_select_track_manual_preferred_language_wins_over_generated_preferred_language(self) -> None:
        manual_english = self.track("en", is_generated=False)
        generated_english = self.track("en", is_generated=True)

        selection = select_transcript_track(
            [generated_english, manual_english],
            ["en"],
        )

        self.assertIsNotNone(selection)
        assert selection is not None
        self.assertEqual(selection.track, manual_english)
        self.assertEqual(selection.selection_reason, "manual_preferred_language")
        self.assertFalse(selection.requires_translation)

    def test_select_track_manual_translatable_wins_over_generated_preferred_language(self) -> None:
        manual_spanish = self.track("es", is_generated=False, translations=["en"])
        generated_english = self.track("en", is_generated=True)

        selection = select_transcript_track(
            [generated_english, manual_spanish],
            ["en"],
        )

        self.assertIsNotNone(selection)
        assert selection is not None
        self.assertEqual(selection.track, manual_spanish)
        self.assertEqual(
            selection.selection_reason,
            "manual_translated_to_preferred_language",
        )
        self.assertTrue(selection.requires_translation)

    def test_select_track_generated_preferred_language_wins_over_generated_translatable(self) -> None:
        generated_spanish = self.track("es", is_generated=True, translations=["en"])
        generated_english = self.track("en", is_generated=True)

        selection = select_transcript_track(
            [generated_spanish, generated_english],
            ["en"],
        )

        self.assertIsNotNone(selection)
        assert selection is not None
        self.assertEqual(selection.track, generated_english)
        self.assertEqual(selection.selection_reason, "generated_preferred_language")
        self.assertFalse(selection.requires_translation)

    def test_select_track_respects_preferred_language_order(self) -> None:
        manual_english = self.track("en", is_generated=False)
        manual_ukrainian = self.track("uk", is_generated=False)

        selection = select_transcript_track(
            [manual_english, manual_ukrainian],
            ["uk", "en"],
        )

        self.assertIsNotNone(selection)
        assert selection is not None
        self.assertEqual(selection.track, manual_ukrainian)
        self.assertEqual(selection.preferred_language_code, "uk")

    def test_select_track_returns_none_when_no_track_matches_policy(self) -> None:
        selection = select_transcript_track(
            [
                self.track("fr", is_generated=False),
                self.track("de", is_generated=True),
            ],
            ["en"],
        )

        self.assertIsNone(selection)

    def test_select_track_unknown_origin_does_not_outrank_known_generated_track(self) -> None:
        unknown_english = self.track("en", is_generated=None)
        generated_spanish = self.track("es", is_generated=True, translations=["en"])

        selection = select_transcript_track(
            [unknown_english, generated_spanish],
            ["en"],
        )

        self.assertIsNotNone(selection)
        assert selection is not None
        self.assertEqual(selection.track, generated_spanish)
        self.assertEqual(
            selection.selection_reason,
            "generated_translated_to_preferred_language",
        )


if __name__ == "__main__":
    unittest.main()
