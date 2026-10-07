from PySide6.QtCore import (
    QObject,
    Signal,
    Qt,
    QPropertyAnimation,
    Property,
)
from PySide6.QtGui import (
    QPainter,
    QPen,
    QColor,
    QPixmap,
)
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QCheckBox,
)
from pathlib import Path


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


class AppearanceToggle(QCheckBox):

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)

        base_dir = Path(__file__).resolve().parent

        sun_icon = (
            base_dir
            / "icons"
            / "sun.png"
        )

        moon_icon = (
            base_dir
            / "icons"
            / "moon.png"
        )

        self.sun_icon = QPixmap(
            str(sun_icon)
        )

        self.moon_icon = QPixmap(
            str(moon_icon)
        )

        self.setFixedSize(
            72,
            36,
        )

        self.setCursor(
            Qt.PointingHandCursor
        )

        self.setFocusPolicy(
            Qt.NoFocus
        )

        self.background = CONTROL_BG[1]
        self.border = BORDER_COLOR[1]
        self.knob_color = "#FFFFFF"

        self._slider_position = 0.0

        self.animation = QPropertyAnimation(
            self,
            b"slider_position",
        )

        self.animation.setDuration(
            180
        )

        self.toggled.connect(
            self.animate_toggle
        )

    def get_slider_position(self):
        return self._slider_position

    def set_slider_position(
        self,
        position,
    ):
        self._slider_position = position
        self.update()

    slider_position = Property(
        float,
        get_slider_position,
        set_slider_position,
    )

    def set_colors(
        self,
        background,
        border,
        knob_color,
        text=None,
    ):
        self.background = background
        self.border = border
        self.knob_color = knob_color
        self.update()

    def mousePressEvent(
        self,
        event,
    ):
        if event.button() == Qt.LeftButton:
            self.setChecked(
                not self.isChecked()
            )
            event.accept()
            return

        super().mousePressEvent(
            event
        )

    def animate_toggle(
        self,
        checked,
    ):
        start = self._slider_position

        end = (
            1.0
            if checked
            else 0.0
        )

        self.animation.stop()

        self.animation.setStartValue(
            start
        )

        self.animation.setEndValue(
            end
        )

        self.animation.start()

    def set_slider_mode(
        self,
        light,
        animate=False,
    ):
        target = (
            1.0
            if light
            else 0.0
        )

        if not animate:
            self.animation.stop()
            self._slider_position = target
            self.update()
            return

        self.animation.stop()

        self.animation.setStartValue(
            self._slider_position
        )

        self.animation.setEndValue(
            target
        )

        self.animation.start()

    def paintEvent(
        self,
        event,
    ):
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
            self.height() / 2,
            self.height() / 2,
        )

        padding = 3

        knob_size = (
            self.height()
            - (
                padding * 2
            )
        )

        min_x = padding

        max_x = (
            self.width()
            - padding
            - knob_size
        )

        knob_x = (
            min_x
            + (
                max_x - min_x
            )
            * self._slider_position
        )

        knob_y = padding

        painter.setBrush(
            QColor(
                self.knob_color
            )
        )

        painter.setPen(
            Qt.NoPen
        )

        painter.drawEllipse(
            int(knob_x),
            knob_y,
            knob_size,
            knob_size,
        )

        icon = (
            self.sun_icon
            if self.isChecked()
            else self.moon_icon
        )

        if not icon.isNull():

            icon_padding = 7

            icon_rect = icon.scaled(
                knob_size - icon_padding,
                knob_size - icon_padding,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )

            icon_x = int(
                knob_x
                + (
                    knob_size
                    - icon_rect.width()
                ) / 2
            )

            icon_y = int(
                knob_y
                + (
                    knob_size
                    - icon_rect.height()
                ) / 2
            )

            painter.drawPixmap(
                icon_x,
                icon_y,
                icon_rect,
            )

        painter.end()


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
        self.refresh_theme()

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

        self.switch = AppearanceToggle(
            self.container
        )

        self.switch.setChecked(
            False
        )

        self.switch.set_slider_mode(
            light=False,
            animate=False,
        )

        self.switch.toggled.connect(
            self.toggle_mode
        )

        self.container_layout.addWidget(
            self.switch
        )

        self.layout.insertWidget(
            0,
            self.container
        )

    def refresh_theme(self):

        if self.mode == "Light":
            background = PANEL_BG[1]
            border = BORDER_COLOR[0]
            text = TEXT_COLOR[0]
            knob_color = PANEL_BG[0]

        else:
            background = CONTROL_BG[0]
            border = BORDER_COLOR[1]
            text = TEXT_COLOR[1]
            knob_color = PANEL_BG[1]

        self.switch.set_colors(
            background,
            border,
            knob_color,
            text,
        )

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

        self.switch.set_slider_mode(
            light=mode == "Light",
            animate=False,
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

    def get_mode(self):
        return self.mode