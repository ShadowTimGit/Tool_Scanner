from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QShortcut, QKeySequence
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QLabel,
    QPushButton,
    QCheckBox,
    QComboBox,
    QScrollArea,
    QHBoxLayout,
    QVBoxLayout,
    QSizePolicy,
    QStyle,
    QStyleOptionButton,
)

from PySide6.QtGui import QPainter, QPen

import cv2
import json
import os
from pathlib import Path

from GUI.gui_constants import (
    CROP_MODE_FULL,
    CROP_MODE_PREVIEW,
    TRIGGER_MANUAL,
    TRIGGER_AUTOMATIC,
    TRIGGER_CONTINUOUS,
)

from settings_menu.config import (
    SETTINGS_FILE,
    DEFAULT_VIDEO_SOURCE,
)

from GUI.appearance_controller import (
    CONTROL_BG,
    PANEL_BG,
    CARD_BG,
    CARD_HOVER,
    INPUT_BG,
    BORDER_COLOR,
    TEXT_COLOR,
    MUTED_TEXT,
    ACCENT_COLOR,
    ACCENT_HOVER,
    DANGER_COLOR,
    DANGER_HOVER,
    INVERTED_TEXT,
    WHITE_TEXT,
    BLACK_TEXT,
)


# ==================================================================
# Video Sources
# ==================================================================

def get_available_video_sources(max_sources=10):
    available = []

    for index in range(max_sources):
        cap = cv2.VideoCapture(index)

        if cap.isOpened():
            success, frame = cap.read()

            if success and frame is not None:
                available.append(index)

        cap.release()

    return available


class XCheckBox(QCheckBox):
    def paintEvent(self, event):
        super().paintEvent(event)

        if not self.isChecked():
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        option = QStyleOptionButton()
        self.initStyleOption(option)

        indicator_rect = self.style().subElementRect(
            QStyle.SE_CheckBoxIndicator,
            option,
            self,
        )

        pen = QPen(Qt.white, 2)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        padding = 4
        left = indicator_rect.left() + padding
        right = indicator_rect.right() - padding
        top = indicator_rect.top() + padding
        bottom = indicator_rect.bottom() - padding

        painter.drawLine(left, top, right, bottom)
        painter.drawLine(right, top, left, bottom)

        painter.end()

# ==================================================================
# Controls Mixin
# ==================================================================

