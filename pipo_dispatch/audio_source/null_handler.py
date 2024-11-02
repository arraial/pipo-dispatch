from typing import Iterable, Optional

from pipo_dispatch.audio_source.base_handler import BaseHandler
from pipo_dispatch.audio_source.source_pair import SourcePair
from pipo_dispatch.audio_source.source_type import SourceType


class NullHandler(BaseHandler):
    """Handles youtube url music."""

    name = SourceType.NULL

    def handle(self, source: Iterable[str]) -> SourcePair:
        """Create handler pair."""
        return SourcePair(query=source, handler_type=NullHandler.name)

    @staticmethod
    def fetch(source: str) -> Optional[str]:
        """Return `None`."""
        return None
