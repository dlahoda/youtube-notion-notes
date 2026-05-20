from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, urlparse


VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")


class TranscriptError(Exception):
    """Raised when a YouTube URL or transcript cannot be processed."""


class _TranscriptDiscoveryUnavailable(Exception):
    """Raised when the installed transcript API cannot list tracks."""


@dataclass(frozen=True)
class TranscriptSnippet:
    start: float
    duration: float
    text: str


@dataclass(frozen=True)
class Transcript:
    video_id: str
    snippets: list[TranscriptSnippet]

    def as_text(self) -> str:
        lines = []
        for snippet in self.snippets:
            timestamp = format_timestamp(snippet.start)
            lines.append(f"[{timestamp}] {snippet.text}")
        return "\n".join(lines).strip() + "\n"


@dataclass(frozen=True)
class TranscriptTranslationLanguage:
    language_code: str
    language_name: str | None


@dataclass(frozen=True)
class TranscriptTrack:
    language_code: str
    language_name: str | None
    is_generated: bool | None
    is_translatable: bool | None
    translation_languages: list[TranscriptTranslationLanguage]


@dataclass(frozen=True)
class TranscriptTrackSelection:
    track: TranscriptTrack
    preferred_language_code: str
    selection_reason: str
    requires_translation: bool


@dataclass(frozen=True)
class _DiscoveredTranscriptTrack:
    raw_track: Any
    metadata: TranscriptTrack


def parse_youtube_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.")

    video_id: str | None = None

    if host == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0]
    elif host in {"youtube.com", "m.youtube.com", "music.youtube.com"}:
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [None])[0]
        else:
            parts = [part for part in parsed.path.split("/") if part]
            if len(parts) >= 2 and parts[0] in {"embed", "shorts", "live"}:
                video_id = parts[1]

    if not video_id or not VIDEO_ID_PATTERN.match(video_id):
        raise TranscriptError("Could not find a valid YouTube video id in the URL.")

    return video_id


def fetch_transcript(video_id: str, languages: list[str]) -> Transcript:
    try:
        discovered_tracks = _discover_transcript_tracks(video_id)
    except _TranscriptDiscoveryUnavailable:
        return _fetch_transcript_by_language_preference(video_id, languages)

    tracks = [discovered_track.metadata for discovered_track in discovered_tracks]
    selection = select_transcript_track(tracks, languages)
    if selection is None:
        available_languages = _format_available_language_codes(tracks)
        message = f"No transcript track matched preferred languages: {', '.join(languages)}."
        if available_languages:
            message = f"{message} Available languages: {available_languages}."
        raise TranscriptError(message)

    raw_track = _raw_track_for_selection(discovered_tracks, selection.track)
    try:
        if selection.requires_translation:
            raw_track = raw_track.translate(selection.preferred_language_code)
        snippets = _fetch_track_snippets(raw_track)
    except Exception as exc:
        raise TranscriptError(f"Could not fetch selected transcript for {video_id}.") from exc

    if not snippets:
        raise TranscriptError(f"No transcript snippets returned for {video_id}.")

    return Transcript(video_id=video_id, snippets=snippets)


def _fetch_transcript_by_language_preference(video_id: str, languages: list[str]) -> Transcript:
    try:
        snippets = _fetch_with_current_api(video_id, languages)
    except AttributeError:
        snippets = _fetch_with_legacy_api(video_id, languages)
    except Exception as exc:
        raise TranscriptError(f"Could not fetch transcript for {video_id}.") from exc

    if not snippets:
        raise TranscriptError(f"No transcript snippets returned for {video_id}.")

    return Transcript(video_id=video_id, snippets=snippets)


def list_transcript_tracks(video_id: str) -> list[TranscriptTrack]:
    try:
        return [
            discovered_track.metadata
            for discovered_track in _discover_transcript_tracks(video_id)
        ]
    except _TranscriptDiscoveryUnavailable as exc:
        raise TranscriptError(f"Could not list transcript tracks for {video_id}.") from exc


def _discover_transcript_tracks(video_id: str) -> list[_DiscoveredTranscriptTrack]:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        api = YouTubeTranscriptApi()
        list_tracks = getattr(api, "list")
    except AttributeError:
        raise _TranscriptDiscoveryUnavailable()

    try:
        transcript_list = list_tracks(video_id)
        return [
            _DiscoveredTranscriptTrack(
                raw_track=track,
                metadata=_normalize_transcript_track(track),
            )
            for track in transcript_list
        ]
    except Exception as exc:
        raise TranscriptError(f"Could not list transcript tracks for {video_id}.") from exc


