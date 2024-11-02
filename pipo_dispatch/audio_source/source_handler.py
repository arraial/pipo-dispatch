import logging
from abc import ABC, abstractmethod
from typing import Iterable

from pipo_dispatch.audio_source.source_pair import SourcePair


class SourceHandler(ABC):
    """Base source handler.

    Declares methods for building the chain of handlers and executing requests.
    """

    name: str
    _logger: logging.Logger
    # TODO implement caching solution

    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)

    @abstractmethod
    def set_next(self, handler):
        """Define next handler."""
        pass

    @abstractmethod
    def handle(self, source: Iterable[str]) -> SourcePair:
        """Check whether handler is able to process source."""
        pass
