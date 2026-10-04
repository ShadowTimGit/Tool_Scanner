import os
import threading

from PIL import Image

from PySide6.QtCore import (
    Qt,
    Signal,
    QSize,
    QEvent,
)

from PySide6.QtGui import (
    QPixmap,
)
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QLabel,
    QPushButton,
    QRadioButton,
    QComboBox,
    QListView,
    QLineEdit,
    QTabWidget,
    QScrollArea,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QDialog,
    QSizePolicy,
    QApplication,
)

from GUI.gui_constants import (
    INVENTORY_PURCHASE,
    INVENTORY_SALE,
)

from GUI.gui_fraction_dropdown import FractionDropdown

from GUI.appearance_controller import (
    CONTROL_BG,
    PANEL_BG,
    CARD_BG,
    INPUT_BG,
    BORDER_COLOR,
    TEXT_COLOR,
    MUTED_TEXT,
    ACCENT_COLOR,
    ACCENT_HOVER,
    DANGER_COLOR,
    DANGER_HOVER,
    WHITE_TEXT,
    BLACK_TEXT,
    INVERTED_TEXT,
)

from tool_logger.workbook import (
    remove_row_from_workbook_by_path,
)
from pathlib import Path

class NoWheelListView(QListView):

    def wheelEvent(self, event):
        super().wheelEvent(event)


class NoWheelComboBox(QComboBox):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setView(
            NoWheelListView()
        )

    def wheelEvent(self, event):
        # Closed combo box:
        # allow the parent panel to receive the wheel.
        event.ignore()

    def showPopup(self):
        super().showPopup()

    def hidePopup(self):
        super().hidePopup()

    def eventFilter(
        self,
        watched,
        event,
    ):

        return super().eventFilter(
            watched,
            event,
        )

