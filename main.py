from data.podcasts import DEFAULT_PODCASTS
from core.podcast_repository import PodcastRepository
from core.audio_manager import AudioManager
from core.rss_manager import RSSWorker
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
    QScrollArea,
    QSlider,
    QSizePolicy,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
)
from PySide6.QtGui import (
    QPixmap,
    QPainter,
    QColor,
    QLinearGradient,
    QRadialGradient,
    QFont,
    QIcon,
)
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtCore import (
    Qt,
    QThread,
    Slot,
    QSize,
    QPropertyAnimation,
    QEasingCurve,
)
import re
import sys
import ctypes
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


# =========================================================
# Colors
# =========================================================

CYAN = "#7BC9E0"
BLUE = "#6E5FBF"
INDIGO = "#5D4E9E"
NAVY = "#2B2743"

WHITE = "#FFFFFF"
SOFT_WHITE = "#F8FCFF"

GLASS = "rgba(255,255,255,112)"
GLASS_LIGHT = "rgba(255,255,255,145)"
GLASS_STRONG = "rgba(255,255,255,185)"

BORDER = "rgba(255,255,255,145)"
BORDER_SOFT = "rgba(255,255,255,95)"

TEXT = "#2B2743"
TEXT_LIGHT = "#59627A"
TEXT_WHITE = "#FFFFFF"

PURPLE = "#8A6FE0"
PINK = "#D96ACB"


# =========================================================
# Windows Mica
# =========================================================

def enable_windows_mica(widget):
    """
    فعال‌سازی Mica روی Windows در صورت پشتیبانی.
    اگر سیستم پشتیبانی نکند، برنامه بدون خطا ادامه می‌دهد.
    """

    try:
        hwnd = int(widget.winId())

        DWMWA_SYSTEMBACKDROP_TYPE = 38
        DWMSBT_MAINWINDOW = 2

        value = ctypes.c_int(DWMSBT_MAINWINDOW)

        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            ctypes.c_void_p(hwnd),
            DWMWA_SYSTEMBACKDROP_TYPE,
            ctypes.byref(value),
            ctypes.sizeof(value),
        )

    except Exception:
        pass


# =========================================================
# Helpers
# =========================================================

def clear_layout(layout):
    """
    تمام Widgetهای داخل Layout را حذف می‌کند.
    """

    while layout.count():

        item = layout.takeAt(0)

        widget = item.widget()

        if widget is not None:
            widget.deleteLater()

        child_layout = item.layout()

        if child_layout is not None:
            clear_layout(child_layout)


def add_shadow(
    widget,
    blur=30,
    x=0,
    y=10,
    opacity=45,
):
    """
    سایه نرم برای کارت‌ها.
    """

    shadow = QGraphicsDropShadowEffect(widget)

    shadow.setBlurRadius(blur)
    shadow.setOffset(x, y)
    shadow.setColor(
        QColor(
            39,
            39,
            67,
            opacity,
        )
    )

    widget.setGraphicsEffect(shadow)


def format_time(milliseconds):
    """
    milliseconds -> MM:SS / HH:MM:SS
    """

    total_seconds = max(
        0,
        int(milliseconds / 1000),
    )

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    return f"{minutes:02d}:{seconds:02d}"


def make_emoji_icon(
    emoji,
    size=22,
    color=TEXT_LIGHT,
):
    """
    یک آیکون از روی یک کاراکتر ایموجی/نماد می‌سازد تا بتوان
    اندازه آن را مستقل از متن کنار آن (مثلاً در Sidebar) کنترل کرد.
    """

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.TextAntialiasing)

    font = QFont("Segoe UI Emoji")
    font.setPixelSize(int(size * 0.72))

    painter.setFont(font)
    painter.setPen(QColor(color))
    painter.drawText(
        pixmap.rect(),
        Qt.AlignCenter,
        emoji,
    )

    painter.end()

    return QIcon(pixmap)


def make_badge_icon(
    char,
    size=36,
    glyph_color=TEXT_LIGHT,
    badge_color=None,
):
    """
    آیکون سمت‌راست Sidebar را به‌صورت یک نماد بزرگ‌تر و واضح‌تر،
    داخل یک Badge گرد رنگی می‌سازد تا در کنار متن گم نشود و
    چشم‌نواز باشد.
    """

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.TextAntialiasing)

    if badge_color:

        painter.setBrush(QColor(badge_color))
        painter.setPen(Qt.NoPen)

        radius = size * 0.32

        painter.drawRoundedRect(
            0,
            0,
            size,
            size,
            radius,
            radius,
        )

    font = QFont("Segoe UI")
    font.setPixelSize(int(size * 0.5))
    font.setWeight(QFont.DemiBold)

    painter.setFont(font)
    painter.setPen(QColor(glyph_color))
    painter.drawText(
        pixmap.rect(),
        Qt.AlignCenter,
        char,
    )

    painter.end()

    return QIcon(pixmap)


def fade_in(widget, duration=240):
    """
    یک ترنزیشن نرم fade-in برای ویجت‌ها (مثلاً هنگام تعویض صفحه).

    نکته مهم: بعد از پایان انیمیشن، Effect را کاملاً از روی Widget
    برمی‌داریم. اگر QGraphicsOpacityEffect برای همیشه روی صفحه‌ای که
    شامل QScrollArea است باقی بماند، رندر آن صفحه هنگام اسکرول موس
    (چون Qt مسیر رندر دیگری برای Effectها استفاده می‌کند) خراب/خالی
    می‌شود؛ همین باعث محو شدن کامل محتوای Home/Library هنگام اسکرول
    بود.
    """

    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)

    animation = QPropertyAnimation(effect, b"opacity", widget)
    animation.setDuration(duration)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    animation.setEasingCurve(QEasingCurve.OutCubic)

    def _remove_effect():

        # فقط در صورتی حذف کن که هنوز همین Effect فعال باشد
        # (تا با فراخوانی‌های سریع/پی‌درپی fade_in تداخل نکند).
        if widget.graphicsEffect() is effect:
            widget.setGraphicsEffect(None)

    animation.finished.connect(_remove_effect)
    animation.start(QPropertyAnimation.DeleteWhenStopped)

    # جلوگیری از garbage-collect شدن زودهنگام Animation
    widget._fade_animation = animation


class VolumeSlider(QSlider):
    """
    Slider مخصوص Volume که رویداد اسکرول موس را محلی نگه می‌دارد
    و اجازه نمی‌دهد اسکرول به صفحه اصلی (ScrollArea پشت آن) منتقل شود.
    """

    def wheelEvent(self, event):

        step = 5 if event.angleDelta().y() > 0 else -5

        self.setValue(
            max(
                self.minimum(),
                min(
                    self.maximum(),
                    self.value() + step,
                ),
            )
        )

        event.accept()


class VolumeHoverWidget(QFrame):
    """
    ظرف دور آیکون Volume که هنگام Hover شدن (چه روی آیکون، چه روی
    فضای خالی اطرافش) کال‌بک باز/بسته شدن Slider صدا زده می‌شود.
    """

    on_hover_enter = None
    on_hover_leave = None

    def enterEvent(self, event):

        super().enterEvent(event)

        if callable(self.on_hover_enter):
            self.on_hover_enter()

    def leaveEvent(self, event):

        super().leaveEvent(event)

        if callable(self.on_hover_leave):
            self.on_hover_leave()


# =========================================================
# Background
# =========================================================

