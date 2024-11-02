"""Music Queue Types."""

from enum import StrEnum


class SourceType(StrEnum):
    """SourceHandler types."""

    NULL = "null"
    YOUTUBE = "youtube"
    SPOTIFY = "spotify"
