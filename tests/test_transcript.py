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


class FakeRuntimeTrack(FakeTrack):
    def __init__(
        self,
        *,
        language_code: str,
        language: str,
        is_generated: bool | None,
        calls: list[tuple[str, str]],
        snippet_text: str,
        translation_languages: list[FakeTranslationLanguage] | None = None,
    ) -> None:
        super().__init__(
            language_code=language_code,
            language=language,
            is_generated=is_generated,  # type: ignore[arg-type]
            translation_languages=translation_languages,
        )
        self.calls = calls
        self.snippet_text = snippet_text
        self.translated_to: str | None = None

    def fetch(self) -> list[FakeSnippet]:
        self.calls.append(("fetch", self.language_code))
        return [FakeSnippet(start=3.0, duration=2.0, text=self.snippet_text)]

    def translate(self, language_code: str) -> "FakeRuntimeTrack":
        self.calls.append(("translate", language_code))
        translated_track = FakeRuntimeTrack(
            language_code=language_code,
            language=f"Translated {language_code}",
            is_generated=self.is_generated,
            calls=self.calls,
            snippet_text=f"{self.snippet_text} translated to {language_code}",
        )
        translated_track.translated_to = language_code
        return translated_track


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

    def test_fetch_transcript_does_not_fallback_when_list_method_raises_attribute_error(self) -> None:
        calls = []

        class FakeYouTubeTranscriptApi:
            def list(self, video_id: str) -> list[FakeSnippet]:
                calls.append(("list", video_id))
                raise AttributeError("list failed internally")

            def fetch(self, video_id: str, *, languages: list[str]) -> list[FakeSnippet]:
                calls.append(("fetch", video_id))
                return [FakeSnippet(start=0.0, duration=1.0, text="Fallback")]

        with patch.dict(
            sys.modules,
            {"youtube_transcript_api": self.fake_youtube_module(FakeYouTubeTranscriptApi)},
        ):
            with self.assertRaisesRegex(
                TranscriptError,
                "Could not list transcript tracks for abc123def45.",
            ):
                fetch_transcript(VIDEO_ID, ["en"])

        self.assertEqual(calls, [("list", VIDEO_ID)])

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
                "Could not list transcript tracks for abc123def45.",
            ):
                list_transcript_tracks(VIDEO_ID)

    def test_fetch_transcript_uses_discovery_selection_and_fetches_manual_preferred_language(self) -> None:
        calls: list[tuple[str, str]] = []
        manual_english = FakeRuntimeTrack(
            language_code="en",
            language="English",
            is_generated=False,
            calls=calls,
            snippet_text="Manual English",
        )
        generated_english = FakeRuntimeTrack(
            language_code="en",
            language="English (auto-generated)",
            is_generated=True,
            calls=calls,
            snippet_text="Generated English",
        )

        class FakeYouTubeTranscriptApi:
            def list(self, video_id: str) -> list[FakeRuntimeTrack]:
                calls.append(("list", video_id))
                return [generated_english, manual_english]

        with patch.dict(
            sys.modules,
            {"youtube_transcript_api": self.fake_youtube_module(FakeYouTubeTranscriptApi)},
        ):
            transcript = fetch_transcript(VIDEO_ID, ["en"])

        self.assertEqual(calls, [("list", VIDEO_ID), ("fetch", "en")])
        self.assertEqual(transcript.video_id, VIDEO_ID)
        self.assertEqual(
            transcript.snippets,
            [TranscriptSnippet(start=3.0, duration=2.0, text="Manual English")],
        )

    def test_fetch_transcript_translates_manual_track_before_generated_preferred_language(self) -> None:
        calls: list[tuple[str, str]] = []
        manual_spanish = FakeRuntimeTrack(
            language_code="es",
            language="Spanish",
            is_generated=False,
            translation_languages=[
                FakeTranslationLanguage(language_code="en", language="English"),
            ],
            calls=calls,
            snippet_text="Manual Spanish",
        )
        generated_english = FakeRuntimeTrack(
            language_code="en",
            language="English (auto-generated)",
            is_generated=True,
            calls=calls,
            snippet_text="Generated English",
        )

        class FakeYouTubeTranscriptApi:
            def list(self, video_id: str) -> list[FakeRuntimeTrack]:
                calls.append(("list", video_id))
                return [generated_english, manual_spanish]

        with patch.dict(
            sys.modules,
            {"youtube_transcript_api": self.fake_youtube_module(FakeYouTubeTranscriptApi)},
        ):
            transcript = fetch_transcript(VIDEO_ID, ["en"])

        self.assertEqual(
            calls,
            [("list", VIDEO_ID), ("translate", "en"), ("fetch", "en")],
        )
        self.assertEqual(
            transcript.snippets,
            [
                TranscriptSnippet(
                    start=3.0,
                    duration=2.0,
                    text="Manual Spanish translated to en",
                )
            ],
        )

    def test_fetch_transcript_uses_unknown_origin_only_when_no_known_track_matches(self) -> None:
        calls: list[tuple[str, str]] = []
        unknown_english = FakeRuntimeTrack(
            language_code="en",
            language="English",
            is_generated=None,
            calls=calls,
            snippet_text="Unknown English",
        )
        generated_german = FakeRuntimeTrack(
            language_code="de",
            language="German (auto-generated)",
            is_generated=True,
            calls=calls,
            snippet_text="Generated German",
        )

        class FakeYouTubeTranscriptApi:
            def list(self, video_id: str) -> list[FakeRuntimeTrack]:
                calls.append(("list", video_id))
                return [unknown_english, generated_german]

        with patch.dict(
            sys.modules,
            {"youtube_transcript_api": self.fake_youtube_module(FakeYouTubeTranscriptApi)},
        ):
            transcript = fetch_transcript(VIDEO_ID, ["en"])

        self.assertEqual(calls, [("list", VIDEO_ID), ("fetch", "en")])
        self.assertEqual(
            transcript.snippets,
            [TranscriptSnippet(start=3.0, duration=2.0, text="Unknown English")],
        )

    def test_fetch_transcript_fails_cleanly_when_no_track_matches_policy(self) -> None:
        class FakeYouTubeTranscriptApi:
            def list(self, video_id: str) -> list[FakeTrack]:
                return [
                    FakeTrack(language_code="fr", language="French", is_generated=False),
                    FakeTrack(language_code="de", language="German", is_generated=True),
                ]

        with patch.dict(
            sys.modules,
            {"youtube_transcript_api": self.fake_youtube_module(FakeYouTubeTranscriptApi)},
        ):
            with self.assertRaisesRegex(
                TranscriptError,
                "No transcript track matched preferred languages: en. Available languages: de, fr.",
            ):
                fetch_transcript(VIDEO_ID, ["en"])

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
            "manual_translatable_to_preferred_language",
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
            "generated_translatable_to_preferred_language",
        )

    def test_select_track_unknown_preferred_language_is_last_resort_fallback(self) -> None:
        unknown_english = self.track("en", is_generated=None)

        selection = select_transcript_track(
            [unknown_english],
            ["en"],
        )

        self.assertIsNotNone(selection)
        assert selection is not None
        self.assertEqual(selection.track, unknown_english)
        self.assertEqual(selection.selection_reason, "unknown_origin_preferred_language")
        self.assertFalse(selection.requires_translation)

    def test_select_track_unknown_translatable_is_last_resort_fallback(self) -> None:
        unknown_spanish = self.track("es", is_generated=None, translations=["en"])

        selection = select_transcript_track(
            [unknown_spanish],
            ["en"],
        )

        self.assertIsNotNone(selection)
        assert selection is not None
        self.assertEqual(selection.track, unknown_spanish)
        self.assertEqual(
            selection.selection_reason,
            "unknown_origin_translatable_to_preferred_language",
        )
        self.assertTrue(selection.requires_translation)

    def test_select_track_known_generated_preferred_outranks_unknown_preferred(self) -> None:
        unknown_english = self.track("en", is_generated=None)
        generated_english = self.track("en", is_generated=True)

        selection = select_transcript_track(
            [unknown_english, generated_english],
            ["en"],
        )

        self.assertIsNotNone(selection)
        assert selection is not None
        self.assertEqual(selection.track, generated_english)
        self.assertEqual(selection.selection_reason, "generated_preferred_language")

    def test_select_track_known_generated_translatable_outranks_unknown_preferred(self) -> None:
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
            "generated_translatable_to_preferred_language",
        )

    def test_select_track_known_manual_translatable_outranks_unknown_preferred(self) -> None:
        unknown_english = self.track("en", is_generated=None)
        manual_spanish = self.track("es", is_generated=False, translations=["en"])

        selection = select_transcript_track(
            [unknown_english, manual_spanish],
            ["en"],
        )

        self.assertIsNotNone(selection)
        assert selection is not None
        self.assertEqual(selection.track, manual_spanish)
        self.assertEqual(
            selection.selection_reason,
            "manual_translatable_to_preferred_language",
        )


if __name__ == "__main__":
    unittest.main()
