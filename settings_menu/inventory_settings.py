import json
import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QComboBox,
    QLineEdit,
    QPushButton,
    QFrame,
    QScrollArea,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QMessageBox,
    QSizePolicy,
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


SETTINGS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "settings",
)

INVENTORY_FILE = os.path.join(
    SETTINGS_DIR,
    "inventory_settings.json",
)

DEFAULT_INVENTORY = {
    "Socket": 8.0,
    "Adapter": 7.0,
    "Crowfoot": 12.0,
    "Extension": 8.0,
    "Wrench": 10.0,
    "Pliers": 12.0,
    "Brake Tool": 15.0,
    "Screwdriver": 8.0,
    "Breaker Bar": 20.0,
    "Ratchet": 20.0,
    "Punch": 8.0,
    "Feeler Gauge": 7.00,
    "Tool Holder": 8.00,
    "Torque Wrench": 50,
    "Allen Key": 6.0,
    "Torx Key": 7.0,
    "Hammer": 15.0,
    "Pick": 7.0,
}


# =========================================================
# Layout / Spacing
# =========================================================

SPACE_1 = 2
SPACE_2 = 4
SPACE_3 = 6
SPACE_4 = 8
SPACE_5 = 10
SPACE_6 = 12
SPACE_7 = 15
SPACE_8 = 18
SPACE_9 = 20
SPACE_10 = 24

PAGE_PADDING = SPACE_2

SECTION_SPACING = SPACE_2
CONTROL_SPACING = SPACE_2
CONTROL_VERTICAL_SPACING = SPACE_3

HEADER_SPACING = SPACE_4
DESCRIPTION_SPACING = SPACE_4

CARD_PADDING = SPACE_2

LIST_PADDING = SPACE_2
LIST_OUTER_SPACING = SPACE_2

BUTTON_PADDING = SPACE_3
BUTTON_LIST_SPACING = SPACE_2


