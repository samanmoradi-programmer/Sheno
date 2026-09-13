from dataclasses import dataclass, field
from typing import List, Optional

from .episode import Episode


@dataclass
class Podcast:
    """
    مدل یک پادکست.
    """

    id: str
    title: str

    author: str = ""
    description: str = ""
    artwork: Optional[str] = None
    feed_url: str = ""

    episodes: List[Episode] = field(default_factory=list)
