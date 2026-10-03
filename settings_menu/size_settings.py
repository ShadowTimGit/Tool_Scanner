from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QListWidget,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QFrame,
)

from settings_menu.settings_config import (
    DEFAULT_SAE_SIZES,
    DEFAULT_METRIC_SIZES,
    DEFAULT_OTHER,
)

from GUI.appearance_controller import (
    AppearanceController,
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
    WHITE_TEXT,
)


class SizeSettings(QWidget):

    def __init__(
        self,
        parent,
        on_sizes_changed,
    ):
        super().__init__(parent)

        self.parent = parent
        self.on_sizes_changed = on_sizes_changed

        self.appearance_mode = getattr(
            parent,
            "appearance_mode",
            "Dark",
        )

        self.sizes = {
            "SAE": list(DEFAULT_SAE_SIZES),
            "Metric": list(DEFAULT_METRIC_SIZES),
            "Other": list(DEFAULT_OTHER),
            "DUAL": [],
        }

        self.create_gui()

    # =========================================================
    # Appearance
    # =========================================================

    def get_color(
        self,
        color,
        mode=None,
    ):
        if mode is None:
            mode = self.appearance_mode

        return AppearanceController.get_color(
            color,
            mode,
        )

    def update_appearance(
        self,
        mode=None,
    ):
        if mode is None:
            mode = "Dark"

        self.appearance_mode = mode

        self.card.setStyleSheet(
            f"""
            QFrame {{
                background-color: {self.get_color(CARD_BG)};
                border: 1px solid {self.get_color(BORDER_COLOR)};
                border-radius: 10px;
            }}
            """
        )

        self.header_label.setStyleSheet(
            f"""
            QLabel {{
                color: {self.get_color(TEXT_COLOR)};
                font-size: 18px;
                font-weight: bold;
                background: transparent;
            }}
            """
        )

        self.description_label.setStyleSheet(
            f"""
            QLabel {{
                color: {self.get_color(MUTED_TEXT)};
                font-size: 12px;
                background: transparent;
            }}
            """
        )

        self.measurement_label.setStyleSheet(
            f"""
            QLabel {{
                color: {self.get_color(TEXT_COLOR)};
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }}
            """
        )

        self.available_sizes_label.setStyleSheet(
            f"""
            QLabel {{
                color: {self.get_color(TEXT_COLOR)};
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }}
            """
        )

        self.measurement_dropdown.setStyleSheet(
            f"""
            QComboBox {{
                background-color: {self.get_color(INPUT_BG)};
                color: {self.get_color(TEXT_COLOR)};
                border: 1px solid {self.get_color(BORDER_COLOR)};
                border-radius: 6px;
                padding: 0 10px;
                font-size: 12px;
            }}

            QComboBox:hover {{
                border-color: {self.get_color(ACCENT_COLOR)};
            }}

            QComboBox:focus {{
                border-color: {self.get_color(ACCENT_COLOR)};
            }}

            QComboBox::drop-down {{
                border: none;
                width: 28px;
            }}

            QComboBox QAbstractItemView {{
                background-color: {self.get_color(PANEL_BG)};
                color: {self.get_color(TEXT_COLOR)};
                border: 1px solid {self.get_color(BORDER_COLOR)};
                selection-background-color: {self.get_color(CARD_HOVER)};
                selection-color: {self.get_color(TEXT_COLOR)};
                padding: 4px;
            }}
            """
        )

        self.size_listbox.setStyleSheet(
            f"""
            QListWidget {{
                background-color: {self.get_color(INPUT_BG)};
                color: {self.get_color(TEXT_COLOR)};
                border: 1px solid {self.get_color(BORDER_COLOR)};
                border-radius: 6px;
                padding: 6px;
                font-size: 11px;
                outline: none;
            }}

            QListWidget::item {{
                padding: 5px;
                border-radius: 4px;
            }}

            QListWidget::item:selected {{
                background-color: {self.get_color(ACCENT_COLOR)};
                color: {self.get_color(WHITE_TEXT)};
            }}

            QListWidget::item:hover {{
                background-color: {self.get_color(CARD_HOVER)};
            }}

            QScrollBar:vertical {{
                background-color: {self.get_color(INPUT_BG)};
                width: 10px;
                margin: 4px;
            }}

            QScrollBar::handle:vertical {{
                background-color: {self.get_color(CARD_BG)};
                border-radius: 5px;
                min-height: 20px;
            }}

            QScrollBar::handle:vertical:hover {{
                background-color: {self.get_color(CARD_HOVER)};
            }}

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            """
        )

        self.size_entry.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: {self.get_color(INPUT_BG)};
                color: {self.get_color(TEXT_COLOR)};
                border: 1px solid {self.get_color(BORDER_COLOR)};
                border-radius: 6px;
                padding: 0 10px;
                font-size: 12px;
            }}

            QLineEdit:hover {{
                border-color: {self.get_color(ACCENT_COLOR)};
            }}

            QLineEdit:focus {{
                border-color: {self.get_color(ACCENT_COLOR)};
            }}

            QLineEdit:disabled {{
                color: {self.get_color(MUTED_TEXT)};
                background-color: {self.get_color(PANEL_BG)};
            }}

            QLineEdit::placeholder {{
                color: {self.get_color(MUTED_TEXT)};
            }}
            """
        )

        self.add_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self.get_color(ACCENT_COLOR)};
                color: {self.get_color(WHITE_TEXT)};
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }}

            QPushButton:hover {{
                background-color: {self.get_color(ACCENT_HOVER)};
            }}

            QPushButton:pressed {{
                background-color: {self.get_color(ACCENT_COLOR)};
            }}

            QPushButton:disabled {{
                background-color: {self.get_color(CARD_BG)};
                color: {self.get_color(MUTED_TEXT)};
            }}
            """
        )

        self.remove_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self.get_color(CARD_BG)};
                color: {self.get_color(TEXT_COLOR)};
                border: 1px solid {self.get_color(BORDER_COLOR)};
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }}

            QPushButton:hover {{
                background-color: {self.get_color(DANGER_HOVER)};
                color: {self.get_color(WHITE_TEXT)};
                border-color: {self.get_color(DANGER_HOVER)};
            }}

            QPushButton:pressed {{
                background-color: {self.get_color(DANGER_COLOR)};
                color: {self.get_color(WHITE_TEXT)};
                border-color: {self.get_color(DANGER_COLOR)};
            }}

            QPushButton:disabled {{
                background-color: {self.get_color(CARD_BG)};
                color: {self.get_color(MUTED_TEXT)};
                border-color: {self.get_color(BORDER_COLOR)};
            }}
            """
        )

        self.update()

    # =========================================================
    # GUI
    # =========================================================

    def create_gui(self):

        main_layout = QVBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            15,
            15,
            15,
            15,
        )

        main_layout.setSpacing(0)

        self.create_size_editor(
            main_layout
        )

    def create_size_editor(
        self,
        parent_layout,
    ):
        self.card = QFrame(
            self
        )

        self.card.setFrameShape(
            QFrame.Shape.NoFrame
        )

        parent_layout.addWidget(
            self.card
        )

        frame = QWidget(
            self.card
        )

        frame.setStyleSheet(
            "background: transparent;"
        )

        frame_layout = QVBoxLayout(
            frame
        )

        frame_layout.setContentsMargins(
            20,
            20,
            20,
            20,
        )

        frame_layout.setSpacing(0)

        # -----------------------------------------------------
        # Header
        # -----------------------------------------------------

        self.header_label = QLabel(
            "General Sizes"
        )

        frame_layout.addWidget(
            self.header_label
        )

        self.description_label = QLabel(
            "Manage the available sizes for each measurement system."
        )

        frame_layout.addWidget(
            self.description_label
        )

        frame_layout.addSpacing(
            18
        )

        # -----------------------------------------------------
        # Measurement System
        # -----------------------------------------------------

        self.measurement_label = QLabel(
            "Measurement System"
        )

        frame_layout.addWidget(
            self.measurement_label
        )

        frame_layout.addSpacing(
            6
        )

        self.measurement_dropdown = QComboBox()

        self.measurement_dropdown.addItems(
            [
                "SAE",
                "Metric",
                "Other",
                "DUAL",
            ]
        )

        self.measurement_dropdown.setCurrentText(
            "SAE"
        )

        self.measurement_dropdown.setFixedWidth(
            220
        )

        self.measurement_dropdown.setFixedHeight(
            36
        )

        self.measurement_dropdown.currentTextChanged.connect(
            self.on_measurement_changed
        )

        frame_layout.addWidget(
            self.measurement_dropdown
        )

        frame_layout.addSpacing(
            18
        )

        # -----------------------------------------------------
        # Size List Label
        # -----------------------------------------------------

        self.available_sizes_label = QLabel(
            "Available Sizes"
        )

        frame_layout.addWidget(
            self.available_sizes_label
        )

        frame_layout.addSpacing(
            6
        )

        # -----------------------------------------------------
        # Size List
        # -----------------------------------------------------

        self.size_listbox = QListWidget()

        self.size_listbox.setMinimumHeight(
            250
        )

        frame_layout.addWidget(
            self.size_listbox,
            1,
        )

        frame_layout.addSpacing(
            12
        )

        # -----------------------------------------------------
        # Controls
        # -----------------------------------------------------

        controls = QWidget()

        controls.setStyleSheet(
            "background: transparent;"
        )

        controls_layout = QHBoxLayout(
            controls
        )

        controls_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        controls_layout.setSpacing(
            6
        )

        self.size_entry = QLineEdit()

        self.size_entry.setFixedHeight(
            36
        )

        self.size_entry.setPlaceholderText(
            "Enter size..."
        )

        controls_layout.addWidget(
            self.size_entry,
            1,
        )

        # -----------------------------------------------------
        # Add Button
        # -----------------------------------------------------

        self.add_button = QPushButton(
            "Add Size"
        )

        self.add_button.setFixedSize(
            110,
            36,
        )

        self.add_button.clicked.connect(
            self.add_size
        )

        controls_layout.addWidget(
            self.add_button
        )

        # -----------------------------------------------------
        # Remove Button
        # -----------------------------------------------------

        self.remove_button = QPushButton(
            "Remove Size"
        )

        self.remove_button.setFixedSize(
            110,
            36,
        )

        self.remove_button.clicked.connect(
            self.remove_size
        )

        controls_layout.addWidget(
            self.remove_button
        )

        frame_layout.addWidget(
            controls
        )

        # -----------------------------------------------------
        # Initial Data
        # -----------------------------------------------------

        self.refresh_size_list()

        self.update_appearance(
            self.appearance_mode
        )

    # =========================================================
    # Measurement Selection
    # =========================================================

    def on_measurement_changed(
        self,
        measurement,
    ):
        self.refresh_size_list()

    # =========================================================
    # Add Size
    # =========================================================

    def add_size(self):
        measurement = (
            self.measurement_dropdown.currentText()
        )

        if measurement in {
            "Other",
            "DUAL",
        }:
            return

        size = (
            self.size_entry
            .text()
            .strip()
        )

        if not size:
            return

        sizes = self.sizes[
            measurement
        ]

        if any(
            existing.casefold() == size.casefold()
            for existing in sizes
        ):
            QMessageBox.warning(
                self.parent,
                "Size Exists",
                (
                    f"{size} already exists in "
                    f"{measurement} sizes."
                ),
            )
            return

        sizes.append(
            size
        )

        self.size_entry.clear()

        self.sort_sizes(
            measurement
        )

        self.save_sizes()

        self.refresh_size_list()

        self.on_sizes_changed()

    # =========================================================
    # Remove Size
    # =========================================================

    def remove_size(self):
        measurement = (
            self.measurement_dropdown.currentText()
        )

        if measurement in {
            "Other",
            "DUAL",
        }:
            return

        selection = (
            self.size_listbox.selectedItems()
        )

        if not selection:
            QMessageBox.warning(
                self.parent,
                "Select Size",
                "Select a size to remove.",
            )
            return

        size = selection[0].text()

        answer = QMessageBox.question(
            self.parent,
            "Remove Size",
            (
                f"Remove '{size}' from "
                f"{measurement} sizes?"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self.sizes[
            measurement
        ].remove(
            size
        )

        self.save_sizes()

        self.refresh_size_list()

        self.on_sizes_changed()

    # =========================================================
    # Refresh
    # =========================================================

    def refresh_size_list(self):
        measurement = (
            self.measurement_dropdown.currentText()
        )

        self.size_listbox.clear()

        if measurement == "Other":
            sizes = self.sizes.get(
                "Other",
                [],
            )

        elif measurement == "DUAL":
            sizes = []

        else:
            sizes = self.sizes.get(
                measurement,
                [],
            )

        self.size_listbox.addItems(
            sizes
        )

        is_editable = measurement not in {
            "Other",
            "DUAL",
        }

        self.size_entry.setEnabled(
            is_editable
        )

        self.add_button.setEnabled(
            is_editable
        )

        self.remove_button.setEnabled(
            is_editable
        )

    # =========================================================
    # Sorting
    # =========================================================

    def sort_sizes(
        self,
        measurement,
    ):
        self.sizes[
            measurement
        ].sort(
            key=self.size_sort_key
        )

    @staticmethod
    def size_sort_key(size):
        value = size.strip().lower()

        # Metric
        if value.endswith("mm"):
            try:
                return (
                    1,
                    float(
                        value[:-2]
                    ),
                )
            except ValueError:
                pass

        # SAE fractions / mixed numbers
        try:
            if "-" in value:
                whole, fraction = (
                    value.split(
                        "-",
                        1,
                    )
                )

                numerator, denominator = (
                    fraction.split(
                        "/",
                        1,
                    )
                )

                numeric = (
                    float(whole)
                    + (
                        float(numerator)
                        / float(denominator)
                    )
                )

            elif "/" in value:
                numerator, denominator = (
                    value.split(
                        "/",
                        1,
                    )
                )

                numeric = (
                    float(numerator)
                    / float(denominator)
                )

            else:
                numeric = float(
                    value
                )

            return (
                0,
                numeric,
            )

        except ValueError:
            return (
                2,
                value,
            )

    # =========================================================
    # Persistence
    # =========================================================

    def save_sizes(self):
        from settings_menu.tool_settings import (
            ToolSettings,
        )

        ToolSettings.save_sizes_data(
            self.sizes
        )
