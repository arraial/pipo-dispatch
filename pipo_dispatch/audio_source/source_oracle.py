import random
from typing import Iterable, Iterator

from pipo_dispatch.audio_source.base_handler import BaseHandler
from pipo_dispatch.audio_source.source_pair import SourcePair
from pipo_dispatch.audio_source.spotify_handler import SpotifyHandler
from pipo_dispatch.audio_source.youtube_handler import (
    YoutubeHandler,
    YoutubeQueryHandler,
)


class SourceOracle:
    """Based on received queries provides the most appropriate source handlers."""

    @staticmethod
    def __handlers() -> BaseHandler:
        """Provide handler chain."""
        handlers = YoutubeHandler()
        handlers.set_next(SpotifyHandler()).set_next(YoutubeQueryHandler())
        return handlers

    @staticmethod
    def process_queries(
        queries: Iterable[str],
        shuffle: bool = False,
    ) -> Iterator[SourcePair]:
        """Match queries with most fitting handlers.

        Parameters
        ----------
        queries : Iterable[str]
            Queries to process.

        Returns
        -------
        Iterable[SourcePair]
            Based on queries provides the most appropriate source handler pairs.
        """
        handlers = SourceOracle.__handlers()
        if shuffle:
            random.shuffle(queries)
        for query in queries:
            result = handlers.handle(query)
            if result is not None:
                yield result