class GlassBackground(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAttribute(
            Qt.WA_TransparentForMouseEvents
        )

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        rect = self.rect()

        # -------------------------------------------------
        # Main gradient
        # -------------------------------------------------

        gradient = QLinearGradient(
            0,
            0,
            rect.width(),
            rect.height(),
        )

        gradient.setColorAt(
            0.0,
            QColor("#F8F7FD"),
        )

        gradient.setColorAt(
            0.35,
            QColor("#EFF2FC"),
        )

        gradient.setColorAt(
            0.70,
            QColor("#EFEBFB"),
        )

        gradient.setColorAt(
            1.0,
            QColor("#F9F2FB"),
        )

        painter.fillRect(
            rect,
            gradient,
        )

        # -------------------------------------------------
        # Cyan/Lilac glow
        # -------------------------------------------------

        cyan_glow = QRadialGradient(
            rect.width() * 0.12,
            rect.height() * 0.08,
            max(rect.width(), rect.height()) * 0.55,
        )

        cyan_glow.setColorAt(
            0.0,
            QColor(
                123,
                201,
                224,
                42,
            ),
        )

        cyan_glow.setColorAt(
            1.0,
            QColor(
                123,
                201,
                224,
                0,
            ),
        )

        painter.fillRect(
            rect,
            cyan_glow,
        )

        # -------------------------------------------------
        # Purple glow
        # -------------------------------------------------

        purple_glow = QRadialGradient(
            rect.width() * 0.90,
            rect.height() * 0.12,
            max(rect.width(), rect.height()) * 0.48,
        )

        purple_glow.setColorAt(
            0.0,
            QColor(
                138,
                111,
                224,
                42,
            ),
        )

        purple_glow.setColorAt(
            1.0,
            QColor(
                138,
                111,
                224,
                0,
            ),
        )

        painter.fillRect(
            rect,
            purple_glow,
        )

        # -------------------------------------------------
        # Bottom pink glow
        # -------------------------------------------------

        pink_glow = QRadialGradient(
            rect.width() * 0.65,
            rect.height() * 1.05,
            max(rect.width(), rect.height()) * 0.50,
        )

        pink_glow.setColorAt(
            0.0,
            QColor(
                217,
                106,
                203,
                26,
            ),
        )

        pink_glow.setColorAt(
            1.0,
            QColor(
                217,
                106,
                203,
                0,
            ),
        )

        painter.fillRect(
            rect,
            pink_glow,
        )


# =========================================================
# Main Window
# =========================================================

class ShenoWindow(QWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "شِنو"
        )

        self.setMinimumSize(
            900,
            600,
        )

        self.resize(
            1200,
            760,
        )

        self.setAttribute(
            Qt.WA_TranslucentBackground
        )

        self.setLayoutDirection(
            Qt.RightToLeft
        )

        # -------------------------------------------------
        # Data / State
        # -------------------------------------------------

        self.podcast = None

        self.podcast_artworks = {}

        self.rss_thread = None
        self.rss_worker = None
        self.rss_loading = False

        self.default_podcasts = DEFAULT_PODCASTS
        self.default_podcast_index = 0
        self.rss_errors = []

        self.podcast_repository = PodcastRepository()

        # -------------------------------------------------
        # Audio
        # -------------------------------------------------

        self.audio_manager = AudioManager()

        # -------------------------------------------------
        # Build UI
        # -------------------------------------------------

        self.build_ui()

        self.connect_audio()

        self.sync_volume_slider(
            self.audio_manager.volume()
        )

        # -------------------------------------------------
        # Initial state
        # -------------------------------------------------

        self.show_home()

        self.start_rss_loading()

    # =====================================================
    # UI
    # =====================================================

    def build_ui(self):

        self.background = GlassBackground(self)

        self.background.setGeometry(
            self.rect()
        )

        root_layout = QHBoxLayout(self)

        root_layout.setContentsMargins(
            18,
            18,
            18,
            18,
        )

        root_layout.setSpacing(
            14
        )

        # =================================================
        # Sidebar
        # =================================================

        self.sidebar = QFrame()

        self.sidebar.setFixedWidth(
            250
        )

        self.sidebar.setStyleSheet(
            """
            QFrame {
                background: rgba(255,255,255,145);
                border: 1px solid rgba(255,255,255,190);
                border-radius: 28px;
            }
            """
        )

        add_shadow(
            self.sidebar,
            35,
            0,
            10,
            30,
        )

        sidebar_layout = QVBoxLayout(
            self.sidebar
        )

        sidebar_layout.setContentsMargins(
            18,
            18,
            18,
            18,
        )

        sidebar_layout.setSpacing(
            8
        )

        # -------------------------------------------------
        # Logo (یک کارت واحد با گوشه‌های کاملاً گرد، به‌جای دو
        # Label جدا که باعث دیده‌شدن لبه‌های مربعی می‌شد)
        # -------------------------------------------------

        brand_card = QFrame()

        brand_card.setStyleSheet(
            f"""
            QFrame {{
                background: {GLASS_LIGHT};
                border: 1px solid {BORDER};
                border-radius: 20px;
            }}
            """
        )

        brand_layout = QVBoxLayout(
            brand_card
        )

        brand_layout.setContentsMargins(
            14,
            12,
            14,
            14,
        )

        brand_layout.setSpacing(
            3
        )

        logo = QLabel(
            "🎧 شِنو"
        )

        logo.setStyleSheet(
            f"""
            QLabel {{
                background: transparent;
                border: none;
                color: {NAVY};
                font-size: 24px;
                font-weight: 900;
            }}
            """
        )

        brand_layout.addWidget(
            logo
        )

        subtitle = QLabel(
            "پادکست‌ها، ساده و زیبا"
        )

        subtitle.setWordWrap(
            True
        )

        subtitle.setStyleSheet(
            f"""
            QLabel {{
                background: transparent;
                border: none;
                color: {TEXT_LIGHT};
                font-size: 10px;
            }}
            """
        )

        brand_layout.addWidget(
            subtitle
        )

        sidebar_layout.addWidget(
            brand_card
        )

        sidebar_layout.addSpacing(
            6
        )

        # -------------------------------------------------
        # Navigation
        # -------------------------------------------------

        self.nav_buttons = {}
        self.nav_icons = {}

        menu_items = [
            ("home", "⌂", "خانه"),
            ("library", "◈", "پادکست‌ها"),
            ("search", "⌕", "جستجو"),
            ("categories", "◫", "دسته‌بندی‌ها"),
            ("favorites", "♡", "علاقه‌مندی‌ها"),
            ("downloads", "↓", "دانلودها"),
            ("history", "◷", "تاریخچه"),
            ("ambient", "◌", "صدای محیط"),
            ("settings", "⚙", "تنظیمات"),
        ]

        for page_name, icon, title in menu_items:

            button = QPushButton(
                f"   {title}"
            )

            button.setIcon(
                make_emoji_icon(
                    icon,
                    22,
                    TEXT_LIGHT,
                )
            )

            button.setIconSize(
                QSize(22, 22)
            )

            button.setCursor(
                Qt.PointingHandCursor
            )

            button.setMinimumHeight(
                46
            )

            button.setStyleSheet(
                f"""
                QPushButton {{
                    text-align: right;
                    padding: 0 14px;
                    border: none;
                    border-radius: 14px;
                    background: transparent;
                    color: {TEXT_LIGHT};
                    font-size: 12px;
                    font-weight: 700;
                }}

                QPushButton:hover {{
                    background: rgba(255,255,255,120);
                    color: {BLUE};
                }}

                QPushButton:pressed {{
                    background: rgba(138,111,224,28);
                }}
                """
            )

            button.clicked.connect(
                lambda checked=False,
                page=page_name:
                self.navigate(page)
            )

            self.nav_buttons[
                page_name
            ] = button

            self.nav_icons[
                page_name
            ] = icon

            sidebar_layout.addWidget(
                button
            )

        sidebar_layout.addStretch()

        version = QLabel(
            "Sheno • v0.1"
        )

        version.setAlignment(
            Qt.AlignCenter
        )

        version.setStyleSheet(
            f"""
            QLabel {{
                color: rgba(89,98,122,150);
                font-size: 9px;
                padding-top: 8px;
            }}
            """
        )

        sidebar_layout.addWidget(
            version
        )

        # =================================================
        # Right Side
        # =================================================

        right_layout = QVBoxLayout()

        right_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        right_layout.setSpacing(
            12
        )

        # -------------------------------------------------
        # Pages
        # -------------------------------------------------

        self.pages = QStackedWidget()

        self.page_widgets = {}

        page_names = [
            "home",
            "library",
            "search",
            "categories",
            "favorites",
            "downloads",
            "history",
            "ambient",
            "settings",
        ]

        for page_name in page_names:

            page = QWidget()

            page_layout = QVBoxLayout(
                page
            )

            page_layout.setContentsMargins(
                0,
                0,
                0,
                0,
            )

            self.pages.addWidget(
                page
            )

            self.page_widgets[
                page_name
            ] = (
                page,
                page_layout,
            )

        right_layout.addWidget(
            self.pages,
            1
        )

        # -------------------------------------------------
        # Player
        # -------------------------------------------------

        self.create_player()

        right_layout.addWidget(
            self.player_bar
        )

        root_layout.addWidget(
            self.sidebar
        )

        root_layout.addLayout(
            right_layout,
            1
        )

        self.update_active_navigation(
            "home"
        )

    # =====================================================
    # Player
    # =====================================================

    def create_player(self):

        self.player_bar = QFrame()

        self.player_bar.setMinimumHeight(
            82
        )

        self.player_bar.setMaximumHeight(
            92
        )

        self.player_bar.setStyleSheet(
            """
            QFrame {
                background: rgba(255,255,255,175);
                border: 1px solid rgba(255,255,255,205);
                border-radius: 24px;
            }
            """
        )

        add_shadow(
            self.player_bar,
            28,
            0,
            8,
            32,
        )

        player_layout = QHBoxLayout(
            self.player_bar
        )

        player_layout.setContentsMargins(
            12,
            10,
            12,
            10,
        )

        player_layout.setSpacing(
            12
        )

        # -------------------------------------------------
        # Artwork
        # -------------------------------------------------

        self.player_artwork_label = self.create_artwork_label(
            58,
            rounded=True,
        )

        player_layout.addWidget(
            self.player_artwork_label
        )

        # -------------------------------------------------
        # Info
        # -------------------------------------------------

        info_layout = QVBoxLayout()

        info_layout.setSpacing(
            2
        )

        self.player_title = QLabel(
            "هنوز چیزی در حال پخش نیست"
        )

        self.player_title.setStyleSheet(
            f"""
            QLabel {{
                color: {NAVY};
                font-size: 11px;
                font-weight: 850;
            }}
            """
        )

        self.player_title.setMaximumHeight(
            32
        )

        self.player_title.setWordWrap(
            True
        )

        self.player_time = QLabel(
            "00:00 / 00:00"
        )

        self.player_time.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT_LIGHT};
                font-size: 9px;
            }}
            """
        )

        info_layout.addWidget(
            self.player_title
        )

        info_layout.addWidget(
            self.player_time
        )

        player_layout.addLayout(
            info_layout,
            1,
        )

        # -------------------------------------------------
        # Progress
        # -------------------------------------------------

        self.progress_slider = QSlider(
            Qt.Horizontal
        )

        # صراحتاً چپ‌به‌راست تا جهت پر شدن Progress Bar
        # مستقل از جهت کلی رابط کاربری (RTL) درست باشد.
        self.progress_slider.setLayoutDirection(
            Qt.LeftToRight
        )

        self.progress_slider.setRange(
            0,
            0,
        )

        self.progress_slider.setMinimumWidth(
            180
        )

        self.progress_slider.setCursor(
            Qt.PointingHandCursor
        )

        self.progress_slider.setStyleSheet(
            f"""
            QSlider::groove:horizontal {{
                height: 5px;
                background: rgba(89,98,122,35);
                border-radius: 3px;
            }}

            QSlider::sub-page:horizontal {{
                background: {BLUE};
                border-radius: 3px;
            }}

            QSlider::add-page:horizontal {{
                background: rgba(89,98,122,35);
                border-radius: 3px;
            }}

            QSlider::handle:horizontal {{
                width: 13px;
                height: 13px;
                margin: -4px 0;
                border-radius: 6px;
                background: {BLUE};
                border: 2px solid white;
            }}

            QSlider::handle:horizontal:hover {{
                background: {INDIGO};
            }}
            """
        )

        self.progress_slider.sliderMoved.connect(
            self.change_position
        )

        player_layout.addWidget(
            self.progress_slider,
            1,
        )

        # -------------------------------------------------
        # Volume (آیکون شیک؛ با Hover باز می‌شود و Slider را نشان می‌دهد)
        # -------------------------------------------------

        self.volume_container = VolumeHoverWidget()

        self.volume_container.setStyleSheet(
            "QFrame { background: transparent; border: none; }"
        )

        self.volume_container.setFixedHeight(
            40
        )

        volume_layout = QHBoxLayout(
            self.volume_container
        )

        volume_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        volume_layout.setSpacing(
            8
        )

        self.volume_button = QPushButton()

        self.volume_button.setIcon(
            make_emoji_icon(
                "🔊",
                17,
                TEXT_LIGHT,
            )
        )

        self.volume_button.setIconSize(
            QSize(17, 17)
        )

        self.volume_button.setFixedSize(
            36,
            36,
        )

        self.volume_button.setCursor(
            Qt.PointingHandCursor
        )

        self.volume_button.setStyleSheet(
            """
            QPushButton {
                background: rgba(255,255,255,130);
                border: 1px solid rgba(255,255,255,180);
                border-radius: 18px;
            }

            QPushButton:hover {
                background: rgba(255,255,255,195);
            }
            """
        )

        self.volume_button.clicked.connect(
            self.toggle_mute
        )

        volume_layout.addWidget(
            self.volume_button
        )

        self.volume_slider = VolumeSlider(
            Qt.Horizontal
        )

        self.volume_slider.setLayoutDirection(
            Qt.LeftToRight
        )

        self.volume_slider.setRange(
            0,
            100,
        )

        self.volume_slider.setValue(
            80
        )

        # به‌صورت پیش‌فرض جمع‌شده (عرض صفر)؛ فقط با Hover باز می‌شود.
        self.volume_slider.setMinimumWidth(
            0
        )

        self.volume_slider.setMaximumWidth(
            0
        )

        self.volume_slider.setCursor(
            Qt.PointingHandCursor
        )

        self.volume_slider.setFocusPolicy(
            Qt.StrongFocus
        )

        self.volume_slider.setStyleSheet(
            f"""
            QSlider::groove:horizontal {{
                height: 6px;
                background: rgba(89,98,122,35);
                border-radius: 3px;
            }}

            QSlider::sub-page:horizontal {{
                background: {PURPLE};
                border-radius: 3px;
            }}

            QSlider::add-page:horizontal {{
                background: rgba(89,98,122,35);
                border-radius: 3px;
            }}

            QSlider::handle:horizontal {{
                width: 15px;
                height: 15px;
                margin: -5px 0;
                border-radius: 8px;
                background: {PURPLE};
                border: 2px solid white;
            }}

            QSlider::handle:horizontal:hover {{
                background: {INDIGO};
            }}
            """
        )

        self.volume_slider.valueChanged.connect(
            self.change_volume
        )

        volume_layout.addWidget(
            self.volume_slider
        )

        self.volume_container.on_hover_enter = (
            self.expand_volume_slider
        )

        self.volume_container.on_hover_leave = (
            self.collapse_volume_slider
        )

        player_layout.addWidget(
            self.volume_container
        )

        # -------------------------------------------------
        # Controls
        # -------------------------------------------------

        self.stop_button = QPushButton(
            "■"
        )

        self.stop_button.setFixedSize(
            36,
            36,
        )

        self.stop_button.setCursor(
            Qt.PointingHandCursor
        )

        self.stop_button.clicked.connect(
            self.stop_audio
        )

        self.stop_button.setStyleSheet(
            f"""
            QPushButton {{
                background: rgba(255,255,255,130);
                border: 1px solid rgba(255,255,255,180);
                border-radius: 12px;
                color: {TEXT_LIGHT};
                font-size: 11px;
            }}

            QPushButton:hover {{
                background: rgba(255,255,255,190);
                color: {BLUE};
            }}
            """
        )

        player_layout.addWidget(
            self.stop_button
        )

        self.play_button = QPushButton(
            "▶"
        )

        self.play_button.setFixedSize(
            48,
            48,
        )

        self.play_button.setCursor(
            Qt.PointingHandCursor
        )

        self.play_button.clicked.connect(
            self.toggle_play_pause
        )

        # نکته: برای دایره کامل، border-radius باید دقیقاً
        # نصف عرض/ارتفاع دکمه (48/2 = 24) باشد.
        self.play_button.setStyleSheet(
            f"""
            QPushButton {{
                background: {BLUE};
                border: none;
                border-radius: 24px;
                color: white;
                font-size: 16px;
                font-weight: 900;
            }}

            QPushButton:hover {{
                background: {INDIGO};
            }}

            QPushButton:pressed {{
                background: {NAVY};
            }}
            """
        )

        player_layout.addWidget(
            self.play_button
        )

    # =====================================================
    # Artwork
    # =====================================================

    def set_artwork_on_label(
        self,
        label,
        artwork_data,
        size,
    ):
        """
        فقط bytes معتبر را به عنوان Artwork قبول می‌کند.
        اگر Artwork قسمت موجود نباشد، Artwork خود Podcast
        در caller به عنوان fallback استفاده می‌شود.
        """

        label.clear()

        if artwork_data is None:
            label.setText("🎧")
            return

        # فقط bytes / bytearray
        if not isinstance(
            artwork_data,
            (bytes, bytearray),
        ):
            label.setText("🎧")
            return

        if not artwork_data:
            label.setText("🎧")
            return

        pixmap = QPixmap()

        if not pixmap.loadFromData(
            bytes(artwork_data)
        ):
            label.setText("🎧")
            return

        scaled = pixmap.scaled(
            size,
            size,
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation,
        )

        label.setPixmap(
            scaled
        )

        label.setText("")

    def get_podcast_artwork(
        self,
        podcast=None,
    ):
        """
        Artwork معتبر Podcast را از cache برمی‌گرداند.
        """

        podcast = podcast or self.podcast

        if podcast is None:
            return None

        feed_url = getattr(
            podcast,
            "feed_url",
            None,
        )

        if not feed_url:
            return None

        artwork = self.podcast_artworks.get(
            feed_url
        )

        if isinstance(
            artwork,
            (bytes, bytearray),
        ):
            return artwork

        return None

    # =====================================================
    # Audio connections
    # =====================================================

    def connect_audio(self):

        self.audio_manager.position_changed.connect(
            self.update_position
        )

        self.audio_manager.duration_changed.connect(
            self.update_duration
        )

        self.audio_manager.state_changed.connect(
            self.update_playback_state
        )

        self.audio_manager.error_occurred.connect(
            self.handle_player_error
        )

        self.audio_manager.volume_changed.connect(
            self.sync_volume_slider
        )

    # =====================================================
    # Navigation
    # =====================================================

    def navigate(
        self,
        page_name,
    ):

        if page_name not in self.page_widgets:
            return

        page_index = list(
            self.page_widgets.keys()
        ).index(
            page_name
        )

        self.pages.setCurrentIndex(
            page_index
        )

        if page_name == "home":

            self.show_home()

        elif page_name == "library":

            self.show_library()

        elif page_name == "search":

            self.show_simple_page(
                "search",
                "⌕",
                "جستجو",
                "جستجوی پادکست‌ها و قسمت‌های مورد علاقه شما.",
            )

        elif page_name == "categories":

            self.show_simple_page(
                "categories",
                "◫",
                "دسته‌بندی‌ها",
                "در این بخش دسته‌بندی‌های پادکست‌ها قرار می‌گیرند.",
            )

        elif page_name == "favorites":

            self.show_simple_page(
                "favorites",
                "♡",
                "علاقه‌مندی‌ها",
                "قسمت‌هایی که ذخیره کرده‌اید اینجا نمایش داده می‌شوند.",
            )

        elif page_name == "downloads":

            self.show_simple_page(
                "downloads",
                "↓",
                "دانلودها",
                "قسمت‌های دانلودشده شما در این بخش قرار می‌گیرند.",
            )

        elif page_name == "history":

            self.show_simple_page(
                "history",
                "◷",
                "تاریخچه",
                "تاریخچه شنیدن قسمت‌های شما در این بخش قرار می‌گیرد.",
            )

        elif page_name == "ambient":

            self.show_simple_page(
                "ambient",
                "◌",
                "صدای محیط",
                "صداهای محیطی برای شنیدن در پس‌زمینه.",
            )

        elif page_name == "settings":

            self.show_simple_page(
                "settings",
                "⚙",
                "تنظیمات",
                "تنظیمات برنامه شِنو.",
            )

        self.update_active_navigation(
            page_name
        )

        current_page = self.pages.currentWidget()

        if current_page is not None:
            fade_in(current_page)

    def update_active_navigation(
        self,
        active_page,
    ):

        for page_name, button in self.nav_buttons.items():

            icon_char = self.nav_icons.get(
                page_name,
                "",
            )

            if page_name == active_page:

                button.setStyleSheet(
                    f"""
                    QPushButton {{
                        text-align: right;
                        padding: 0 14px;
                        border: 1px solid rgba(138,111,224,60);
                        border-radius: 14px;
                        background: rgba(138,111,224,32);
                        color: {BLUE};
                        font-size: 12px;
                        font-weight: 850;
                    }}

                    QPushButton:hover {{
                        background: rgba(138,111,224,48);
                    }}
                    """
                )

                button.setIcon(
                    make_emoji_icon(
                        icon_char,
                        22,
                        BLUE,
                    )
                )

            else:

                button.setStyleSheet(
                    f"""
                    QPushButton {{
                        text-align: right;
                        padding: 0 14px;
                        border: none;
                        border-radius: 14px;
                        background: transparent;
                        color: {TEXT_LIGHT};
                        font-size: 12px;
                        font-weight: 700;
                    }}

                    QPushButton:hover {{
                        background: rgba(255,255,255,120);
                        color: {BLUE};
                    }}

                    QPushButton:pressed {{
                        background: rgba(138,111,224,28);
                    }}
                    """
                )

                button.setIcon(
                    make_emoji_icon(
                        icon_char,
                        22,
                        TEXT_LIGHT,
                    )
                )

    # =====================================================
    # Scroll
    # =====================================================

    def make_scroll_area(
        self,
        page_layout,
    ):

        scroll = QScrollArea()

        scroll.setWidgetResizable(
            True
        )

        scroll.setFrameShape(
            QFrame.NoFrame
        )

        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        scroll.setStyleSheet(
            """
            QScrollArea {
                background: transparent;
                border: none;
            }

            QScrollBar:vertical {
                width: 7px;
                background: transparent;
                margin: 8px 0 8px 0;
            }

            QScrollBar::handle:vertical {
                background: rgba(39,39,67,55);
                border-radius: 3px;
                min-height: 35px;
            }

            QScrollBar::handle:vertical:hover {
                background: rgba(110,95,191,110);
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
            }
            """
        )

        content = QWidget()

        content.setStyleSheet(
            "background: transparent;"
        )

        content_layout = QVBoxLayout(
            content
        )

        content_layout.setContentsMargins(
            6,
            6,
            10,
            12,
        )

        content_layout.setSpacing(
            14
        )

        scroll.setWidget(
            content
        )

        page_layout.addWidget(
            scroll
        )

        return content_layout

    # =====================================================
    # Home
    # =====================================================

    def show_home(self):

        page, page_layout = self.page_widgets[
            "home"
        ]

        clear_layout(
            page_layout
        )

        content_layout = self.make_scroll_area(
            page_layout
        )

        # -------------------------------------------------
        # Header
        # -------------------------------------------------

        header_layout = QHBoxLayout()

        title_layout = QVBoxLayout()

        title = QLabel(
            "سلام 👋"
        )

        title.setStyleSheet(
            f"""
            QLabel {{
                color: {NAVY};
                font-size: 27px;
                font-weight: 900;
            }}
            """
        )

        subtitle = QLabel(
            "چیزی برای شنیدن پیدا کنیم؟"
        )

        subtitle.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT_LIGHT};
                font-size: 11px;
            }}
            """
        )

        title_layout.addWidget(
            title
        )

        title_layout.addWidget(
            subtitle
        )

        header_layout.addLayout(
            title_layout
        )

        header_layout.addStretch()

        if self.podcast is not None:

            active_label = QLabel(
                f"در حال نمایش: {self.podcast.title}"
            )

            active_label.setStyleSheet(
                f"""
                QLabel {{
                    color: {BLUE};
                    background: rgba(138,111,224,28);
                    border: 1px solid rgba(138,111,224,60);
                    border-radius: 12px;
                    padding: 8px 12px;
                    font-size: 9px;
                    font-weight: 800;
                }}
                """
            )

            header_layout.addWidget(
                active_label
            )

        content_layout.addLayout(
            header_layout
        )

        # -------------------------------------------------
        # Quick navigation
        # -------------------------------------------------

        quick_layout = QHBoxLayout()

        quick_items = [
            ("✨", "جدیدترین‌ها"),
            ("🎙️", "پادکست‌ها"),
            ("♡", "علاقه‌مندی‌ها"),
        ]

        for icon, text in quick_items:

            button = QPushButton(
                f"{icon}  {text}"
            )

            button.setCursor(
                Qt.PointingHandCursor
            )

            button.setFixedHeight(
                36
            )

            button.setStyleSheet(
                f"""
                QPushButton {{
                    background: rgba(255,255,255,125);
                    border: 1px solid rgba(255,255,255,175);
                    border-radius: 12px;
                    color: {TEXT_LIGHT};
                    padding: 0 14px;
                    font-size: 9px;
                    font-weight: 700;
                }}

                QPushButton:hover {{
                    background: rgba(255,255,255,190);
                    color: {BLUE};
                }}
                """
            )

            quick_layout.addWidget(
                button
            )

        quick_layout.addStretch()

        content_layout.addLayout(
            quick_layout
        )

        # -------------------------------------------------
        # Loading
        # -------------------------------------------------

        if self.podcast is None:

            loading_card = self.create_glass_card(
                strong=True
            )

            loading_layout = QVBoxLayout(
                loading_card
            )

            loading_layout.setContentsMargins(
                30,
                40,
                30,
                40,
            )

            icon = QLabel(
                "🎧"
            )

            icon.setAlignment(
                Qt.AlignCenter
            )

            icon.setStyleSheet(
                """
                QLabel {
                    font-size: 48px;
                }
                """
            )

            loading_title = QLabel(
                "در حال دریافت پادکست‌ها..."
            )

            loading_title.setAlignment(
                Qt.AlignCenter
            )

            loading_title.setStyleSheet(
                f"""
                QLabel {{
                    color: {NAVY};
                    font-size: 17px;
                    font-weight: 850;
                }}
                """
            )

            loading_text = QLabel(
                "برای اولین اجرا، شِنو اطلاعات پادکست‌ها و تصاویر آن‌ها را از RSS دریافت می‌کند."
            )

            loading_text.setAlignment(
                Qt.AlignCenter
            )

            loading_text.setWordWrap(
                True
            )

            loading_text.setStyleSheet(
                f"""
                QLabel {{
                    color: {TEXT_LIGHT};
                    font-size: 10px;
                }}
                """
            )

            loading_layout.addWidget(
                icon
            )

            loading_layout.addWidget(
                loading_title
            )

            loading_layout.addSpacing(
                6
            )

            loading_layout.addWidget(
                loading_text
            )

            content_layout.addWidget(
                loading_card
            )

            content_layout.addStretch()

            self.update_active_navigation(
                "home"
            )

            return

        # -------------------------------------------------
        # No episodes
        # -------------------------------------------------

        if not self.podcast.episodes:

            empty = QLabel(
                "برای این پادکست هنوز قسمتی دریافت نشده است."
            )

            empty.setStyleSheet(
                f"""
                QLabel {{
                    color: {TEXT_LIGHT};
                    font-size: 13px;
                }}
                """
            )

            content_layout.addWidget(
                empty
            )

            content_layout.addStretch()

            return

        # -------------------------------------------------
        # Latest episode
        # -------------------------------------------------

        latest_header = self.create_section_header(
            "آخرین قسمت",
            "جدیدترین چیزی که می‌توانی گوش بدهی",
        )

        content_layout.addLayout(
            latest_header
        )

        latest_episode = self.podcast.episodes[0]

        hero = self.create_hero_card(
            latest_episode
        )

        content_layout.addWidget(
            hero
        )

        # -------------------------------------------------
        # Continue
        # -------------------------------------------------

        continue_header = self.create_section_header(
            "ادامه پخش",
            "از همان‌جایی که متوقف شدی",
        )

        content_layout.addLayout(
            continue_header
        )

        continue_card = self.create_continue_card(
            latest_episode
        )

        content_layout.addWidget(
            continue_card
        )

        # -------------------------------------------------
        # Episodes
        # -------------------------------------------------

        episodes_header = self.create_section_header(
            "قسمت‌های جدید",
            "آخرین قسمت‌های منتشرشده",
        )

        content_layout.addLayout(
            episodes_header
        )

        episode_scroll = QScrollArea()

        episode_scroll.setWidgetResizable(
            True
        )

        episode_scroll.setFixedHeight(
            285
        )

        episode_scroll.setFrameShape(
            QFrame.NoFrame
        )

        episode_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        episode_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        episode_scroll.setStyleSheet(
            """
            QScrollArea {
                background: transparent;
                border: none;
            }

            QScrollBar:horizontal {
                height: 6px;
                background: transparent;
            }

            QScrollBar::handle:horizontal {
                background: rgba(39,39,67,55);
                border-radius: 3px;
                min-width: 45px;
            }

            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                width: 0;
            }
            """
        )

        episode_container = QWidget()

        episode_layout = QHBoxLayout(
            episode_container
        )

        episode_layout.setContentsMargins(
            4,
            4,
            4,
            10,
        )

        episode_layout.setSpacing(
            14
        )

        for episode in self.podcast.episodes[:12]:

            card = self.create_episode_card(
                episode
            )

            episode_layout.addWidget(
                card
            )

        episode_layout.addStretch()

        episode_scroll.setWidget(
            episode_container
        )

        content_layout.addWidget(
            episode_scroll
        )

        content_layout.addStretch()

        self.update_active_navigation(
            "home"
        )

    # =====================================================
    # Section Header
    # =====================================================

    def create_section_header(
        self,
        title_text,
        subtitle_text="",
    ):

        layout = QHBoxLayout()

        text_layout = QVBoxLayout()

        title = QLabel(
            title_text
        )

        title.setStyleSheet(
            f"""
            QLabel {{
                color: {NAVY};
                font-size: 17px;
                font-weight: 900;
            }}
            """
        )

        text_layout.addWidget(
            title
        )

        if subtitle_text:

            subtitle = QLabel(
                subtitle_text
            )

            subtitle.setStyleSheet(
                f"""
                QLabel {{
                    color: {TEXT_LIGHT};
                    font-size: 9px;
                }}
                """
            )

            text_layout.addWidget(
                subtitle
            )

        layout.addLayout(
            text_layout
        )

        layout.addStretch()

        return layout

    # =====================================================
    # Glass Card
    # =====================================================

    def create_glass_card(
        self,
        strong=False,
    ):

        card = QFrame()

        background = (
            GLASS_STRONG
            if strong
            else GLASS
        )

        card.setStyleSheet(
            f"""
            QFrame {{
                background: {background};
                border: 1px solid {BORDER};
                border-radius: 24px;
            }}
            """
        )

        add_shadow(
            card,
            28,
            0,
            7,
            25,
        )

        return card

    # =====================================================
    # Hero Card
    # =====================================================

    def create_hero_card(
        self,
        episode,
    ):

        card = QFrame()

        card.setMinimumHeight(
            225
        )

        card.setMaximumHeight(
            255
        )

        card.setStyleSheet(
            f"""
            QFrame {{
                background: qlineargradient(
                    x1: 0,
                    y1: 0,
                    x2: 1,
                    y2: 1,
                    stop: 0 rgba(93,78,158,220),
                    stop: 0.45 rgba(110,95,191,225),
                    stop: 1 rgba(138,111,224,215)
                );
                border: 1px solid rgba(255,255,255,110);
                border-radius: 28px;
            }}
            """
        )

        add_shadow(
            card,
            35,
            0,
            12,
            40,
        )

        layout = QHBoxLayout(
            card
        )

        layout.setContentsMargins(
            18,
            18,
            18,
            18,
        )

        layout.setSpacing(
            18
        )

        # -------------------------------------------------
        # Artwork
        # -------------------------------------------------

        artwork = self.create_artwork_label(
            185,
            rounded=True,
        )

        # مهم:
        # در Home عمداً Artwork قسمت را در اولویت قرار
        # نمی‌دهیم. Artwork Podcast مطمئن‌تر است.
        artwork_data = self.get_podcast_artwork()

        self.set_artwork_on_label(
            artwork,
            artwork_data,
            185,
        )

        layout.addWidget(
            artwork
        )

        # -------------------------------------------------
        # Info
        # -------------------------------------------------

        info_layout = QVBoxLayout()

        info_layout.setSpacing(
            7
        )

        latest = QLabel(
            "آخرین قسمت"
        )

        latest.setStyleSheet(
            """
            QLabel {
                color: rgba(255,255,255,210);
                font-size: 10px;
                font-weight: 800;
            }
            """
        )

        podcast_name = QLabel(
            self.podcast.title
        )

        podcast_name.setStyleSheet(
            """
            QLabel {
                color: rgba(255,255,255,205);
                font-size: 10px;
                font-weight: 700;
            }
            """
        )

        title = QLabel(
            getattr(
                episode,
                "title",
                "بدون عنوان",
            )
        )

        title.setWordWrap(
            True
        )

        title.setMaximumHeight(
            65
        )

        title.setStyleSheet(
            """
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: 900;
            }
            """
        )

        description_text = self.clean_html(
            getattr(
                episode,
                "description",
                "",
            )
        )

        if len(description_text) > 150:

            description_text = (
                description_text[:150]
                + "..."
            )

        description = QLabel(
            description_text
        )

        description.setWordWrap(
            True
        )

        description.setMaximumHeight(
            48
        )

        description.setStyleSheet(
            """
            QLabel {
                color: rgba(255,255,255,190);
                font-size: 10px;
            }
            """
        )

        info_layout.addWidget(
            latest
        )

        info_layout.addWidget(
            podcast_name
        )

        info_layout.addWidget(
            title
        )

        info_layout.addWidget(
            description
        )

        info_layout.addStretch()

        # -------------------------------------------------
        # Play
        # -------------------------------------------------

        play_button = QPushButton(
            "▶  پخش قسمت"
        )

        play_button.setCursor(
            Qt.PointingHandCursor
        )

        play_button.setMinimumSize(
            135,
            43,
        )

        play_button.setMaximumWidth(
            160
        )

        play_button.setStyleSheet(
            """
            QPushButton {
                background: rgba(255,255,255,225);
                border: 1px solid rgba(255,255,255,245);
                border-radius: 15px;
                color: #2B2743;
                font-size: 11px;
                font-weight: 850;
                padding: 0 18px;
            }

            QPushButton:hover {
                background: white;
                color: #6E5FBF;
            }

            QPushButton:pressed {
                background: rgba(255,255,255,180);
            }
            """
        )

        play_button.clicked.connect(
            lambda checked=False,
            current_episode=episode:
            self.play_episode(
                current_episode
            )
        )

        info_layout.addWidget(
            play_button,
            0,
            Qt.AlignLeft,
        )

        layout.addLayout(
            info_layout,
            1,
        )

        return card

    # =====================================================
    # Continue Card
    # =====================================================

    def create_continue_card(
        self,
        episode,
    ):

        card = self.create_glass_card()

        card.setMinimumHeight(
            92
        )

        layout = QHBoxLayout(
            card
        )

        layout.setContentsMargins(
            15,
            12,
            15,
            12,
        )

        layout.setSpacing(
            13
        )

        icon = QLabel(
            "▶"
        )

        icon.setFixedSize(
            48,
            48,
        )

        icon.setAlignment(
            Qt.AlignCenter
        )

        icon.setStyleSheet(
            f"""
            QLabel {{
                background: rgba(138,111,224,30);
                border: 1px solid rgba(138,111,224,70);
                border-radius: 15px;
                color: {BLUE};
                font-size: 17px;
                font-weight: 900;
            }}
            """
        )

        layout.addWidget(
            icon
        )

        text_layout = QVBoxLayout()

        text_layout.setSpacing(
            3
        )

        title = QLabel(
            "ادامه پخش"
        )

        title.setStyleSheet(
            f"""
            QLabel {{
                color: {NAVY};
                font-size: 12px;
                font-weight: 850;
            }}
            """
        )

        episode_title = getattr(
            episode,
            "title",
            "قسمت انتخاب‌شده",
        )

        label = QLabel(
            f"{episode_title}  •  شروع نشده"
        )

        label.setWordWrap(
            True
        )

        label.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT_LIGHT};
                font-size: 9px;
            }}
            """
        )

        text_layout.addWidget(
            title
        )

        text_layout.addWidget(
            label
        )

        layout.addLayout(
            text_layout,
            1,
        )

        button = QPushButton(
            "پخش"
        )

        button.setCursor(
            Qt.PointingHandCursor
        )

        button.setFixedSize(
            72,
            38,
        )

        button.setStyleSheet(
            f"""
            QPushButton {{
                background: rgba(138,111,224,30);
                border: 1px solid rgba(138,111,224,75);
                border-radius: 13px;
                color: {BLUE};
                font-weight: 850;
            }}

            QPushButton:hover {{
                background: rgba(138,111,224,55);
            }}
            """
        )

        button.clicked.connect(
            lambda checked=False,
            current_episode=episode:
            self.play_episode(
                current_episode
            )
        )

        layout.addWidget(
            button
        )

        return card

    # =====================================================
    # Episode Card
    # =====================================================

    def create_episode_card(
        self,
        episode,
    ):

        card = QFrame()

        card.setFixedWidth(
            285
        )

        card.setMinimumHeight(
            255
        )

        card.setMaximumHeight(
            265
        )

        card.setStyleSheet(
            f"""
            QFrame {{
                background: rgba(255,255,255,145);
                border: 1px solid rgba(255,255,255,175);
                border-radius: 22px;
            }}

            QFrame:hover {{
                background: rgba(255,255,255,190);
                border: 1px solid rgba(138,111,224,85);
            }}
            """
        )

        add_shadow(
            card,
            22,
            0,
            5,
            20,
        )

        layout = QVBoxLayout(
            card
        )

        layout.setContentsMargins(
            12,
            12,
            12,
            12,
        )

        layout.setSpacing(
            8
        )

        # -------------------------------------------------
        # Artwork
        # -------------------------------------------------

        artwork = self.create_artwork_label(
            82,
            rounded=True,
        )

        artwork_data = self.get_podcast_artwork()

        self.set_artwork_on_label(
            artwork,
            artwork_data,
            82,
        )

        # -------------------------------------------------
        # Top
        # -------------------------------------------------

        top_layout = QHBoxLayout()

        top_layout.addWidget(
            artwork
        )

        info = QVBoxLayout()

        info.setSpacing(
            4
        )

        badge = QLabel(
            "جدید"
        )

        badge.setStyleSheet(
            f"""
            QLabel {{
                background: rgba(138,111,224,28);
                color: {BLUE};
                border-radius: 7px;
                padding: 3px 7px;
                font-size: 8px;
                font-weight: 900;
            }}
            """
        )

        badge.setFixedWidth(
            45
        )

        title = QLabel(
            getattr(
                episode,
                "title",
                "بدون عنوان",
            )
        )

        title.setWordWrap(
            True
        )

        title.setMaximumHeight(
            62
        )

        title.setStyleSheet(
            f"""
            QLabel {{
                color: {NAVY};
                font-size: 11px;
                font-weight: 850;
            }}
            """
        )

        date_text = getattr(
            episode,
            "published_at",
            "",
        )

        date_label = QLabel(
            date_text or "قسمت جدید"
        )

        date_label.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT_LIGHT};
                font-size: 8px;
            }}
            """
        )

        info.addWidget(
            badge,
            0,
            Qt.AlignLeft,
        )

        info.addWidget(
            title
        )

        info.addWidget(
            date_label
        )

        info.addStretch()

        top_layout.addLayout(
            info,
            1,
        )

        layout.addLayout(
            top_layout
        )

        # -------------------------------------------------
        # Description
        # -------------------------------------------------

        description_text = self.clean_html(
            getattr(
                episode,
                "description",
                "",
            )
        )

        if len(description_text) > 105:

            description_text = (
                description_text[:105]
                + "..."
            )

        description = QLabel(
            description_text
        )

        description.setWordWrap(
            True
        )

        description.setMaximumHeight(
            42
        )

        description.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT_LIGHT};
                font-size: 9px;
            }}
            """
        )

        layout.addWidget(
            description
        )

        # -------------------------------------------------
        # Bottom
        # -------------------------------------------------

        bottom_layout = QHBoxLayout()

        bottom_layout.addStretch()

        play = QPushButton(
            "▶  پخش"
        )

        play.setCursor(
            Qt.PointingHandCursor
        )

        play.setFixedHeight(
            34
        )

        play.setMinimumWidth(
            82
        )

        play.setStyleSheet(
            f"""
            QPushButton {{
                background: rgba(255,255,255,155);
                border: 1px solid rgba(255,255,255,185);
                border-radius: 12px;
                color: {BLUE};
                font-size: 10px;
                font-weight: 850;
                padding: 0 12px;
            }}

            QPushButton:hover {{
                background: rgba(138,111,224,40);
                border: 1px solid rgba(138,111,224,75);
            }}
            """
        )

        play.clicked.connect(
            lambda checked=False,
            current_episode=episode:
            self.play_episode(
                current_episode
            )
        )

        bottom_layout.addWidget(
            play
        )

        layout.addLayout(
            bottom_layout
        )

        return card

    # =====================================================
    # Artwork Label
    # =====================================================

    def create_artwork_label(
        self,
        size,
        rounded=True,
    ):

        label = QLabel()

        label.setFixedSize(
            size,
            size,
        )

        label.setAlignment(
            Qt.AlignCenter
        )

        radius = (
            20
            if rounded
            else 0
        )

        label.setStyleSheet(
            f"""
            QLabel {{
                background: rgba(255,255,255,95);
                border: 1px solid rgba(255,255,255,160);
                border-radius: {radius}px;
                color: rgba(255,255,255,185);
                font-size: 28px;
                font-weight: 800;
            }}
            """
        )

        label.setText(
            "🎧"
        )

        return label

    # =====================================================
    # Podcast Library
    # =====================================================

    def show_library(self):

        page, page_layout = self.page_widgets[
            "library"
        ]

        clear_layout(
            page_layout
        )

        content_layout = self.make_scroll_area(
            page_layout
        )

        # -------------------------------------------------
        # Header
        # -------------------------------------------------

        header = QLabel(
            "🎙️  پادکست‌ها"
        )

        header.setStyleSheet(
            f"""
            QLabel {{
                color: {NAVY};
                font-size: 27px;
                font-weight: 900;
            }}
            """
        )

        content_layout.addWidget(
            header
        )

        subtitle = QLabel(
            "پادکست‌های دریافت‌شده در شِنو"
        )

        subtitle.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT_LIGHT};
                font-size: 10px;
            }}
            """
        )

        content_layout.addWidget(
            subtitle
        )

        podcasts = (
            self.podcast_repository.get_all()
        )

        if not podcasts:

            empty_card = self.create_glass_card(
                strong=True
            )

            empty_layout = QVBoxLayout(
                empty_card
            )

            empty_layout.setContentsMargins(
                25,
                35,
                25,
                35,
            )

            icon = QLabel(
                "🎧"
            )

            icon.setAlignment(
                Qt.AlignCenter
            )

            icon.setStyleSheet(
                """
                QLabel {
                    font-size: 42px;
                }
                """
            )

            empty = QLabel(
                "هنوز پادکستی دریافت نشده است."
            )

            empty.setAlignment(
                Qt.AlignCenter
            )

            empty.setStyleSheet(
                f"""
                QLabel {{
                    color: {TEXT_LIGHT};
                    font-size: 13px;
                }}
                """
            )

            empty_layout.addWidget(
                icon
            )

            empty_layout.addWidget(
                empty
            )

            content_layout.addWidget(
                empty_card
            )

            content_layout.addStretch()

            self.update_active_navigation(
                "library"
            )

            return

        # -------------------------------------------------
        # Podcast Cards
        # -------------------------------------------------

        for podcast in podcasts:

            card = self.create_glass_card()

            card.setMinimumHeight(
                125
            )

            layout = QHBoxLayout(
                card
            )

            layout.setContentsMargins(
                14,
                12,
                14,
                12,
            )

            layout.setSpacing(
                15
            )

            # -------------------------------------------------
            # Artwork
            # -------------------------------------------------

            artwork = self.create_artwork_label(
                92,
                rounded=True,
            )

            artwork_data = self.get_podcast_artwork(
                podcast
            )

            self.set_artwork_on_label(
                artwork,
                artwork_data,
                92,
            )

            layout.addWidget(
                artwork
            )

            # -------------------------------------------------
            # Text
            # -------------------------------------------------

            text_layout = QVBoxLayout()

            text_layout.setSpacing(
                5
            )

            title = QLabel(
                podcast.title
                or "پادکست بدون عنوان"
            )

            title.setStyleSheet(
                f"""
                QLabel {{
                    color: {NAVY};
                    font-size: 16px;
                    font-weight: 900;
                }}
                """
            )

            author_text = (
                podcast.author
                or "گوینده نامشخص"
            )

            author = QLabel(
                f"🎙️  {author_text}"
            )

            author.setStyleSheet(
                f"""
                QLabel {{
                    color: {TEXT_LIGHT};
                    font-size: 10px;
                }}
                """
            )

            episodes_count = len(
                podcast.episodes
            )

            episodes_label = QLabel(
                f"🎧  {episodes_count} قسمت"
            )

            episodes_label.setStyleSheet(
                f"""
                QLabel {{
                    color: {TEXT_LIGHT};
                    font-size: 9px;
                }}
                """
            )

            text_layout.addWidget(
                title
            )

            text_layout.addWidget(
                author
            )

            text_layout.addWidget(
                episodes_label
            )

            text_layout.addStretch()

            layout.addLayout(
                text_layout,
                1,
            )

            # -------------------------------------------------
            # Select
            # -------------------------------------------------

            is_active = (
                self.podcast is not None
                and self.podcast.feed_url
                == podcast.feed_url
            )

            button = QPushButton(
                "در حال نمایش"
                if is_active
                else "انتخاب"
            )

            button.setCursor(
                Qt.PointingHandCursor
            )

            button.setFixedSize(
                95,
                38,
            )

            if is_active:

                button.setStyleSheet(
                    f"""
                    QPushButton {{
                        background: rgba(138,111,224,45);
                        border: 1px solid rgba(138,111,224,80);
                        border-radius: 13px;
                        color: {BLUE};
                        font-size: 10px;
                        font-weight: 850;
                    }}
                    """
                )

            else:

                button.setStyleSheet(
                    f"""
                    QPushButton {{
                        background: rgba(255,255,255,130);
                        border: 1px solid rgba(255,255,255,180);
                        border-radius: 13px;
                        color: {BLUE};
                        font-size: 10px;
                        font-weight: 850;
                    }}

                    QPushButton:hover {{
                        background: rgba(138,111,224,45);
                        border: 1px solid rgba(138,111,224,75);
                    }}
                    """
                )

            button.clicked.connect(
                lambda checked=False,
                p=podcast:
                self.select_podcast(p)
            )

            layout.addWidget(
                button
            )

            content_layout.addWidget(
                card
            )

        content_layout.addStretch()

        self.update_active_navigation(
            "library"
        )

    # =====================================================
    # Select Podcast
    # =====================================================

    def select_podcast(
        self,
        podcast,
    ):

        if podcast is None:
            return

        feed_url = getattr(
            podcast,
            "feed_url",
            None,
        )

        if not feed_url:
            return

        success = (
            self.podcast_repository.set_active(
                feed_url
            )
        )

        if not success:
            return

        self.podcast = (
            self.podcast_repository.get_active()
        )

        if self.podcast is None:
            return

        print(
            "Active podcast:",
            self.podcast.title
        )

        self.update_player_artwork()

        self.show_home()

        self.pages.setCurrentIndex(
            list(
                self.page_widgets.keys()
            ).index("home")
        )

        self.update_active_navigation(
            "home"
        )

    # =====================================================
    # Simple Pages
    # =====================================================

    def show_simple_page(
        self,
        page_name,
        icon,
        title_text,
        description_text,
    ):

        page, page_layout = self.page_widgets[
            page_name
        ]

        clear_layout(
            page_layout
        )

        content_layout = self.make_scroll_area(
            page_layout
        )

        header = QLabel(
            f"{icon}   {title_text}"
        )

        header.setStyleSheet(
            f"""
            QLabel {{
                color: {NAVY};
                font-size: 27px;
                font-weight: 900;
                padding: 5px 0;
            }}
            """
        )

        content_layout.addWidget(
            header
        )

        description = QLabel(
            description_text
        )

        description.setWordWrap(
            True
        )

        description.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT_LIGHT};
                font-size: 11px;
                padding-bottom: 8px;
            }}
            """
        )

        content_layout.addWidget(
            description
        )

        card = self.create_glass_card(
            strong=True
        )

        card_layout = QVBoxLayout(
            card
        )

        card_layout.setContentsMargins(
            35,
            35,
            35,
            35,
        )

        big_icon = QLabel(
            icon
        )

        big_icon.setAlignment(
            Qt.AlignCenter
        )

        big_icon.setStyleSheet(
            """
            QLabel {
                font-size: 45px;
            }
            """
        )

        message = QLabel(
            "این بخش را در مرحله بعدی کامل می‌کنیم ✨"
        )

        message.setAlignment(
            Qt.AlignCenter
        )

        message.setStyleSheet(
            f"""
            QLabel {{
                color: {NAVY};
                font-size: 17px;
                font-weight: 850;
            }}
            """
        )

        card_layout.addWidget(
            big_icon
        )

        card_layout.addWidget(
            message
        )

        content_layout.addWidget(
            card
        )

        content_layout.addStretch()

    # =====================================================
    # RSS Loading
    # =====================================================

    def start_rss_loading(self):

        if self.rss_loading:
            return

        if (
            self.default_podcast_index
            >= len(self.default_podcasts)
        ):
            return

        config = (
            self.default_podcasts[
                self.default_podcast_index
            ]
        )

        feed_url = config.get(
            "feed_url",
            "",
        )

        if not feed_url:
            self.default_podcast_index += 1
            self.start_rss_loading()
            return

        self.rss_loading = True

        print(
            "Loading podcast:",
            config.get(
                "title",
                "Unknown",
            )
        )

        self.rss_thread = QThread()

        self.rss_worker = RSSWorker(
            feed_url
        )

        self.rss_worker.moveToThread(
            self.rss_thread
        )

        self.rss_thread.started.connect(
            self.rss_worker.run
        )

        self.rss_worker.finished.connect(
            self.on_rss_finished
        )

        self.rss_worker.error.connect(
            self.on_rss_error
        )

        self.rss_worker.finished.connect(
            self.rss_thread.quit
        )

        self.rss_worker.error.connect(
            self.rss_thread.quit
        )

        self.rss_thread.finished.connect(
            self.rss_worker.deleteLater
        )

        self.rss_thread.finished.connect(
            self.rss_thread.deleteLater
        )

        self.rss_thread.finished.connect(
            self.rss_thread_finished
        )

        self.rss_thread.start()

    # =====================================================
    # RSS Finished
    # =====================================================

    @Slot(object, object)
    def on_rss_finished(
        self,
        podcast,
        artwork_data,
    ):

        if podcast is None:
            self.default_podcast_index += 1
            self.rss_loading = False
            return

        # -------------------------------------------------
        # Repository
        # -------------------------------------------------

        self.podcast_repository.add(
            podcast
        )

        # -------------------------------------------------
        # Artwork
        # -------------------------------------------------

        if isinstance(
            artwork_data,
            (bytes, bytearray),
        ) and artwork_data:

            self.podcast_artworks[
                podcast.feed_url
            ] = bytes(artwork_data)

        # -------------------------------------------------
        # Log
        # -------------------------------------------------

        print(
            "Podcast loaded:",
            podcast.title,
            "| Episodes:",
            len(podcast.episodes),
            "| Artwork:",
            bool(
                self.podcast_artworks.get(
                    podcast.feed_url
                )
            ),
        )

        # -------------------------------------------------
        # First podcast becomes active
        # -------------------------------------------------

        if self.podcast is None:

            self.podcast_repository.set_active(
                podcast.feed_url
            )

            self.podcast = (
                self.podcast_repository.get_active()
            )

            if self.podcast is not None:

                print(
                    "Active podcast:",
                    self.podcast.title
                )

                self.update_player_artwork()

        # -------------------------------------------------
        # Move to next RSS
        # -------------------------------------------------

        self.default_podcast_index += 1

        self.rss_loading = False

    # =====================================================
    # RSS Error
    # =====================================================

    @Slot(str)
    def on_rss_error(
        self,
        message,
    ):

        print(
            "RSS Error:",
            message
        )

        self.rss_errors.append(
            {
                "index": self.default_podcast_index,
                "message": message,
            }
        )

        self.default_podcast_index += 1

        self.rss_loading = False

    # =====================================================
    # RSS Thread Finished
    # =====================================================

    def rss_thread_finished(self):

        self.rss_thread = None
        self.rss_worker = None
        self.rss_loading = False

        # -------------------------------------------------
        # More podcasts
        # -------------------------------------------------

        if (
            self.default_podcast_index
            < len(self.default_podcasts)
        ):

            self.start_rss_loading()

            return

        # -------------------------------------------------
        # All loaded
        # -------------------------------------------------

        self.podcast = (
            self.podcast_repository.get_active()
        )

        print(
            "All default podcasts loaded."
        )

        print(
            "Total podcasts:",
            len(
                self.podcast_repository.get_all()
            )
        )

        if self.podcast is None:

            self.show_rss_error(
                "هیچ پادکستی دریافت نشد."
            )

            return

        self.show_home()

        self.update_player_artwork()

    # =====================================================
    # RSS Error UI
    # =====================================================

    def show_rss_error(
        self,
        message,
    ):

        page, page_layout = self.page_widgets[
            "home"
        ]

        clear_layout(
            page_layout
        )

        content_layout = self.make_scroll_area(
            page_layout
        )

        title = QLabel(
            "سلام 👋"
        )

        title.setStyleSheet(
            f"""
            QLabel {{
                color: {NAVY};
                font-size: 30px;
                font-weight: 900;
            }}
            """
        )

        content_layout.addWidget(
            title
        )

        card = self.create_glass_card(
            strong=True
        )

        card_layout = QVBoxLayout(
            card
        )

        card_layout.setContentsMargins(
            30,
            30,
            30,
            30,
        )

        icon = QLabel(
            "⚠️"
        )

        icon.setAlignment(
            Qt.AlignCenter
        )

        icon.setStyleSheet(
            """
            QLabel {
                font-size: 40px;
            }
            """
        )

        error_title = QLabel(
            "دریافت پادکست کامل نشد"
        )

        error_title.setAlignment(
            Qt.AlignCenter
        )

        error_title.setStyleSheet(
            f"""
            QLabel {{
                color: {NAVY};
                font-size: 17px;
                font-weight: 850;
            }}
            """
        )

        error_text = QLabel(
            message
        )

        error_text.setAlignment(
            Qt.AlignCenter
        )

        error_text.setWordWrap(
            True
        )

        error_text.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT_LIGHT};
                font-size: 10px;
            }}
            """
        )

        retry = QPushButton(
            "↻  تلاش دوباره"
        )

        retry.setCursor(
            Qt.PointingHandCursor
        )

        retry.setFixedSize(
            135,
            40,
        )

        retry.setStyleSheet(
            f"""
            QPushButton {{
                background: rgba(138,111,224,32);
                border: 1px solid rgba(138,111,224,75);
                border-radius: 13px;
                color: {BLUE};
                font-weight: 850;
            }}

            QPushButton:hover {{
                background: rgba(138,111,224,58);
            }}
            """
        )

        retry.clicked.connect(
            self.start_rss_loading
        )

        card_layout.addWidget(
            icon
        )

        card_layout.addWidget(
            error_title
        )

        card_layout.addSpacing(
            6
        )

        card_layout.addWidget(
            error_text
        )

        card_layout.addSpacing(
            12
        )

        card_layout.addWidget(
            retry,
            0,
            Qt.AlignCenter,
        )

        content_layout.addWidget(
            card
        )

        content_layout.addStretch()

    # =====================================================
    # Play Episode
    # =====================================================

    def play_episode(
        self,
        episode,
    ):

        if episode is None:
            print(
                "Episode not found."
            )
            return

        url = getattr(
            episode,
            "audio_url",
            "",
        )

        title = getattr(
            episode,
            "title",
            "بدون عنوان",
        )

        if not url:

            print(
                "Audio URL not found."
            )

            return

        try:

            self.audio_manager.play(
                episode
            )

            self.player_title.setText(
                title
            )

            self.play_button.setText(
                "Ⅱ"
            )

            self.update_player_artwork()

        except Exception as error:

            print(
                "Play Error:",
                error
            )

    # =====================================================
    # Toggle Play / Pause
    # =====================================================

    def toggle_play_pause(self):

        if not self.audio_manager.source_valid():
            return

        self.audio_manager.toggle()

    # =====================================================
    # Stop
    # =====================================================

    def stop_audio(self):

        self.audio_manager.stop()

        self.progress_slider.setValue(
            0
        )

        self.play_button.setText(
            "▶"
        )

        self.player_time.setText(
            "00:00 / 00:00"
        )

    # =====================================================
    # Position
    # =====================================================

    def change_position(
        self,
        position,
    ):

        self.audio_manager.seek(
            position
        )

    def update_position(
        self,
        position,
    ):

        if not self.progress_slider.isSliderDown():

            self.progress_slider.setValue(
                position
            )

        playback_state = (
            self.audio_manager.playback_state
        )

        self.player_time.setText(
            f"{format_time(playback_state.position)} / "
            f"{format_time(playback_state.duration)}"
        )

    # =====================================================
    # Duration
    # =====================================================

    def update_duration(
        self,
        duration,
    ):

        playback_state = (
            self.audio_manager.playback_state
        )

        self.progress_slider.setRange(
            0,
            max(
                playback_state.duration,
                0,
            ),
        )

        self.player_time.setText(
            f"{format_time(playback_state.position)} / "
            f"{format_time(playback_state.duration)}"
        )

    # =====================================================
    # Playback State
    # =====================================================

    def update_playback_state(
        self,
        state,
    ):

        if state == QMediaPlayer.PlayingState:

            self.play_button.setText(
                "Ⅱ"
            )

        else:

            self.play_button.setText(
                "▶"
            )

    # =====================================================
    # Media Status
    # =====================================================

    def update_media_status(
        self,
        status,
    ):

        if status == QMediaPlayer.EndOfMedia:

            self.play_button.setText(
                "▶"
            )

            self.progress_slider.setValue(
                0
            )

    # =====================================================
    # Player Error
    # =====================================================

    def handle_player_error(
        self,
        error_string,
    ):

        print(
            "Player Error:",
            error_string
        )

    # =====================================================
    # Volume
    # =====================================================

    def change_volume(
        self,
        value,
    ):
        """
        تغییر میزان صدا. AudioManager دقیقاً set_volume(0.0-1.0)
        را پیاده‌سازی کرده، پس مستقیم صدا زده می‌شود.
        """

        volume = max(
            0.0,
            min(
                1.0,
                value / 100.0,
            ),
        )

        self.audio_manager.set_volume(volume)

        self.update_volume_icon(
            value
        )

    def sync_volume_slider(
        self,
        volume,
    ):
        """
        اگر Volume از جایی دیگر (مثلاً mute/unmute) تغییر کند،
        اسلایدر پایین پلیر را هم‌گام نگه می‌دارد بدون ایجاد حلقه.
        """

        value = int(round(volume * 100))

        self.volume_slider.blockSignals(True)

        self.volume_slider.setValue(
            value
        )

        self.volume_slider.blockSignals(False)

        self.update_volume_icon(
            value
        )

    def update_volume_icon(
        self,
        value,
    ):
        """
        بسته به میزان صدا (یا Mute بودن)، آیکون بلندگو را عوض می‌کند.
        """

        is_muted = (
            hasattr(self.audio_manager, "is_muted")
            and self.audio_manager.is_muted()
        )

        if is_muted or value <= 0:
            emoji = "🔇"
        elif value < 50:
            emoji = "🔉"
        else:
            emoji = "🔊"

        self.volume_button.setIcon(
            make_emoji_icon(
                emoji,
                17,
                TEXT_LIGHT,
            )
        )

    def toggle_mute(self):
        """
        با کلیک روی آیکون بلندگو، صدا Mute/Unmute می‌شود.
        """

        if not hasattr(self.audio_manager, "is_muted"):
            return

        if self.audio_manager.is_muted():
            self.audio_manager.unmute()
        else:
            self.audio_manager.mute()

        self.update_volume_icon(
            self.volume_slider.value()
        )

    def expand_volume_slider(self):
        """
        هنگام Hover روی ناحیه Volume، Slider با انیمیشن نرم باز می‌شود.
        """

        self._animate_volume_width(
            112
        )

    def collapse_volume_slider(self):
        """
        هنگام خروج موس از ناحیه Volume، Slider دوباره جمع می‌شود.
        """

        self._animate_volume_width(
            0
        )

    def _animate_volume_width(
        self,
        target_width,
    ):

        animation = QPropertyAnimation(
            self.volume_slider,
            b"maximumWidth",
            self,
        )

        animation.setDuration(
            200
        )

        animation.setStartValue(
            self.volume_slider.maximumWidth()
        )

        animation.setEndValue(
            target_width
        )

        animation.setEasingCurve(
            QEasingCurve.OutCubic
        )

        animation.start(
            QPropertyAnimation.DeleteWhenStopped
        )

        self._volume_width_animation = animation

    # =====================================================
    # Player Artwork
    # =====================================================

    def update_player_artwork(self):

        podcast = self.podcast

        if podcast is None:
            return

        artwork_data = self.get_podcast_artwork(
            podcast
        )

        if not artwork_data:
            return

        self.set_artwork_on_label(
            self.player_artwork_label,
            artwork_data,
            58,
        )

    # =====================================================
    # Clean HTML
    # =====================================================

    def clean_html(
        self,
        text,
    ):

        if not text:
            return ""

        text = re.sub(
            r"<[^>]+>",
            "",
            str(text),
        )

        text = (
            text
            .replace("&nbsp;", " ")
            .replace("&amp;", "&")
            .replace("&quot;", '"')
            .replace("&#39;", "'")
        )

        return " ".join(
            text.split()
        )

    # =====================================================
    # Resize
    # =====================================================

    def resizeEvent(
        self,
        event,
    ):

        super().resizeEvent(
            event
        )

        self.background.setGeometry(
            self.rect()
        )

        self.background.lower()

    # =====================================================
    # Close
    # =====================================================

    def closeEvent(
        self,
        event,
    ):

        if (
            self.rss_thread
            and self.rss_thread.isRunning()
        ):

            self.rss_thread.quit()

            self.rss_thread.wait(
                2000
            )

        self.audio_manager.stop()

        super().closeEvent(
            event
        )


# =========================================================
# Application
# =========================================================

def main():

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "شِنو"
    )

    app.setLayoutDirection(
        Qt.RightToLeft
    )

    app.setStyle(
        "Fusion"
    )

    font = QFont(
        "Segoe UI Variable Text"
    )

    font.setStyleStrategy(
        QFont.PreferAntialias
    )

    app.setFont(
        font
    )

    window = ShenoWindow()

    window.show()

    enable_windows_mica(
        window
    )

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()
