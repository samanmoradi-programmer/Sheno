from PySide6.QtCore import (
    QObject,
    Signal,
    QUrl,
    QTimer
)

from PySide6.QtMultimedia import (
    QMediaPlayer,
    QAudioOutput
)

from .episode import Episode
from .playback_state import PlaybackState


class AudioManager(QObject):

    # =================================================
    # Signals for UI
    # =================================================

    position_changed = Signal(int)

    duration_changed = Signal(int)

    # همچنان وضعیت QMediaPlayer را برای UI ارسال می‌کنیم
    state_changed = Signal(object)

    error_occurred = Signal(str)

    volume_changed = Signal(float)

    speed_changed = Signal(float)

    sleep_finished = Signal()

    def __init__(self):

        super().__init__()

        # -----------------------------
        # Core Player
        # -----------------------------

        self.audio_output = QAudioOutput()

        self.player = QMediaPlayer()

        self.player.setAudioOutput(
            self.audio_output
        )

        self.audio_output.setVolume(
            0.8
        )

        # -----------------------------
        # Playback State
        # -----------------------------

        self.playback_state = PlaybackState(
            parent=self
        )

        # -----------------------------
        # Legacy / Current Info
        # -----------------------------

        self.current_title = ""

        self.current_url = ""

        # -----------------------------
        # Sleep Timer
        # -----------------------------

        self.sleep_timer = QTimer()

        self.sleep_timer.setSingleShot(
            True
        )

        self.sleep_timer.timeout.connect(
            self.on_sleep_finished
        )

        # -----------------------------
        # Connections
        # -----------------------------

        self.connect_signals()

    # =================================================
    # Signals
    # =================================================

    def connect_signals(self):

        self.player.positionChanged.connect(
            self.on_position_changed
        )

        self.player.durationChanged.connect(
            self.on_duration_changed
        )

        self.player.playbackStateChanged.connect(
            self.on_playback_state_changed
        )

        self.player.errorOccurred.connect(
            self.handle_error
        )

    # =================================================
    # Playback State
    # =================================================

    def set_current_episode(self, episode):

        if episode is None:

            self.playback_state.set_current_episode(
                None
            )

            self.current_title = ""
            self.current_url = ""

            return

        if not isinstance(
            episode,
            Episode
        ):
            return

        self.playback_state.set_current_episode(
            episode
        )

        self.current_title = episode.title

        self.current_url = episode.audio_url

    def current_episode(self):

        return self.playback_state.current_episode

    def on_playback_state_changed(self, state):

        # ---------------------------------------------
        # تبدیل وضعیت QMediaPlayer به وضعیت داخلی شنو
        # ---------------------------------------------

        if state == QMediaPlayer.PlayingState:

            playback_state = "playing"

        elif state == QMediaPlayer.PausedState:

            playback_state = "paused"

        else:

            playback_state = "stopped"

        # ---------------------------------------------
        # ذخیره در PlaybackState
        # ---------------------------------------------

        self.playback_state.set_state(
            playback_state
        )

        # ---------------------------------------------
        # سیگنال قبلی برای UI
        # ---------------------------------------------

        self.state_changed.emit(
            state
        )

    def on_position_changed(self, position):

        self.playback_state.set_position(
            position
        )

        self.position_changed.emit(
            position
        )

    def on_duration_changed(self, duration):

        self.playback_state.set_duration(
            duration
        )

        self.duration_changed.emit(
            duration
        )

    # =================================================
    # Playback
    # =================================================

    def play(
        self,
        episode_or_url,
        title=""
    ):

        if not episode_or_url:
            return

        # ---------------------------------------------
        # New API:
        # play(Episode)
        # ---------------------------------------------

        if isinstance(
            episode_or_url,
            Episode
        ):

            episode = episode_or_url

            if not episode.audio_url:
                return

            self.set_current_episode(
                episode
            )

            url = episode.audio_url

            title = episode.title

        # ---------------------------------------------
        # Existing API:
        # play(url, title)
        # ---------------------------------------------

        else:

            url = episode_or_url

            self.current_url = url

            self.current_title = title

        # ---------------------------------------------
        # Start playback
        # ---------------------------------------------

        self.player.setSource(
            QUrl(url)
        )

        self.player.play()

    def pause(self):

        self.player.pause()

    def resume(self):

        self.player.play()

    def toggle(self):

        state = self.player.playbackState()

        if state == QMediaPlayer.PlayingState:

            self.pause()

        else:

            self.resume()

    def stop(self):

        self.player.stop()

    # =================================================
    # Seek
    # =================================================

    def seek(
        self,
        position
    ):

        self.player.setPosition(
            position
        )

    def position(self):

        return self.player.position()

    def duration(self):

        return self.player.duration()

    # =================================================
    # Volume
    # =================================================

    def set_volume(
        self,
        value
    ):

        value = max(
            0,
            min(
                value,
                1
            )
        )

        self.audio_output.setVolume(
            value
        )

        self.volume_changed.emit(
            value
        )

    def volume(self):

        return self.audio_output.volume()

    def mute(self):

        self.audio_output.setMuted(
            True
        )

    def unmute(self):

        self.audio_output.setMuted(
            False
        )

    def is_muted(self):

        return self.audio_output.isMuted()

    # =================================================
    # Playback Speed
    # =================================================

    def set_speed(
        self,
        speed
    ):

        self.player.setPlaybackRate(
            speed
        )

        self.speed_changed.emit(
            speed
        )

    def speed(self):

        return self.player.playbackRate()

    # =================================================
    # Sleep Timer
    # =================================================

    def start_sleep_timer(
        self,
        minutes
    ):

        milliseconds = (
            minutes * 60 * 1000
        )

        self.sleep_timer.start(
            milliseconds
        )

    def cancel_sleep_timer(self):

        self.sleep_timer.stop()

    def on_sleep_finished(self):

        self.pause()

        self.sleep_finished.emit()

    # =================================================
    # Info
    # =================================================

    def is_playing(self):

        return (
            self.player.playbackState()
            ==
            QMediaPlayer.PlayingState
        )

    def source_valid(self):

        return (
            self.player.source()
            .isValid()
        )

    # =================================================
    # Error
    # =================================================

    def handle_error(
        self,
        error,
        message
    ):

        if message:

            self.error_occurred.emit(
                message
            )
