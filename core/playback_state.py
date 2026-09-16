from typing import Optional

from PySide6.QtCore import QObject, Signal

from .episode import Episode


class PlaybackState(QObject):
    """
    وضعیت مرکزی پخش در شنو.

    این کلاس فقط وضعیت را نگهداری و اعلام می‌کند.
    مسئول پخش واقعی صدا نیست.
    """

    # =================================================
    # Signals
    # =================================================

    current_episode_changed = Signal(object)

    state_changed = Signal(str)

    position_changed = Signal(int)

    duration_changed = Signal(int)

    # =================================================
    # Initialization
    # =================================================

    def __init__(self, parent=None):
        super().__init__(parent)

        self._current_episode: Optional[Episode] = None

        self._state = "stopped"

        self._position = 0

        self._duration = 0

    # =================================================
    # Current Episode
    # =================================================

    @property
    def current_episode(self) -> Optional[Episode]:
        return self._current_episode

    def set_current_episode(
        self,
        episode: Optional[Episode]
    ):
        if episode is not None and not isinstance(
            episode,
            Episode
        ):
            return

        if self._current_episode is episode:
            return

        self._current_episode = episode

        self.current_episode_changed.emit(
            episode
        )

    # =================================================
    # State
    # =================================================

    @property
    def state(self) -> str:
        return self._state

    def set_state(self, state: str):

        if state == self._state:
            return

        self._state = state

        self.state_changed.emit(
            state
        )

    # =================================================
    # Position
    # =================================================

    @property
    def position(self) -> int:
        return self._position

    def set_position(self, position: int):

        position = max(
            0,
            int(position)
        )

        if position == self._position:
            return

        self._position = position

        self.position_changed.emit(
            position
        )

    # =================================================
    # Duration
    # =================================================

    @property
    def duration(self) -> int:
        return self._duration

    def set_duration(self, duration: int):

        duration = max(
            0,
            int(duration)
        )

        if duration == self._duration:
            return

        self._duration = duration

        self.duration_changed.emit(
            duration
        )

    # =================================================
    # State Helpers
    # =================================================

    def is_playing(self) -> bool:
        return self._state == "playing"

    def is_paused(self) -> bool:
        return self._state == "paused"

    def is_stopped(self) -> bool:
        return self._state == "stopped"

    # =================================================
    # Reset
    # =================================================

    def reset(self):

        self.set_current_episode(
            None
        )

        self.set_state(
            "stopped"
        )

        self.set_position(
            0
        )

        self.set_duration(
            0
        )
