from typing import Optional, Union

from PySide6.QtCore import QObject, QTimer, Signal, QUrl
from PySide6.QtMultimedia import (
    QAudioOutput,
    QMediaPlayer,
)

from .episode import Episode
from .playback_state import PlaybackState


class AudioManager(QObject):
    """
    مدیریت کامل پخش صوت در شنو.

    مسئولیت‌های این کلاس:
    - پخش / توقف / مکث
    - seek
    - volume
    - playback speed
    - sleep timer
    - هماهنگ نگه داشتن QMediaPlayer و PlaybackState
    - گزارش خطاهای صوتی
    """

    position_changed = Signal(int)
    duration_changed = Signal(int)

    # وضعیت خام QMediaPlayer را برای UI ارسال می‌کنیم.
    state_changed = Signal(object)

    error_occurred = Signal(str)

    volume_changed = Signal(float)
    speed_changed = Signal(float)

    sleep_finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # -----------------------------------------------------
        # Playback State
        # -----------------------------------------------------

        self.playback_state = PlaybackState(self)

        # -----------------------------------------------------
        # Audio Output
        # -----------------------------------------------------

        self.audio_output = QAudioOutput(self)
        self.audio_output.setVolume(0.8)

        # -----------------------------------------------------
        # Media Player
        # -----------------------------------------------------

        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(self.audio_output)

        # -----------------------------------------------------
        # Current Media
        # -----------------------------------------------------

        self.current_title: str = ""
        self.current_url: str = ""

        # -----------------------------------------------------
        # Sleep Timer
        # -----------------------------------------------------

        self._sleep_timer = QTimer(self)
        self._sleep_timer.setSingleShot(True)
        self._sleep_timer.timeout.connect(self._on_sleep_finished)

        # -----------------------------------------------------
        # Connections
        # -----------------------------------------------------

        self.player.positionChanged.connect(
            self._on_position_changed
        )

        self.player.durationChanged.connect(
            self._on_duration_changed
        )

        self.player.playbackStateChanged.connect(
            self._on_playback_state_changed
        )

        self.player.mediaStatusChanged.connect(
            self._on_media_status_changed
        )

        self.player.errorOccurred.connect(
            self._on_error
        )

        self.audio_output.volumeChanged.connect(
            self._on_volume_changed
        )

    # =========================================================
    # Episode
    # =========================================================

    def set_current_episode(
        self,
        episode: Optional[Episode],
    ) -> None:
        """
        اپیزود فعلی را در PlaybackState ثبت می‌کند.
        """

        self.playback_state.set_current_episode(episode)

        if episode is None:
            self.current_title = ""
            self.current_url = ""
        else:
            self.current_title = episode.title
            self.current_url = episode.audio_url

    def current_episode(self) -> Optional[Episode]:
        return self.playback_state.current_episode

    # =========================================================
    # Play
    # =========================================================

    def play(
        self,
        episode_or_url: Union[Episode, str],
        title: str = "",
    ) -> None:
        """
        پخش یک Episode یا URL.

        روش پیشنهادی:
            audio_manager.play(episode)

        برای سازگاری با کدهای قدیمی:
            audio_manager.play(url, title)
        """

        # -----------------------------------------------------
        # Episode
        # -----------------------------------------------------

        if isinstance(episode_or_url, Episode):
            episode = episode_or_url

            if not episode.audio_url:
                self._emit_error(
                    "برای این قسمت، آدرس فایل صوتی وجود ندارد."
                )
                return

            self.set_current_episode(episode)

            url = episode.audio_url

        # -----------------------------------------------------
        # Legacy URL Mode
        # -----------------------------------------------------

        elif isinstance(episode_or_url, str):
            url = episode_or_url.strip()

            if not url:
                self._emit_error(
                    "آدرس فایل صوتی معتبر نیست."
                )
                return

            self.current_title = title
            self.current_url = url

        else:
            self._emit_error(
                "نوع ورودی برای پخش صوت معتبر نیست."
            )
            return

        # -----------------------------------------------------
        # Set Source
        # -----------------------------------------------------

        self.player.setSource(QUrl(url))

        # وضعیت داخلی را قبل از play آماده می‌کنیم.
        self.playback_state.set_state("stopped")
        self.playback_state.set_position(0)
        self.playback_state.set_duration(0)

        # -----------------------------------------------------
        # Start
        # -----------------------------------------------------

        self.player.play()

    # =========================================================
    # Pause / Resume
    # =========================================================

    def pause(self) -> None:
        if not self.source_valid():
            return

        self.player.pause()

    def resume(self) -> None:
        if not self.source_valid():
            return

        self.player.play()

    def toggle(self) -> None:
        """
        بین Play و Pause جابه‌جا می‌شود.
        """

        if not self.source_valid():
            return

        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.pause()

        elif self.player.playbackState() == QMediaPlayer.PausedState:
            self.resume()

        else:
            self.resume()

    # =========================================================
    # Stop
    # =========================================================

    def stop(self) -> None:
        """
        پخش را متوقف می‌کند ولی Episode فعلی را پاک نمی‌کند.

        این رفتار برای یک Podcast Player حرفه‌ای مهم است؛
        Stop به معنی حذف انتخاب کاربر نیست.
        """

        self.player.stop()

        self.playback_state.set_state("stopped")
        self.playback_state.set_position(0)

    # =========================================================
    # Seek
    # =========================================================

    def seek(self, position: int) -> None:
        if not self.source_valid():
            return

        position = max(0, int(position))

        if self.playback_state.duration > 0:
            position = min(
                position,
                self.playback_state.duration,
            )

        self.player.setPosition(position)

    def set_position(self, position: int) -> None:
        self.seek(position)

    def position(self) -> int:
        return self.player.position()

    def duration(self) -> int:
        return self.player.duration()

    # =========================================================
    # Volume
    # =========================================================

    def set_volume(self, volume: float) -> None:
        """
        volume باید بین 0.0 و 1.0 باشد.
        """

        volume = max(0.0, min(1.0, float(volume)))

        self.audio_output.setVolume(volume)

    def volume(self) -> float:
        return self.audio_output.volume()

    def mute(self) -> None:
        self.audio_output.setMuted(True)

    def unmute(self) -> None:
        self.audio_output.setMuted(False)

    def is_muted(self) -> bool:
        return self.audio_output.isMuted()

    # =========================================================
    # Playback Speed
    # =========================================================

    def set_speed(self, speed: float) -> None:
        """
        سرعت پخش.

        مثال:
            0.75
            1.0
            1.25
            1.5
            2.0
        """

        speed = float(speed)

        if speed <= 0:
            self._emit_error(
                "سرعت پخش باید بزرگ‌تر از صفر باشد."
            )
            return

        self.player.setPlaybackRate(speed)
        self.speed_changed.emit(speed)

    def speed(self) -> float:
        return self.player.playbackRate()

    # =========================================================
    # Sleep Timer
    # =========================================================

    def set_sleep_timer(self, minutes: int) -> None:
        """
        تایمر خواب را بر اساس دقیقه فعال می‌کند.
        """

        minutes = int(minutes)

        if minutes <= 0:
            self.cancel_sleep_timer()
            return

        self._sleep_timer.start(minutes * 60 * 1000)

    def cancel_sleep_timer(self) -> None:
        self._sleep_timer.stop()

    def has_sleep_timer(self) -> bool:
        return self._sleep_timer.isActive()

    def _on_sleep_finished(self) -> None:
        self.stop()
        self.sleep_finished.emit()

    # =========================================================
    # Player State
    # =========================================================

    def _on_playback_state_changed(self, state) -> None:
        self.state_changed.emit(state)

        if state == QMediaPlayer.PlayingState:
            self.playback_state.set_state("playing")

        elif state == QMediaPlayer.PausedState:
            self.playback_state.set_state("paused")

        else:
            self.playback_state.set_state("stopped")

    # =========================================================
    # Position
    # =========================================================

    def _on_position_changed(self, position: int) -> None:
        self.playback_state.set_position(position)
        self.position_changed.emit(position)

    # =========================================================
    # Duration
    # =========================================================

    def _on_duration_changed(self, duration: int) -> None:
        self.playback_state.set_duration(duration)
        self.duration_changed.emit(duration)

    # =========================================================
    # Media Status
    # =========================================================

    def _on_media_status_changed(self, status) -> None:
        """
        وضعیت Media را بررسی می‌کند.

        EndOfMedia را عمداً اینجا به reset کامل تبدیل نمی‌کنیم؛
        چون تصمیم درباره رفتار UI و تاریخچه باید در لایه بالاتر باشد.
        """

        if status == QMediaPlayer.EndOfMedia:
            self.playback_state.set_state("stopped")

    # =========================================================
    # Error
    # =========================================================

    def _on_error(self, error, error_string: str) -> None:
        if error_string:
            message = error_string
        else:
            message = "خطایی هنگام پخش فایل صوتی رخ داد."

        self._emit_error(message)

    def _emit_error(self, message: str) -> None:
        self.error_occurred.emit(message)

    # =========================================================
    # Volume Signal
    # =========================================================

    def _on_volume_changed(self, volume: float) -> None:
        self.volume_changed.emit(volume)

    # =========================================================
    # Source
    # =========================================================

    def source_valid(self) -> bool:
        source = self.player.source()

        return source.isValid() and bool(
            source.toString().strip()
        )

    # =========================================================
    # State Helpers
    # =========================================================

    def is_playing(self) -> bool:
        return (
            self.player.playbackState()
            == QMediaPlayer.PlayingState
        )

    def is_paused(self) -> bool:
        return (
            self.player.playbackState()
            == QMediaPlayer.PausedState
        )

    def is_stopped(self) -> bool:
        return (
            self.player.playbackState()
            == QMediaPlayer.StoppedState
        )
