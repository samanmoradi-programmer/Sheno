from typing import Dict, List, Optional

from .podcast import Podcast


class PodcastRepository:
    """
    مدیریت پادکست‌های شنو در حافظه.
    """

    def __init__(self):
        self._podcasts: Dict[str, Podcast] = {}
        self._active_feed_url: Optional[str] = None

    def add(self, podcast: Podcast) -> None:
        self._podcasts[podcast.feed_url] = podcast

        if self._active_feed_url is None:
            self._active_feed_url = podcast.feed_url

    def remove(self, feed_url: str) -> None:
        self._podcasts.pop(feed_url, None)

        if self._active_feed_url == feed_url:
            self._active_feed_url = None

    def get(self, feed_url: str) -> Optional[Podcast]:
        return self._podcasts.get(feed_url)

    def get_all(self) -> List[Podcast]:
        return list(self._podcasts.values())

    def exists(self, feed_url: str) -> bool:
        return feed_url in self._podcasts

    def set_active(self, feed_url: str) -> bool:
        if feed_url not in self._podcasts:
            return False

        self._active_feed_url = feed_url
        return True

    def get_active(self) -> Optional[Podcast]:
        if self._active_feed_url is None:
            return None

        return self._podcasts.get(
            self._active_feed_url
        )

    def get_active_feed_url(self) -> Optional[str]:
        return self._active_feed_url

    def clear(self) -> None:
        self._podcasts.clear()
        self._active_feed_url = None