class RightPanelMixin:

    # =========================================================
    # Color Helpers
    # =========================================================

    def get_color(self, color):
        """
        Supports the existing:

            ("light_color", "dark_color")

        color format.
        """

        mode = getattr(
            self,
            "appearance_mode",
            "Dark",
        )

        if isinstance(color, tuple):

            if mode == "Light":
                return color[0]

            return color[1]

        return color

    # =========================================================
    # Generic Widget Styling
    # =========================================================

    def _style_frame(
        self,
        widget,
        background=CARD_BG,
        border=BORDER_COLOR,
        radius=8,
        border_width=1,
    ):

        widget.setStyleSheet(
            f"""
            QFrame {{
                background-color: {self.get_color(background)};
                border: {border_width}px solid {self.get_color(border)};
                border-radius: {radius}px;
            }}
            """
        )

    def _style_label(
        self,
        widget,
        color=TEXT_COLOR,
        size=12,
        bold=True,
    ):

        weight = "600" if bold else "400"

        widget.setStyleSheet(
            f"""
            QLabel {{
                color: {self.get_color(color)};
                font-size: {size}px;
                font-weight: {weight};
                background: transparent;
                border: none;
            }}
            """
        )

    def _style_button(
        self,
        widget,
        background=CARD_BG,
        hover=BORDER_COLOR,
        text_color=TEXT_COLOR,
        radius=6,
    ):

        widget.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self.get_color(background)};
                color: {self.get_color(text_color)};
                border: none;
                border-radius: {radius}px;
                padding: 6px 12px;
            }}

            QPushButton:hover {{
                background-color: {self.get_color(hover)};
            }}

            QPushButton:pressed {{
                background-color: {self.get_color(hover)};
            }}
            """
        )

    def _style_input(
        self,
        widget,
    ):

        base_dir = Path(__file__).resolve().parent

        arrow_icon = (
            base_dir
            / "icons"
            / "arrow.png"
        )

        widget.setStyleSheet(
            f"""
            QLineEdit,
            QComboBox {{
                background-color: {self.get_color(INPUT_BG)};
                color: {self.get_color(TEXT_COLOR)};
                border: 1px solid {self.get_color(BORDER_COLOR)};
                border-radius: 6px;
                padding: 6px 8px;
                selection-background-color: {self.get_color(ACCENT_COLOR)};
            }}

            QLineEdit:focus,
            QComboBox:focus {{
                border: 1px solid {self.get_color(ACCENT_COLOR)};
            }}

            QComboBox::drop-down {{
                background-color: {self.get_color(INPUT_BG)};
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
                background-color: {self.get_color(PANEL_BG)};
                color: {self.get_color(TEXT_COLOR)};
                border: 1px solid {self.get_color(BORDER_COLOR)};
                selection-background-color: {self.get_color(ACCENT_COLOR)};
                selection-color: {self.get_color(WHITE_TEXT)};
            }}

            QComboBox QAbstractItemView QScrollBar:vertical {{
                background: {self.get_color(PANEL_BG)};
                width: 10px;
                margin: 0px;
                border: none;
            }}

            QComboBox QAbstractItemView QScrollBar::handle:vertical {{
                background: #183A66;
                border: none;
                border-radius: 5px;
                min-height: 30px;
            }}

            QComboBox QAbstractItemView QScrollBar::handle:vertical:hover {{
                background: #24558F;
            }}

            QComboBox QAbstractItemView QScrollBar::add-line:vertical,
            QComboBox QAbstractItemView QScrollBar::sub-line:vertical {{
                height: 0px;
                border: none;
                background: transparent;
            }}

            QComboBox QAbstractItemView QScrollBar::add-page:vertical,
            QComboBox QAbstractItemView QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
            """
        )

    # =========================================================
    # Main Right Panel
    # =========================================================
    def create_right_panel(self):

        self.right_panel = QFrame(
            self.root
        )

        self.right_panel.setFixedWidth(320)

        self._style_frame(
            self.right_panel,
            PANEL_BG,
            BORDER_COLOR,
            radius=10,
        )

        self.panel_content_layout = QVBoxLayout(
            self.right_panel
        )

        self.panel_content_layout.setContentsMargins(
            8,
            8,
            8,
            8,
        )

        self.panel_content_layout.setSpacing(0)

        # ---------------------------------------------------------
        # Notebook replacement
        # ---------------------------------------------------------

        self.right_panel_notebook = QTabWidget(
            self.right_panel
        )

        self.right_panel_notebook.setDocumentMode(
            True
        )

        self.right_panel_notebook.setStyleSheet(
            f"""
            QTabWidget {{
                background-color: {self.get_color(PANEL_BG)};
                color: {self.get_color(TEXT_COLOR)};
                border: none;
            }}

            QTabWidget::pane {{
                background-color: {self.get_color(PANEL_BG)};
                color: {self.get_color(TEXT_COLOR)};
                border: none;
            }}

            QTabBar {{
                background-color: {self.get_color(PANEL_BG)};
            }}

            QTabBar::scroller {{
                background-color: {self.get_color(PANEL_BG)};
            }}

            QTabWidget::left-corner,
            QTabWidget::right-corner {{
                background-color: {self.get_color(PANEL_BG)};
            }}

            QTabBar::tab {{
                background-color: {self.get_color(CARD_BG)};
                color: {self.get_color(TEXT_COLOR)};
                border: none;
                padding: 8px 14px;
                margin-right: 2px;
                border-radius: 6px;
            }}

            QTabBar::tab:selected {{
                background-color: {self.get_color(ACCENT_COLOR)};
                color: {self.get_color(BLACK_TEXT)};
            }}

            QTabBar::tab:hover {{
                background-color: {self.get_color(ACCENT_HOVER)};
                color: {self.get_color(INVERTED_TEXT)};
            }}
            """
        )

        self.panel_content_layout.addWidget(
            self.right_panel_notebook,
            1,
        )

        self.selection_tab = QWidget()

        self.recent_crops_tab = QWidget()

        self.right_panel_notebook.addTab(
            self.selection_tab,
            "Selection",
        )

        self.right_panel_notebook.addTab(
            self.recent_crops_tab,
            "Recent Crops",
        )

        # ---------------------------------------------------------
        # Selection scrollable frame
        # ---------------------------------------------------------

        self.right_panel_content = QScrollArea(
            self.selection_tab
        )

        self.right_panel_content.setWidgetResizable(
            True
        )

        self.right_panel_content.setFrameShape(
            QFrame.NoFrame
        )

        self.right_panel_content.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self._refresh_scroll_area_theme(
            self.right_panel_content
        )

        self.right_panel_content_widget = QWidget()

        self.right_panel_content_layout = QVBoxLayout(
            self.right_panel_content_widget
        )

        self.right_panel_content_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.right_panel_content_layout.setSpacing(
            4
        )

        self.right_panel_content_layout.addStretch()

        self.right_panel_content.setWidget(
            self.right_panel_content_widget
        )

        selection_layout = QVBoxLayout(
            self.selection_tab
        )

        selection_layout.setContentsMargins(
            0,
            8,
            0,
            0,
        )

        selection_layout.addWidget(
            self.right_panel_content
        )

        # ---------------------------------------------------------
        # Existing controls
        # ---------------------------------------------------------

        self.create_inventory_selection(
            self.right_panel_content_widget
        )

        self.create_tool_selection(
            self.right_panel_content_widget
        )

        self.create_metadata_selection(
            self.right_panel_content_widget
        )

        self.install_panel_wheel_filter()

        # ---------------------------------------------------------
        # Recent crops
        # ---------------------------------------------------------

        self.create_recent_crops_tab(
            self.recent_crops_tab
        )

        self.refresh_recent_crops()

        self._recent_crop_timer = self.root.startTimer(
            2000
        )

        self.right_panel_layout.addWidget(
            self.right_panel,
            1,
        )

    # =========================================================
    # Panel Wheel Scrolling
    # =========================================================

    def eventFilter(
        self,
        watched,
        event,
    ):

        if event.type() == QEvent.Wheel:

            scroll_area = getattr(
                self,
                "right_panel_content",
                None,
            )

            content = getattr(
                self,
                "right_panel_content_widget",
                None,
            )

            if (
                scroll_area is not None
                and content is not None
                and (
                    watched is content
                    or content.isAncestorOf(watched)
                )
            ):

                scrollbar = (
                    scroll_area.verticalScrollBar()
                )

                delta = event.pixelDelta().y()

                if delta == 0:
                    delta = event.angleDelta().y()

                    if delta != 0:
                        delta = int(delta * 0.8)

                if delta != 0:
                    scrollbar.setValue(
                        scrollbar.value() - delta
                    )

                    event.accept()

                    return True

        return super().eventFilter(
            watched,
            event,
        )
    
    def install_panel_wheel_filter(self):

        content = getattr(
            self,
            "right_panel_content_widget",
            None,
        )

        if content is None:
            return

        content.installEventFilter(self)

        for child in content.findChildren(QWidget):
            child.installEventFilter(self)


    # =========================================================
    # Timer
    # =========================================================

    def timerEvent(self, event):

        if getattr(
            event,
            "timerId",
            lambda: None,
        )() == getattr(
            self,
            "_recent_crop_timer",
            None,
        ):

            if getattr(
                self,
                "running",
                False,
            ):

                self.refresh_recent_crops()

    # =========================================================
    # Recent Crops Tab
    # =========================================================

    def create_recent_crops_tab(self, parent):
        layout = QVBoxLayout(parent)

        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title = QLabel("Recently Cropped Items")
        self._style_label(
            title,
            self.get_color(TEXT_COLOR),
            size=14,
            bold=True,
        )
        layout.addWidget(title)

        refresh_button = QPushButton("Refresh")
        refresh_button.setFixedHeight(34)
        self._style_button(refresh_button)
        refresh_button.clicked.connect(self.refresh_recent_crops)
        layout.addWidget(refresh_button)

        self.recent_crops_list = QScrollArea(parent)
        self.recent_crops_list.setWidgetResizable(True)
        self.recent_crops_list.setFrameShape(QFrame.NoFrame)
        self.recent_crops_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        self.recent_crops_list.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self._refresh_scroll_area_theme(
            self.recent_crops_list
        )

        self.recent_crops_list_widget = QWidget()
        self.recent_crops_list_widget.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred,
        )

        self.recent_crops_list_layout = QVBoxLayout(
            self.recent_crops_list_widget
        )
        self.recent_crops_list_layout.setContentsMargins(
            0, 0, 0, 0
        )
        self.recent_crops_list_layout.setSpacing(6)
        self.recent_crops_list_layout.addStretch()

        self.recent_crops_list.setWidget(
            self.recent_crops_list_widget
        )

        # This is the important part:
        # the scroll area gets all remaining space in the tab.
        layout.addWidget(
            self.recent_crops_list,
            1,
        )

    # =========================================================
    # Recent Crop List
    # =========================================================

    def refresh_recent_crops(self):

        if not hasattr(
            self,
            "recent_crops_list_layout",
        ):
            return

        entries = self.get_recent_crop_entries()

        signature = tuple(
            (
                entry.get("image_path"),
                entry.get("json_path"),
                entry.get("display_name"),
                entry.get("tool_name"),
            )
            for entry in entries
        )

        if getattr(
            self,
            "_recent_crop_signature",
            None,
        ) == signature:

            return

        self._recent_crop_signature = signature

        # ---------------------------------------------------------
        # Remove existing widgets
        # ---------------------------------------------------------

        while (
            self.recent_crops_list_layout.count()
            > 0
        ):

            item = (
                self.recent_crops_list_layout.takeAt(
                    0
                )
            )

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        # ---------------------------------------------------------
        # Empty state
        # ---------------------------------------------------------

        if not entries:

            empty_label = QLabel(
                "No recent cropped images found."
            )

            empty_label.setWordWrap(
                True
            )

            self._style_label(
                empty_label,
                MUTED_TEXT,
                size=10,
                bold=False,
            )

            self.recent_crops_list_layout.addWidget(
                empty_label
            )

            self.recent_crops_list_layout.addStretch()

            return

        # ---------------------------------------------------------
        # Entries
        # ---------------------------------------------------------

        for entry in entries:

            row = QFrame()

            row.setMinimumHeight(
                120
            )

            row.setSizePolicy(
                row.sizePolicy().horizontalPolicy(),
                row.sizePolicy().verticalPolicy(),
            )

            self._style_frame(
                row,
                CARD_BG,
                BORDER_COLOR,
                radius=8,
            )

            row_layout = QVBoxLayout(
                row
            )

            row_layout.setContentsMargins(
                8,
                8,
                8,
                8,
            )

            row_layout.setSpacing(
                5
            )

            body = QWidget()

            body_layout = QHBoxLayout(
                body
            )

            body_layout.setContentsMargins(
                0,
                0,
                0,
                0,
            )

            body_layout.setSpacing(
                8
            )

            image_path = entry.get(
                "image_path"
            )

            thumbnail = self.load_thumbnail(
                image_path
            )

            image_label = QLabel()

            image_label.setPixmap(
                thumbnail
            )

            image_label.setFixedSize(
                80,
                80,
            )

            image_label.setAlignment(
                Qt.AlignCenter
            )

            image_label.setCursor(
                Qt.PointingHandCursor
            )

            image_label.mousePressEvent = (
                lambda event,
                item=entry:
                self.open_recent_crop_image(
                    item
                )
            )

            body_layout.addWidget(
                image_label
            )

            info_text = (
                f"{entry.get('display_name', os.path.basename(image_path or ''))}\n"
                f"{entry.get('tool_name', 'Unknown')}\n"
                f"{os.path.basename(entry.get('json_path', ''))}"
            )

            info = QLabel(
                info_text
            )

            info.setWordWrap(
                True
            )

            info.setAlignment(
                Qt.AlignLeft |
                Qt.AlignVCenter
            )

            self._style_label(
                info,
                TEXT_COLOR,
                size=10,
                bold=False,
            )

            body_layout.addWidget(
                info,
                1,
            )

            row_layout.addWidget(
                body
            )

            remove_button = QPushButton(
                "Remove JSON"
            )

            remove_button.setFixedHeight(
                30
            )

            self._style_button(
                remove_button,
                background=DANGER_COLOR,
                hover=DANGER_HOVER,
                text_color=WHITE_TEXT,
                radius=5,
            )

            remove_button.clicked.connect(
                lambda checked=False,
                item=entry:
                self.remove_recent_crop(
                    item
                )
            )

            row_layout.addWidget(
                remove_button
            )

            self.recent_crops_list_layout.addWidget(
                row
            )

        self.recent_crops_list_layout.addStretch()

    # =========================================================
    # Recent Crop Data
    # =========================================================

    def get_recent_crop_entries(self):

        if self.camera is None:
            return []

        session_entries = getattr(
            self.camera,
            "recent_session_crops",
            [],
        )

        entries = []

        for entry in session_entries:

            json_path = entry.get(
                "json_path"
            )

            image_path = entry.get(
                "image_path"
            )

            if not json_path and not image_path:
                continue

            if (
                image_path
                and os.path.exists(image_path)
            ):
                entries.append(
                    entry
                )

                continue

            if (
                json_path
                and os.path.exists(json_path)
            ):
                entries.append(
                    entry
                )

        return entries[:25]

    # =========================================================
    # Thumbnail
    # =========================================================

    def load_thumbnail(
        self,
        image_path,
    ):

        if (
            not image_path
            or not os.path.exists(image_path)
        ):

            image = Image.new(
                "RGB",
                (80, 80),
                color="#808080",
            )

        else:

            try:

                image = Image.open(
                    image_path
                )

                image = image.convert(
                    "RGB"
                )

                image.thumbnail(
                    (
                        80,
                        80,
                    ),
                    Image.Resampling.LANCZOS,
                )

            except Exception:

                image = Image.new(
                    "RGB",
                    (80, 80),
                    color="#DC2626",
                )

        image = image.convert(
            "RGBA"
        )

        image_data = image.tobytes(
            "raw",
            "RGBA",
        )

        from PySide6.QtGui import QImage

        qimage = QImage(
            image_data,
            image.width,
            image.height,
            image.width * 4,
            QImage.Format_RGBA8888,
        )

        return QPixmap.fromImage(
            qimage.copy()
        )

    # =========================================================
    # Preview Windows
    # =========================================================

    def _close_recent_crop_preview(
        self,
        preview,
    ):

        if hasattr(
            self,
            "_recent_crop_previews",
        ):

            self._recent_crop_previews.discard(
                preview
            )

        try:
            preview.close()
        except Exception:
            pass

    def close_recent_crop_previews(
        self,
    ):

        previews = getattr(
            self,
            "_recent_crop_previews",
            set(),
        )

        for preview in list(
            previews
        ):

            try:
                preview.close()
            except Exception:
                pass

        previews.clear()

    def open_recent_crop_image(
        self,
        entry,
    ):

        image_path = entry.get(
            "image_path"
        )

        if (
            not image_path
            or not os.path.exists(image_path)
        ):
            return

        if not hasattr(
            self,
            "_recent_crop_previews",
        ):

            self._recent_crop_previews = set()

        preview = QDialog(
            self.root
        )

        self._recent_crop_previews.add(
            preview
        )

        preview.setWindowTitle(
            f"Recent Crop - "
            f"{os.path.basename(image_path)}"
        )

        preview.resize(
            900,
            700,
        )

        preview.setStyleSheet(
            f"""
            QDialog {{
                background-color: {self.get_color(CONTROL_BG)};
            }}
            """
        )

        preview_layout = QVBoxLayout(
            preview
        )

        preview_layout.setContentsMargins(
            10,
            6,
            10,
            6,
        )

        try:

            image = Image.open(
                image_path
            )

            image = image.convert(
                "RGB"
            )

            image_width, image_height = (
                image.size
            )

            max_width = 850
            max_height = 600

            if (
                image_width > max_width
                or image_height > max_height
            ):

                scale = min(
                    max_width / image_width,
                    max_height / image_height,
                )

                image = image.resize(
                    (
                        max(
                            1,
                            int(
                                image_width * scale
                            ),
                        ),
                        max(
                            1,
                            int(
                                image_height * scale
                            ),
                        ),
                    ),
                    Image.Resampling.LANCZOS,
                )

            pixmap = self._pil_to_pixmap(
                image
            )

            label = QLabel()

            label.setPixmap(
                pixmap
            )

            label.setAlignment(
                Qt.AlignCenter
            )

            label.setSizePolicy(
                label.sizePolicy().horizontalPolicy(),
                label.sizePolicy().verticalPolicy(),
            )

            preview_layout.addWidget(
                label,
                1,
            )

            close_button = QPushButton(
                "Close"
            )

            close_button.setFixedSize(
                120,
                36,
            )

            self._style_button(
                close_button,
                background=ACCENT_COLOR,
                hover=ACCENT_HOVER,
                text_color=WHITE_TEXT,
            )

            close_button.clicked.connect(
                lambda:
                self._close_recent_crop_preview(
                    preview
                )
            )

            preview_layout.addWidget(
                close_button,
                0,
                Qt.AlignHCenter,
            )

        except Exception:

            error_label = QLabel(
                "Unable to load preview "
                "for this image."
            )

            self._style_label(
                error_label,
                MUTED_TEXT,
                size=11,
                bold=False,
            )

            error_label.setAlignment(
                Qt.AlignCenter
            )

            preview_layout.addWidget(
                error_label,
                1,
            )

        preview.finished.connect(
            lambda:
            self._recent_crop_previews.discard(
                preview
            )
        )

        preview.show()

    # =========================================================
    # PIL -> QPixmap
    # =========================================================

    @staticmethod
    def _pil_to_pixmap(
        image,
    ):

        from PySide6.QtGui import QImage

        image = image.convert(
            "RGBA"
        )

        data = image.tobytes(
            "raw",
            "RGBA",
        )

        qimage = QImage(
            data,
            image.width,
            image.height,
            image.width * 4,
            QImage.Format_RGBA8888,
        )

        return QPixmap.fromImage(
            qimage.copy()
        )

    # =========================================================
    # Remove Recent Crop
    # =========================================================

    def remove_recent_crop(
        self,
        entry,
    ):

        json_path = entry.get(
            "json_path"
        )

        image_path = entry.get(
            "image_path"
        )

        if not json_path and not image_path:
            return

        result = QMessageBox.question(
            self.root,
            "Remove crop entry",
            (
                "This will remove the selected crop "
                "image and JSON.\n"
                "The spreadsheet will be rebuilt afterward.\n\n"
                f"{os.path.basename(json_path or image_path or '')}"
            ),
            QMessageBox.Yes |
            QMessageBox.No,
            QMessageBox.No,
        )

        if result != QMessageBox.Yes:
            return

        # ---------------------------------------------------------
        # Remove files immediately
        # ---------------------------------------------------------

        for path in (
            json_path,
            image_path,
        ):

            if (
                path
                and os.path.exists(path)
            ):

                try:
                    os.remove(path)

                except OSError:
                    pass

        # ---------------------------------------------------------
        # Update in-memory list
        # ---------------------------------------------------------

        if self.camera is not None:

            recent = getattr(
                self.camera,
                "recent_session_crops",
                [],
            )

            self.camera.recent_session_crops = [
                item
                for item in recent
                if item.get("json_path") != json_path
                and item.get("image_path") != image_path
            ]

        self._recent_crop_signature = None

        self.refresh_recent_crops()

        # ---------------------------------------------------------
        # Rebuild workbook in background
        # ---------------------------------------------------------

        def rebuild_workbook():

            try:

                remove_row_from_workbook_by_path(
                    json_path=json_path,
                    image_path=image_path,
                )

            except Exception as error:

                print(
                    "ERROR: Could not remove crop "
                    f"row from workbook: {error}"
                )

            finally:

                self.root.post_to_gui(
                    self._finish_remove_recent_crop
                )

        threading.Thread(
            target=rebuild_workbook,
            daemon=True,
        ).start()

    def _finish_remove_recent_crop(
        self,
    ):

        self._recent_crop_signature = None

        self.refresh_recent_crops()

    # =========================================================
    # Inventory Selection
    # =========================================================

    def create_inventory_selection(
        self,
        parent,
    ):

        frame = QFrame(
            parent
        )

        self._style_frame(
            frame,
            CARD_BG,
            BORDER_COLOR,
            radius=8,
        )

        layout = QVBoxLayout(
            frame
        )

        layout.setContentsMargins(
            10,
            8,
            10,
            8,
        )

        layout.setSpacing(
            4
        )

        title = QLabel(
            "Inventory"
        )

        self._style_label(
            title,
            TEXT_COLOR,
            size=12,
            bold=True,
        )

        layout.addWidget(
            title
        )

        # ---------------------------------------------------------
        # Initialize inventory selection before creating radios
        # ---------------------------------------------------------

        if not isinstance(
            getattr(
                self,
                "inventory_type_var",
                None,
            ),
            str,
        ) or self.inventory_type_var not in (
            INVENTORY_PURCHASE,
            INVENTORY_SALE,
        ):
            self.inventory_type_var = INVENTORY_PURCHASE

        # ---------------------------------------------------------
        # Purchase
        # ---------------------------------------------------------

        self.inventory_purchase_radio = QRadioButton(
            "Purchase / Incoming"
        )

        self.inventory_purchase_radio.setChecked(
            self.inventory_type_var == INVENTORY_PURCHASE
        )

        self._style_radio_button(
            self.inventory_purchase_radio
        )

        self.inventory_purchase_radio.toggled.connect(
            lambda checked:
            self.on_inventory_type_changed()
            if checked
            else None
        )

        layout.addWidget(
            self.inventory_purchase_radio
        )

        # ---------------------------------------------------------
        # Sale
        # ---------------------------------------------------------

        self.inventory_sale_radio = QRadioButton(
            "Sale / Outgoing"
        )

        self.inventory_sale_radio.setChecked(
            self.inventory_type_var == INVENTORY_SALE
        )

        self._style_radio_button(
            self.inventory_sale_radio
        )

        self.inventory_sale_radio.toggled.connect(
            lambda checked:
            self.on_inventory_type_changed()
            if checked
            else None
        )

        layout.addWidget(
            self.inventory_sale_radio
        )

        self._add_right_panel_widget(
            parent,
            frame,
        )

    # =========================================================
    # Radio Button Style
    # =========================================================

    def _style_radio_button(
        self,
        widget,
    ):

        widget.setStyleSheet(
            f"""
            QRadioButton {{
                color: {self.get_color(TEXT_COLOR)};
                background: {self.get_color(CARD_BG)};
                spacing: 8px;
            }}

            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 8px;
                border: 1px solid {self.get_color(BORDER_COLOR)};
                background: {self.get_color(PANEL_BG)};
            }}

            QRadioButton::indicator:checked {{
                background: {self.get_color(ACCENT_COLOR)};
                border: 1px solid {self.get_color(ACCENT_COLOR)};
            }}
            """
        )

    # =========================================================
    # Tool Selection
    # =========================================================

    def create_tool_selection(
        self,
        parent,
    ):

        frame = QFrame(
            parent
        )

        self._style_frame(
            frame,
            CARD_BG,
            BORDER_COLOR,
            radius=8,
        )

        layout = QVBoxLayout(
            frame
        )

        layout.setContentsMargins(
            10,
            8,
            10,
            8,
        )

        layout.setSpacing(
            4
        )

        self._tool_selection_layout = layout

        self.create_tool_dropdown(
            frame
        )

        self.create_size_dropdown(
            frame
        )

        self.create_size_2_dropdown(
            frame
        )

        self.create_brand_dropdown(
            frame
        )

        self._add_right_panel_widget(
            parent,
            frame,
        )

    # =========================================================
    # Tool Dropdown
    # =========================================================

    def create_tool_dropdown(
        self,
        parent,
    ):

        layout = parent.layout()

        label = QLabel(
            "Tool"
        )

        self._style_label(
            label,
            TEXT_COLOR,
            size=12,
            bold=True,
        )

        layout.addWidget(
            label
        )

        self.tool_var = ""

        self.tool_dropdown = NoWheelComboBox()

        self.tool_dropdown.setEditable(
            False
        )


        self.tool_dropdown.setFixedHeight(
            34
        )

        self._style_input(
            self.tool_dropdown
        )

        layout.addWidget(
            self.tool_dropdown
        )

        self.tool_dropdown.currentTextChanged.connect(
            self.on_tool_selected
        )

    # =========================================================
    # Size Dropdown
    # =========================================================

    def create_size_dropdown(
        self,
        parent,
    ):

        layout = parent.layout()

        label = QLabel(
            "Size-1"
        )

        self._style_label(
            label,
            TEXT_COLOR,
            size=12,
            bold=True,
        )

        layout.addWidget(
            label
        )

        self.size_var = ""

        self.size_dropdown = FractionDropdown(
            parent,
            command=self.on_size_selected,
            dual_measurement="SAE",
            appearance_mode=getattr(
                self,
                "appearance_mode",
                "Dark",
            ),
        )

        layout.addWidget(
            self.size_dropdown
        )

    # =========================================================
    # Size 2 Dropdown
    # =========================================================

    def create_size_2_dropdown(
        self,
        parent,
    ):

        layout = parent.layout()

        label = QLabel(
            "Size-2"
        )

        self._style_label(
            label,
            TEXT_COLOR,
            size=12,
            bold=True,
        )

        layout.addWidget(
            label
        )

        self.size_2_var = ""

        self.size_2_dropdown = FractionDropdown(
            parent,
            command=self.on_size_selected,
            dual_measurement="Metric",
            appearance_mode=getattr(
                self,
                "appearance_mode",
                "Dark",
            ),
        )
        
        layout.addWidget(
            self.size_2_dropdown
        )

    # =========================================================
    # Brand Dropdown
    # =========================================================

    def create_brand_dropdown(
        self,
        parent,
    ):

        layout = parent.layout()

        label = QLabel(
            "Brand"
        )

        self._style_label(
            label,
            TEXT_COLOR,
            size=12,
            bold=True,
        )

        layout.addWidget(
            label
        )

        self.brand_var = ""

        self.brand_dropdown = NoWheelComboBox()

        self.brand_dropdown.setEditable(
            False
        )



        self.brand_dropdown.setFixedHeight(
            34
        )

        self._style_input(
            self.brand_dropdown
        )

        layout.addWidget(
            self.brand_dropdown
        )

        self.brand_dropdown.currentTextChanged.connect(
            self.on_brand_selected
        )

        self.refresh_brand_dropdown()

    # =========================================================
    # Metadata
    # =========================================================

    def create_metadata_selection(
        self,
        parent,
    ):

        frame = QFrame(
            parent
        )

        self._style_frame(
            frame,
            CARD_BG,
            BORDER_COLOR,
            radius=8,
        )

        layout = QVBoxLayout(
            frame
        )

        layout.setContentsMargins(
            10,
            8,
            10,
            8,
        )

        layout.setSpacing(
            4
        )

        self.create_measurement_dropdown(
            frame
        )

        self.create_drive_dropdown(
            frame
        )

        self.create_point_dropdown(
            frame
        )

        self.create_specialty_socket_dropdown(
            frame
        )

        self.create_invoice_entry(
            frame
        )

        self.create_ebay_id_entry(
            frame
        )

        self.create_part_number_entry(
            frame
        )

        self.create_invoice_price_entry(
            frame
        )

        self.refresh_metadata_dropdowns()

        self._add_right_panel_widget(
            parent,
            frame,
        )

    # =========================================================
    # Metadata Dropdown Helper
    # =========================================================

    def _create_metadata_dropdown(
        self,
        parent,
        label_text,
        variable_name,
        widget_name,
        values=None,
        callback=None,
    ):

        layout = parent.layout()

        label = QLabel(
            label_text
        )

        self._style_label(
            label,
            TEXT_COLOR,
            size=12,
            bold=True,
        )

        layout.addWidget(
            label
        )

        dropdown = NoWheelComboBox()

        dropdown.setFixedHeight(
            34
        )

        dropdown.setEditable(
            False
        )


        if values:
            dropdown.addItems(
                values
            )

        self._style_input(
            dropdown
        )

        setattr(
            self,
            variable_name,
            ""
        )

        setattr(
            self,
            widget_name,
            dropdown
        )

        layout.addWidget(
            dropdown
        )

        if callback:

            dropdown.currentTextChanged.connect(
                callback
            )

        return dropdown

    # =========================================================
    # Measurement
    # =========================================================

    def create_measurement_dropdown(
        self,
        parent,
    ):

        self._create_metadata_dropdown(
            parent,
            "Measurement",
            "measurement_var",
            "measurement_dropdown",
            [
                "SAE",
                "Metric",
                "Other",
                "DUAL",
            ],
            self.on_measurement_selected,
        )

    # =========================================================
    # Drive
    # =========================================================

    def create_drive_dropdown(
        self,
        parent,
    ):

        self._create_metadata_dropdown(
            parent,
            "Drive",
            "drive_var",
            "drive_dropdown",
            callback=self.on_drive_selected,
        )

    # =========================================================
    # Point
    # =========================================================

    def create_point_dropdown(
        self,
        parent,
    ):

        self._create_metadata_dropdown(
            parent,
            "Point",
            "point_var",
            "point_dropdown",
            callback=self.on_point_selected,
        )

    # =========================================================
    # Specialty Socket
    # =========================================================

    def create_specialty_socket_dropdown(
        self,
        parent,
    ):

        self._create_metadata_dropdown(
            parent,
            "Specialty Socket",
            "specialty_socket_var",
            "specialty_socket_dropdown",
            callback=self.on_specialty_socket_selected,
        )

    # =========================================================
    # Metadata Text Inputs
    # =========================================================

    def commit_metadata_entries(
        self,
    ):

        self.on_invoice_changed()

        self.on_ebay_id_changed()

        self.on_part_number_changed()

        self.on_invoice_price_changed()

    # =========================================================
    # Invoice
    # =========================================================

    def create_invoice_entry(
        self,
        parent,
    ):

        self.create_metadata_entry(
            parent,
            "Invoice #:",
            "invoice_var",
            "invoice_entry",
            self.on_invoice_changed,
        )

    # =========================================================
    # eBay ID
    # =========================================================

    def create_ebay_id_entry(
        self,
        parent,
    ):

        self.create_metadata_entry(
            parent,
            "eBay ID:",
            "ebay_id_var",
            "ebay_id_entry",
            self.on_ebay_id_changed,
        )

    # =========================================================
    # Part Number
    # =========================================================

    def create_part_number_entry(
        self,
        parent,
    ):

        self.create_metadata_entry(
            parent,
            "Part Number:",
            "part_number_var",
            "part_number_entry",
            self.on_part_number_changed,
        )

    # =========================================================
    # Invoice Price
    # =========================================================

    def create_invoice_price_entry(
        self,
        parent,
    ):

        self.create_metadata_entry(
            parent,
            "Invoice Price:",
            "invoice_price_var",
            "invoice_price_entry",
            self.on_invoice_price_changed,
        )

    # =========================================================
    # Generic Metadata Entry
    # =========================================================

    def create_metadata_entry(
        self,
        parent,
        label_text,
        variable_name,
        entry_name,
        callback,
    ):

        layout = parent.layout()

        label = QLabel(
            label_text
        )

        self._style_label(
            label,
            TEXT_COLOR,
            size=12,
            bold=True,
        )

        layout.addWidget(
            label
        )

        entry = QLineEdit()

        entry.setFixedHeight(
            34
        )

        self._style_input(
            entry
        )

        setattr(
            self,
            variable_name,
            ""
        )

        setattr(
            self,
            entry_name,
            entry
        )

        layout.addWidget(
            entry
        )

        entry.editingFinished.connect(
            callback
        )

    # =========================================================
    # Add Widget To Right Panel
    # =========================================================

    def _add_right_panel_widget(
        self,
        parent,
        widget,
    ):

        layout = parent.layout()

        if layout is None:

            layout = QVBoxLayout(
                parent
            )

        # Remove trailing stretch if present.
        while layout.count():

            item = layout.itemAt(
                layout.count() - 1
            )

            if item.spacerItem():

                layout.takeAt(
                    layout.count() - 1
                )

            else:

                break

        layout.addWidget(
            widget
        )

        layout.addStretch()

    def _refresh_scroll_area_theme(
        self,
        scroll_area,
    ):

        if scroll_area is None:
            return

        panel_bg = self.get_color(
            PANEL_BG
        )

        card_bg = self.get_color(
            CARD_BG
        )

        border = self.get_color(
            BORDER_COLOR
        )

        text = self.get_color(
            TEXT_COLOR
        )

        scroll_area.setStyleSheet(
            f"""
            QScrollArea {{
                background-color: {panel_bg};
                color: {text};
                border: none;
            }}

            QScrollArea > QWidget {{
                background-color: {panel_bg};
            }}

            QScrollArea > QWidget > QWidget {{
                background-color: {panel_bg};
                color: {text};
            }}

            QScrollBar:vertical {{
                background: {panel_bg};
                width: 10px;
                margin: 0px;
                border: none;
            }}

            QScrollBar::handle:vertical {{
                background: {card_bg};
                border: 1px solid {border};
                border-radius: 5px;
                min-height: 30px;
            }}

            QScrollBar::handle:vertical:hover {{
                background: {border};
            }}

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
                border: none;
                background: transparent;
            }}

            QScrollBar:horizontal {{
                background: {panel_bg};
                height: 10px;
                margin: 0px;
                border: none;
            }}

            QScrollBar::handle:horizontal {{
                background: {card_bg};
                border: 1px solid {border};
                border-radius: 5px;
                min-width: 30px;
            }}

            QScrollBar::handle:horizontal:hover {{
                background: {border};
            }}

            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                width: 0px;
                border: none;
                background: transparent;
            }}
            """
        )

        # ---------------------------------------------------------
        # Explicit viewport
        # ---------------------------------------------------------

        viewport = scroll_area.viewport()

        if viewport is not None:
            viewport.setStyleSheet(
                f"""
                QWidget {{
                    background-color: {panel_bg};
                    color: {text};
                }}
                """
            )

    # =========================================================
    # Recursive Theme Refresh
    # =========================================================

    def refresh_right_panel_theme(self):

        if not hasattr(
            self,
            "right_panel",
        ):
            return
        
        mode = getattr(
            self,
            "appearance_mode",
            "Dark",
        )



        # ---------------------------------------------------------
        # Main panel
        # ---------------------------------------------------------

        self._style_frame(
            self.right_panel,
            PANEL_BG,
            BORDER_COLOR,
            radius=10,
        )

        # ---------------------------------------------------------
        # Panel containers
        # ---------------------------------------------------------

        for name in (
            "selection_tab",
            "recent_crops_tab",
            "right_panel_content_widget",
            "recent_crops_list_widget",
        ):

            widget = getattr(
                self,
                name,
                None,
            )

            if widget is not None:
                widget.setStyleSheet(
                    f"""
                    QWidget {{
                        background-color: {self.get_color(PANEL_BG)};
                        color: {self.get_color(TEXT_COLOR)};
                    }}
                    """
                )

        # ---------------------------------------------------------
        # Refresh widgets
        #
        # Do not blindly restyle specialized buttons here.
        # ---------------------------------------------------------

        self._refresh_widget_theme_recursive(
            self.right_panel
        )

        # ---------------------------------------------------------
        # Explicit tab styling
        # ---------------------------------------------------------

        self._refresh_tab_widget_theme()

        # ---------------------------------------------------------
        # Scroll areas
        # ---------------------------------------------------------

        self._refresh_scroll_area_theme(
            getattr(
                self,
                "right_panel_content",
                None,
            )
        )

        self._refresh_scroll_area_theme(
            getattr(
                self,
                "recent_crops_list",
                None,
            )
        )

        # ---------------------------------------------------------
        # Explicit content widget backgrounds
        # ---------------------------------------------------------

        for name in (
            "right_panel_content_widget",
            "recent_crops_list_widget",
        ):

            widget = getattr(
                self,
                name,
                None,
            )

            if widget is not None:
                widget.setStyleSheet(
                    f"""
                    QWidget {{
                        background-color: {self.get_color(PANEL_BG)};
                        color: {self.get_color(TEXT_COLOR)};
                    }}
                    """
                )

        # ---------------------------------------------------------
        # Recent crops
        #
        # This rebuilds the list if necessary and ensures newly
        # created rows use the current theme.
        # ---------------------------------------------------------

        self._recent_crop_signature = None

        self.refresh_recent_crops()

        if hasattr(
            self,
            "size_dropdown",
        ):
            self.size_dropdown.set_appearance_mode(
                mode
            )

        if hasattr(
            self,
            "size_2_dropdown",
        ):
            self.size_2_dropdown.set_appearance_mode(
                mode
            )

        # ---------------------------------------------------------
        # Existing preview windows
        # ---------------------------------------------------------

        previews = getattr(
            self,
            "_recent_crop_previews",
            set(),
        )

        for preview in list(
            previews
        ):

            if preview is not None:
                self._refresh_recent_crop_preview_theme(
                    preview
                )

    def _refresh_widget_theme_recursive(
        self,
        widget,
    ):

        if widget is None:
            return

        if widget is getattr(
            self,
            "recent_crops_list_widget",
            None,
        ):
            return


        # ---------------------------------------------------------
        # QFrame
        # ---------------------------------------------------------

        if isinstance(
            widget,
            QFrame,
        ):

            if widget is not getattr(
                self,
                "right_panel",
                None,
            ):

                self._style_frame(
                    widget,
                    CARD_BG,
                    BORDER_COLOR,
                    radius=8,
                )

        # ---------------------------------------------------------
        # QLabel
        # ---------------------------------------------------------

        elif isinstance(
            widget,
            QLabel,
        ):

            point_size = widget.font().pointSize()

            if point_size <= 0:
                point_size = 10

            self._style_label(
                widget,
                TEXT_COLOR,
                size=point_size,
                bold=widget.font().bold(),
            )

        # ---------------------------------------------------------
        # QLineEdit
        # ---------------------------------------------------------

        elif isinstance(
            widget,
            QLineEdit,
        ):

            self._style_input(
                widget
            )

        # ---------------------------------------------------------
        # QComboBox
        # ---------------------------------------------------------

        elif isinstance(
            widget,
            QComboBox,
        ):

            self._style_input(
                widget
            )

        # ---------------------------------------------------------
        # QRadioButton
        # ---------------------------------------------------------

        elif isinstance(
            widget,
            QRadioButton,
        ):

            self._style_radio_button(
                widget
            )

        elif isinstance(widget, FractionDropdown) and widget in (
            getattr(self, "size_dropdown", None),
            getattr(self, "size_2_dropdown", None),
        ):

            if hasattr(widget, "refresh_dropdown_theme"):
                widget.refresh_dropdown_theme()

            widget.button.setAlignment(
                Qt.AlignLeft | Qt.AlignVCenter
            )

            return

        # ---------------------------------------------------------
        # FractionDropdown
        # ---------------------------------------------------------

        elif isinstance(widget, FractionDropdown):

            if hasattr(widget, "refresh_dropdown_theme"):
                widget.refresh_dropdown_theme()

            widget.button.setAlignment(
                Qt.AlignLeft | Qt.AlignVCenter
            )

            return

        
        # ---------------------------------------------------------
        # QPushButton
        #
        # IMPORTANT:
        #
        # Do not blindly call _style_button().
        # Specialized buttons have their own colors.
        # ---------------------------------------------------------

        elif isinstance(
            widget,
            QPushButton,
        ):

            if widget is getattr(
                self,
                "stop_button",
                None,
            ):
                pass

            elif widget.text() == "Remove JSON":

                self._style_button(
                    widget,
                    background=DANGER_COLOR,
                    hover=DANGER_HOVER,
                    text_color=WHITE_TEXT,
                    radius=5,
                )

            elif widget.text() == "Close":

                self._style_button(
                    widget,
                    background=ACCENT_COLOR,
                    hover=ACCENT_HOVER,
                    text_color=WHITE_TEXT,
                    radius=6,
                )

            else:

                self._style_button(
                    widget
                )

        # ---------------------------------------------------------
        # Child widgets
        # ---------------------------------------------------------

        for child in widget.findChildren(
            QWidget,
            options=Qt.FindDirectChildrenOnly,
        ):

            self._refresh_widget_theme_recursive(
                child
            )


    def _refresh_tab_widget_theme(self):

        if not hasattr(
            self,
            "right_panel_notebook",
        ):
            return

        panel_bg = self.get_color(
            PANEL_BG
        )

        card_bg = self.get_color(
            CARD_BG
        )

        text = self.get_color(
            TEXT_COLOR
        )

        inverted_text = self.get_color(
            INVERTED_TEXT
        )

        accent = self.get_color(
            ACCENT_COLOR
        )

        accent_hover = self.get_color(
            ACCENT_HOVER
        )

        white = self.get_color(
            WHITE_TEXT
        )

        self.right_panel_notebook.setStyleSheet(
            f"""
            QTabWidget {{
                background-color: {panel_bg};
                color: {text};
                border: none;
            }}

            QTabWidget::pane {{
                background-color: {panel_bg};
                color: {text};
                border: none;
            }}

            QTabBar {{
                background-color: {panel_bg};
                color: {text};
            }}

            QTabBar::scroller {{
                background-color: {panel_bg};
            }}

            QTabWidget::left-corner,
            QTabWidget::right-corner {{
                background-color: {panel_bg};
            }}

            QTabBar::tab {{
                background-color: {card_bg};
                color: {text};
                border: none;
                padding: 8px 14px;
                margin-right: 2px;
                border-radius: 6px;
            }}

            QTabBar::tab:selected {{
                background-color: {accent};
                color: {white};
            }}

            QTabBar::tab:hover {{
                background-color: {accent_hover};
                color: {inverted_text};
            }}

            QTabBar::tab:disabled {{
                background-color: {panel_bg};
                color: {text};
            }}
            """
        )

        # ---------------------------------------------------------
        # Tab pages
        # ---------------------------------------------------------

        for tab in (
            getattr(
                self,
                "selection_tab",
                None,
            ),
            getattr(
                self,
                "recent_crops_tab",
                None,
            ),
        ):

            if tab is not None:

                tab.setStyleSheet(
                    f"""
                    QWidget {{
                        background-color: {panel_bg};
                        color: {text};
                    }}
                    """
                )

        # ---------------------------------------------------------
        # Explicitly refresh the internal tab widget container
        # ---------------------------------------------------------

        for widget in (
            self.right_panel_notebook,
            self.right_panel_notebook.tabBar(),
        ):

            if widget is not None:
                widget.setAttribute(
                    Qt.WA_StyledBackground,
                    True,
                )

        # ---------------------------------------------------------
        # Tab pages
        # ---------------------------------------------------------

        for tab in (
            getattr(
                self,
                "selection_tab",
                None,
            ),
            getattr(
                self,
                "recent_crops_tab",
                None,
            ),
        ):

            if tab is not None:
                tab.setStyleSheet(
                    f"""
                    QWidget {{
                        background-color: {panel_bg};
                        color: {text};
                    }}
                    """
                )