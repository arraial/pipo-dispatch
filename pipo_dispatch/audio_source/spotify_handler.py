from enum import StrEnum
import logging
from typing import Iterable

from pipo_dispatch.audio_source.base_handler import BaseHandler
from pipo_dispatch.audio_source.source_pair import SourcePair
from pipo_dispatch.audio_source.source_type import SourceType


class SpotifyOperations(StrEnum):
    """Spotify operation types."""

    URL = "url"


class SpotifyHandler(BaseHandler):
    """Handles spotify url music."""

    name = SourceType.SPOTIFY

    @staticmethod
    def __valid_source(source: Iterable[str]) -> bool:
        """Check whether source is a spotify url."""
        return source and ("spotify" in source) and SpotifyHandler.is_url(source)

    def handle(self, source: str) -> SourcePair:
        if self.__valid_source(source):
            logging.getLogger(__name__).info(
                "Processing spotify audio source '%s'", source
            )
            return SourcePair(
                query=source, handler_type=SpotifyHandler.name, operation="url"
            )
        else:
            return super().handle(source)
