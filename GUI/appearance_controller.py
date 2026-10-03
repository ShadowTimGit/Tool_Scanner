from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import (
    QPainter,
    QPen,
    QColor,
)
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QCheckBox,
)


# ==================================================================
# Application Appearance
# ==================================================================

CONTROL_BG = (
    "#E7E9ED",
    "#111318",
)

PANEL_BG = (
    "#F3F4F6",
    "#181B21",
)

CARD_BG = (
    "#E9EBEF",
    "#20242C",
)

CARD_HOVER = (
    "#DDE1E7",
    "#292E38",
)

INPUT_BG = (
    "#F5F6F8",
    "#181B21",
)

BORDER_COLOR = (
    "#C7CBD2",
    "#2C313B",
)

TEXT_COLOR = (
    "#1F2937",
    "#F1F3F5",
)

INVERTED_TEXT = (
    "#F1F3F5",
    "#1F2937",
)

MUTED_TEXT = (
    "#667085",
    "#9AA1AC",
)

ACCENT_COLOR = (
    "#0D98BB",
    "#0D98BB",
)

ACCENT_HOVER = (
    "#334155",
    "#CBD5E1",
)

DANGER_COLOR = (
    "#EF4444",
    "#EF4444",
)

DANGER_HOVER = (
    "#B91C1C",
    "#B91C1C",
)

WHITE_TEXT = (
    "#FFFFFF",
    "#FFFFFF",
)

BLACK_TEXT = (
    "#000000",
    "#000000",
)


# ==================================================================
# Appearance Toggle
# ==================================================================

class AppearanceToggle(QCheckBox):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedSize(
            100,
            30,
        )

        self.setCursor(
            Qt.PointingHandCursor
        )

        self.setFocusPolicy(
            Qt.NoFocus
        )

        self.background = CONTROL_BG[1]
        self.border = BORDER_COLOR[1]
        self.text_color = TEXT_COLOR[1]

    # --------------------------------------------------------------
    # Colors
    # --------------------------------------------------------------

    def set_colors(
        self,
        background,
        border,
        text,
    ):
        self.background = background
        self.border = border
        self.text_color = text

        self.update()

    # --------------------------------------------------------------
    # Mouse
    # --------------------------------------------------------------

    def mousePressEvent(self, event):

        if event.button() == Qt.LeftButton:
            self.setChecked(
                not self.isChecked()
            )

            event.accept()
            return

        super().mousePressEvent(event)

    # --------------------------------------------------------------
    # Paint
    # --------------------------------------------------------------

    def paintEvent(self, event):

        painter = QPainter(self)

        if not painter.isActive():
            return

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        painter.setBrush(
            QColor(
                self.background
            )
        )

        painter.setPen(
            QPen(
                QColor(
                    self.border
                ),
                1,
            )
        )

        painter.drawRoundedRect(
            0,
            0,
            self.width() - 1,
            self.height() - 1,
            15,
            15,
        )

        painter.setPen(
            QColor(
                self.text_color
            )
        )

        font = painter.font()
        font.setPointSize(12)
        font.setBold(True)
        painter.setFont(font)

        mode = (
            "Light"
            if self.isChecked()
            else "Dark"
        )

        painter.drawText(
            self.rect(),
            Qt.AlignCenter,
            mode,
        )

        painter.end()


# ==================================================================
# Appearance Controller
# ==================================================================

class AppearanceController(QObject):

    mode_changed = Signal(str)

    def __init__(
        self,
        parent=None,
        on_changed=None,
    ):
        super().__init__(parent)

        self.parent = parent
        self.on_changed = on_changed

        self.mode = "Dark"

        self.create_gui()

    # --------------------------------------------------------------
    # Color
    # --------------------------------------------------------------

    @staticmethod
    def get_color(
        color,
        mode=None,
    ):
        if isinstance(color, tuple):

            if mode is None:
                mode = "Dark"

            return (
                color[0]
                if mode == "Light"
                else color[1]
            )

        return color

    # --------------------------------------------------------------
    # GUI
    # --------------------------------------------------------------

    def create_gui(self):

        self.frame = QWidget(
            self.parent
        )

        self.layout = QHBoxLayout(
            self.frame
        )

        self.layout.setContentsMargins(
            8,
            4,
            8,
            4,
        )

        self.layout.setSpacing(0)

        # ----------------------------------------------------------
        # Appearance Container
        # ----------------------------------------------------------

        self.container = QWidget(
            self.frame
        )

        self.container_layout = QHBoxLayout(
            self.container
        )

        self.container_layout.setContentsMargins(
            6,
            4,
            6,
            4,
        )

        self.container_layout.setSpacing(0)

        # ----------------------------------------------------------
        # Appearance Toggle
        # ----------------------------------------------------------

        self.switch = AppearanceToggle(
            self.container
        )

        self.switch.setChecked(
            False
        )

        self.switch.toggled.connect(
            self.toggle_mode
        )

        self.container_layout.addWidget(
            self.switch
        )

        # Add Appearance Container at the top
        self.layout.insertWidget(
            0,
            self.container
        )

    # --------------------------------------------------------------
    # Theme
    # --------------------------------------------------------------

    def refresh_theme(self):

        if self.mode == "Light":

            background = CONTROL_BG[0]
            border = BORDER_COLOR[0]
            text = TEXT_COLOR[0]

        else:

            background = CONTROL_BG[1]
            border = BORDER_COLOR[1]
            text = TEXT_COLOR[1]

        self.switch.set_colors(
            background,
            border,
            text,
        )

    # --------------------------------------------------------------
    # Mode
    # --------------------------------------------------------------

    def toggle_mode(
        self,
        checked,
    ):

        self.mode = (
            "Light"
            if checked
            else "Dark"
        )

        self.refresh_theme()

        self.mode_changed.emit(
            self.mode
        )

        if self.on_changed:
            self.on_changed(
                self.mode
            )

    # --------------------------------------------------------------
    # Set Mode
    # --------------------------------------------------------------

    def set_mode(
        self,
        mode,
        emit=True,
    ):

        mode = mode.capitalize()

        if mode not in (
            "Light",
            "Dark",
        ):
            mode = "Dark"

        self.mode = mode

        self.switch.blockSignals(
            True
        )

        self.switch.setChecked(
            mode == "Light"
        )

        self.switch.blockSignals(
            False
        )

        self.refresh_theme()

        if emit:

            self.mode_changed.emit(
                mode
            )

            if self.on_changed:

                self.on_changed(
                    mode
                )

    # --------------------------------------------------------------
    # Get Mode
    # --------------------------------------------------------------

    def get_mode(self):
        return self.mode