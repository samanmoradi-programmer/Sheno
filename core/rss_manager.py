from urllib.request import Request, urlopen

import feedparser

from PySide6.QtCore import QObject, Signal, Slot

from .episode import Episode
from .podcast import Podcast


class RSSWorker(QObject):
    """
    مسئول دریافت RSS و تبدیل اطلاعات خام RSS
    به مدل‌های Podcast و Episode.
    """

    finished = Signal(object, object)
    error = Signal(str)

    def __init__(self, feed_url):
        super().__init__()

        self.feed_url = feed_url

    # =========================================================
    # ابزارهای کمکی
    # =========================================================

    @staticmethod
    def _get_value(obj, *names, default=""):
        """
        اولین مقدار موجود از بین نام‌های داده‌شده را برمی‌گرداند.
        """

        for name in names:
            value = getattr(obj, name, None)

            if value:
                return value

        return default

    @staticmethod
    def _get_artwork_url(feed):
        """
        پیدا کردن Artwork اصلی پادکست.
        """

        # feed.image.href
        image = getattr(feed.feed, "image", None)

        if image:

            href = getattr(image, "href", None)

            if href:
                return href

        # feed.itunes_image.href
        itunes_image = getattr(
            feed.feed,
            "itunes_image",
            None
        )

        if itunes_image:

            href = getattr(
                itunes_image,
                "href",
                None
            )

            if href:
                return href

        return None

    @staticmethod
    def _get_episode_artwork(entry, fallback=None):
        """
        پیدا کردن Artwork اختصاصی یک Episode.
        اگر وجود نداشت، Artwork پادکست استفاده می‌شود.
        """

        # entry.image.href
        image = getattr(entry, "image", None)

        if image:

            href = getattr(
                image,
                "href",
                None
            )

            if href:
                return href

        # entry.itunes_image.href
        itunes_image = getattr(
            entry,
            "itunes_image",
            None
        )

        if itunes_image:

            href = getattr(
                itunes_image,
                "href",
                None
            )

            if href:
                return href

        return fallback

    @staticmethod
    def _get_audio_url(entry):
        """
        پیدا کردن URL فایل صوتی Episode.
        """

        # روش اول: enclosures
        enclosures = getattr(
            entry,
            "enclosures",
            []
        )

        if enclosures:

            for enclosure in enclosures:

                url = getattr(
                    enclosure,
                    "href",
                    None
                )

                if not url:
                    url = getattr(
                        enclosure,
                        "url",
                        None
                    )

                if url:
                    return url

        # روش دوم: links
        links = getattr(
            entry,
            "links",
            []
        )

        for link in links:

            rel = getattr(
                link,
                "rel",
                ""
            )

            if rel == "enclosure":

                url = getattr(
                    link,
                    "href",
                    None
                )

                if url:
                    return url

        return ""

    @staticmethod
    def _get_description(entry):
        """
        پیدا کردن توضیحات Episode.
        """

        description = RSSWorker._get_value(
            entry,
            "description",
            "summary",
            default=""
        )

        if description:
            return description

        content = getattr(
            entry,
            "content",
            []
        )

        if content:

            first_content = content[0]

            value = getattr(
                first_content,
                "value",
                ""
            )

            if value:
                return value

        return ""

    # =========================================================
    # تبدیل RSS به Podcast / Episode
    # =========================================================

    def _build_podcast(self, feed):
        """
        تبدیل FeedParser result به مدل Podcast.
        """

        podcast_data = feed.feed

        artwork_url = self._get_artwork_url(
            feed
        )

        podcast_id = self._get_value(
            podcast_data,
            "id",
            "guid",
            default=self.feed_url
        )

        title = self._get_value(
            podcast_data,
            "title",
            default="پادکست بدون عنوان"
        )

        author = self._get_value(
            podcast_data,
            "author",
            "itunes_author",
            default=""
        )

        description = self._get_value(
            podcast_data,
            "description",
            "subtitle",
            "summary",
            default=""
        )

        episodes = []

        for index, entry in enumerate(
            feed.entries
        ):

            audio_url = self._get_audio_url(
                entry
            )

            # Episode بدون فایل صوتی
            # برای پخش کاربردی ندارد.
            if not audio_url:
                continue

            episode_id = self._get_value(
                entry,
                "id",
                "guid",
                default=f"{podcast_id}-episode-{index}"
            )

            episode_title = self._get_value(
                entry,
                "title",
                default="قسمت بدون عنوان"
            )

            episode_description = (
                self._get_description(entry)
            )

            episode_artwork = (
                self._get_episode_artwork(
                    entry,
                    fallback=artwork_url
                )
            )

            published_at = self._get_value(
                entry,
                "published",
                "updated",
                default=None
            )

            duration = self._get_value(
                entry,
                "itunes_duration",
                "duration",
                default=None
            )

            episode = Episode(
                id=str(episode_id),
                title=str(episode_title),
                audio_url=str(audio_url),
                description=str(
                    episode_description
                ),
                artwork=episode_artwork,
                published_at=published_at,
                duration=duration,
            )

            episodes.append(
                episode
            )

        podcast = Podcast(
            id=str(podcast_id),
            title=str(title),
            author=str(author),
            description=str(description),
            artwork=artwork_url,
            feed_url=self.feed_url,
            episodes=episodes,
        )

        return podcast

    # =========================================================
    # دریافت RSS
    # =========================================================

    @Slot()
    def run(self):

        try:

            request = Request(
                self.feed_url,
                headers={
                    "User-Agent": "Mozilla/5.0"
                }
            )

            with urlopen(
                request,
                timeout=15
            ) as response:

                data = response.read()

            feed = feedparser.parse(
                data
            )

            if not feed.entries:

                raise Exception(
                    "هیچ قسمتی از پادکست دریافت نشد."
                )

            # -------------------------------------------------
            # تبدیل RSS خام به مدل‌های داخلی شِنو
            # -------------------------------------------------

            podcast = self._build_podcast(
                feed
            )

            # -------------------------------------------------
            # دریافت Artwork برای استفاده مستقیم UI
            # -------------------------------------------------

            artwork_url = podcast.artwork

            artwork_data = None

            if artwork_url:

                try:

                    artwork_request = Request(
                        artwork_url,
                        headers={
                            "User-Agent": "Mozilla/5.0"
                        }
                    )

                    with urlopen(
                        artwork_request,
                        timeout=10
                    ) as image_response:

                        artwork_data = (
                            image_response.read()
                        )

                except Exception as image_error:

                    print(
                        "Artwork Error:",
                        image_error
                    )

            # -------------------------------------------------
            # خروجی
            # -------------------------------------------------

            self.finished.emit(
                podcast,
                artwork_data
            )

        except Exception as error:

            self.error.emit(
                str(error)
            )
