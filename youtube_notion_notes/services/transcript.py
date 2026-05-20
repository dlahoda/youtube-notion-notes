from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, urlparse


VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")


class TranscriptError(Exception):
    """Raised when a YouTube URL or transcript cannot be processed."""


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
        snippets = _fetch_with_current_api(video_id, languages)
    except AttributeError:
        snippets = _fetch_with_legacy_api(video_id, languages)
    except Exception as exc:
        raise TranscriptError(f"Could not fetch transcript for {video_id}: {exc}") from exc

    if not snippets:
        raise TranscriptError(f"No transcript snippets returned for {video_id}.")

    return Transcript(video_id=video_id, snippets=snippets)


def list_transcript_tracks(video_id: str) -> list[TranscriptTrack]:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        transcript_list = YouTubeTranscriptApi().list(video_id)
        return [_normalize_transcript_track(track) for track in transcript_list]
    except Exception as exc:
        raise TranscriptError(f"Could not list transcript tracks for {video_id}: {exc}") from exc


def _fetch_with_current_api(
    video_id: str,
    languages: list[str],
) -> list[TranscriptSnippet]:
    from youtube_transcript_api import YouTubeTranscriptApi

    fetched = YouTubeTranscriptApi().fetch(video_id, languages=languages)
    return [
        TranscriptSnippet(
            start=float(snippet.start),
            duration=float(snippet.duration),
            text=str(snippet.text).replace("\n", " ").strip(),
        )
        for snippet in fetched
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
