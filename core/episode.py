from dataclasses import dataclass
from typing import Optional


@dataclass
class Episode:
    """
    مدل یک قسمت از پادکست.
    """

    id: str
    title: str
    audio_url: str

    description: str = ""
    artwork: Optional[str] = None
    published_at: Optional[str] = None
    duration: Optional[str] = None
