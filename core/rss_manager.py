from .podcast import Podcast
from .episode import Episode
from PySide6.QtCore import QObject, Signal, Slot
import feedparser
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from typing import Any, Optional


class RSSWorker(QObject):
    """
    دریافت و پردازش RSS Feed.

    این کلاس هیچ کاری با UI انجام نمی‌دهد.
    فقط Feed را دریافت می‌کند، اطلاعات Podcast و Episodeها را استخراج
    می‌کند و نتیجه را از طریق Signal برمی‌گرداند.
    """

    finished = Signal(object, object)
    error = Signal(str)

    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/153.0.0.0 Safari/537.36"
    )

    FEED_TIMEOUT = 15
    ARTWORK_TIMEOUT = 10

    def __init__(self, feed_url: str, parent=None):
        super().__init__(parent)

        self.feed_url = (feed_url or "").strip()

    # =========================================================
    # Generic Helpers
    # =========================================================

    @staticmethod
    def _get_value(
        obj: Any,
        *names: str,
        default: str = "",
    ) -> str:
        """
        اولین مقدار معتبر را از بین نام‌های داده‌شده برمی‌گرداند.
        """

        if obj is None:
            return default

        for name in names:
            try:
                value = getattr(obj, name, None)
            except Exception:
                value = None

            if value is None:
                continue

            if isinstance(value, str):
                value = value.strip()

            if value:
                return str(value).strip()

        return default

    @staticmethod
    def _safe_text(value: Any) -> str:
        """
        تبدیل مقدار RSS به متن تمیز.
        """

        if value is None:
            return ""

        if isinstance(value, str):
            return value.strip()

        return str(value).strip()

    # =========================================================
    # Artwork
    # =========================================================

    def _get_artwork_url(
        self,
        feed_info: Any,
    ) -> Optional[str]:
        """
        URL تصویر اصلی Podcast را پیدا می‌کند.

        اطلاعات Podcast در feedparser معمولاً داخل parsed.feed
        قرار دارند.
        """

        if feed_info is None:
            return None

        # -----------------------------------------------------
        # feed.image.href
        # -----------------------------------------------------

        image = getattr(
            feed_info,
            "image",
            None,
        )

        if image:
            href = self._get_value(
                image,
                "href",
                "url",
            )

            if href:
                return href

        # -----------------------------------------------------
        # feed.itunes_image.href
        # -----------------------------------------------------

        itunes_image = getattr(
            feed_info,
            "itunes_image",
            None,
        )

        if itunes_image:
            href = self._get_value(
                itunes_image,
                "href",
                "url",
            )

            if href:
                return href

        # -----------------------------------------------------
        # Direct image URL
        # -----------------------------------------------------

        direct = self._get_value(
            feed_info,
            "image",
            "image_url",
            default="",
        )

        if direct.startswith(
            ("http://", "https://")
        ):
            return direct

        return None

    def _get_episode_artwork(
        self,
        entry: Any,
        fallback: Optional[str] = None,
    ) -> Optional[str]:
        """
        تصویر مخصوص Episode را پیدا می‌کند.

        اگر Episode تصویر اختصاصی نداشته باشد،
        تصویر Podcast به عنوان fallback استفاده می‌شود.
        """

        # -----------------------------------------------------
        # entry.image.href
        # -----------------------------------------------------

        image = getattr(
            entry,
            "image",
            None,
        )

        if image:
            href = self._get_value(
                image,
                "href",
                "url",
            )

            if href:
                return href

        # -----------------------------------------------------
        # entry.itunes_image.href
        # -----------------------------------------------------

        itunes_image = getattr(
            entry,
            "itunes_image",
            None,
        )

        if itunes_image:
            href = self._get_value(
                itunes_image,
                "href",
                "url",
            )

            if href:
                return href

        return fallback

    # =========================================================
    # Audio URL
    # =========================================================

    def _get_audio_url(
        self,
        entry: Any,
    ) -> Optional[str]:
        """
        آدرس فایل صوتی Episode را پیدا می‌کند.
        """

        # -----------------------------------------------------
        # Standard RSS enclosure
        # -----------------------------------------------------

        enclosures = getattr(
            entry,
            "enclosures",
            [],
        )

        if enclosures:
            for enclosure in enclosures:
                href = self._get_value(
                    enclosure,
                    "href",
                    "url",
                )

                if (
                    href
                    and href.startswith(
                        ("http://", "https://")
                    )
                ):
                    return href

        # -----------------------------------------------------
        # Alternative RSS links
        # -----------------------------------------------------

        links = getattr(
            entry,
            "links",
            [],
        )

        for link in links:
            rel = self._get_value(
                link,
                "rel",
            ).lower()

            href = self._get_value(
                link,
                "href",
            )

            if (
                href
                and rel == "enclosure"
                and href.startswith(
                    ("http://", "https://")
                )
            ):
                return href

        # -----------------------------------------------------
        # media_content
        # -----------------------------------------------------

        media_content = getattr(
            entry,
            "media_content",
            [],
        )

        if media_content:
            for media in media_content:
                href = self._get_value(
                    media,
                    "url",
                    "href",
                )

                if (
                    href
                    and href.startswith(
                        ("http://", "https://")
                    )
                ):
                    return href

        return None

    # =========================================================
    # Description
    # =========================================================

    def _get_description(
        self,
        entry: Any,
    ) -> str:
        """
        توضیحات Episode را از فرمت‌های رایج RSS استخراج می‌کند.
        """

        description = self._get_value(
            entry,
            "description",
            "summary",
        )

        if description:
            return description

        content = getattr(
            entry,
            "content",
            [],
        )

        if content:
            for item in content:
                value = self._get_value(
                    item,
                    "value",
                )

                if value:
                    return value

        return ""

    # =========================================================
    # Episode ID
    # =========================================================

    def _get_episode_id(
        self,
        entry: Any,
        index: int,
    ) -> str:
        """
        شناسه Episode را استخراج می‌کند.

        اولویت:
        1. id
        2. guid
        3. link
        4. fallback
        """

        episode_id = self._get_value(
            entry,
            "id",
            "guid",
        )

        if episode_id:
            return episode_id

        link = self._get_value(
            entry,
            "link",
        )

        if link:
            return link

        return f"{self.feed_url}#episode-{index}"

    # =========================================================
    # Podcast ID
    # =========================================================

    def _get_podcast_id(
        self,
        feed_info: Any,
    ) -> str:
        """
        شناسه Podcast را استخراج می‌کند.
        """

        podcast_id = self._get_value(
            feed_info,
            "id",
            "guid",
        )

        if podcast_id:
            return podcast_id

        return self.feed_url

    # =========================================================
    # Build Podcast
    # =========================================================

    def _build_podcast(
        self,
        feed_info: Any,
        entries: list,
    ) -> Podcast:
        """
        ساخت مدل Podcast و تمام Episodeهای معتبر آن.
        """

        # -----------------------------------------------------
        # Podcast metadata
        # -----------------------------------------------------

        title = self._get_value(
            feed_info,
            "title",
            default="پادکست بدون عنوان",
        )

        author = self._get_value(
            feed_info,
            "author",
            "itunes_author",
            default="",
        )

        description = self._get_value(
            feed_info,
            "description",
            "subtitle",
            "summary",
            default="",
        )

        artwork = self._get_artwork_url(
            feed_info
        )

        podcast_id = self._get_podcast_id(
            feed_info
        )

        # -----------------------------------------------------
        # Episodes
        # -----------------------------------------------------

        episodes = []

        for index, entry in enumerate(
            entries,
            start=1,
        ):
            try:
                audio_url = self._get_audio_url(
                    entry
                )

                # Episode بدون فایل صوتی قابل پخش نیست.
                if not audio_url:
                    continue

                episode_title = self._get_value(
                    entry,
                    "title",
                    default=f"قسمت {index}",
                )

                episode_description = (
                    self._get_description(entry)
                )

                episode_artwork = (
                    self._get_episode_artwork(
                        entry,
                        fallback=artwork,
                    )
                )

                episode_id = self._get_episode_id(
                    entry,
                    index,
                )

                published_at = self._get_value(
                    entry,
                    "published",
                    "pubDate",
                    "updated",
                    default="",
                )

                duration = self._get_value(
                    entry,
                    "itunes_duration",
                    "duration",
                    default="",
                )

                episode = Episode(
                    id=episode_id,
                    title=episode_title,
                    audio_url=audio_url,
                    description=episode_description,
                    artwork=episode_artwork,
                    published_at=published_at,
                    duration=duration,
                )

                episodes.append(episode)

            except Exception as exc:
                print(
                    f"[RSS] Skipping invalid episode "
                    f"{index}: {exc}"
                )

        return Podcast(
            id=podcast_id,
            title=title,
            author=author,
            description=description,
            artwork=artwork,
            feed_url=self.feed_url,
            episodes=episodes,
        )

    # =========================================================
    # Download Artwork
    # =========================================================

    def _download_artwork(
        self,
        artwork_url: Optional[str],
    ) -> Optional[bytes]:
        """
        تصویر Podcast را دانلود می‌کند.

        خروجی این تابع:
            bytes
            یا None
        """

        if not artwork_url:
            return None

        if not artwork_url.startswith(
            ("http://", "https://")
        ):
            return None

        try:
            request = Request(
                artwork_url,
                headers={
                    "User-Agent": self.USER_AGENT,
                    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
                },
            )

            with urlopen(
                request,
                timeout=self.ARTWORK_TIMEOUT,
            ) as response:

                artwork_data = response.read()

                if not isinstance(
                    artwork_data,
                    bytes,
                ):
                    print(
                        "[RSS] Artwork is not bytes:",
                        type(artwork_data),
                    )
                    return None

                return artwork_data

        except Exception as exc:
            print(
                f"[RSS] Artwork download failed: {exc}"
            )
            return None

    # =========================================================
    # Main Worker
    # =========================================================

    @Slot()
    def run(self) -> None:
        """
        دریافت و پردازش RSS.
        """

        # -----------------------------------------------------
        # Validate URL
        # -----------------------------------------------------

        if not self.feed_url:
            self.error.emit(
                "آدرس RSS خالی است."
            )
            return

        if not self.feed_url.startswith(
            ("http://", "https://")
        ):
            self.error.emit(
                "آدرس RSS معتبر نیست."
            )
            return

        # -----------------------------------------------------
        # Request Feed
        # -----------------------------------------------------

        try:
            request = Request(
                self.feed_url,
                headers={
                    "User-Agent": self.USER_AGENT,
                    "Accept": (
                        "application/rss+xml, "
                        "application/xml, "
                        "text/xml, "
                        "text/html;q=0.9, "
                        "*/*;q=0.8"
                    ),
                },
            )

            with urlopen(
                request,
                timeout=self.FEED_TIMEOUT,
            ) as response:

                data = response.read()

        except HTTPError as exc:
            self.error.emit(
                f"خطای HTTP در دریافت RSS: "
                f"{exc.code}"
            )
            return

        except URLError as exc:
            reason = getattr(
                exc,
                "reason",
                "خطای شبکه",
            )

            self.error.emit(
                f"خطا در اتصال به RSS: {reason}"
            )
            return

        except TimeoutError:
            self.error.emit(
                "دریافت RSS بیش از حد طول کشید."
            )
            return

        except Exception as exc:
            self.error.emit(
                f"خطا در دریافت RSS: {exc}"
            )
            return

        # -----------------------------------------------------
        # Parse Feed
        # -----------------------------------------------------

        try:
            parsed = feedparser.parse(data)

        except Exception as exc:
            self.error.emit(
                f"خطا در پردازش RSS: {exc}"
            )
            return

        # -----------------------------------------------------
        # Parser Warning
        # -----------------------------------------------------

        bozo = getattr(
            parsed,
            "bozo",
            False,
        )

        if bozo:
            bozo_exception = getattr(
                parsed,
                "bozo_exception",
                None,
            )

            print(
                "[RSS] Feed parser warning:",
                bozo_exception,
            )

        # -----------------------------------------------------
        # Feed Metadata
        # -----------------------------------------------------

        feed_info = getattr(
            parsed,
            "feed",
            None,
        )

        if feed_info is None:
            self.error.emit(
                "اطلاعات اصلی Podcast در RSS پیدا نشد."
            )
            return

        # -----------------------------------------------------
        # Entries
        # -----------------------------------------------------

        entries = getattr(
            parsed,
            "entries",
            [],
        )

        if not entries:
            self.error.emit(
                "این RSS هیچ قسمتی قابل پردازش ندارد."
            )
            return

        # -----------------------------------------------------
        # Debug Information
        # -----------------------------------------------------

        print(
            "[RSS] Feed title:",
            self._get_value(
                feed_info,
                "title",
                default="",
            ),
        )

        print(
            "[RSS] Feed author:",
            self._get_value(
                feed_info,
                "author",
                "itunes_author",
                default="",
            ),
        )

        # -----------------------------------------------------
        # Build Podcast
        # -----------------------------------------------------

        try:
            podcast = self._build_podcast(
                feed_info,
                entries,
            )

        except Exception as exc:
            self.error.emit(
                f"خطا در ساخت اطلاعات Podcast: {exc}"
            )
            return

        # -----------------------------------------------------
        # Validate Episodes
        # -----------------------------------------------------

        if not podcast.episodes:
            self.error.emit(
                "در این RSS هیچ قسمت صوتی قابل پخش پیدا نشد."
            )
            return

        # -----------------------------------------------------
        # Artwork
        # -----------------------------------------------------

        print(
            "[RSS] Artwork URL:",
            podcast.artwork,
        )

        artwork_data = self._download_artwork(
            podcast.artwork
        )

        print(
            "[RSS] Artwork data type:",
            type(artwork_data).__name__
            if artwork_data is not None
            else "None",
        )

        print(
            "[RSS] Artwork available:",
            artwork_data is not None,
        )

        # -----------------------------------------------------
        # Finished
        # -----------------------------------------------------

        self.finished.emit(
            podcast,
            artwork_data,
        )
