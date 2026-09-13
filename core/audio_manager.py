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


class AudioManager(QObject):

    # Signals for UI

    position_changed = Signal(int)

    duration_changed = Signal(int)

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
        # State
        # -----------------------------

        self.current_title = ""

        self.current_url = ""

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
            self.position_changed.emit
        )

        self.player.durationChanged.connect(
            self.duration_changed.emit
        )

        self.player.playbackStateChanged.connect(
            self.state_changed.emit
        )

        self.player.errorOccurred.connect(
            self.handle_error
        )

    # =================================================
    # Playback
    # =================================================

    def play(
        self,
        url,
        title=""
    ):

        if not url:
            return

        self.current_url = url

        self.current_title = title

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
