from pipo_dispatch.audio_source.base_handler import BaseHandler
from pipo_dispatch.audio_source.null_handler import NullHandler
from pipo_dispatch.audio_source.spotify_handler import SpotifyHandler
from pipo_dispatch.audio_source.youtube_handler import (
    YoutubeHandler,
    YoutubeQueryHandler,
)


class SourceFactory:
    """Source handler factory."""

    @staticmethod
    def get_source(source_type: str) -> BaseHandler:
        """Get source by name."""
        handlers = (
            SpotifyHandler,
            YoutubeHandler,
            YoutubeQueryHandler,
            NullHandler,
        )
        return {handler.name: handler for handler in handlers}.get(
            source_type, NullHandler.name
        )
