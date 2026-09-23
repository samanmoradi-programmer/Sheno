from typing import Optional

from PySide6.QtCore import QObject, Signal

from .episode import Episode


class PlaybackState(QObject):
    """
    منبع اصلی وضعیت پخش در شنو.

    این کلاس فقط وضعیت را نگه می‌دارد و درباره رابط کاربری
    یا QMediaPlayer تصمیم‌گیری نمی‌کند.
    """

    current_episode_changed = Signal(object)
    state_changed = Signal(str)
    position_changed = Signal(int)
    duration_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._current_episode: Optional[Episode] = None
        self._state: str = "stopped"
        self._position: int = 0
        self._duration: int = 0

    # ---------------------------------------------------------
    # Current Episode
    # ---------------------------------------------------------

    @property
    def current_episode(self) -> Optional[Episode]:
        return self._current_episode

    def set_current_episode(self, episode: Optional[Episode]) -> None:
        if episode is not None and not isinstance(episode, Episode):
            raise TypeError("episode must be an Episode or None")

        if self._current_episode == episode:
            return

        self._current_episode = episode
        self.current_episode_changed.emit(episode)

    def clear_current_episode(self) -> None:
        """
        فقط اپیزود فعلی را پاک می‌کند.

        این متد با stop() فرق دارد؛
        توقف پخش لزوماً به معنی پاک شدن اپیزود فعلی نیست.
        """
        self.set_current_episode(None)

    # ---------------------------------------------------------
    # State
    # ---------------------------------------------------------

    @property
    def state(self) -> str:
        return self._state

    def set_state(self, state: str) -> None:
        if state not in {"playing", "paused", "stopped"}:
            raise ValueError(
                "state must be 'playing', 'paused' or 'stopped'"
            )

        if self._state == state:
            return

        self._state = state
        self.state_changed.emit(state)

    def is_playing(self) -> bool:
        return self._state == "playing"

    def is_paused(self) -> bool:
        return self._state == "paused"

    def is_stopped(self) -> bool:
        return self._state == "stopped"

    # ---------------------------------------------------------
    # Position
    # ---------------------------------------------------------

    @property
    def position(self) -> int:
        return self._position

    def set_position(self, position: int) -> None:
        position = max(0, int(position))

        if self._position == position:
            return

        self._position = position
        self.position_changed.emit(position)

    # ---------------------------------------------------------
    # Duration
    # ---------------------------------------------------------

    @property
    def duration(self) -> int:
        return self._duration

    def set_duration(self, duration: int) -> None:
        duration = max(0, int(duration))

        if self._duration == duration:
            return

        self._duration = duration
        self.duration_changed.emit(duration)

    # ---------------------------------------------------------
    # Reset
    # ---------------------------------------------------------

    def reset(self) -> None:
        """
        وضعیت را کاملاً به حالت اولیه برمی‌گرداند.

        این متد برای زمانی است که واقعاً می‌خواهیم
        اپیزود فعلی هم از وضعیت پخش حذف شود.
        """

        self.set_current_episode(None)
        self.set_state("stopped")
        self.set_position(0)
        self.set_duration(0)
