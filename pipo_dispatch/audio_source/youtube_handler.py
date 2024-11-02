import logging
from typing import Iterable
from enum import StrEnum

from pipo_dispatch.audio_source.base_handler import BaseHandler
from pipo_dispatch.audio_source.source_pair import SourcePair
from pipo_dispatch.audio_source.source_type import SourceType


class YoutubeOperations(StrEnum):
    """Youtube operation types."""

    URL = "url"
    PLAYLIST = "playlist"
    QUERY = "query"


class YoutubeHandler(BaseHandler):
    """Handles youtube url music."""

    name = SourceType.YOUTUBE

    @staticmethod
    def __valid_source(source: Iterable[str]) -> bool:
        """Check whether source is a youtube url."""
        return source and ("youtube" in source) and YoutubeHandler.is_url(source)

    def handle(self, source: str) -> SourcePair:
        if self.__valid_source(source):
            logging.getLogger(__name__).info(
                "Processing youtube audio source '%s'", source
            )
            if "list=" in source:
                return SourcePair(
                    query=source,
                    handler_type=YoutubeHandler.name,
                    operation=YoutubeOperations.PLAYLIST,
                )
            else:
                return SourcePair(
                    query=source,
                    handler_type=YoutubeHandler.name,
                    operation=YoutubeOperations.URL,
                )
        else:
            return super().handle(source)


class YoutubeQueryHandler(BaseHandler):
    """Youtube query handler.

    Handles youtube search queries. Exposes no accept condition therefore should only be
    used as terminal handler.
    """

    name = SourceType.YOUTUBE

    @staticmethod
    def __valid_source(source: str) -> bool:
        """Check whether source is an url."""
        return source and (not source.startswith(("https", "http")))

    def handle(self, source: str) -> SourcePair:
        if self.__valid_source(source):
            logging.getLogger(__name__).info(
                "Processing youtube query audio source '%s'", source
            )
            return SourcePair(
                query=source,
                handler_type=SourceType.YOUTUBE,
                operation=YoutubeOperations.QUERY,
            )
        else:
            return super().handle(source)
