import sys
import ctypes


from PySide6.QtCore import (
    Qt,
    QThread,
    Slot,
)
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtGui import (
    QPixmap,
    QPainter,
    QColor,
    QLinearGradient,
    QRadialGradient,
    QFont,
)
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
)
from core.rss_manager import RSSWorker
from core.audio_manager import AudioManager
from core.podcast_repository import PodcastRepository
from data.podcasts import DEFAULT_PODCASTS
# =========================================================
# تنظیمات اصلی
# =========================================================


# =========================================================
# رنگ‌ها
# =========================================================

CYAN = "#09C7D9"
BLUE = "#176EA3"
INDIGO = "#485196"
NAVY = "#272743"

WHITE = "#FFFFFF"
SOFT_WHITE = "#F8FCFF"

GLASS = "rgba(255, 255, 255, 112)"
GLASS_LIGHT = "rgba(255, 255, 255, 145)"
GLASS_STRONG = "rgba(255, 255, 255, 180)"

BORDER = "rgba(255, 255, 255, 145)"
BORDER_SOFT = "rgba(255, 255, 255, 95)"

TEXT = "#272743"
TEXT_LIGHT = "#59627A"
TEXT_WHITE = "#FFFFFF"

PURPLE = "#7667D9"
PINK = "#D96ACB"


# =========================================================
# Mica / Windows 11
# =========================================================

def enable_windows_mica(widget):
    try:
        if sys.platform != "win32":
            return

        hwnd = int(widget.winId())

        DWMWA_SYSTEMBACKDROP_TYPE = 38
        DWMSBT_MAINWINDOW = 2

        value = ctypes.c_int(DWMSBT_MAINWINDOW)

        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            ctypes.c_void_p(hwnd),
            DWMWA_SYSTEMBACKDROP_TYPE,
            ctypes.byref(value),
            ctypes.sizeof(value)
        )

    except Exception as error:
        print("Mica:", error)


# =========================================================
# پس‌زمینه‌ی رنگی
# =========================================================

class GlassBackground(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()

        # -------------------------------------------------
        # Base Gradient
        # -------------------------------------------------

        base_gradient = QLinearGradient(
            0,
            0,
            rect.width(),
            rect.height()
        )

        base_gradient.setColorAt(
            0.0,
            QColor("#EAF7FC")
        )

        base_gradient.setColorAt(
            0.38,
            QColor("#F6FBFF")
        )

        base_gradient.setColorAt(
            0.72,
            QColor("#EEF6FF")
        )

        base_gradient.setColorAt(
            1.0,
            QColor("#F8F5FF")
        )

        painter.fillRect(rect, base_gradient)

        # -------------------------------------------------
        # Cyan Glow
        # -------------------------------------------------

        cyan_center = (
            int(rect.width() * 0.78),
            int(rect.height() * 0.12)
        )

        cyan_gradient = QRadialGradient(
            cyan_center[0],
            cyan_center[1],
            max(rect.width(), rect.height()) * 0.42
        )

        cyan_gradient.setColorAt(
            0.0,
            QColor(9, 199, 217, 80)
        )

        cyan_gradient.setColorAt(
            0.45,
            QColor(9, 199, 217, 32)
        )

        cyan_gradient.setColorAt(
            1.0,
            QColor(9, 199, 217, 0)
        )

        painter.fillRect(rect, cyan_gradient)

        # -------------------------------------------------
        # Purple Glow
        # -------------------------------------------------

        purple_center = (
            int(rect.width() * 0.08),
            int(rect.height() * 0.80)
        )

        purple_gradient = QRadialGradient(
            purple_center[0],
            purple_center[1],
            max(rect.width(), rect.height()) * 0.38
        )

        purple_gradient.setColorAt(
            0.0,
            QColor(118, 103, 217, 55)
        )

        purple_gradient.setColorAt(
            0.5,
            QColor(118, 103, 217, 20)
        )

        purple_gradient.setColorAt(
            1.0,
            QColor(118, 103, 217, 0)
        )

        painter.fillRect(rect, purple_gradient)

        # -------------------------------------------------
        # Blue Glow
        # -------------------------------------------------

        blue_center = (
            int(rect.width() * 0.90),
            int(rect.height() * 0.78)
        )

        blue_gradient = QRadialGradient(
            blue_center[0],
            blue_center[1],
            max(rect.width(), rect.height()) * 0.32
        )

        blue_gradient.setColorAt(
            0.0,
            QColor(23, 110, 163, 38)
        )

        blue_gradient.setColorAt(
            1.0,
            QColor(23, 110, 163, 0)
        )

        painter.fillRect(rect, blue_gradient)

        painter.end()


# =========================================================
# ابزارهای کمکی
# =========================================================

def clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)

        widget = item.widget()

        if widget is not None:
            widget.deleteLater()

        child_layout = item.layout()

        if child_layout is not None:
            clear_layout(child_layout)


def add_shadow(widget, blur=28, y=8, alpha=35):

    shadow = QGraphicsDropShadowEffect(widget)

    shadow.setBlurRadius(blur)
    shadow.setOffset(0, y)
    shadow.setColor(
        QColor(39, 39, 67, alpha)
    )

    widget.setGraphicsEffect(shadow)


def format_time(milliseconds):

    if milliseconds <= 0:
        return "00:00"

    total_seconds = milliseconds // 1000

    minutes = total_seconds // 60
    seconds = total_seconds % 60

    return f"{minutes:02}:{seconds:02}"


# =========================================================
# Main Window
# =========================================================

