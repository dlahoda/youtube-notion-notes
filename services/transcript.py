from __future__ import annotations

import re
from dataclasses import dataclass
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


def format_timestamp(seconds: float) -> str:
    total_seconds = int(seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"