class ControlsMixin:

    # ------------------------------------------------------------------
    # Appearance helper
    # ------------------------------------------------------------------

    def _get_color(self, color):
        """
        Resolve a light/dark color tuple.

        The main application should provide:

            self.appearance_mode

        with either "Light" or "Dark".
        """

        if isinstance(color, tuple):
            mode = getattr(
                self,
                "appearance_mode",
                "Dark",
            )

            if mode == "Light":
                return color[0]

            return color[1]

        return color

    # ------------------------------------------------------------------
    # Below webcam layout order
    # ------------------------------------------------------------------

    BELOW_WEBCAM_ORDER = {
        "control_frame": 30,
        "status_label": 10,
        "count_label": 20,
        "action_buttons_frame": 40,
    }

    def _add_below_webcam_widget(
        self,
        widget,
        order,
    ):
        layout = self.below_webcam_content_layout

        insert_at = layout.count()

        for index in range(layout.count()):
            item = layout.itemAt(index)
            existing_widget = item.widget()

            if existing_widget is None:
                continue

            existing_order = getattr(
                existing_widget,
                "_below_webcam_order",
                float("inf"),
            )

            if order < existing_order:
                insert_at = index
                break

        widget._below_webcam_order = order

        layout.insertWidget(
            insert_at,
            widget,
        )

    # ------------------------------------------------------------------
    # Font helper
    # ------------------------------------------------------------------

    def _font(
        self,
        size=12,
        weight=QFont.Normal,
    ):
        font = QFont()
        font.setPointSize(size)
        font.setWeight(weight)
        return font

    # ------------------------------------------------------------------
    # Below webcam container
    # ------------------------------------------------------------------

    def create_below_webcam_frame(self):
        self.below_webcam_container = QFrame(
            self.root
        )

        self.below_webcam_container.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.below_webcam_container.setStyleSheet(
            f"""
            QFrame {{
                background: {self._get_color(CONTROL_BG)};
                border-radius: 12px;
            }}
            """
        )

        # --------------------------------------------------------------
        # Main layout
        # --------------------------------------------------------------

        self.below_webcam_layout = QVBoxLayout(
            self.below_webcam_container
        )

        self.below_webcam_layout.setContentsMargins(
            4,
            4,
            4,
            4,
        )

        self.below_webcam_layout.setSpacing(5)

        # --------------------------------------------------------------
        # Add to main application layout
        # --------------------------------------------------------------

        # self.left_layout.addWidget(
        #     self.below_webcam_container,
        #     0,
        # )

        # --------------------------------------------------------------
        # Scroll area
        # --------------------------------------------------------------

        self.below_webcam_scroll = QScrollArea(
            self.below_webcam_container
        )

        self.below_webcam_scroll.setWidgetResizable(
            True
        )

        self.below_webcam_scroll.setFrameShape(
            QFrame.NoFrame
        )

        self.below_webcam_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.below_webcam_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        self.below_webcam_scroll.setStyleSheet(
            f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}

            QScrollBar:vertical {{
                background: transparent;
                width: 10px;
                margin: 4px 0px 4px 0px;
            }}

            QScrollBar::handle:vertical {{
                background: {self._get_color(BORDER_COLOR)};
                border-radius: 5px;
                min-height: 30px;
            }}

            QScrollBar::handle:vertical:hover {{
                background: {self._get_color(ACCENT_COLOR)};
            }}

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            """
        )

        # --------------------------------------------------------------
        # Scroll content
        # --------------------------------------------------------------

        self.below_webcam_frame = QWidget()

        self.below_webcam_frame.setStyleSheet(
            f"""
            QWidget {{
                background: {self._get_color(PANEL_BG)};
            }}
            """
        )

        self.below_webcam_content_layout = QVBoxLayout(
            self.below_webcam_frame
        )

        self.below_webcam_content_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.below_webcam_content_layout.setSpacing(5)

        self.below_webcam_scroll.setWidget(
            self.below_webcam_frame
        )

        self.below_webcam_layout.addWidget(
            self.below_webcam_scroll
        )

    # ------------------------------------------------------------------
    # Video source
    # ------------------------------------------------------------------

    def on_video_source_changed(
        self,
        index=None,
    ):
        if self.camera is None:
            return

        try:
            source = int(
                self.video_source_dropdown.currentText()
            )

        except ValueError:
            return

        self.camera.set_video_source(
            source
        )

    # ------------------------------------------------------------------
    # Main control frame
    # ------------------------------------------------------------------

    def create_control_frame(self):
        self.control_frame = QFrame(
            self.below_webcam_frame
        )

        self.control_frame.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

        self.control_frame.setStyleSheet(
            f"""
            QFrame {{
                background: {self._get_color(CARD_BG)};
                border: 1px solid {self._get_color(BORDER_COLOR)};
                border-radius: 10px;
            }}
            """
        )

        self._add_below_webcam_widget(
            self.control_frame,
            self.BELOW_WEBCAM_ORDER["control_frame"],
        )

        # --------------------------------------------------------------
        # Scroll area
        # --------------------------------------------------------------

        self.control_scroll = QScrollArea(
            self.control_frame
        )

        self.control_scroll.setWidgetResizable(
            True
        )

        self.control_scroll.setFrameShape(
            QFrame.NoFrame
        )

        self.control_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.control_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        self.control_scroll.setMinimumHeight(
            72
        )

        self.control_scroll.setStyleSheet(
            f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}

            QScrollBar:horizontal {{
                background: transparent;
                height: 10px;
                margin: 0px 8px 4px 8px;
            }}

            QScrollBar::handle:horizontal {{
                background: {self._get_color(BORDER_COLOR)};
                border-radius: 5px;
                min-width: 30px;
            }}

            QScrollBar::handle:horizontal:hover {{
                background: {self._get_color(ACCENT_COLOR)};
            }}

            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
            """
        )

        # --------------------------------------------------------------
        # Control content
        # --------------------------------------------------------------

        self.control_content = QWidget()

        self.control_content.setStyleSheet(
            f"""
            QWidget {{
                background: {self._get_color(CARD_BG)};
            }}
            """
        )

        self.control_layout = QHBoxLayout(
            self.control_content
        )

        self.control_layout.setContentsMargins(
            8,
            8,
            8,
            8,
        )

        self.control_layout.setSpacing(8)

        self.control_scroll.setWidget(
            self.control_content
        )

        control_outer_layout = QVBoxLayout(
            self.control_frame
        )

        control_outer_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        control_outer_layout.addWidget(
            self.control_scroll
        )

        # --------------------------------------------------------------
        # Require Red
        # --------------------------------------------------------------


        self.require_red_check = XCheckBox(
            "Require Red Scan"
        )

        self.require_red_check.setChecked(
            False
        )

        self.require_red_check.setFont(
            self._font(12)
        )

        self._style_checkbox(
            self.require_red_check
        )

        self.require_red_check.toggled.connect(
            self.on_require_red_changed
        )

        self.control_layout.addWidget(
            self.require_red_check
        )

        # --------------------------------------------------------------
        # Trigger mode label
        # --------------------------------------------------------------

        self.trigger_label = QLabel(
            "Mode:"
        )

        self.trigger_label.setFont(
            self._font(
                12,
                QFont.Bold,
            )
        )

        self._style_control_label(
            self.trigger_label
        )

        self.control_layout.addWidget(
            self.trigger_label
        )

        # --------------------------------------------------------------
        # Trigger mode
        # --------------------------------------------------------------

        self.trigger_mode_var = TRIGGER_MANUAL

        self.trigger_mode_dropdown = QComboBox()

        self.trigger_mode_dropdown.addItems(
            [
                TRIGGER_MANUAL,
                TRIGGER_AUTOMATIC,
                TRIGGER_CONTINUOUS,
            ]
        )

        self.trigger_mode_dropdown.setCurrentText(
            TRIGGER_MANUAL
        )

        self.trigger_mode_dropdown.setFixedSize(
            180,
            36,
        )

        self.trigger_mode_dropdown.setFont(
            self._font(12)
        )

        self._configure_control_dropdown(
            self.trigger_mode_dropdown
        )

        self.trigger_mode_dropdown.currentTextChanged.connect(
            self.on_trigger_mode_changed
        )

        self.control_layout.addWidget(
            self.trigger_mode_dropdown
        )

        # --------------------------------------------------------------
        # Camera label
        # --------------------------------------------------------------

        self.camera_label = QLabel(
            "Camera:"
        )

        self.camera_label.setFont(
            self._font(
                12,
                QFont.Bold,
            )
        )

        self._style_control_label(
            self.camera_label
        )

        self.control_layout.addWidget(
            self.camera_label
        )

        # --------------------------------------------------------------
        # Camera
        # --------------------------------------------------------------

        default_source = DEFAULT_VIDEO_SOURCE

        self.video_source_var = str(
            default_source
        )

        self.video_source_dropdown = QComboBox()

        self.video_source_dropdown.addItems(
            [
                "0",
                "1",
                "2",
                "3",
            ]
        )

        self.video_source_dropdown.setCurrentText(
            str(default_source)
        )

        self.video_source_dropdown.setFixedSize(
            80,
            36,
        )

        self.video_source_dropdown.setFont(
            self._font(12)
        )

        self._configure_control_dropdown(
            self.video_source_dropdown
        )

        self.video_source_dropdown.currentTextChanged.connect(
            self.on_video_source_changed
        )

        self.control_layout.addWidget(
            self.video_source_dropdown
        )

        # --------------------------------------------------------------
        # Manual capture key
        # --------------------------------------------------------------

        self.manual_capture_key = "space"

        if os.path.exists(SETTINGS_FILE):
            try:
                with open(
                    SETTINGS_FILE,
                    "r",
                    encoding="utf-8",
                ) as file:
                    settings = json.load(file)

                self.manual_capture_key = settings.get(
                    "manual_capture_key",
                    "space",
                )

            except (
                OSError,
                ValueError,
                TypeError,
                json.JSONDecodeError,
            ):
                pass

        # --------------------------------------------------------------
        # Manual trigger button
        # --------------------------------------------------------------

        self.manual_trigger_button = QPushButton(
            f"Capture [{self.manual_capture_key}]"
        )

        self.manual_trigger_button.setFixedSize(
            160,
            36,
        )

        self.manual_trigger_button.setFont(
            self._font(
                12,
                QFont.Bold,
            )
        )

        self._style_accent_button(
            self.manual_trigger_button
        )

        self.manual_trigger_button.clicked.connect(
            self.manual_trigger
        )

        self.control_layout.addWidget(
            self.manual_trigger_button
        )

        # --------------------------------------------------------------
        # Crop label
        # --------------------------------------------------------------

        self.crop_label = QLabel(
            "Crop:"
        )

        self.crop_label.setFont(
            self._font(
                12,
                QFont.Bold,
            )
        )

        self._style_control_label(
            self.crop_label
        )

        self.control_layout.addWidget(
            self.crop_label
        )

        # --------------------------------------------------------------
        # Crop mode
        # --------------------------------------------------------------

        self.crop_mode_var = CROP_MODE_FULL

        self.crop_mode_dropdown = QComboBox()

        self.crop_mode_dropdown.addItems(
            [
                CROP_MODE_FULL,
                CROP_MODE_PREVIEW,
            ]
        )

        self.crop_mode_dropdown.setCurrentText(
            CROP_MODE_FULL
        )

        self.crop_mode_dropdown.setFixedSize(
            240,
            36,
        )

        self.crop_mode_dropdown.setFont(
            self._font(12)
        )

        self._configure_control_dropdown(
            self.crop_mode_dropdown
        )

        self.crop_mode_dropdown.currentTextChanged.connect(
            self.on_crop_mode_changed
        )

        self.control_layout.addWidget(
            self.crop_mode_dropdown
        )

        self.control_layout.addStretch()

        self.update_manual_button_state()

        self.update_manual_capture_key(
            self.manual_capture_key
        )

    # ------------------------------------------------------------------
    # Label styling
    # ------------------------------------------------------------------

    def _style_control_label(
        self,
        label,
        size=None,
        list=False,
    ):
        label.setStyleSheet(
            f"""
            QLabel {{
                color: {self._get_color(TEXT_COLOR)};
                background: transparent;
                {"font-size: " + str(size) + "px;" if size else ""}
            }}
            """
        )

    # ------------------------------------------------------------------
    # Dropdown configuration
    # ------------------------------------------------------------------

    def _configure_control_dropdown(
        self,
        dropdown,
    ):

        base_dir = Path(__file__).resolve().parent

        arrow_icon = (
            base_dir
            / "icons"
            / "arrow.png"
        )

        dropdown.setStyleSheet(
            f"""
            QComboBox {{
                color: {self._get_color(TEXT_COLOR)};
                background: {self._get_color(INPUT_BG)};
                border: 1px solid {self._get_color(BORDER_COLOR)};
                border-radius: 8px;
                padding: 4px 10px;
            }}

            QComboBox:hover {{
                border: 1px solid {self._get_color(ACCENT_COLOR)};
            }}

            QComboBox:focus {{
                border: 1px solid {self._get_color(ACCENT_COLOR)};
            }}

            QComboBox::drop-down {{
                border: none;
                width: 28px;
            }}

            QComboBox::down-arrow {{
                width: 16px;
                height: 16px;
                image: url("{arrow_icon.as_posix()}");
                border: none;
            }}

            QComboBox QAbstractItemView {{
                color: {self._get_color(TEXT_COLOR)};
                background: {self._get_color(PANEL_BG)};
                border: 1px solid {self._get_color(BORDER_COLOR)};
                selection-background-color: {self._get_color(ACCENT_COLOR)};
                selection-color: {self._get_color(TEXT_COLOR)};
                padding: 4px;
            }}
            """
        )

    # ------------------------------------------------------------------
    # Button styling
    # ------------------------------------------------------------------

    def _style_accent_button(
        self,
        button,
    ):
        button.setStyleSheet(
            f"""
            QPushButton {{
                color: {self._get_color(WHITE_TEXT)};
                background: {self._get_color(ACCENT_COLOR)};
                border: none;
                border-radius: 8px;
                padding: 6px 12px;
            }}

            QPushButton:hover {{
                background: {self._get_color(ACCENT_HOVER)};
            }}

            QPushButton:pressed {{
                background: {self._get_color(ACCENT_HOVER)};
            }}

            QPushButton:disabled {{
                background: {self._get_color(BORDER_COLOR)};
                color: {self._get_color(MUTED_TEXT)};
            }}
            """
        )

    # ------------------------------------------------------------------
    # Theme refresh
    # ------------------------------------------------------------------

    def refresh_control_theme(self):
        """
        Reapply the current theme without recreating widgets.
        """

        # --------------------------------------------------------------
        # Below webcam container
        # --------------------------------------------------------------

        if hasattr(
            self,
            "below_webcam_container",
        ):
            self.below_webcam_container.setStyleSheet(
                f"""
                QFrame {{
                    background: {self._get_color(CONTROL_BG)};
                    border-radius: 12px;
                }}
                """
            )

        # --------------------------------------------------------------
        # Below webcam content
        # --------------------------------------------------------------

        if hasattr(
            self,
            "below_webcam_frame",
        ):
            self.below_webcam_frame.setStyleSheet(
                f"""
                QWidget {{
                    background: {self._get_color(PANEL_BG)};
                }}
                """
            )

        # --------------------------------------------------------------
        # Control labels
        # --------------------------------------------------------------

        for name in (
            "trigger_label",
            "camera_label",
            "crop_label",
        ):
            if hasattr(
                self,
                name,
            ):
                self._style_control_label(
                    getattr(self, name)
                )

        # --------------------------------------------------------------
        # Main control frame
        # --------------------------------------------------------------

        if hasattr(
            self,
            "control_frame",
        ):
            self.control_frame.setStyleSheet(
                f"""
                QFrame {{
                    background: {self._get_color(CARD_BG)};
                    border: 1px solid {self._get_color(BORDER_COLOR)};
                    border-radius: 10px;
                }}
                """
            )

        # --------------------------------------------------------------
        # Control content
        # --------------------------------------------------------------

        if hasattr(
            self,
            "control_content",
        ):
            self.control_content.setStyleSheet(
                f"""
                QWidget {{
                    background: {self._get_color(CARD_BG)};
                }}
                """
            )

        # --------------------------------------------------------------
        # Below webcam scroll
        # --------------------------------------------------------------

        if hasattr(
            self,
            "below_webcam_scroll",
        ):
            self.below_webcam_scroll.setStyleSheet(
                f"""
                QScrollArea {{
                    background: transparent;
                    border: none;
                }}

                QScrollBar:vertical {{
                    background: transparent;
                    width: 10px;
                    margin: 4px 0px 4px 0px;
                }}

                QScrollBar::handle:vertical {{
                    background: {self._get_color(BORDER_COLOR)};
                    border-radius: 5px;
                    min-height: 30px;
                }}

                QScrollBar::handle:vertical:hover {{
                    background: {self._get_color(ACCENT_COLOR)};
                }}

                QScrollBar::add-line:vertical,
                QScrollBar::sub-line:vertical {{
                    height: 0px;
                }}
                """
            )

        # --------------------------------------------------------------
        # Control scroll
        # --------------------------------------------------------------

        if hasattr(
            self,
            "control_scroll",
        ):
            self.control_scroll.setStyleSheet(
                f"""
                QScrollArea {{
                    background: transparent;
                    border: none;
                }}

                QScrollBar:horizontal {{
                    background: transparent;
                    height: 10px;
                    margin: 0px 8px 4px 8px;
                }}

                QScrollBar::handle:horizontal {{
                    background: {self._get_color(BORDER_COLOR)};
                    border-radius: 5px;
                    min-width: 30px;
                }}

                QScrollBar::handle:horizontal:hover {{
                    background: {self._get_color(ACCENT_COLOR)};
                }}

                QScrollBar::add-line:horizontal,
                QScrollBar::sub-line:horizontal {{
                    width: 0px;
                }}
                """
            )

        # --------------------------------------------------------------
        # Action buttons frame
        # --------------------------------------------------------------

        if hasattr(
            self,
            "action_buttons_frame",
        ):
            self.action_buttons_frame.setStyleSheet(
                f"""
                QFrame {{
                    background: {self._get_color(PANEL_BG)};
                }}
                """
            )

        # --------------------------------------------------------------
        # Checkboxes
        # --------------------------------------------------------------

        for name in (
            "require_red_check",
            "crop_box_check",
            "counting_box_check",
        ):
            if hasattr(
                self,
                name,
            ):
                self._style_checkbox(
                    getattr(self, name)
                )

        # --------------------------------------------------------------
        # Dropdowns
        # --------------------------------------------------------------

        for name in (
            "trigger_mode_dropdown",
            "video_source_dropdown",
            "crop_mode_dropdown",
        ):
            if hasattr(
                self,
                name,
            ):
                self._configure_control_dropdown(
                    getattr(self, name)
                )

        # --------------------------------------------------------------
        # Accent button
        # --------------------------------------------------------------

        if hasattr(
            self,
            "manual_trigger_button",
        ):
            self._style_accent_button(
                self.manual_trigger_button
            )

        # --------------------------------------------------------------
        # Settings button
        # --------------------------------------------------------------

        if hasattr(
            self,
            "settings_button",
        ):
            self._style_settings_button(
                self.settings_button
            )

        # --------------------------------------------------------------
        # Stop button
        # --------------------------------------------------------------

        if hasattr(
            self,
            "stop_button",
        ):
            self._style_stop_button(
                self.stop_button
            )

        # --------------------------------------------------------------
        # Status label
        # --------------------------------------------------------------

        if hasattr(
            self,
            "status_label",
        ):
            self.status_label.setStyleSheet(
                f"""
                QLabel {{
                    color: {self._get_color(MUTED_TEXT)};
                    background: transparent;
                }}
                """
            )

        # --------------------------------------------------------------
        # Count label
        # --------------------------------------------------------------

        if hasattr(
            self,
            "count_label",
        ):
            self.count_label.setStyleSheet(
                f"""
                QLabel {{
                    color: {self._get_color(TEXT_COLOR)};
                    background: transparent;
                }}
                """
            )

    # ------------------------------------------------------------------
    # Require red
    # ------------------------------------------------------------------

    def on_require_red_changed(
        self,
        checked,
    ):
        if self.camera is None:
            return

        self.camera.set_require_red_for_automatic(
            checked
        )

    # ------------------------------------------------------------------
    # Trigger mode
    # ------------------------------------------------------------------

    def on_trigger_mode_changed(
        self,
        mode,
    ):
        self.trigger_mode_var = mode

        if self.camera is None:
            return

        self.camera.set_trigger_mode(
            mode
        )

        self.update_manual_button_state()

    def update_manual_button_state(self):
        if not hasattr(
            self,
            "manual_trigger_button",
        ):
            return

        self.manual_trigger_button.setEnabled(
            True
        )

    # ------------------------------------------------------------------
    # Crop mode
    # ------------------------------------------------------------------

    def on_crop_mode_changed(
        self,
        mode,
    ):
        self.crop_mode_var = mode

        if self.camera is None:
            return

        self.camera.set_crop_mode(
            mode
        )

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def commit_metadata_entries(self):
        self.update_camera_metadata()

    # ------------------------------------------------------------------
    # Manual capture key
    # ------------------------------------------------------------------

    def update_manual_capture_key(
        self,
        key,
    ):
        self.manual_capture_key = key

        if hasattr(
            self,
            "_manual_shortcut",
        ):
            self._manual_shortcut.setEnabled(
                False
            )

            self._manual_shortcut.deleteLater()

            self._manual_shortcut = None

        if hasattr(
            self,
            "manual_trigger_button",
        ):
            self.manual_trigger_button.setText(
                f"Capture [{self.manual_capture_key}]"
            )

        qt_key = key

        if key.lower() == "space":
            qt_key = "Space"

        self._manual_shortcut = QShortcut(
            QKeySequence(qt_key),
            self.root,
        )

        self._manual_shortcut.activated.connect(
            self.on_manual_key
        )

    # ------------------------------------------------------------------
    # Manual capture
    # ------------------------------------------------------------------

    def manual_trigger(self):
        if self.camera is None:
            return

        self.camera.request_manual_capture()

    def on_manual_key(self):
        if self.trigger_mode_var == TRIGGER_MANUAL:
            self.manual_trigger()

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def create_status_display(self):
        self.status_label = QLabel(
            "Waiting for objects..."
        )

        self.status_label.setFont(
            self._font(14)
        )

        self.status_label.setAlignment(
            Qt.AlignLeft | Qt.AlignVCenter
        )

        self.status_label.setStyleSheet(
            f"""
            QLabel {{
                color: {self._get_color(MUTED_TEXT)};
                background: transparent;
            }}
            """
        )

        self._add_below_webcam_widget(
            self.status_label,
            self.BELOW_WEBCAM_ORDER["status_label"],
        )

    # ------------------------------------------------------------------
    # Count
    # ------------------------------------------------------------------

    def create_count_display(self):
        self.count_label = QLabel(
            "Crops: 0"
        )

        self.count_label.setFont(
            self._font(
                14,
                QFont.Bold,
            )
        )

        self.count_label.setAlignment(
            Qt.AlignLeft | Qt.AlignVCenter
        )

        self.count_label.setStyleSheet(
            f"""
            QLabel {{
                color: {self._get_color(TEXT_COLOR)};
                background: transparent;
            }}
            """
        )

        self._add_below_webcam_widget(
            self.count_label,
            self.BELOW_WEBCAM_ORDER["count_label"],
        )
    # ------------------------------------------------------------------
    # Box display controls
    # ------------------------------------------------------------------

    def create_box_display_controls(
        self,
        parent,
    ):
        self.crop_box_var = False

        self.crop_box_check = XCheckBox(
            "Preview Crop",
            parent,
        )

        self.crop_box_check.setChecked(
            False
        )

        self.crop_box_check.setFont(
            self._font(12)
        )

        self._style_checkbox(
            self.crop_box_check
        )

        self.crop_box_check.toggled.connect(
            self.update_box_display
        )

        parent.layout().addWidget(
            self.crop_box_check
        )

        self.counting_box_var = False

        self.counting_box_check = XCheckBox(
            "Counting Box",
            parent,
        )

        self.counting_box_check.setChecked(
            False
        )

        self.counting_box_check.setFont(
            self._font(12)
        )

        self._style_checkbox(
            self.counting_box_check
        )

        self.counting_box_check.toggled.connect(
            self.update_box_display
        )

        parent.layout().addWidget(
            self.counting_box_check
        )

    # ------------------------------------------------------------------
    # Checkbox styling
    # ------------------------------------------------------------------

    def _style_checkbox(
        self,
        checkbox,
    ):
        checkbox.setStyleSheet(
            f"""
            QCheckBox {{
                color: {self._get_color(TEXT_COLOR)};
                spacing: 6px;
            }}

            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid {self._get_color(ACCENT_COLOR)};
                background: {self._get_color(INPUT_BG)};
            }}

            QCheckBox::indicator:hover {{
                border: 1px solid {self._get_color(ACCENT_COLOR)};
            }}

            QCheckBox::indicator:checked {{
                background: {self._get_color(ACCENT_COLOR)};
                border: 1px solid {self._get_color(ACCENT_COLOR)};
                image: url(:/qt-project.org/styles/commonstyle/images/checkbox_checked.png);
            }}
            """
        )

    def update_box_display(self):
        self.show_crop_box = (
            self.crop_box_check.isChecked()
        )

        self.show_counting_box = (
            self.counting_box_check.isChecked()
        )

        self.crop_box_var = (
            self.show_crop_box
        )

        self.counting_box_var = (
            self.show_counting_box
        )

        if self.camera is not None:
            self.camera.set_box_display(
                self.show_crop_box,
                self.show_counting_box,
            )

    # ------------------------------------------------------------------
    # Action buttons
    # ------------------------------------------------------------------

    def create_action_buttons(self):
        self.action_buttons_frame = QFrame(
            self.below_webcam_frame
        )

        self.action_buttons_frame.setStyleSheet(
            f"""
            QFrame {{
                background: {self._get_color(PANEL_BG)};
            }}
            """
        )

        layout = QHBoxLayout(
            self.action_buttons_frame
        )

        layout.setContentsMargins(
            10,
            5,
            10,
            5,
        )

        layout.setSpacing(5)

        self.create_box_display_controls(
            self.action_buttons_frame
        )

        self.create_settings_button(
            self.action_buttons_frame
        )

        self.create_stop_button(
            self.action_buttons_frame
        )

        self._add_below_webcam_widget(
            self.action_buttons_frame,
            self.BELOW_WEBCAM_ORDER["action_buttons_frame"],
        )

    # ------------------------------------------------------------------
    # Settings button
    # ------------------------------------------------------------------

    def create_settings_button(
        self,
        parent,
    ):
        self.settings_button = QPushButton(
            "Settings",
            parent,
        )

        self.settings_button.setFixedSize(
            110,
            38,
        )

        self.settings_button.setFont(
            self._font(
                12,
                QFont.Bold,
            )
        )

        self._style_settings_button(
            self.settings_button
        )

        self.settings_button.clicked.connect(
            self.open_settings
        )

        parent.layout().addWidget(
            self.settings_button
        )

    def _style_settings_button(
        self,
        button,
    ):
        button.setStyleSheet(
            f"""
            QPushButton {{
                color: {self._get_color(WHITE_TEXT)};
                background: {self._get_color(ACCENT_COLOR)};
                border: none;
                border-radius: 8px;
                padding: 6px 12px;
            }}

            QPushButton:hover {{
                background: {self._get_color(ACCENT_HOVER)};
            }}

            QPushButton:pressed {{
                background: {self._get_color(ACCENT_HOVER)};
            }}

            QPushButton:disabled {{
                background: {self._get_color(BORDER_COLOR)};
                color: {self._get_color(MUTED_TEXT)};
            }}
            """
        )

    # ------------------------------------------------------------------
    # Stop button
    # ------------------------------------------------------------------

    def create_stop_button(
        self,
        parent,
    ):
        self.stop_button = QPushButton(
            "Stop",
            parent,
        )

        self.stop_button.setFixedSize(
            110,
            36,
        )

        self.stop_button.setFont(
            self._font(
                12,
                QFont.Bold,
            )
        )

        self._style_stop_button(
            self.stop_button
        )

        self.stop_button.clicked.connect(
            self.stop
        )

        parent.layout().addStretch()

        parent.layout().addWidget(
            self.stop_button
        )

    def _style_stop_button(
        self,
        button,
    ):
        button.setStyleSheet(
            f"""
            QPushButton {{
                color: {self._get_color(WHITE_TEXT)};
                background: {self._get_color(DANGER_COLOR)};
                border: none;
                border-radius: 8px;
                padding: 6px 12px;
            }}

            QPushButton:hover {{
                background: {self._get_color(DANGER_HOVER)};
            }}

            QPushButton:pressed {{
                background: {self._get_color(DANGER_HOVER)};
            }}
            """
        )