class ShenoWindow(QWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("شنو")

        self.podcast_repository = PodcastRepository()

        self.resize(1200, 760)

        self.setMinimumSize(
            900,
            600
        )

        self.setAttribute(
            Qt.WA_TranslucentBackground
        )

        self.setLayoutDirection(
            Qt.RightToLeft
        )

        # -------------------------------------------------
        # State
        # -------------------------------------------------

        self.podcast = None
        self.podcast_artwork = None

        self.rss_thread = None
        self.rss_worker = None
        self.rss_loading = False

        # -------------------------------------------------
        # مدیریت پادکست‌های پیش‌فرض
        # -------------------------------------------------

        self.default_podcasts = DEFAULT_PODCASTS
        self.default_podcast_index = 0
        self.rss_errors = []

        # -------------------------------------------------
        # Audio Manager
        # -------------------------------------------------

        self.audio_manager = AudioManager()

        # -------------------------------------------------
        # Main UI
        # -------------------------------------------------

        self.build_ui()

        self.connect_audio()

        self.show_home()

        self.start_rss_loading()

    # =====================================================
    # UI
    # =====================================================

    def build_ui(self):

        # ---------------------------------------------
        # Root
        # ---------------------------------------------

        root_layout = QHBoxLayout(self)

        root_layout.setContentsMargins(
            18,
            18,
            18,
            18
        )

        root_layout.setSpacing(14)

        # ---------------------------------------------
        # Background
        # ---------------------------------------------

        self.background = GlassBackground(self)

        self.background.lower()

        # ---------------------------------------------
        # Sidebar
        # ---------------------------------------------

        self.sidebar = QFrame()

        self.sidebar.setFixedWidth(
            238
        )

        self.sidebar.setStyleSheet(
            """
            QFrame {
                background: rgba(255,255,255,125);
                border: 1px solid rgba(255,255,255,145);
                border-radius: 26px;
            }
            """
        )

        add_shadow(
            self.sidebar,
            30,
            8,
            25
        )

        sidebar_layout = QVBoxLayout(
            self.sidebar
        )

        sidebar_layout.setContentsMargins(
            16,
            18,
            16,
            16
        )

        sidebar_layout.setSpacing(8)

        # ---------------------------------------------
        # Logo
        # ---------------------------------------------

        logo = QLabel(
            "🎧  شِنو"
        )

        logo.setStyleSheet(
            f"""
            QLabel {{
                color: {NAVY};
                font-size: 25px;
                font-weight: 800;
                padding: 8px 10px 18px 10px;
            }}
            """
        )

        sidebar_layout.addWidget(
            logo
        )

        subtitle = QLabel(
            "پادکست، موسیقی و آرامش"
        )

        subtitle.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT_LIGHT};
                font-size: 11px;
                padding: 0 10px 15px 10px;
            }}
            """
        )

        sidebar_layout.addWidget(
            subtitle
        )

        # ---------------------------------------------
        # Navigation
        # ---------------------------------------------

        self.nav_buttons = {}

        menu_items = [
            ("home", "🏠", "خانه"),
            ("search", "🔎", "جستجو"),
            ("categories", "📚", "دسته‌بندی‌ها"),
            ("favorites", "❤️", "مورد علاقه‌ها"),
            ("downloads", "⬇️", "دانلودها"),
            ("history", "🕘", "تاریخچه"),
            ("ambient", "🌧️", "صداهای آرامش‌بخش"),
            ("settings", "⚙️", "تنظیمات"),
        ]

        for key, icon, text in menu_items:

            button = QPushButton(
                f"{icon}   {text}"
            )

            button.setCursor(
                Qt.PointingHandCursor
            )

            button.setMinimumHeight(
                47
            )

            button.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Fixed
            )

            button.setStyleSheet(
                f"""
                QPushButton {{
                    background: transparent;
                    border: 1px solid transparent;
                    border-radius: 15px;
                    color: {TEXT_LIGHT};
                    text-align: right;
                    padding: 0 14px;
                    font-size: 13px;
                    font-weight: 600;
                }}

                QPushButton:hover {{
                    background: rgba(255,255,255,135);
                    color: {BLUE};
                    border: 1px solid rgba(255,255,255,145);
                }}

                QPushButton:pressed {{
                    background: rgba(9,199,217,38);
                }}
                """
            )

            button.clicked.connect(
                lambda checked=False,
                page=key:
                self.navigate(page)
            )

            self.nav_buttons[key] = button

            sidebar_layout.addWidget(
                button
            )

        sidebar_layout.addStretch()

        # ---------------------------------------------
        # Sidebar bottom
        # ---------------------------------------------

        version_card = QFrame()

        version_card.setStyleSheet(
            """
            QFrame {
                background: rgba(255,255,255,105);
                border: 1px solid rgba(255,255,255,125);
                border-radius: 17px;
            }
            """
        )

        version_layout = QVBoxLayout(
            version_card
        )

        version_layout.setContentsMargins(
            12,
            10,
            12,
            10
        )

        version_title = QLabel(
            "شِنو"
        )

        version_title.setStyleSheet(
            f"""
            QLabel {{
                color: {NAVY};
                font-weight: 700;
                font-size: 12px;
            }}
            """
        )

        version_text = QLabel(
            "نسخه‌ی آزمایشی • Windows"
        )

        version_text.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT_LIGHT};
                font-size: 10px;
            }}
            """
        )

        version_layout.addWidget(
            version_title
        )

        version_layout.addWidget(
            version_text
        )

        sidebar_layout.addWidget(
            version_card
        )

        # ---------------------------------------------
        # Right side
        # ---------------------------------------------

        right_layout = QVBoxLayout()

        right_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        right_layout.setSpacing(10)

        # ---------------------------------------------
        # Pages
        # ---------------------------------------------

        self.pages = QStackedWidget()

        self.pages.setStyleSheet(
            """
            QStackedWidget {
                background: transparent;
                border: none;
            }
            """
        )

        self.page_widgets = {}

        for key in [
            "home",
            "search",
            "categories",
            "favorites",
            "downloads",
            "history",
            "ambient",
            "settings"
        ]:

            page = QWidget()

            page_layout = QVBoxLayout(
                page
            )

            page_layout.setContentsMargins(
                6,
                4,
                6,
                0
            )

            page_layout.setSpacing(0)

            self.page_widgets[key] = (
                page,
                page_layout
            )

            self.pages.addWidget(
                page
            )

        right_layout.addWidget(
            self.pages,
            1
        )

        # ---------------------------------------------
        # Floating player
        # ---------------------------------------------

        self.create_player(
            right_layout
        )

        root_layout.addWidget(
            self.sidebar
        )

        root_layout.addLayout(
            right_layout,
            1
        )

    # =====================================================
    # Player
    # =====================================================

    def create_player(
        self,
        parent_layout
    ):

        player_outer = QFrame()

        player_outer.setStyleSheet(
            """
            QFrame {
                background: transparent;
                border: none;
            }
            """
        )

        outer_layout = QHBoxLayout(
            player_outer
        )

        outer_layout.setContentsMargins(
            4,
            4,
            4,
            4
        )

        self.player_bar = QFrame()

        self.player_bar.setMinimumHeight(
            82
        )

        self.player_bar.setStyleSheet(
            f"""
            QFrame {{
                background: rgba(255,255,255,165);
                border: 1px solid rgba(255,255,255,180);
                border-radius: 24px;
            }}

            QPushButton {{
                background: rgba(255,255,255,130);
                border: 1px solid rgba(255,255,255,150);
                border-radius: 15px;
                color: {NAVY};
                font-size: 15px;
                font-weight: 700;
            }}

            QPushButton:hover {{
                background: rgba(255,255,255,205);
                color: {BLUE};
            }}

            QPushButton:pressed {{
                background: rgba(9,199,217,55);
            }}

            QSlider::groove:horizontal {{
                height: 5px;
                background: rgba(72,81,150,35);
                border-radius: 3px;
            }}

            QSlider::handle:horizontal {{
                width: 13px;
                height: 13px;
                margin: -4px 0;
                background: {CYAN};
                border-radius: 6px;
            }}

            QSlider::sub-page:horizontal {{
                background: {CYAN};
                border-radius: 3px;
            }}
            """
        )

        add_shadow(
            self.player_bar,
            30,
            8,
            30
        )

        outer_layout.addWidget(
            self.player_bar
        )

        player_layout = QHBoxLayout(
            self.player_bar
        )

        player_layout.setContentsMargins(
            13,
            10,
            13,
            10
        )

        player_layout.setSpacing(10)

        # ---------------------------------------------
        # Artwork
        # ---------------------------------------------

        self.player_artwork = QLabel()

        self.player_artwork.setFixedSize(
            58,
            58
        )

        self.player_artwork.setAlignment(
            Qt.AlignCenter
        )

        self.player_artwork.setStyleSheet(
            """
            QLabel {
                background: rgba(255,255,255,115);
                border: 1px solid rgba(255,255,255,150);
                border-radius: 14px;
            }
            """
        )

        player_layout.addWidget(
            self.player_artwork
        )

        # ---------------------------------------------
        # Info
        # ---------------------------------------------

        info_layout = QVBoxLayout()

        info_layout.setSpacing(3)

        self.player_title = QLabel(
            "هنوز چیزی در حال پخش نیست"
        )

        self.player_title.setStyleSheet(
            f"""
            QLabel {{
                color: {NAVY};
                font-size: 12px;
                font-weight: 700;
            }}
            """
        )

        self.player_title.setWordWrap(
            False
        )

        self.player_time = QLabel(
            "00:00 / 00:00"
        )

        self.player_time.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT_LIGHT};
                font-size: 10px;
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
            1
        )

        # ---------------------------------------------
        # Progress
        # ---------------------------------------------

        self.progress_slider = QSlider(
            Qt.Horizontal
        )

        self.progress_slider.setRange(
            0,
            0
        )

        self.progress_slider.setMinimumWidth(
            180
        )

        self.progress_slider.setCursor(
            Qt.PointingHandCursor
        )

        self.progress_slider.sliderMoved.connect(
            self.change_position
        )

        player_layout.addWidget(
            self.progress_slider,
            2
        )

        # ---------------------------------------------
        # Buttons
        # ---------------------------------------------

        self.play_button = QPushButton(
            "▶"
        )

        self.play_button.setFixedSize(
            44,
            44
        )

        self.play_button.setCursor(
            Qt.PointingHandCursor
        )

        self.play_button.clicked.connect(
            self.toggle_play_pause
        )

        self.stop_button = QPushButton(
            "■"
        )

        self.stop_button.setFixedSize(
            38,
            38
        )

        self.stop_button.setCursor(
            Qt.PointingHandCursor
        )

        self.stop_button.clicked.connect(
            self.stop_audio
        )

        player_layout.addWidget(
            self.stop_button
        )

        player_layout.addWidget(
            self.play_button
        )

        parent_layout.addWidget(
            player_outer
        )

    # =====================================================
    # Audio connections
    # =====================================================
    def connect_audio(self):

        # ---------------------------------------------
        # اصلاح‌شده: به سیگنال‌های خودِ AudioManager
        # وصل می‌شیم، نه مستقیم به audio_manager.player
        # این‌طوری AudioManager واقعاً یه لایه‌ی
        # مستقل و قابل تعویض می‌مونه
        # ---------------------------------------------

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

    # =====================================================
    # Navigation
    # =====================================================

    def navigate(
        self,
        page_name
    ):

        if page_name not in self.page_widgets:
            return

        index = self.pages.indexOf(
            self.page_widgets[page_name][0]
        )

        if index >= 0:

            self.pages.setCurrentIndex(
                index
            )

        # ---------------------------------------------
        # Refresh home
        # ---------------------------------------------

        if page_name == "home":

            self.show_home()

        elif page_name == "search":

            self.show_simple_page(
                "search",
                "🔎",
                "جستجو",
                "اینجا قرار است جستجوی هوشمند اپیزودها را بسازیم."
            )

        elif page_name == "categories":

            self.show_simple_page(
                "categories",
                "📚",
                "دسته‌بندی‌ها",
                "موضوعات مختلف پادکست‌ها در این بخش قرار می‌گیرند."
            )

        elif page_name == "favorites":

            self.show_simple_page(
                "favorites",
                "❤️",
                "مورد علاقه‌ها",
                "قسمت‌هایی که دوست داری اینجا ذخیره می‌شوند."
            )

        elif page_name == "downloads":

            self.show_simple_page(
                "downloads",
                "⬇️",
                "دانلودها",
                "مدیریت اپیزودهای دانلودشده در این بخش خواهد بود."
            )

        elif page_name == "history":

            self.show_simple_page(
                "history",
                "🕘",
                "تاریخچه",
                "تاریخچه‌ی پخش‌های اخیر اینجا نمایش داده می‌شود."
            )

        elif page_name == "ambient":

            self.show_simple_page(
                "ambient",
                "🌧️",
                "صداهای آرامش‌بخش",
                "یک فضای آرام برای تمرکز، مطالعه و استراحت."
            )

        elif page_name == "settings":

            self.show_simple_page(
                "settings",
                "⚙️",
                "تنظیمات",
                "تنظیمات برنامه در این بخش قرار خواهد گرفت."
            )

        self.update_active_navigation(
            page_name
        )

    # =====================================================
    # Active navigation
    # =====================================================

    def update_active_navigation(
        self,
        active
    ):

        for key, button in self.nav_buttons.items():

            if key == active:

                button.setStyleSheet(
                    f"""
                    QPushButton {{
                        background: rgba(9,199,217,42);
                        border: 1px solid rgba(9,199,217,75);
                        border-radius: 15px;
                        color: {BLUE};
                        text-align: right;
                        padding: 0 14px;
                        font-size: 13px;
                        font-weight: 800;
                    }}

                    QPushButton:hover {{
                        background: rgba(9,199,217,58);
                    }}
                    """
                )

            else:

                button.setStyleSheet(
                    f"""
                    QPushButton {{
                        background: transparent;
                        border: 1px solid transparent;
                        border-radius: 15px;
                        color: {TEXT_LIGHT};
                        text-align: right;
                        padding: 0 14px;
                        font-size: 13px;
                        font-weight: 600;
                    }}

                    QPushButton:hover {{
                        background: rgba(255,255,255,135);
                        color: {BLUE};
                        border: 1px solid rgba(255,255,255,145);
                    }}

                    QPushButton:pressed {{
                        background: rgba(9,199,217,38);
                    }}
                    """
                )

    # =====================================================
    # Scroll page
    # =====================================================

    def make_scroll_area(
        self,
        page_layout
    ):

        scroll = QScrollArea()

        scroll.setWidgetResizable(
            True
        )

        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        scroll.setStyleSheet(
            """
            QScrollArea {
                background: transparent;
                border: none;
            }

            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 8px 0 8px 0;
            }

            QScrollBar::handle:vertical {
                background: rgba(72,81,150,70);
                border-radius: 4px;
                min-height: 45px;
            }

            QScrollBar::handle:vertical:hover {
                background: rgba(23,110,163,110);
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
            20,
            15,
            20,
            25
        )

        content_layout.setSpacing(
            18
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

        page, page_layout = (
            self.page_widgets["home"]
        )

        clear_layout(
            page_layout
        )

        content_layout = self.make_scroll_area(
            page_layout
        )

        # ---------------------------------------------
        # Header
        # ---------------------------------------------

        header_layout = QHBoxLayout()

        title_box = QVBoxLayout()

        title = QLabel(
            "سلام 👋"
        )

        title.setStyleSheet(
            f"""
            QLabel {{
                color: {NAVY};
                font-size: 30px;
                font-weight: 850;
            }}
            """
        )

        subtitle = QLabel(
            "امروز چی دوست داری گوش بدی؟"
        )

        subtitle.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT_LIGHT};
                font-size: 14px;
                margin-top: 3px;
            }}
            """
        )

        title_box.addWidget(
            title
        )

        title_box.addWidget(
            subtitle
        )

        header_layout.addLayout(
            title_box
        )

        header_layout.addStretch()

        status = QLabel(
            "●  شِنو آماده است"
        )

        status.setStyleSheet(
            f"""
            QLabel {{
                background: rgba(9,199,217,28);
                color: {BLUE};
                border: 1px solid rgba(9,199,217,55);
                border-radius: 15px;
                padding: 8px 14px;
                font-size: 11px;
                font-weight: 700;
            }}
            """
        )

        header_layout.addWidget(
            status
        )

        content_layout.addLayout(
            header_layout
        )

        # ---------------------------------------------
        # Quick category floating buttons
        # ---------------------------------------------

        category_row = QHBoxLayout()

        category_row.setSpacing(
            10
        )

        quick_categories = [
            ("🤖", "هوش مصنوعی"),
            ("🐍", "پایتون"),
            ("💻", "برنامه‌نویسی"),
            ("📚", "آموزش"),
            ("🌙", "آرامش"),
        ]

        for icon, text in quick_categories:

            button = QPushButton(
                f"{icon}  {text}"
            )

            button.setCursor(
                Qt.PointingHandCursor
            )

            button.setMinimumHeight(
                42
            )

            button.setStyleSheet(
                f"""
                QPushButton {{
                    background: rgba(255,255,255,125);
                    border: 1px solid rgba(255,255,255,150);
                    border-radius: 15px;
                    color: {NAVY};
                    padding: 0 15px;
                    font-size: 11px;
                    font-weight: 700;
                }}

                QPushButton:hover {{
                    background: rgba(255,255,255,205);
                    border: 1px solid rgba(9,199,217,80);
                    color: {BLUE};
                }}

                QPushButton:pressed {{
                    background: rgba(9,199,217,45);
                }}
                """
            )

            category_row.addWidget(
                button
            )

        category_row.addStretch()

        content_layout.addLayout(
            category_row
        )

        # ---------------------------------------------
        # Loading
        # ---------------------------------------------

        if not self.podcast:

            loading_card = self.create_glass_card()

            loading_layout = QVBoxLayout(
                loading_card
            )

            loading_layout.setContentsMargins(
                28,
                30,
                28,
                30
            )

            loading_icon = QLabel(
                "☁️"
            )

            loading_icon.setAlignment(
                Qt.AlignCenter
            )

            loading_icon.setStyleSheet(
                """
                QLabel {
                    font-size: 34px;
                }
                """
            )

            loading_text = QLabel(
                "در حال دریافت آخرین اپیزودها..."
            )

            loading_text.setAlignment(
                Qt.AlignCenter
            )

            loading_text.setStyleSheet(
                f"""
                QLabel {{
                    color: {NAVY};
                    font-size: 15px;
                    font-weight: 700;
                }}
                """
            )

            loading_layout.addWidget(
                loading_icon
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

        # ---------------------------------------------
        # Latest title
        # ---------------------------------------------

        latest_header = self.create_section_header(
            "آخرین قسمت",
            "جدیدترین چیزی که شِنو از فید دریافت کرده"
        )

        content_layout.addWidget(
            latest_header
        )

        # ---------------------------------------------
        # Hero
        # ---------------------------------------------

        latest_episode = (
            self.podcast.episodes[0]
        )

        hero = self.create_hero_card(
            latest_episode
        )

        content_layout.addWidget(
            hero
        )

        # ---------------------------------------------
        # Continue
        # ---------------------------------------------

        continue_header = self.create_section_header(
            "ادامه پخش",
            "دوباره از همان‌جایی که متوقف شدی"
        )

        content_layout.addWidget(
            continue_header
        )

        continue_card = self.create_continue_card(
            latest_episode
        )

        content_layout.addWidget(
            continue_card
        )

        # ---------------------------------------------
        # Episodes
        # ---------------------------------------------

        episodes_header = self.create_section_header(
            "آخرین قسمت‌ها",
            "چند قسمت اخیر پادکست"
        )

        content_layout.addWidget(
            episodes_header
        )

        episode_scroll = QScrollArea()

        episode_scroll.setWidgetResizable(
            True
        )

        episode_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        episode_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        episode_scroll.setFixedHeight(
            235
        )

        episode_scroll.setStyleSheet(
            """
            QScrollArea {
                background: transparent;
                border: none;
            }
            """
        )

        episode_container = QWidget()

        episode_container.setStyleSheet(
            "background: transparent;"
        )

        episode_layout = QHBoxLayout(
            episode_container
        )

        episode_layout.setContentsMargins(
            4,
            4,
            4,
            4
        )

        episode_layout.setSpacing(
            14
        )

        for episode in self.podcast.episodes[:10]:

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
    # Section header
    # =====================================================

    def create_section_header(
        self,
        title_text,
        subtitle_text
    ):

        wrapper = QWidget()

        wrapper.setStyleSheet(
            "background: transparent;"
        )

        layout = QVBoxLayout(
            wrapper
        )

        layout.setContentsMargins(
            2,
            3,
            2,
            0
        )

        layout.setSpacing(
            2
        )

        title = QLabel(
            title_text
        )

        title.setStyleSheet(
            f"""
            QLabel {{
                color: {NAVY};
                font-size: 18px;
                font-weight: 850;
            }}
            """
        )

        subtitle = QLabel(
            subtitle_text
        )

        subtitle.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT_LIGHT};
                font-size: 10px;
            }}
            """
        )

        layout.addWidget(
            title
        )

        layout.addWidget(
            subtitle
        )

        return wrapper

    # =====================================================
    # Glass Card
    # =====================================================

    def create_glass_card(
        self,
        strong=False
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
            7,
            25
        )

        return card

    # =====================================================
    # Hero
    # =====================================================

    def create_hero_card(
        self,
        episode
    ):

        card = QFrame()

        card.setMinimumHeight(
            270
        )

        card.setStyleSheet(
            """
            QFrame {
                background: qlineargradient(
                    x1: 0,
                    y1: 0,
                    x2: 1,
                    y2: 1,
                    stop: 0 rgba(39,39,67,235),
                    stop: 0.45 rgba(72,81,150,225),
                    stop: 0.75 rgba(23,110,163,225),
                    stop: 1 rgba(9,199,217,220)
                );

                border: 1px solid rgba(255,255,255,80);
                border-radius: 28px;
            }
            """
        )

        add_shadow(
            card,
            35,
            10,
            40
        )

        layout = QHBoxLayout(
            card
        )

        layout.setContentsMargins(
            24,
            24,
            24,
            24
        )

        layout.setSpacing(
            24
        )

        # ---------------------------------------------
        # Artwork
        # ---------------------------------------------

        artwork = self.create_artwork_label(
            190,
            rounded=True
        )

        if self.podcast_artwork:

            pixmap = QPixmap()

            pixmap.loadFromData(
                self.podcast_artwork
            )

            if not pixmap.isNull():

                artwork.setPixmap(
                    pixmap.scaled(
                        190,
                        190,
                        Qt.KeepAspectRatioByExpanding,
                        Qt.SmoothTransformation
                    )
                )

        layout.addWidget(
            artwork
        )

        # ---------------------------------------------
        # Text
        # ---------------------------------------------

        info_layout = QVBoxLayout()

        info_layout.setSpacing(
            8
        )

        latest = QLabel(
            "✦  LATEST EPISODE"
        )

        latest.setStyleSheet(
            """
            QLabel {
                color: rgba(255,255,255,210);
                font-size: 10px;
                font-weight: 800;
                letter-spacing: 1px;
            }
            """
        )

        podcast_name = QLabel(
            getattr(
                self.podcast,
                "title",
                "پادکست"
            )
        )

        podcast_name.setStyleSheet(
            """
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: 700;
            }
            """
        )

        title = QLabel(
            getattr(
                episode,
                "title",
                "بدون عنوان"
            )
        )

        title.setWordWrap(
            True
        )

        title.setStyleSheet(
            """
            QLabel {
                color: white;
                font-size: 21px;
                font-weight: 850;
                line-height: 1.3;
            }
            """
        )

        description_text = getattr(
            episode,
            "description",
            "قسمت جدید پادکست."
        )

        description_text = self.clean_html(
            description_text
        )

        if len(description_text) > 210:

            description_text = (
                description_text[:210]
                + "..."
            )

        description = QLabel(
            description_text
        )

        description.setWordWrap(
            True
        )

        description.setStyleSheet(
            """
            QLabel {
                color: rgba(255,255,255,190);
                font-size: 11px;
                line-height: 1.4;
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

        # ---------------------------------------------
        # Play
        # ---------------------------------------------

        play_button = QPushButton(
            "▶   پخش قسمت"
        )

        play_button.setCursor(
            Qt.PointingHandCursor
        )

        play_button.setMinimumSize(
            135,
            43
        )

        play_button.setStyleSheet(
            """
            QPushButton {
                background: rgba(255,255,255,225);
                border: 1px solid rgba(255,255,255,245);
                border-radius: 15px;
                color: #272743;
                font-size: 12px;
                font-weight: 800;
                padding: 0 18px;
            }

            QPushButton:hover {
                background: white;
                color: #176EA3;
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
            Qt.AlignLeft
        )

        layout.addLayout(
            info_layout,
            1
        )

        return card

    # =====================================================
    # Continue card
    # =====================================================

    def create_continue_card(
        self,
        episode
    ):

        card = self.create_glass_card()

        card.setMinimumHeight(
            100
        )

        layout = QHBoxLayout(
            card
        )

        layout.setContentsMargins(
            16,
            12,
            16,
            12
        )

        layout.setSpacing(
            14
        )

        # ---------------------------------------------
        # Icon
        # ---------------------------------------------

        icon = QLabel(
            "▶"
        )

        icon.setFixedSize(
            50,
            50
        )

        icon.setAlignment(
            Qt.AlignCenter
        )

        icon.setStyleSheet(
            f"""
            QLabel {{
                background: rgba(9,199,217,35);
                border: 1px solid rgba(9,199,217,70);
                border-radius: 16px;
                color: {BLUE};
                font-size: 18px;
                font-weight: 800;
            }}
            """
        )

        layout.addWidget(
            icon
        )

        # ---------------------------------------------
        # Text
        # ---------------------------------------------

        text_layout = QVBoxLayout()

        title = QLabel(
            "ادامه‌ی پخش"
        )

        title.setStyleSheet(
            f"""
            QLabel {{
                color: {NAVY};
                font-size: 13px;
                font-weight: 800;
            }}
            """
        )

        episode_title = episode.title

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
                font-size: 10px;
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
            1
        )

        # ---------------------------------------------
        # Button
        # ---------------------------------------------

        button = QPushButton(
            "پخش"
        )

        button.setCursor(
            Qt.PointingHandCursor
        )

        button.setFixedSize(
            72,
            38
        )

        button.setStyleSheet(
            f"""
            QPushButton {{
                background: rgba(9,199,217,35);
                border: 1px solid rgba(9,199,217,75);
                border-radius: 13px;
                color: {BLUE};
                font-weight: 800;
            }}

            QPushButton:hover {{
                background: rgba(9,199,217,60);
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
    # Episode card
    # =====================================================

    def create_episode_card(
        self,
        episode
    ):

        card = QFrame()

        card.setFixedWidth(
            280
        )

        card.setMinimumHeight(
            205
        )

        card.setStyleSheet(
            f"""
            QFrame {{
                background: rgba(255,255,255,135);
                border: 1px solid rgba(255,255,255,160);
                border-radius: 22px;
            }}

            QFrame:hover {{
                background: rgba(255,255,255,180);
                border: 1px solid rgba(9,199,217,70);
            }}
            """
        )

        add_shadow(
            card,
            22,
            6,
            22
        )

        layout = QVBoxLayout(
            card
        )

        layout.setContentsMargins(
            12,
            12,
            12,
            12
        )

        layout.setSpacing(
            8
        )

        # ---------------------------------------------
        # Artwork + info
        # ---------------------------------------------

        top_layout = QHBoxLayout()

        artwork = self.create_artwork_label(
            78,
            rounded=True
        )

        if self.podcast_artwork:

            pixmap = QPixmap()

            pixmap.loadFromData(
                self.podcast_artwork
            )

            if not pixmap.isNull():

                artwork.setPixmap(
                    pixmap.scaled(
                        78,
                        78,
                        Qt.KeepAspectRatioByExpanding,
                        Qt.SmoothTransformation
                    )
                )

        top_layout.addWidget(
            artwork
        )

        info = QVBoxLayout()

        info.setSpacing(
            4
        )

        badge = QLabel(
            "NEW"
        )

        badge.setStyleSheet(
            f"""
            QLabel {{
                background: rgba(9,199,217,32);
                color: {BLUE};
                border-radius: 7px;
                padding: 3px 7px;
                font-size: 8px;
                font-weight: 900;
            }}
            """
        )

        badge.setFixedWidth(
            42
        )

        title = QLabel(
            getattr(
                episode,
                "title",
                "بدون عنوان"
            )
        )

        title.setWordWrap(
            True
        )

        title.setMaximumHeight(
            52
        )

        title.setStyleSheet(
            f"""
            QLabel {{
                color: {NAVY};
                font-size: 11px;
                font-weight: 800;
            }}
            """
        )

        date_text = getattr(
            episode,
            "published_at",
            "قسمت جدید"
        )

        date_label = QLabel(
            date_text
        )

        date_label.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT_LIGHT};
                font-size: 9px;
            }}
            """
        )

        info.addWidget(
            badge,
            0,
            Qt.AlignLeft
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
            1
        )

        layout.addLayout(
            top_layout
        )

        # ---------------------------------------------
        # Description
        # ---------------------------------------------

        description_text = self.clean_html(
            getattr(
                episode,
                "description",
                ""
            )
        )

        if len(description_text) > 90:

            description_text = (
                description_text[:90]
                + "..."
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
                font-size: 9px;
                line-height: 1.3;
            }}
            """
        )

        layout.addWidget(
            description
        )

        # ---------------------------------------------
        # Bottom
        # ---------------------------------------------

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
            80
        )

        play.setStyleSheet(
            f"""
            QPushButton {{
                background: rgba(255,255,255,155);
                border: 1px solid rgba(255,255,255,180);
                border-radius: 12px;
                color: {BLUE};
                font-size: 10px;
                font-weight: 800;
                padding: 0 12px;
            }}

            QPushButton:hover {{
                background: rgba(9,199,217,42);
                border: 1px solid rgba(9,199,217,70);
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
    # Artwork
    # =====================================================

    def create_artwork_label(
        self,
        size,
        rounded=True
    ):

        label = QLabel()

        label.setFixedSize(
            size,
            size
        )

        label.setAlignment(
            Qt.AlignCenter
        )

        radius = 20 if rounded else 0

        label.setStyleSheet(
            f"""
            QLabel {{
                background: rgba(255,255,255,100);
                border: 1px solid rgba(255,255,255,145);
                border-radius: {radius}px;
                color: rgba(255,255,255,180);
                font-size: 28px;
            }}
            """
        )

        if not self.podcast_artwork:

            label.setText(
                "🎧"
            )

        return label

    # =====================================================
    # Simple pages
    # =====================================================

    def show_simple_page(
        self,
        page_name,
        icon,
        title_text,
        description_text
    ):

        page, page_layout = (
            self.page_widgets[page_name]
        )

        clear_layout(
            page_layout
        )

        content_layout = self.make_scroll_area(
            page_layout
        )

        # ---------------------------------------------
        # Header
        # ---------------------------------------------

        header = QLabel(
            f"{icon}   {title_text}"
        )

        header.setStyleSheet(
            f"""
            QLabel {{
                color: {NAVY};
                font-size: 27px;
                font-weight: 850;
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
                font-size: 12px;
                padding-bottom: 8px;
            }}
            """
        )

        content_layout.addWidget(
            description
        )

        # ---------------------------------------------
        # Placeholder glass card
        # ---------------------------------------------

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
            35
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
            "این بخش را در مرحله‌ی بعدی کامل می‌کنیم ✨"
        )

        message.setAlignment(
            Qt.AlignCenter
        )

        message.setStyleSheet(
            f"""
            QLabel {{
                color: {NAVY};
                font-size: 17px;
                font-weight: 800;
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
    # RSS
    # =====================================================

    def start_rss_loading(self):

        if self.rss_loading:
            return

        # اگر همه‌ی پادکست‌ها قبلاً دریافت شده‌اند،
        # دوباره کاری نکن.
        if (
            self.default_podcast_index
            >= len(self.default_podcasts)
        ):
            return

        self.rss_loading = True

        podcast_config = (
            self.default_podcasts[
                self.default_podcast_index
            ]
        )

        feed_url = podcast_config["feed_url"]

        print(
            "Loading podcast:",
            podcast_config["title"]
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
    # RSS finished
    # =====================================================
    @Slot(object, object)
    def on_rss_finished(
        self,
        podcast,
        artwork_data
    ):

        # ---------------------------------------------
        # ذخیره‌ی پادکست در Repository
        # ---------------------------------------------

        self.podcast_repository.add(
            podcast
        )

        print(
            "Podcast loaded:",
            podcast.title
        )

        # ---------------------------------------------
        # اولین پادکست به عنوان پادکست فعال
        # ---------------------------------------------

        if (
            self.podcast_repository.get_active()
            is None
        ):

            self.podcast_repository.set_active(
                podcast.feed_url
            )

            self.podcast = (
                self.podcast_repository.get_active()
            )

            self.podcast_artwork = artwork_data

    # ---------------------------------------------
    # پادکست فعلی دریافت شد
    # ---------------------------------------------

        self.default_podcast_index += 1

        self.rss_loading = False

    @Slot(str)
    def on_rss_error(
        self,
        message
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
    # RSS thread finished
    # =====================================================

    def rss_thread_finished(self):

        self.rss_thread = None
        self.rss_worker = None
        self.rss_loading = False

        # ---------------------------------------------
        # هنوز پادکست دیگری باقی مانده؟
        # ---------------------------------------------

        if (
            self.default_podcast_index
            < len(self.default_podcasts)
        ):

            self.start_rss_loading()

            return

        # ---------------------------------------------
        # تمام پادکست‌ها دریافت شدند
        # ---------------------------------------------

        self.podcast = (
            self.podcast_repository.get_active()
        )

        if self.podcast is None:

            self.show_rss_error(
                "هیچ پادکستی دریافت نشد."
            )

            return

        print(
            "All default podcasts loaded."
        )

        self.show_home()

        self.update_player_artwork()

    # =====================================================
    # RSS Error UI
    # =====================================================

    def show_rss_error(
        self,
        message
    ):

        page, page_layout = (
            self.page_widgets["home"]
        )

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
                font-weight: 850;
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
            30
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
            "دریافت پادکست انجام نشد"
        )

        error_title.setAlignment(
            Qt.AlignCenter
        )

        error_title.setStyleSheet(
            f"""
            QLabel {{
                color: {NAVY};
                font-size: 17px;
                font-weight: 800;
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
                font-size: 11px;
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
            130,
            40
        )

        retry.setStyleSheet(
            f"""
            QPushButton {{
                background: rgba(9,199,217,38);
                border: 1px solid rgba(9,199,217,75);
                border-radius: 13px;
                color: {BLUE};
                font-weight: 800;
            }}

            QPushButton:hover {{
                background: rgba(9,199,217,65);
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
            Qt.AlignCenter
        )

        content_layout.addWidget(
            card
        )

        content_layout.addStretch()

    # =====================================================
    # Audio URL
    # =====================================================

    # =====================================================
    # Play episode
    # =====================================================

    def play_episode(
        self,
        episode
    ):

        if episode is None:
            print(
                "Episode not found."
            )
            return

        url = getattr(
            episode,
            "audio_url",
            ""
        )

        title = getattr(
            episode,
            "title",
            "بدون عنوان"
        )

        if not url:
            print(
                "Audio URL not found."
            )
            return

        try:

            # ---------------------------------------------
            # PlaybackState از اینجا به بعد مرجع اصلی
            # اپیزود در حال پخش است.
            # ---------------------------------------------

            self.audio_manager.play(
                episode
            )

            # ---------------------------------------------
            # UI فقط وضعیت را نمایش می‌دهد
            # ---------------------------------------------

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
    # Toggle play pause
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
    # Change position
    # =====================================================

    def change_position(
        self,
        position
    ):

        self.audio_manager.seek(
            position
        )

    # =====================================================
    # Update position
    # =====================================================

    def update_position(
        self,
        position
    ):

        if not self.progress_slider.isSliderDown():

            self.progress_slider.setValue(
                position
            )

        # ---------------------------------------------
        # PlaybackState مرجع وضعیت فعلی پخش است
        # ---------------------------------------------

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
        duration
    ):

        playback_state = (
            self.audio_manager.playback_state
        )

        self.progress_slider.setRange(
            0,
            max(playback_state.duration, 0)
        )

        self.player_time.setText(
            f"{format_time(playback_state.position)} / "
            f"{format_time(playback_state.duration)}"
        )

    # =====================================================
    # Playback state
    # =====================================================

    def update_playback_state(
        self,
        state
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
    # Media status
    # =====================================================

    def update_media_status(
        self,
        status
    ):

        if status == QMediaPlayer.EndOfMedia:

            self.play_button.setText(
                "▶"
            )

            self.progress_slider.setValue(
                0
            )

    # =====================================================
    # Player error
    # =====================================================

    def handle_player_error(
        self,
        error_string
    ):

        # ---------------------------------------------
        # اصلاح‌شده: چون به AudioManager.error_occurred
        # وصل شدیم (نه مستقیم به player.errorOccurred)،
        # این سیگنال فقط یک پارامتر (پیام خطا) می‌فرسته
        # ---------------------------------------------

        print(
            "Player Error:",
            error_string
        )

    # =====================================================
    # Artwork player
    # =====================================================

    def update_player_artwork(self):

        if not self.podcast_artwork:
            return

        pixmap = QPixmap()

        pixmap.loadFromData(
            self.podcast_artwork
        )

        if pixmap.isNull():
            return

        self.player_artwork.setPixmap(
            pixmap.scaled(
                58,
                58,
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
        )

    # =====================================================
    # Clean HTML
    # =====================================================

    def clean_html(
        self,
        text
    ):

        if not text:
            return ""

        import re

        text = re.sub(
            r"<[^>]+>",
            "",
            text
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
    # Resize background
    # =====================================================

    def resizeEvent(self, event):

        super().resizeEvent(
            event
        )

        self.background.setGeometry(
            self.rect()
        )

        self.background.lower()

    # =====================================================
    # Close event
    # =====================================================

    def closeEvent(self, event):

        # ---------------------------------------------
        # اضافه‌شده: اگه ترد RSS هنوز در حال اجراست،
        # قبل از بستن پنجره درست متوقفش می‌کنیم تا
        # کرش یا هشدار "QThread: Destroyed while
        # thread is still running" نگیریم
        # ---------------------------------------------

        if self.rss_thread and self.rss_thread.isRunning():

            self.rss_thread.quit()

            self.rss_thread.wait(2000)

        self.audio_manager.stop()

        super().closeEvent(event)


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

    # -----------------------------------------------------
    # Font
    # -----------------------------------------------------

    font = QFont(
        "Segoe UI"
    )

    font.setStyleStrategy(
        QFont.PreferAntialias
    )

    app.setFont(
        font
    )

    # -----------------------------------------------------
    # Window
    # -----------------------------------------------------

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
