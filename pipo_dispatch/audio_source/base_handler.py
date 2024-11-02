from abc import abstractmethod
from urllib.parse import urlparse

from pipo_dispatch.audio_source.source_handler import SourceHandler
from pipo_dispatch.audio_source.source_pair import SourcePair


class BaseHandler(SourceHandler):
    """Defines handler default behavior."""

    _next_handler: SourceHandler = None

    def set_next(self, handler: SourceHandler) -> SourceHandler:
        """Define next handler."""
        self._next_handler = handler
        return handler

    @abstractmethod
    def handle(self, source: str) -> SourcePair:
        """Check whether handler is able to process source."""
        if self._next_handler:
            return self._next_handler.handle(source)
        return None

    @staticmethod
    def is_url(url: str) -> bool:
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False
