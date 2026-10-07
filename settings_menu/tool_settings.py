import copy
import json
import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
)

from settings_menu.tool_repository import ToolRepository
from settings_menu.settings_config import (
    DEFAULT_SAE_SIZES,
    DEFAULT_METRIC_SIZES,
    DEFAULT_OTHER,
)

from GUI.appearance_controller import (
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


class ToolSettings(QWidget):
    # =========================================================
    # Files
    # =========================================================

    SETTINGS_DIR = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
        ),
        "settings",
    )

    BRANDS_FILE = os.path.join(
        SETTINGS_DIR,
        "brands.json",
    )

    SIZES_FILE = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
        ),
        "sizes.json",
    )

    DEFAULT_BRANDS = {
        "Blue Point": ["Blue Point"],
        "Cornwell": ["Cornwell"],
        "Craftsman": ["Craftsman"],
        "GearWrench": ["GearWrench"],
        "Husky": ["Husky"],
        "Kobalt": ["Kobalt"],
        "MAC": ["MAC"],
        "Matco": ["Matco"],
        "Proto": ["Proto"],
        "SK Tools": ["SK Tools"],
        "Snap-on": ["Snap-on"],
    }

    # =========================================================
    # INIT
    # =========================================================

    def __init__(
        self,
        parent,
        tools,
        on_tools_changed,
        on_brands_changed=None,
    ):
        super().__init__(parent)

        self.parent = parent

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.tools = tools
        self.on_tools_changed = on_tools_changed
        self.on_brands_changed = on_brands_changed

        self.appearance_mode = getattr(
            parent,
            "appearance_mode",
            "Dark",
        )

        print("[DEBUG] ToolSettings CREATED")

        self.brands = self.load_brands()

        self.create_gui()

    # =========================================================
    # Appearance
    # =========================================================

    def get_color(self, color):
        return (
            color[0]
            if self.appearance_mode == "Light"
            else color[1]
        )

    def update_appearance(self, mode):
        self.appearance_mode = (
            mode.capitalize()
            if mode
            else "Dark"
        )

        if self.appearance_mode not in (
            "Light",
            "Dark",
        ):
            self.appearance_mode = "Dark"

        self.refresh_theme()

    def refresh_theme(self):
        # -----------------------------------------------------
        # Main frame
        # -----------------------------------------------------

        if hasattr(self, "main_frame"):
            self.main_frame.setStyleSheet(
                f"""
                QFrame#toolSettingsMainFrame {{
                    background-color: {self.get_color(PANEL_BG)};
                    border: none;
                }}
                """
            )

        # -----------------------------------------------------
        # Columns
        # -----------------------------------------------------

        if hasattr(self, "columns"):
            self.columns.setStyleSheet(
                "background: transparent;"
            )

        # -----------------------------------------------------
        # Cards
        # -----------------------------------------------------

        for frame in (
            getattr(self, "add_frame", None),
            getattr(self, "remove_frame", None),
        ):
            if frame is not None:
                frame.setStyleSheet(
                    f"""
                    QFrame#card {{
                        background-color: {self.get_color(CARD_BG)};
                        border: 1px solid {self.get_color(BORDER_COLOR)};
                        border-radius: 10px;
                    }}
                    """
                )

        # -----------------------------------------------------
        # Labels
        # -----------------------------------------------------

        text_labels = (
            "add_brand_title",
            "brand_name_label",
            "add_tool_title",
            "tool_name_label",
            "remove_brand_title",
            "remove_brand_label",
            "remove_tool_title",
            "remove_tool_label",
        )

        muted_labels = (
            "add_brand_description",
            "add_tool_description",
            "remove_brand_description",
            "remove_tool_description",
        )

        for name in text_labels:
            label = getattr(
                self,
                name,
                None,
            )

            if label is not None:
                label.setStyleSheet(
                    f"""
                    QLabel {{
                        color: {self.get_color(TEXT_COLOR)};
                        background: transparent;
                    }}
                    """
                )

        for name in muted_labels:
            label = getattr(
                self,
                name,
                None,
            )

            if label is not None:
                label.setStyleSheet(
                    f"""
                    QLabel {{
                        color: {self.get_color(MUTED_TEXT)};
                        background: transparent;
                    }}
                    """
                )

        # -----------------------------------------------------
        # Line edits
        # -----------------------------------------------------

        for entry in (
            getattr(self, "brand_name_entry", None),
            getattr(self, "tool_entry", None),
        ):
            if entry is not None:
                entry.setStyleSheet(
                    self.get_line_edit_style()
                )

        # -----------------------------------------------------
        # Combo boxes
        # -----------------------------------------------------

        for combo in (
            getattr(self, "remove_brand_dropdown", None),
            getattr(self, "remove_tool_dropdown", None),
        ):
            if combo is not None:
                combo.setStyleSheet(
                    self.get_combo_box_style()
                )

        # -----------------------------------------------------
        # Buttons
        # -----------------------------------------------------

        if hasattr(self, "add_brand_button"):
            self.add_brand_button.setStyleSheet(
                self.get_button_style(
                    ACCENT_COLOR,
                    ACCENT_HOVER,
                    WHITE_TEXT,
                )
            )

        if hasattr(self, "add_tool_button"):
            self.add_tool_button.setStyleSheet(
                self.get_button_style(
                    ACCENT_COLOR,
                    ACCENT_HOVER,
                    WHITE_TEXT,
                )
            )

        if hasattr(self, "remove_brand_button"):
            self.remove_brand_button.setStyleSheet(
                self.get_button_style(
                    DANGER_COLOR,
                    DANGER_HOVER,
                    WHITE_TEXT,
                )
            )

        if hasattr(self, "remove_tool_button"):
            self.remove_tool_button.setStyleSheet(
                self.get_button_style(
                    DANGER_COLOR,
                    DANGER_HOVER,
                    WHITE_TEXT,
                )
            )

        self.update()

    # =========================================================
    # GUI
    # =========================================================

    def create_gui(self):
        self.main_frame = QFrame(self)

        self.main_frame.setObjectName(
            "toolSettingsMainFrame"
        )

        self.main_frame.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.main_frame.setStyleSheet(
            f"""
            QFrame#toolSettingsMainFrame {{
                background-color: {self.get_color(PANEL_BG)};
                border: none;
            }}
            """
        )

        main_layout = QVBoxLayout(
            self.main_frame
        )

        main_layout.setContentsMargins(
            12,
            12,
            12,
            12,
        )

        main_layout.setSpacing(0)

        self.columns = QWidget(
            self.main_frame
        )

        self.columns.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.columns.setStyleSheet(
            "background: transparent;"
        )

        columns_layout = QGridLayout(
            self.columns
        )

        columns_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        columns_layout.setHorizontalSpacing(12)
        columns_layout.setVerticalSpacing(0)

        columns_layout.setColumnStretch(0, 1)
        columns_layout.setColumnStretch(1, 1)

        columns_layout.setRowStretch(0, 1)

        main_layout.addWidget(
            self.columns
        )

        self.create_add_section(
            self.columns
        )

        self.create_remove_section(
            self.columns
        )

        columns_layout.addWidget(
            self.add_frame,
            0,
            0,
        )

        columns_layout.addWidget(
            self.remove_frame,
            0,
            1,
        )

        self.refresh_brand_dropdown()
        self.refresh_tool_dropdown()
    # =========================================================
    # Helpers
    # =========================================================

    def make_label(
        self,
        text,
        color,
        size=12,
        bold=False,
    ):
        label = QLabel(text)

        font = label.font()
        font.setPointSize(max(1, size))
        font.setBold(bold)

        label.setFont(font)

        label.setStyleSheet(
            f"""
            QLabel {{
                color: {self.get_color(color)};
                background: transparent;
            }}
            """
        )

        return label

    def make_button(
        self,
        text,
        background,
        hover,
        callback,
    ):
        button = QPushButton(text)

        button.setFixedHeight(30)
        button.setMinimumWidth(100)

        font = button.font()
        font.setPointSize(12)
        font.setBold(True)

        button.setFont(font)

        button.setCursor(
            Qt.PointingHandCursor
        )

        button.setStyleSheet(
            self.get_button_style(
                background,
                hover,
                WHITE_TEXT,
            )
        )

        button.clicked.connect(callback)

        return button

    def make_line_edit(
        self,
        placeholder,
    ):
        entry = QLineEdit()

        entry.setFixedHeight(38)

        entry.setPlaceholderText(
            placeholder
        )

        entry.setStyleSheet(
            self.get_line_edit_style()
        )

        return entry

    def make_combo_box(self):
        combo = QComboBox()

        combo.setFixedHeight(38)

        combo.setCursor(
            Qt.PointingHandCursor
        )

        combo.setStyleSheet(
            self.get_combo_box_style()
        )

        return combo

    def make_card(
        self,
    ):
        frame = QFrame(
            self.columns
        )

        frame.setObjectName(
            "card"
        )

        frame.setStyleSheet(
            f"""
            QFrame#card {{
                background-color: {self.get_color(CARD_BG)};
                border: 1px solid {self.get_color(BORDER_COLOR)};
                border-radius: 8px;
            }}
            """
        )

        return frame

    # =========================================================
    # Styles
    # =========================================================

    def get_combo_box_style(self):
        return f"""
        QComboBox {{
            background-color: {self.get_color(INPUT_BG)};
            color: {self.get_color(TEXT_COLOR)};
            border: 1px solid {self.get_color(BORDER_COLOR)};
            border-radius: 6px;
            padding: 0 10px;
        }}

        QComboBox:hover {{
            border: 1px solid {self.get_color(ACCENT_COLOR)};
        }}

        QComboBox:focus {{
            border: 1px solid {self.get_color(ACCENT_COLOR)};
        }}

        QComboBox::drop-down {{
            width: 30px;
            border: none;
            background: transparent;
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

    def get_line_edit_style(self):
        return f"""
        QLineEdit {{
            background-color: {self.get_color(INPUT_BG)};
            color: {self.get_color(TEXT_COLOR)};
            border: 1px solid {self.get_color(BORDER_COLOR)};
            border-radius: 6px;
            padding: 0 10px;
            selection-background-color: {self.get_color(ACCENT_COLOR)};
        }}

        QLineEdit:focus {{
            border: 1px solid {self.get_color(ACCENT_COLOR)};
        }}

        QLineEdit::placeholder {{
            color: {self.get_color(MUTED_TEXT)};
        }}
        """

    def get_button_style(
        self,
        background,
        hover,
        text_color,
    ):
        return f"""
        QPushButton {{
            background-color: {self.get_color(background)};
            color: {self.get_color(text_color)};
            border: none;
            border-radius: 6px;
            padding: 0 14px;
        }}

        QPushButton:hover {{
            background-color: {self.get_color(hover)};
        }}

        QPushButton:pressed {{
            background-color: {self.get_color(hover)};
        }}
        """

    # =========================================================
    # LEFT = ADD
    # =========================================================

    def create_add_section(
        self,
        parent,
    ):
        self.add_frame = self.make_card()

        layout = QVBoxLayout(
            self.add_frame
        )

        layout.setContentsMargins(
            18,
            18,
            18,
            18,
        )

        layout.setSpacing(8)

        # -----------------------------------------------------
        # Brand
        # -----------------------------------------------------

        self.add_brand_title = self.make_label(
            "Add Brand",
            TEXT_COLOR,
            size=15,
            bold=True,
        )

        layout.addWidget(
            self.add_brand_title
        )

        self.add_brand_description = self.make_label(
            "Create a new product brand.",
            MUTED_TEXT,
            size=11,
        )

        layout.addWidget(
            self.add_brand_description
        )

        layout.addSpacing(14)

        self.brand_name_label = self.make_label(
            "Brand Name",
            TEXT_COLOR,
            size=12,
            bold=True,
        )

        layout.addWidget(
            self.brand_name_label
        )

        layout.addSpacing(6)

        self.brand_name_entry = self.make_line_edit(
            "Enter brand name..."
        )

        layout.addWidget(
            self.brand_name_entry
        )

        self.add_brand_button = self.make_button(
            "Add Brand",
            ACCENT_COLOR,
            ACCENT_HOVER,
            self.add_brand,
        )

        button_layout = QHBoxLayout()

        button_layout.setContentsMargins(
            0,
            12,
            0,
            24,
        )

        button_layout.addStretch()

        button_layout.addWidget(
            self.add_brand_button
        )

        layout.addLayout(
            button_layout
        )

        # -----------------------------------------------------
        # General Tool
        # -----------------------------------------------------

        self.add_tool_title = self.make_label(
            "Add General Tool",
            TEXT_COLOR,
            size=15,
            bold=True,
        )

        layout.addWidget(
            self.add_tool_title
        )

        self.add_tool_description = self.make_label(
            "Create a new general tool.",
            MUTED_TEXT,
            size=11,
        )

        layout.addWidget(
            self.add_tool_description
        )

        layout.addSpacing(14)

        self.tool_name_label = self.make_label(
            "Tool Name",
            TEXT_COLOR,
            size=12,
            bold=True,
        )

        layout.addWidget(
            self.tool_name_label
        )

        layout.addSpacing(6)

        self.tool_entry = self.make_line_edit(
            "Enter tool name..."
        )

        layout.addWidget(
            self.tool_entry
        )

        self.add_tool_button = self.make_button(
            "Add Tool",
            ACCENT_COLOR,
            ACCENT_HOVER,
            self.add_tool,
        )

        button_layout = QHBoxLayout()

        button_layout.setContentsMargins(
            0,
            12,
            0,
            0,
        )

        button_layout.addStretch()

        button_layout.addWidget(
            self.add_tool_button
        )

        layout.addLayout(
            button_layout
        )

        layout.addStretch()

    # =========================================================
    # RIGHT = REMOVE
    # =========================================================

    def create_remove_section(
        self,
        parent,
    ):
        self.remove_frame = self.make_card()

        layout = QVBoxLayout(
            self.remove_frame
        )

        layout.setContentsMargins(
            18,
            18,
            18,
            18,
        )

        layout.setSpacing(8)

        # -----------------------------------------------------
        # Brand
        # -----------------------------------------------------

        self.remove_brand_title = self.make_label(
            "Remove Brand",
            TEXT_COLOR,
            size=15,
            bold=True,
        )

        layout.addWidget(
            self.remove_brand_title
        )

        self.remove_brand_description = self.make_label(
            "Select a brand to remove.",
            MUTED_TEXT,
            size=11,
        )

        layout.addWidget(
            self.remove_brand_description
        )

        layout.addSpacing(8)

        self.remove_brand_label = self.make_label(
            "Brand",
            TEXT_COLOR,
            size=12,
            bold=True,
        )

        layout.addWidget(
            self.remove_brand_label
        )

        layout.addSpacing(6)

        self.remove_brand_dropdown = self.make_combo_box()

        layout.addWidget(
            self.remove_brand_dropdown
        )

        self.remove_brand_button = self.make_button(
            "Remove Brand",
            DANGER_COLOR,
            DANGER_HOVER,
            self.remove_brand,
        )

        button_layout = QHBoxLayout()

        button_layout.setContentsMargins(
            0,
            12,
            0,
            24,
        )

        button_layout.addStretch()

        button_layout.addWidget(
            self.remove_brand_button
        )

        layout.addLayout(
            button_layout
        )

        # -----------------------------------------------------
        # General Tool
        # -----------------------------------------------------

        self.remove_tool_title = self.make_label(
            "Remove General Tool",
            TEXT_COLOR,
            size=15,
            bold=True,
        )

        layout.addWidget(
            self.remove_tool_title
        )

        self.remove_tool_description = self.make_label(
            "Select a general tool to remove.",
            MUTED_TEXT,
            size=11,
        )

        layout.addWidget(
            self.remove_tool_description
        )

        layout.addSpacing(14)

        self.remove_tool_label = self.make_label(
            "General Tool",
            TEXT_COLOR,
            size=12,
            bold=True,
        )

        layout.addWidget(
            self.remove_tool_label
        )

        layout.addSpacing(6)

        self.remove_tool_dropdown = self.make_combo_box()

        layout.addWidget(
            self.remove_tool_dropdown
        )

        self.remove_tool_button = self.make_button(
            "Remove Tool",
            DANGER_COLOR,
            DANGER_HOVER,
            self.remove_tool,
        )

        button_layout = QHBoxLayout()

        button_layout.setContentsMargins(
            0,
            12,
            0,
            0,
        )

        button_layout.addStretch()

        button_layout.addWidget(
            self.remove_tool_button
        )

        layout.addLayout(
            button_layout
        )

        layout.addStretch()

    # =========================================================
    # BRAND MANAGEMENT
    # =========================================================

    def add_brand(self):
        brand_name = (
            self.brand_name_entry
            .text()
            .strip()
        )

        if not brand_name:
            return

        for existing in self.brands:
            if (
                existing.casefold()
                == brand_name.casefold()
            ):
                QMessageBox.warning(
                    self.parent,
                    "Brand Exists",
                    f"{brand_name} already exists.",
                )
                return

        self.brands[brand_name] = [
            brand_name
        ]

        self.brand_name_entry.clear()

        self.save_brands()
        self.refresh_brand_dropdown()
        self.notify_brands_changed()

    def remove_brand(self):
        index = (
            self.remove_brand_dropdown
            .currentIndex()
        )

        if index < 0:
            QMessageBox.warning(
                self.parent,
                "Select Brand",
                "Select a brand to remove.",
            )
            return

        brand_name = (
            self.remove_brand_dropdown
            .currentText()
        )

        if not brand_name:
            QMessageBox.warning(
                self.parent,
                "Select Brand",
                "Select a brand to remove.",
            )
            return

        answer = QMessageBox.question(
            self.parent,
            "Remove Brand",
            f"Remove '{brand_name}'?",
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        del self.brands[brand_name]

        self.save_brands()
        self.refresh_brand_dropdown()
        self.notify_brands_changed()

    def refresh_brand_dropdown(self):
        brand_names = sorted(
            self.brands.keys(),
            key=str.casefold,
        )

        self.remove_brand_dropdown.blockSignals(
            True
        )

        self.remove_brand_dropdown.clear()

        self.remove_brand_dropdown.addItems(
            brand_names
        )

        self.remove_brand_dropdown.blockSignals(
            False
        )

    def save_brands(self):
        try:
            os.makedirs(
                self.SETTINGS_DIR,
                exist_ok=True,
            )

            with open(
                self.BRANDS_FILE,
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    self.brands,
                    file,
                    indent=4,
                )

        except OSError as error:
            QMessageBox.critical(
                self.parent,
                "Save Error",
                (
                    "Could not save brand "
                    f"settings:\n{error}"
                ),
            )

    @classmethod
    def load_brands(cls):
        if not os.path.exists(
            cls.BRANDS_FILE
        ):
            try:
                os.makedirs(
                    cls.SETTINGS_DIR,
                    exist_ok=True,
                )

                with open(
                    cls.BRANDS_FILE,
                    "w",
                    encoding="utf-8",
                ) as file:
                    json.dump(
                        cls.DEFAULT_BRANDS,
                        file,
                        indent=4,
                    )

                return copy.deepcopy(
                    cls.DEFAULT_BRANDS
                )

            except OSError:
                return copy.deepcopy(
                    cls.DEFAULT_BRANDS
                )

        try:
            with open(
                cls.BRANDS_FILE,
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

            if not isinstance(
                data,
                dict,
            ):
                return copy.deepcopy(
                    cls.DEFAULT_BRANDS
                )

            normalized_brands = {}

            for brand_name in data.keys():
                if not isinstance(
                    brand_name,
                    str,
                ):
                    continue

                brand_name = brand_name.strip()

                if not brand_name:
                    continue

                normalized_brands[
                    brand_name
                ] = [brand_name]

            if not normalized_brands:
                return copy.deepcopy(
                    cls.DEFAULT_BRANDS
                )

            return normalized_brands

        except (
            OSError,
            json.JSONDecodeError,
            TypeError,
            ValueError,
        ):
            return copy.deepcopy(
                cls.DEFAULT_BRANDS
            )

    # =========================================================
    # TOOL MANAGEMENT
    # =========================================================

    def add_tool(self):
        tool_name = (
            self.tool_entry
            .text()
            .strip()
            .title()
        )

        if (
            not tool_name
            or tool_name == "Na"
        ):
            QMessageBox.warning(
                self.parent,
                "Invalid Tool Name",
                (
                    "The reserved NA entry "
                    "cannot be added as a tool."
                ),
            )
            return

        if any(
            existing.casefold()
            == tool_name.casefold()
            for existing in self.tools
        ):
            QMessageBox.warning(
                self.parent,
                "Tool Exists",
                f"{tool_name} already exists.",
            )
            return

        self.tools[tool_name] = ["NA"]

        self.tool_entry.clear()

        self.save_tools()
        self.refresh_tool_dropdown()
        self.notify_tools_changed()

    def remove_tool(self):
        index = (
            self.remove_tool_dropdown
            .currentIndex()
        )

        if index < 0:
            QMessageBox.warning(
                self.parent,
                "Select Tool",
                "Select a general tool to remove.",
            )
            return

        tool_name = (
            self.remove_tool_dropdown
            .currentText()
        )

        if not tool_name:
            QMessageBox.warning(
                self.parent,
                "Select Tool",
                "Select a general tool to remove.",
            )
            return

        answer = QMessageBox.question(
            self.parent,
            "Remove Tool",
            (
                f"Remove '{tool_name}'?\n\n"
                "This will also remove all of "
                "its sizes."
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        del self.tools[tool_name]

        if not self.tools:
            self.tools = {
                "NA": ["NA"]
            }

        self.save_tools()
        self.refresh_tool_dropdown()
        self.notify_tools_changed()

    def refresh_tool_dropdown(self):
        tool_names = sorted(
            [
                name
                for name in self.tools.keys()
                if name != "NA"
            ],
            key=str.casefold,
        )

        self.remove_tool_dropdown.blockSignals(
            True
        )

        self.remove_tool_dropdown.clear()

        self.remove_tool_dropdown.addItems(
            tool_names
        )

        self.remove_tool_dropdown.blockSignals(
            False
        )

    def save_tools(self):
        if not ToolRepository.save_tools(
            self.tools
        ):
            QMessageBox.critical(
                self.parent,
                "Save Error",
                "Could not save tool settings.",
            )

    # =========================================================
    # CHANGE NOTIFICATION
    # =========================================================

    def notify_tools_changed(self):
        if self.on_tools_changed:
            self.on_tools_changed()

    def notify_brands_changed(self):
        if self.on_brands_changed:
            self.on_brands_changed()

    # =========================================================
    # GENERAL SIZE PERSISTENCE
    # =========================================================

    @classmethod
    def load_sizes_data(cls):
        default_sizes = {
            "SAE": list(
                DEFAULT_SAE_SIZES
            ),
            "Metric": list(
                DEFAULT_METRIC_SIZES
            ),
            "Other": list(
                DEFAULT_OTHER
            ),
            "DUAL": [],
        }

        if not os.path.exists(
            cls.SIZES_FILE
        ):
            return default_sizes

        try:
            with open(
                cls.SIZES_FILE,
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

            return {
                "SAE": data.get(
                    "SAE",
                    list(DEFAULT_SAE_SIZES),
                ),
                "Metric": data.get(
                    "Metric",
                    list(DEFAULT_METRIC_SIZES),
                ),
                "Other": data.get(
                    "Other",
                    list(DEFAULT_OTHER),
                ),
                "DUAL": data.get(
                    "DUAL",
                    [],
                ),
            }

        except (
            OSError,
            json.JSONDecodeError,
        ):
            return default_sizes

    @classmethod
    def save_sizes_data(
        cls,
        sizes,
    ):
        try:
            with open(
                cls.SIZES_FILE,
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    sizes,
                    file,
                    indent=4,
                )

            return True

        except OSError:
            return False