class InventorySettings(QWidget):

    def __init__(
        self,
        parent,
        tools,
        on_inventory_changed=None,
    ):
        super().__init__(parent)

        self.parent = parent
        self.tools = tools
        self.on_inventory_changed = on_inventory_changed

        self.inventory = self.load_inventory()

        self._value_buttons = {}
        self.selected_tool = None

        self.appearance_mode = getattr(
            parent,
            "appearance_mode",
            "Dark",
        )

        self.create_gui()

    # =========================================================
    # Persistence
    # =========================================================

    @staticmethod
    def load_inventory():
        os.makedirs(
            SETTINGS_DIR,
            exist_ok=True,
        )

        default_inventory = {
            "estimated_values": DEFAULT_INVENTORY.copy()
        }

        if not os.path.exists(INVENTORY_FILE):
            InventorySettings.save_inventory(
                default_inventory
            )
            return default_inventory

        try:
            with open(
                INVENTORY_FILE,
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

        except (
            json.JSONDecodeError,
            OSError,
        ):
            data = {}

        saved_values = data.get(
            "estimated_values",
            {},
        )

        if not isinstance(
            saved_values,
            dict,
        ):
            saved_values = {}

        estimated_values = DEFAULT_INVENTORY.copy()
        estimated_values.update(saved_values)

        inventory = {
            "estimated_values": estimated_values
        }

        InventorySettings.save_inventory(
            inventory
        )

        return inventory

    @staticmethod
    def save_inventory(inventory):
        os.makedirs(
            SETTINGS_DIR,
            exist_ok=True,
        )

        with open(
            INVENTORY_FILE,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                inventory,
                file,
                indent=4,
            )

    def on_tools_changed(self):
        self.refresh_tool_dropdown()

    # =========================================================
    # GUI
    # =========================================================

    def create_gui(self):
        main_layout = QVBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            PAGE_PADDING,
            PAGE_PADDING,
            PAGE_PADDING,
            PAGE_PADDING,
        )

        main_layout.setSpacing(0)

        # -----------------------------------------------------
        # Title
        # -----------------------------------------------------

        self.title_label = QLabel(
            "Estimated Tool Values"
        )

        self.title_label.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT_COLOR[1]};
                font-size: 15px;
                font-weight: 700;
            }}
            """
        )

        main_layout.addWidget(
            self.title_label
        )

        main_layout.addSpacing(
            HEADER_SPACING
        )

        # -----------------------------------------------------
        # Description
        # -----------------------------------------------------

        self.description_label = QLabel(
            "Set the estimated value for each tool type. "
            "These values are used when calculating the "
            "estimated value of purchased invoices."
        )

        self.description_label.setWordWrap(True)

        self.description_label.setMaximumWidth(
            650
        )

        self.description_label.setStyleSheet(
            f"""
            QLabel {{
                color: {MUTED_TEXT[1]};
                font-size: 11px;
            }}
            """
        )

        main_layout.addWidget(
            self.description_label
        )

        main_layout.addSpacing(
            DESCRIPTION_SPACING
        )

        self.create_estimated_value_editor(
            self,
            main_layout,
        )

    # =========================================================
    # Estimated Value Editor
    # =========================================================

    def create_estimated_value_editor(
        self,
        parent,
        main_layout,
    ):
        frame = QFrame(parent)

        frame.setObjectName(
            "inventoryCard"
        )

        frame.setStyleSheet(
            f"""
            QFrame#inventoryCard {{
                background-color: {CARD_BG[1]};
                border: 1px solid {BORDER_COLOR[1]};
                border-radius: 10px;
            }}
            """
        )

        main_layout.addWidget(
            frame,
            1,
        )

        content = QGridLayout(frame)

        content.setContentsMargins(
            CARD_PADDING,
            CARD_PADDING,
            CARD_PADDING,
            CARD_PADDING,
        )

        content.setHorizontalSpacing(
            CONTROL_SPACING
        )

        content.setVerticalSpacing(
            CONTROL_VERTICAL_SPACING
        )

        content.setColumnStretch(
            0,
            1,
        )

        content.setColumnStretch(
            1,
            1,
        )

        content.setRowStretch(
            3,
            1,
        )

        # -----------------------------------------------------
        # Header
        # -----------------------------------------------------

        header_label = QLabel(
            "Estimated Value by Tool Type"
        )

        header_label.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT_COLOR[1]};
                font-size: 13px;
                font-weight: 700;
                border: none;
            }}
            """
        )

        content.addWidget(
            header_label,
            0,
            0,
            1,
            3,
        )

        # -----------------------------------------------------
        # Input Labels
        # -----------------------------------------------------

        tool_type_label = QLabel(
            "Tool Type"
        )

        tool_type_label.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT_COLOR[1]};
                font-size: 11px;
                font-weight: 700;
                border: none;
            }}
            """
        )

        content.addWidget(
            tool_type_label,
            1,
            0,
        )

        estimated_value_label = QLabel(
            "Estimated Value"
        )

        estimated_value_label.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT_COLOR[1]};
                font-size: 11px;
                font-weight: 700;
                border: none;
            }}
            """
        )

        content.addWidget(
            estimated_value_label,
            1,
            1,
        )

        # -----------------------------------------------------
        # Tool Dropdown
        # -----------------------------------------------------

        self.tool_dropdown = QComboBox()

        self.tool_dropdown.setEditable(
            False
        )

        self.tool_dropdown.setFixedHeight(
            38
        )

        self.tool_dropdown.setStyleSheet(
            self.get_combo_box_style()
        )

        content.addWidget(
            self.tool_dropdown,
            2,
            0,
        )

        # -----------------------------------------------------
        # Value Entry
        # -----------------------------------------------------

        self.value_entry = QLineEdit()

        self.value_entry.setPlaceholderText(
            "Enter value..."
        )

        self.value_entry.setFixedHeight(
            38
        )

        self.value_entry.setStyleSheet(
            self.get_line_edit_style()
        )

        content.addWidget(
            self.value_entry,
            2,
            1,
        )

        # -----------------------------------------------------
        # Add / Update
        # -----------------------------------------------------

        self.update_button = QPushButton(
            "Add / Update"
        )

        self.update_button.setFixedSize(
            120,
            38,
        )

        self.update_button.setCursor(
            Qt.PointingHandCursor
        )

        self.update_button.setStyleSheet(
            self.get_button_style(
                ACCENT_COLOR,
                ACCENT_HOVER,
                WHITE_TEXT,
            )
        )

        self.update_button.clicked.connect(
            self.add_or_update_value
        )

        content.addWidget(
            self.update_button,
            2,
            2,
        )

        # -----------------------------------------------------
        # Values List
        # -----------------------------------------------------

        list_frame = QFrame()

        list_frame.setObjectName(
            "valuesListFrame"
        )

        list_frame.setStyleSheet(
            f"""
            QFrame#valuesListFrame {{
                background-color: {INPUT_BG[1]};
                border: 1px solid {BORDER_COLOR[1]};
                border-radius: 6px;
            }}
            """
        )

        content.addWidget(
            list_frame,
            3,
            0,
            1,
            2,
        )

        list_layout = QVBoxLayout(
            list_frame
        )

        list_layout.setContentsMargins(
            LIST_PADDING,
            LIST_PADDING,
            LIST_PADDING,
            LIST_PADDING,
        )

        self.values_scroll_area = QScrollArea()

        self.values_scroll_area.setWidgetResizable(
            True
        )

        self.values_scroll_area.setFrameShape(
            QFrame.NoFrame
        )

        self.values_scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.values_scroll_area.setStyleSheet(
            """
            QScrollArea {
                background: transparent;
                border: none;
            }
            """
        )

        list_layout.addWidget(
            self.values_scroll_area
        )

        self.values_scroll_widget = QWidget()

        self.values_scroll_layout = QVBoxLayout(
            self.values_scroll_widget
        )

        self.values_scroll_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.values_scroll_layout.setSpacing(
            BUTTON_LIST_SPACING
        )

        self.values_scroll_layout.addStretch()

        self.values_scroll_area.setWidget(
            self.values_scroll_widget
        )

        # -----------------------------------------------------
        # Remove
        # -----------------------------------------------------

        self.remove_button = QPushButton(
            "Remove"
        )

        self.remove_button.setFixedSize(
            100,
            36,
        )

        self.remove_button.setCursor(
            Qt.PointingHandCursor
        )

        self.remove_button.setStyleSheet(
            self.get_button_style(
                DANGER_COLOR,
                DANGER_HOVER,
                WHITE_TEXT,
            )
        )

        self.remove_button.clicked.connect(
            self.remove_value
        )

        content.addWidget(
            self.remove_button,
            3,
            2,
            alignment=Qt.AlignTop,
        )

        self.refresh_tool_dropdown()
        self.refresh_values_list()

    # =========================================================
    # Styles
    # =========================================================

    def get_color(self, color):
        return (
            color[0]
            if self.appearance_mode == "Light"
            else color[1]
        )

    def get_combo_box_style(self):
        input_bg = self.get_color(INPUT_BG)
        text = self.get_color(TEXT_COLOR)
        border = self.get_color(BORDER_COLOR)
        accent = self.get_color(ACCENT_COLOR)
        panel_bg = self.get_color(PANEL_BG)
        hover = self.get_color(CARD_HOVER)

        return f"""
        QComboBox {{
            background-color: {input_bg};
            color: {text};
            border: 1px solid {border};
            border-radius: 6px;
            padding: 0 10px;
            font-size: 11px;
        }}

        QComboBox:hover {{
            border-color: {accent};
        }}

        QComboBox:focus {{
            border-color: {accent};
        }}

        QComboBox::drop-down {{
            border: none;
            width: 28px;
        }}

        QComboBox QAbstractItemView {{
            background-color: {panel_bg};
            color: {text};
            border: 1px solid {border};
            selection-background-color: {hover};
            selection-color: {text};
            padding: 4px;
        }}
        """

    def get_line_edit_style(self):
        input_bg = self.get_color(INPUT_BG)
        text = self.get_color(TEXT_COLOR)
        border = self.get_color(BORDER_COLOR)
        accent = self.get_color(ACCENT_COLOR)
        muted = self.get_color(MUTED_TEXT)

        return f"""
        QLineEdit {{
            background-color: {input_bg};
            color: {text};
            border: 1px solid {border};
            border-radius: 6px;
            padding: 0 10px;
            font-size: 11px;
        }}

        QLineEdit:hover {{
            border-color: {accent};
        }}

        QLineEdit:focus {{
            border-color: {accent};
        }}

        QLineEdit::placeholder {{
            color: {muted};
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
            font-size: 11px;
            font-weight: 700;
        }}

        QPushButton:hover {{
            background-color: {self.get_color(hover)};
        }}

        QPushButton:pressed {{
            background-color: {self.get_color(background)};
        }}
        """

    def get_value_button_style(
        self,
        selected,
    ):
        if selected:
            background = ACCENT_COLOR
            hover = ACCENT_HOVER
            text = WHITE_TEXT

        else:
            background = INPUT_BG
            hover = CARD_HOVER
            text = TEXT_COLOR

        return f"""
        QPushButton {{
            background-color: {self.get_color(background)};
            color: {self.get_color(text)};
            border: none;
            border-radius: 5px;
            padding-left: 10px;
            text-align: left;
            font-size: 11px;
        }}

        QPushButton:hover {{
            background-color: {self.get_color(hover)};
        }}
        """

    def update_appearance(self, mode):
        self.appearance_mode = mode

        if hasattr(self, "title_label"):
            self.title_label.setStyleSheet(
                f"""
                QLabel {{
                    color: {self.get_color(TEXT_COLOR)};
                    font-size: 15px;
                    font-weight: 700;
                }}
                """
            )

        if hasattr(self, "description_label"):
            self.description_label.setStyleSheet(
                f"""
                QLabel {{
                    color: {self.get_color(MUTED_TEXT)};
                    font-size: 11px;
                }}
                """
            )

        if hasattr(self, "tool_dropdown"):
            self.tool_dropdown.setStyleSheet(
                self.get_combo_box_style()
            )

        if hasattr(self, "value_entry"):
            self.value_entry.setStyleSheet(
                self.get_line_edit_style()
            )

        if hasattr(self, "update_button"):
            self.update_button.setStyleSheet(
                self.get_button_style(
                    ACCENT_COLOR,
                    ACCENT_HOVER,
                    WHITE_TEXT,
                )
            )

        if hasattr(self, "remove_button"):
            self.remove_button.setStyleSheet(
                self.get_button_style(
                    DANGER_COLOR,
                    DANGER_HOVER,
                    WHITE_TEXT,
                )
            )

        if hasattr(self, "values_scroll_area"):
            self.values_scroll_area.setStyleSheet(
                """
                QScrollArea {
                    background: transparent;
                    border: none;
                }
                """
            )

        inventory_card = self.findChild(
            QFrame,
            "inventoryCard",
        )

        if inventory_card:
            inventory_card.setStyleSheet(
                f"""
                QFrame#inventoryCard {{
                    background-color: {self.get_color(CARD_BG)};
                    border: 1px solid {self.get_color(BORDER_COLOR)};
                    border-radius: 10px;
                }}
                """
            )

        values_list = self.findChild(
            QFrame,
            "valuesListFrame",
        )

        if values_list:
            values_list.setStyleSheet(
                f"""
                QFrame#valuesListFrame {{
                    background-color: {self.get_color(INPUT_BG)};
                    border: 1px solid {self.get_color(BORDER_COLOR)};
                    border-radius: 6px;
                }}
                """
            )

        self.refresh_values_list()

    # =========================================================
    # Dropdown Behavior
    # =========================================================

    def _make_dropdown_clickable(
        self,
        dropdown,
    ):
        return

    # =========================================================
    # Tool List
    # =========================================================

    def refresh_tool_dropdown(self):
        if hasattr(
            self.tools,
            "tools",
        ):
            tools = list(
                self.tools.tools
            )

        elif isinstance(
            self.tools,
            dict,
        ):
            tools = list(
                self.tools.keys()
            )

        elif isinstance(
            self.tools,
            (list, tuple),
        ):
            tools = list(
                self.tools
            )

        else:
            tools = []

        tools = [
            str(tool)
            for tool in tools
            if tool
        ]

        tools.sort(
            key=str.casefold
        )

        current_tool = (
            self.tool_dropdown.currentText()
        )

        self.tool_dropdown.blockSignals(
            True
        )

        self.tool_dropdown.clear()
        self.tool_dropdown.addItems(
            tools
        )

        if current_tool in tools:
            self.tool_dropdown.setCurrentText(
                current_tool
            )

        elif tools:
            self.tool_dropdown.setCurrentIndex(
                0
            )

        self.tool_dropdown.blockSignals(
            False
        )

    # =========================================================
    # Estimated Values
    # =========================================================

    def add_or_update_value(self):
        tool = (
            self.tool_dropdown
            .currentText()
            .strip()
        )

        value = (
            self.value_entry
            .text()
            .strip()
        )

        if not tool:
            QMessageBox.warning(
                self.parent,
                "Missing Tool Type",
                "Select a tool type.",
            )
            return

        try:
            numeric_value = float(value)

        except ValueError:
            QMessageBox.warning(
                self.parent,
                "Invalid Value",
                "Estimated value must be a number.",
            )
            return

        if numeric_value < 0:
            QMessageBox.warning(
                self.parent,
                "Invalid Value",
                "Estimated value cannot be negative.",
            )
            return

        self.inventory[
            "estimated_values"
        ][tool] = numeric_value

        self.save_and_notify()

        self.selected_tool = None

        self.value_entry.clear()

        self.refresh_values_list()

    # =========================================================
    # Remove Value
    # =========================================================

    def remove_value(self):
        tool = self.selected_tool

        if not tool:
            return

        if tool in self.inventory[
            "estimated_values"
        ]:
            del self.inventory[
                "estimated_values"
            ][tool]

        self.selected_tool = None

        self.save_and_notify()

        self.value_entry.clear()

        self.refresh_values_list()

    # =========================================================
    # Value Selection
    # =========================================================

    def on_value_selected(
        self,
        tool,
    ):
        if not tool:
            return

        self.selected_tool = tool

        value = self.inventory[
            "estimated_values"
        ].get(
            tool,
            "",
        )

        self.tool_dropdown.setCurrentText(
            tool
        )

        self.value_entry.setText(
            str(value)
        )

        self._update_selected_value_button()

    # =========================================================
    # Values List
    # =========================================================

    def refresh_values_list(self):
        if not hasattr(
            self,
            "values_scroll_layout",
        ):
            return

        while (
            self.values_scroll_layout.count()
            > 1
        ):
            item = (
                self.values_scroll_layout.takeAt(
                    0
                )
            )

            widget = item.widget()

            if widget:
                widget.deleteLater()

        self._value_buttons.clear()

        for tool, value in sorted(
            self.inventory[
                "estimated_values"
            ].items(),
            key=lambda item: item[0].casefold(),
        ):
            selected = (
                tool == self.selected_tool
            )

            button = QPushButton(
                f"{tool} = ${value:.2f}"
            )

            button.setFixedHeight(
                34
            )

            button.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Fixed,
            )

            button.setCursor(
                Qt.PointingHandCursor
            )

            button.setStyleSheet(
                self.get_value_button_style(
                    selected
                )
            )

            button.clicked.connect(
                lambda checked=False,
                name=tool:
                self.on_value_selected(name)
            )

            self.values_scroll_layout.insertWidget(
                self.values_scroll_layout.count() - 1,
                button,
            )

            self._value_buttons[
                tool
            ] = button

        self._update_selected_value_button()

    def _update_selected_value_button(self):
        for tool, button in (
            self._value_buttons.items()
        ):
            selected = (
                tool == self.selected_tool
            )

            try:
                button.setStyleSheet(
                    self.get_value_button_style(
                        selected
                    )
                )

            except RuntimeError:
                pass

    # =========================================================
    # Notifications
    # =========================================================

    def save_and_notify(self):
        self.save_inventory(
            self.inventory
        )

        if self.on_inventory_changed:
            self.on_inventory_changed()