def select_transcript_track(
    tracks: list[TranscriptTrack],
    preferred_language_codes: list[str],
) -> TranscriptTrackSelection | None:
    """Choose the best discovered track without fetching transcript snippets.

    Tracks with unknown origin are selected only as a last-resort fallback after
    known manual and generated tracks have been considered.
    """

    preferred_languages = [
        language_code.strip()
        for language_code in preferred_language_codes
        if language_code.strip()
    ]

    for reason, origin, requires_translation in (
        ("manual_preferred_language", False, False),
        ("manual_translatable_to_preferred_language", False, True),
        ("generated_preferred_language", True, False),
        ("generated_translatable_to_preferred_language", True, True),
        ("unknown_origin_preferred_language", None, False),
        ("unknown_origin_translatable_to_preferred_language", None, True),
    ):
        selection = _select_first_matching_track(
            tracks,
            preferred_languages,
            is_generated=origin,
            requires_translation=requires_translation,
            selection_reason=reason,
        )
        if selection is not None:
            return selection

    return None


def _fetch_with_current_api(
    video_id: str,
    languages: list[str],
) -> list[TranscriptSnippet]:
    from youtube_transcript_api import YouTubeTranscriptApi

    fetched = YouTubeTranscriptApi().fetch(video_id, languages=languages)
    return _normalize_transcript_snippets(fetched)


def _fetch_track_snippets(track: Any) -> list[TranscriptSnippet]:
    fetched = track.fetch()
    return _normalize_transcript_snippets(fetched)


def _normalize_transcript_snippets(raw_snippets: Any) -> list[TranscriptSnippet]:
    return [
        TranscriptSnippet(
            start=float(snippet.start),
            duration=float(snippet.duration),
            text=str(snippet.text).replace("\n", " ").strip(),
        )
        for snippet in raw_snippets
    ]


def _fetch_with_legacy_api(
    video_id: str,
    languages: list[str],
) -> list[TranscriptSnippet]:
    from youtube_transcript_api import YouTubeTranscriptApi

    raw_snippets = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
    return [
        TranscriptSnippet(
            start=float(snippet["start"]),
            duration=float(snippet.get("duration", 0.0)),
            text=str(snippet["text"]).replace("\n", " ").strip(),
        )
        for snippet in raw_snippets
    ]


def _select_first_matching_track(
    tracks: list[TranscriptTrack],
    preferred_languages: list[str],
    *,
    is_generated: bool | None,
    requires_translation: bool,
    selection_reason: str,
) -> TranscriptTrackSelection | None:
    for preferred_language in preferred_languages:
        for track in tracks:
            if track.is_generated is not is_generated:
                continue
            if requires_translation:
                if _track_can_translate_to(track, preferred_language):
                    return TranscriptTrackSelection(
                        track=track,
                        preferred_language_code=preferred_language,
                        selection_reason=selection_reason,
                        requires_translation=True,
                    )
            elif track.language_code == preferred_language:
                return TranscriptTrackSelection(
                    track=track,
                    preferred_language_code=preferred_language,
                    selection_reason=selection_reason,
                    requires_translation=False,
                )

    return None


def _track_can_translate_to(track: TranscriptTrack, language_code: str) -> bool:
    if track.is_translatable is False:
        return False
    return any(
        language.language_code == language_code
        for language in track.translation_languages
    )


def _raw_track_for_selection(
    discovered_tracks: list[_DiscoveredTranscriptTrack],
    selected_track: TranscriptTrack,
) -> Any:
    for discovered_track in discovered_tracks:
        if discovered_track.metadata is selected_track:
            return discovered_track.raw_track
    for discovered_track in discovered_tracks:
        if discovered_track.metadata == selected_track:
            return discovered_track.raw_track
    raise TranscriptError("Selected transcript track was not available for fetching.")


def _format_available_language_codes(tracks: list[TranscriptTrack]) -> str:
    language_codes = sorted(
        {
            track.language_code
            for track in tracks
            if track.language_code.strip()
        }
    )
    return ", ".join(language_codes)


def _normalize_transcript_track(track: Any) -> TranscriptTrack:
    translation_languages = _get_value(track, "translation_languages", [])
    if translation_languages is None:
        translation_languages = []

    return TranscriptTrack(
        language_code=str(_get_value(track, "language_code", "")),
        language_name=_optional_str(_get_value(track, "language")),
        is_generated=_optional_bool(_get_value(track, "is_generated")),
        is_translatable=_optional_bool(_get_value(track, "is_translatable")),
        translation_languages=[
            _normalize_translation_language(language)
            for language in translation_languages
        ],
    )


def _normalize_translation_language(language: Any) -> TranscriptTranslationLanguage:
    return TranscriptTranslationLanguage(
        language_code=str(_get_value(language, "language_code", "")),
        language_name=_optional_str(_get_value(language, "language")),
    )


def _get_value(source: Any, name: str, default: Any = None) -> Any:
    if isinstance(source, Mapping):
        return source.get(name, default)
    return getattr(source, name, default)


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(value)


def format_timestamp(seconds: float) -> str:
    total_seconds = int(seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"
