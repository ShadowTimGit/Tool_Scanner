import os
from PIL import Image

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QDialog,
    QSizePolicy,
)

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
    INVERTED_TEXT,
)


class RecentCropsTabMixin:

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

        layout.addWidget(
            self.recent_crops_list,
            1,
        )

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

        if not entries:

            empty_label = QLabel(
                "No recent cropped images found."
            )

            empty_label.setWordWrap(True)

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

        for entry in entries:

            row = QFrame()

            row.setMinimumHeight(120)

            self._style_frame(
                row,
                CARD_BG,
                BORDER_COLOR,
                radius=8,
            )

            row_layout = QVBoxLayout(row)

            row_layout.setContentsMargins(
                8,
                8,
                8,
                8,
            )

            row_layout.setSpacing(5)

            body = QWidget()

            body_layout = QHBoxLayout(body)

            body_layout.setContentsMargins(
                0,
                0,
                0,
                0,
            )

            body_layout.setSpacing(8)

            image_path = entry.get("image_path")

            thumbnail = self.load_thumbnail(
                image_path
            )

            image_label = QLabel()

            image_label.setPixmap(thumbnail)
            image_label.setFixedSize(80, 80)
            image_label.setAlignment(Qt.AlignCenter)
            image_label.setCursor(
                Qt.PointingHandCursor
            )

            image_label.mousePressEvent = (
                lambda event,
                item=entry:
                self.open_recent_crop_image(item)
            )

            body_layout.addWidget(image_label)

            info_text = (
                f"{entry.get('display_name', os.path.basename(image_path or ''))}\n"
                f"{entry.get('tool_name', 'Unknown')}\n"
                f"{os.path.basename(entry.get('json_path', ''))}"
            )

            info = QLabel(info_text)

            info.setWordWrap(True)

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

            body_layout.addWidget(info, 1)

            row_layout.addWidget(body)

            remove_button = QPushButton(
                "Remove JSON"
            )

            remove_button.setFixedHeight(30)

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
                self.remove_recent_crop(item)
            )

            row_layout.addWidget(remove_button)

            self.recent_crops_list_layout.addWidget(row)

        self.recent_crops_list_layout.addStretch()

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

            json_path = entry.get("json_path")
            image_path = entry.get("image_path")

            if not json_path and not image_path:
                continue

            if (
                image_path
                and os.path.exists(image_path)
            ):
                entries.append(entry)
                continue

            if (
                json_path
                and os.path.exists(json_path)
            ):
                entries.append(entry)

        return entries[:25]

    def load_thumbnail(self, image_path):

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

                image = Image.open(image_path)
                image = image.convert("RGB")

                image.thumbnail(
                    (80, 80),
                    Image.Resampling.LANCZOS,
                )

            except Exception:

                image = Image.new(
                    "RGB",
                    (80, 80),
                    color="#DC2626",
                )

        image = image.convert("RGBA")

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

        return QPixmap.fromImage(qimage.copy())

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

    def close_recent_crop_previews(self):

        previews = getattr(
            self,
            "_recent_crop_previews",
            set(),
        )

        for preview in list(previews):

            try:
                preview.close()
            except Exception:
                pass

        previews.clear()

    def open_recent_crop_image(
        self,
        entry,
    ):

        image_path = entry.get("image_path")

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

        preview = QDialog(self.root)

        self._recent_crop_previews.add(preview)

        preview.setWindowTitle(
            f"Recent Crop - "
            f"{os.path.basename(image_path)}"
        )

        preview.resize(900, 700)

        preview.setStyleSheet(
            f"""
            QDialog {{
                background-color: {self.get_color(CONTROL_BG)};
            }}
            """
        )

        preview_layout = QVBoxLayout(preview)

        preview_layout.setContentsMargins(
            10,
            6,
            10,
            6,
        )

        try:

            image = Image.open(image_path)
            image = image.convert("RGB")

            image_width, image_height = image.size

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
                            int(image_width * scale),
                        ),
                        max(
                            1,
                            int(image_height * scale),
                        ),
                    ),
                    Image.Resampling.LANCZOS,
                )

            pixmap = self._pil_to_pixmap(image)

            label = QLabel()

            label.setPixmap(pixmap)
            label.setAlignment(Qt.AlignCenter)
            label.setSizePolicy(
                label.sizePolicy().horizontalPolicy(),
                label.sizePolicy().verticalPolicy(),
            )

            preview_layout.addWidget(label, 1)

            close_button = QPushButton("Close")

            close_button.setFixedSize(120, 36)

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

            error_label.setAlignment(Qt.AlignCenter)

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

    @staticmethod
    def _pil_to_pixmap(image):

        from PySide6.QtGui import QImage

        image = image.convert("RGBA")

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

        return QPixmap.fromImage(qimage.copy())

    def remove_recent_crop(
        self,
        entry,
    ):

        json_path = entry.get("json_path")
        image_path = entry.get("image_path")

        if not json_path and not image_path:
            return

        confirm_box = QMessageBox(self.root)

        confirm_box.setWindowTitle(
            "Remove crop entry"
        )

        confirm_box.setText(
            "This will remove the selected crop "
            "image and JSON.\n"
            "The spreadsheet will be rebuilt afterward.\n\n"
            f"{os.path.basename(json_path or image_path or '')}"
        )

        confirm_box.setStandardButtons(
            QMessageBox.Yes |
            QMessageBox.No
        )

        confirm_box.setDefaultButton(
            QMessageBox.No
        )

        confirm_box.setStyleSheet(
            f"""
            QMessageBox {{
                background-color: {self.get_color(CONTROL_BG)};
                color: {self.get_color(TEXT_COLOR)};
            }}

            QMessageBox QLabel {{
                color: {self.get_color(TEXT_COLOR)};
                background-color: transparent;
            }}

            QMessageBox QPushButton {{
                background-color: {self.get_color(CARD_BG)};
                color: {self.get_color(TEXT_COLOR)};
                border: 1px solid {self.get_color(BORDER_COLOR)};
                border-radius: 6px;
                padding: 6px 16px;
                min-width: 70px;
            }}

            QMessageBox QPushButton:hover {{
                background-color: {self.get_color(ACCENT_HOVER)};
                color: {self.get_color(INVERTED_TEXT)};
            }}

            QMessageBox QPushButton:default {{
                background-color: {self.get_color(ACCENT_COLOR)};
                color: {self.get_color(WHITE_TEXT)};
                border: 1px solid {self.get_color(ACCENT_COLOR)};
            }}
            """
        )

        result = confirm_box.exec()

        if result != QMessageBox.Yes:
            return

        from tool_logger.logger_worker import (
            submit_remove_crop,
        )

        future = submit_remove_crop(
            json_path,
            image_path,
            on_complete=lambda future, item=entry:
                self._remove_recent_crop_complete(
                    future,
                    item,
                ),
        )

        if future is None:
            self._finish_remove_recent_crop(
                False,
                entry,
            )

    def _remove_recent_crop_complete(
        self,
        future,
        entry,
    ):

        try:
            success = future.result()

        except Exception as error:

            print(
                f"ERROR: Crop removal worker failed: {error}"
            )

            success = False

        self.finish_remove_recent_crop.emit(
            success,
            entry,
        )

    def _finish_remove_recent_crop(
        self,
        success,
        entry,
    ):

        if not success:
            self._recent_crop_signature = None
            self.refresh_recent_crops()
            return

        if self.camera is not None:

            json_path = entry.get("json_path")
            image_path = entry.get("image_path")

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