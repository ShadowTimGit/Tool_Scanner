
import json
import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QLabel,
)

from GUI.appearance_controller import (
    CARD_BG,
    CARD_HOVER,
    INPUT_BG,
    BORDER_COLOR,
    TEXT_COLOR,
    MUTED_TEXT,
    WHITE_TEXT,
    ACCENT_COLOR,
    ACCENT_HOVER,
)

from settings_menu.settings_config import (
    DEFAULT_METADATA,
)


# =========================================================
# SETTINGS PATHS
# =========================================================

SETTINGS_DIR = os.path.join(
    "settings_menu",
    "settings",
)

METADATA_FILE = os.path.join(
    SETTINGS_DIR,
    "metadata.json",
)


# =========================================================
# UI SIZING
# =========================================================

SETTINGS_OUTER_PADDING = 8

CARD_GAP = 6
CARD_PADDING = 8

HEADER_BOTTOM_GAP = 0
HEADER_DESCRIPTION_GAP = 0
CARD_TITLE_BOTTOM_GAP = 2

LIST_HEIGHT = 150
LIST_ENTRY_HEIGHT = 20
LIST_ENTRY_X_PADDING = 2
LIST_ENTRY_Y_PADDING = 1

CONTROL_TOP_GAP = 5

INPUT_HEIGHT = 30
BUTTON_HEIGHT = 30
BUTTON_WIDTH = 65
BUTTON_GAP = 3

DROPDOWN_HEIGHT = 30
DROPDOWN_BOTTOM_GAP = 5

BORDER_RADIUS = 6
CONTROL_RADIUS = 4

LIST_COLUMNS = 2


# =========================================================
# UI TEXT SIZES
# =========================================================

HEADER_TEXT_SIZE = 12
HEADER_DESCRIPTION_TEXT_SIZE = 12

CARD_TITLE_TEXT_SIZE = 12

LIST_TEXT_SIZE = 12
BUTTON_TEXT_SIZE = 12


# =========================================================
# TWO-COLUMN SELECTABLE LIST
# =========================================================

class SelectableList(QTableWidget):
    """
    Simple two-column selectable list.

    Supports:
        insert()
        delete()
        get()
        curselection()
        select_item()
        refresh()
        update_appearance()
    """

    def __init__(
        self,
        parent=None,
        height=LIST_HEIGHT,
    ):
        super().__init__(
            parent,
        )

        self.items = []
        self.selected_index = None
        self.appearance_mode = "Dark"

        self.setColumnCount(
            LIST_COLUMNS
        )

        self.setRowCount(0)

        self.setMinimumHeight(
            height
        )

        self.horizontalHeader().setVisible(
            False
        )

        self.verticalHeader().setVisible(
            False
        )

        self.horizontalHeader().setStretchLastSection(
            True
        )

        self.setShowGrid(
            False
        )

        self.setSelectionMode(
            QTableWidget.SingleSelection
        )

        self.setSelectionBehavior(
            QTableWidget.SelectItems
        )

        self.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        self.setFocusPolicy(
            Qt.StrongFocus
        )

        self.update_appearance(
            self.appearance_mode
        )

        self.cellClicked.connect(
            self._on_cell_clicked
        )

    # ---------------------------------------------------------
    # Theme
    # ---------------------------------------------------------

    def get_color(self, color):
        return (
            color[0]
            if self.appearance_mode == "Light"
            else color[1]
        )

    def update_appearance(self, mode):
        self.appearance_mode = mode

        self.setStyleSheet(
            f"""
            QTableWidget {{
                background-color: {self.get_color(INPUT_BG)};
                border: 1px solid {self.get_color(BORDER_COLOR)};
                border-radius: {CONTROL_RADIUS}px;
                gridline-color: transparent;
                outline: none;
            }}

            QTableWidget::item {{
                background-color: transparent;
                color: {self.get_color(TEXT_COLOR)};
                border: none;
                padding: 1px 2px;
                min-height: {LIST_ENTRY_HEIGHT}px;
            }}

            QTableWidget::item:hover {{
                background-color: {self.get_color(CARD_HOVER)};
            }}

            QTableWidget::item:selected {{
                background-color: {self.get_color(ACCENT_COLOR)};
                color: {self.get_color(WHITE_TEXT)};
            }}

            QScrollBar:vertical {{
                width: 8px;
                background: transparent;
            }}

            QScrollBar::handle:vertical {{
                background: {self.get_color(BORDER_COLOR)};
                border-radius: 4px;
                min-height: 20px;
            }}

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            """
        )

        self.viewport().update()
        self.update()

    # ---------------------------------------------------------
    # Selection
    # ---------------------------------------------------------

    def _on_cell_clicked(
        self,
        row,
        column,
    ):
        index = (
            row * LIST_COLUMNS
            + column
        )

        if index >= len(self.items):
            return

        self.selected_index = index

    def select_item(
        self,
        index,
    ):
        index = int(index)

        if not (
            0 <= index < len(self.items)
        ):
            return

        self.selected_index = index

        row = index // LIST_COLUMNS
        column = index % LIST_COLUMNS

        self.setCurrentCell(
            row,
            column,
        )

    # ---------------------------------------------------------
    # Insert
    # ---------------------------------------------------------

    def insert(
        self,
        index,
        value,
    ):
        if index == "end":
            self.items.append(
                value
            )
        else:
            self.items.insert(
                int(index),
                value,
            )

        self.refresh()

    # ---------------------------------------------------------
    # Delete
    # ---------------------------------------------------------

    def delete(
        self,
        index,
    ):
        if not self.items:
            return

        if index == "end":
            index = len(self.items) - 1

        index = int(index)

        if 0 <= index < len(
            self.items
        ):
            del self.items[index]

        self.selected_index = None

        self.refresh()

    # ---------------------------------------------------------
    # Get
    # ---------------------------------------------------------

    def get(
        self,
        index,
    ):
        if not self.items:
            return ""

        if index == "end":
            index = len(self.items) - 1

        index = int(index)

        if 0 <= index < len(
            self.items
        ):
            return self.items[index]

        return ""

    # ---------------------------------------------------------
    # Current Selection
    # ---------------------------------------------------------

    def curselection(self):
        if self.selected_index is None:
            return ()

        return (
            self.selected_index,
        )

    # ---------------------------------------------------------
    # Refresh
    # ---------------------------------------------------------

    def refresh(self):
        self.blockSignals(
            True
        )

        self.clearContents()

        row_count = (
            (
                len(self.items)
                + LIST_COLUMNS
                - 1
            )
            // LIST_COLUMNS
        )

        self.setRowCount(
            row_count
        )

        for index, value in enumerate(
            self.items
        ):
            row = (
                index
                // LIST_COLUMNS
            )

            column = (
                index
                % LIST_COLUMNS
            )

            item = QTableWidgetItem(
                str(value)
            )

            item.setTextAlignment(
                Qt.AlignLeft
                | Qt.AlignVCenter
            )

            self.setItem(
                row,
                column,
                item,
            )

        for row in range(
            row_count
        ):
            self.setRowHeight(
                row,
                LIST_ENTRY_HEIGHT,
            )

        self.setColumnWidth(
            0,
            max(
                1,
                self.viewport().width()
                // LIST_COLUMNS,
            ),
        )

        self.setColumnWidth(
            1,
            max(
                1,
                self.viewport().width()
                // LIST_COLUMNS,
            ),
        )

        self.blockSignals(
            False
        )

        if (
            self.selected_index
            is not None
            and self.selected_index
            < len(self.items)
        ):
            row = (
                self.selected_index
                // LIST_COLUMNS
            )

            column = (
                self.selected_index
                % LIST_COLUMNS
            )

            self.setCurrentCell(
                row,
                column,
            )

    # ---------------------------------------------------------
    # Resize
    # ---------------------------------------------------------

    def resizeEvent(
        self,
        event,
    ):
        super().resizeEvent(
            event
        )

        width = (
            self.viewport().width()
            // LIST_COLUMNS
        )

        for column in range(
            LIST_COLUMNS
        ):
            self.setColumnWidth(
                column,
                width,
            )


# =========================================================
# METADATA SETTINGS
# =========================================================

class MetadataSettings(QWidget):

    def __init__(
        self,
        parent=None,
        on_metadata_changed=None,
    ):
        super().__init__(
            parent
        )

        self.on_metadata_changed = (
            on_metadata_changed
        )

        self.appearance_mode = getattr(
            parent,
            "appearance_mode",
            "Dark",
        )

        self.metadata = (
            self.load_metadata()
        )

        self.metadata_cards = []
        self.card_title_labels = []
        self.primary_buttons = []
        self.secondary_buttons = []
        self.entry_widgets = []
        self.selectable_lists = []

        self.header_title = None
        self.header_description = None
        self.size_dataset_dropdown = None

        self.create_gui()

    # =====================================================
    # THEME
    # =====================================================

    def get_color(self, color):
        return (
            color[0]
            if self.appearance_mode == "Light"
            else color[1]
        )

    def update_appearance(self, mode):
        self.appearance_mode = mode

        if self.header_title:
            self.header_title.setStyleSheet(
                f"""
                QLabel {{
                    color: {self.get_color(TEXT_COLOR)};
                    font-size: {HEADER_TEXT_SIZE}px;
                    font-weight: bold;
                    background: transparent;
                }}
                """
            )

        if self.header_description:
            self.header_description.setStyleSheet(
                f"""
                QLabel {{
                    color: {self.get_color(MUTED_TEXT)};
                    font-size: {HEADER_DESCRIPTION_TEXT_SIZE}px;
                    background: transparent;
                }}
                """
            )

        for card in self.metadata_cards:
            card.setStyleSheet(
                f"""
                QFrame#metadataCard {{
                    background-color: {self.get_color(CARD_BG)};
                    border: 1px solid {self.get_color(BORDER_COLOR)};
                    border-radius: {BORDER_RADIUS}px;
                }}
                """
            )

        for label in self.card_title_labels:
            label.setStyleSheet(
                f"""
                QLabel {{
                    color: {self.get_color(TEXT_COLOR)};
                    font-size: {CARD_TITLE_TEXT_SIZE}px;
                    font-weight: bold;
                    background: transparent;
                }}
                """
            )

        if self.size_dataset_dropdown:
            self.size_dataset_dropdown.setStyleSheet(
                self.get_combo_box_style()
            )

        for entry in self.entry_widgets:
            entry.setStyleSheet(
                self.get_entry_style()
            )

        for button in self.primary_buttons:
            button.setStyleSheet(
                self.get_primary_button_style()
            )

        for button in self.secondary_buttons:
            button.setStyleSheet(
                self.get_secondary_button_style()
            )

        for listbox in self.selectable_lists:
            listbox.update_appearance(
                mode
            )

        self.update()

    # =====================================================
    # METADATA LOAD / SAVE
    # =====================================================

    @staticmethod
    def load_metadata():
        os.makedirs(
            SETTINGS_DIR,
            exist_ok=True,
        )

        if not os.path.exists(
            METADATA_FILE
        ):
            return json.loads(
                json.dumps(
                    DEFAULT_METADATA
                )
            )

        try:
            with open(
                METADATA_FILE,
                "r",
                encoding="utf-8",
            ) as file:
                saved_metadata = (
                    json.load(file)
                )

            metadata = json.loads(
                json.dumps(
                    DEFAULT_METADATA
                )
            )

            if isinstance(
                saved_metadata,
                dict,
            ):
                metadata.update(
                    saved_metadata
                )

            if (
                "specialty_socket"
                in DEFAULT_METADATA
            ):
                metadata[
                    "specialty_socket"
                ] = DEFAULT_METADATA[
                    "specialty_socket"
                ]

            return metadata

        except (
            json.JSONDecodeError,
            OSError,
        ):
            return json.loads(
                json.dumps(
                    DEFAULT_METADATA
                )
            )

    def save_metadata(self):
        os.makedirs(
            SETTINGS_DIR,
            exist_ok=True,
        )

        metadata_to_save = (
            json.loads(
                json.dumps(
                    self.metadata
                )
            )
        )

        metadata_to_save.pop(
            "specialty_socket",
            None,
        )

        try:
            with open(
                METADATA_FILE,
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    metadata_to_save,
                    file,
                    indent=4,
                )

            if self.on_metadata_changed:
                self.on_metadata_changed(
                    self.metadata
                )

        except OSError:
            pass

    # =====================================================
    # GUI
    # =====================================================

    def create_gui(self):
        self.main_layout = QGridLayout(self)

        self.main_layout.setContentsMargins(
            SETTINGS_OUTER_PADDING,
            SETTINGS_OUTER_PADDING,
            SETTINGS_OUTER_PADDING,
            SETTINGS_OUTER_PADDING,
        )

        self.main_layout.setHorizontalSpacing(0)
        self.main_layout.setVerticalSpacing(4)

        self.create_header()
        self.create_settings_area()

        self.main_layout.setRowStretch(0, 0)
        self.main_layout.setRowStretch(1, 1)

        self.update_appearance(
            self.appearance_mode
        )

    # =====================================================
    # HEADER
    # =====================================================

    def create_header(self):
        header = QWidget()

        layout = QVBoxLayout(header)

        layout.setContentsMargins(
            0,
            0,
            0,
            2,
        )

        layout.setSpacing(0)

        self.header_title = QLabel(
            "Product Metadata"
        )

        self.header_description = QLabel(
            "Configure product attributes used throughout the application."
        )

        self.header_title.setFixedHeight(20)
        self.header_description.setFixedHeight(18)

        layout.addWidget(
            self.header_title
        )

        layout.addWidget(
            self.header_description
        )

        self.main_layout.addWidget(
            header,
            0,
            0,
        )

    # =====================================================
    # SETTINGS AREA
    # =====================================================

    def create_settings_area(self):
        settings_frame = QWidget()

        layout = QGridLayout(settings_frame)

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.setHorizontalSpacing(
            CARD_GAP
        )

        layout.setVerticalSpacing(
            CARD_GAP
        )

        for column in range(3):
            layout.setColumnStretch(
                column,
                1,
            )

        layout.setRowStretch(
            0,
            1,
        )

        self.create_size_editor(
            settings_frame,
            layout,
            0,
            0,
        )

        self.create_point_editor(
            settings_frame,
            layout,
            0,
            1,
        )

        self.create_drive_editor(
            settings_frame,
            layout,
            0,
            2,
        )

        self.main_layout.addWidget(
            settings_frame,
            1,
            0,
        )
    # =====================================================
    # CARD CREATION
    # =====================================================

    def create_card(
        self,
        parent,
        title,
    ):
        card = QFrame(
            parent
        )

        card.setObjectName(
            "metadataCard"
        )

        layout = QGridLayout(
            card
        )

        layout.setContentsMargins(
            CARD_PADDING,
            6,
            CARD_PADDING,
            CARD_PADDING,
        )


        layout.setVerticalSpacing(
            CARD_TITLE_BOTTOM_GAP
        )

        title_label = QLabel(
            title
        )

        layout.addWidget(
            title_label,
            0,
            0,
        )

        self.metadata_cards.append(
            card
        )

        self.card_title_labels.append(
            title_label
        )

        card.setStyleSheet(
            f"""
            QFrame#metadataCard {{
                background-color: {self.get_color(CARD_BG)};
                border: 1px solid {self.get_color(BORDER_COLOR)};
                border-radius: {BORDER_RADIUS}px;
            }}
            """
        )

        title_label.setStyleSheet(
            f"""
            QLabel {{
                color: {self.get_color(TEXT_COLOR)};
                font-size: {CARD_TITLE_TEXT_SIZE}px;
                font-weight: bold;
                background: transparent;
            }}
            """
        )

        return card, layout

    # =====================================================
    # SIZE EDITOR
    # =====================================================

    def create_size_editor(
        self,
        parent,
        parent_layout,
        row,
        column,
    ):
        card, layout = self.create_card(
            parent,
            "Sizes",
        )

        layout.setRowStretch(
            2,
            1,
        )

        self.size_dataset_dropdown = (
            QComboBox()
        )

        self.size_dataset_dropdown.addItems(
            [
                "SAE",
                "Metric",
                "Other",
            ]
        )

        self.size_dataset_dropdown.setFixedHeight(
            DROPDOWN_HEIGHT
        )

        self.size_dataset_dropdown.setStyleSheet(
            self.get_combo_box_style()
        )

        self.size_dataset_dropdown.currentTextChanged.connect(
            self.on_size_dataset_changed
        )

        self.size_dataset_dropdown.setCurrentText(
            "SAE"
        )

        layout.addWidget(
            self.size_dataset_dropdown,
            1,
            0,
        )

        self.size_list = SelectableList(
            card,
            height=LIST_HEIGHT,
        )

        self.size_list.update_appearance(
            self.appearance_mode
        )

        self.selectable_lists.append(
            self.size_list
        )

        layout.addWidget(
            self.size_list,
            2,
            0,
        )

        controls = QWidget()

        controls_layout = QGridLayout(
            controls
        )

        controls_layout.setContentsMargins(
            0,
            CONTROL_TOP_GAP,
            0,
            0,
        )

        controls_layout.setHorizontalSpacing(
            BUTTON_GAP
        )

        controls_layout.setColumnStretch(
            0,
            1,
        )

        self.size_entry = self.create_entry()

        controls_layout.addWidget(
            self.size_entry,
            0,
            0,
        )

        add_button = self.create_primary_button(
            "Add"
        )

        add_button.clicked.connect(
            self.add_size
        )

        controls_layout.addWidget(
            add_button,
            0,
            1,
        )

        remove_button = self.create_secondary_button(
            "Remove"
        )

        remove_button.clicked.connect(
            self.remove_size
        )

        controls_layout.addWidget(
            remove_button,
            0,
            2,
        )

        layout.addWidget(
            controls,
            3,
            0,
        )

        parent_layout.addWidget(
            card,
            row,
            column,
        )

        self.populate_size_list()

    # =====================================================
    # SIZE DATASET CHANGED
    # =====================================================

    def on_size_dataset_changed(
        self,
        dataset,
    ):
        self.populate_size_list()

    # =====================================================
    # POPULATE SIZE LIST
    # =====================================================

    def populate_size_list(self):
        dataset = (
            self.size_dataset_dropdown.currentText()
        )

        sizes = self.metadata.get(
            "sizes",
            {},
        )

        if not isinstance(
            sizes,
            dict,
        ):
            sizes = {}

        values = sizes.get(
            dataset,
            [],
        )

        self.size_list.items = []
        self.size_list.selected_index = None
        self.size_list.refresh()

        for value in values:
            self.size_list.insert(
                "end",
                value,
            )

    # =====================================================
    # POINT EDITOR
    # =====================================================

    def create_point_editor(
        self,
        parent,
        parent_layout,
        row,
        column,
    ):
        card, layout = self.create_card(
            parent,
            "Point",
        )

        layout.setRowStretch(
            1,
            1,
        )

        self.point_list = SelectableList(
            card,
            height=LIST_HEIGHT,
        )

        self.selectable_lists.append(
            self.point_list
        )

        layout.addWidget(
            self.point_list,
            1,
            0,
        )

        self.populate_list(
            self.point_list,
            self.metadata.get(
                "point",
                [],
            ),
        )

        controls = QWidget()

        controls_layout = QGridLayout(
            controls
        )

        controls_layout.setContentsMargins(
            0,
            CARD_PADDING,
            0,
            0,
        )

        controls_layout.setHorizontalSpacing(
            BUTTON_GAP
        )

        controls_layout.setColumnStretch(
            0,
            1,
        )

        self.point_entry = self.create_entry()

        controls_layout.addWidget(
            self.point_entry,
            0,
            0,
        )

        add_button = self.create_primary_button(
            "Add"
        )

        add_button.clicked.connect(
            self.add_option
        )

        controls_layout.addWidget(
            add_button,
            0,
            1,
        )

        remove_button = self.create_secondary_button(
            "Remove"
        )

        remove_button.clicked.connect(
            self.remove_option
        )

        controls_layout.addWidget(
            remove_button,
            1,
            1,
        )

        layout.addWidget(
            controls,
            2,
            0,
        )

        parent_layout.addWidget(
            card,
            row,
            column,
        )

    # =====================================================
    # DRIVE EDITOR
    # =====================================================

    def create_drive_editor(
        self,
        parent,
        parent_layout,
        row,
        column,
    ):
        card, layout = self.create_card(
            parent,
            "Drive",
        )

        layout.setRowStretch(
            1,
            1,
        )

        self.drive_list = SelectableList(
            card,
            height=LIST_HEIGHT,
        )

        self.selectable_lists.append(
            self.drive_list
        )

        layout.addWidget(
            self.drive_list,
            1,
            0,
        )

        self.populate_list(
            self.drive_list,
            self.metadata.get(
                "drive",
                [],
            ),
        )

        controls = QWidget()

        controls_layout = QGridLayout(
            controls
        )

        controls_layout.setContentsMargins(
            0,
            CARD_PADDING,
            0,
            0,
        )

        controls_layout.setHorizontalSpacing(
            BUTTON_GAP
        )

        controls_layout.setColumnStretch(
            0,
            1,
        )

        self.drive_entry = self.create_entry()

        controls_layout.addWidget(
            self.drive_entry,
            0,
            0,
        )

        add_button = self.create_primary_button(
            "Add"
        )

        add_button.clicked.connect(
            self.add_option
        )

        controls_layout.addWidget(
            add_button,
            0,
            1,
        )

        remove_button = self.create_secondary_button(
            "Remove"
        )

        remove_button.clicked.connect(
            self.remove_option
        )

        controls_layout.addWidget(
            remove_button,
            1,
            1,
        )

        layout.addWidget(
            controls,
            2,
            0,
        )

        parent_layout.addWidget(
            card,
            row,
            column,
        )

    # =====================================================
    # WIDGET STYLES
    # =====================================================

    def get_combo_box_style(self):
        return f"""
        QComboBox {{
            background-color: {self.get_color(INPUT_BG)};
            color: {self.get_color(TEXT_COLOR)};
            border: 1px solid {self.get_color(BORDER_COLOR)};
            border-radius: {CONTROL_RADIUS}px;
            padding: 0 8px;
        }}

        QComboBox:hover {{
            border-color: {self.get_color(ACCENT_COLOR)};
        }}

        QComboBox:focus {{
            border-color: {self.get_color(ACCENT_COLOR)};
        }}

        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}

        QComboBox QAbstractItemView {{
            background-color: {self.get_color(CARD_BG)};
            color: {self.get_color(TEXT_COLOR)};
            border: 1px solid {self.get_color(BORDER_COLOR)};
            selection-background-color: {self.get_color(ACCENT_COLOR)};
            selection-color: {self.get_color(WHITE_TEXT)};
        }}
        """

    def get_entry_style(self):
        return f"""
        QLineEdit {{
            background-color: {self.get_color(INPUT_BG)};
            color: {self.get_color(TEXT_COLOR)};
            border: 1px solid {self.get_color(BORDER_COLOR)};
            border-radius: {CONTROL_RADIUS}px;
            padding: 0 7px;
            selection-background-color: {self.get_color(ACCENT_COLOR)};
            selection-color: {self.get_color(WHITE_TEXT)};
        }}

        QLineEdit:focus {{
            border: 1px solid {self.get_color(ACCENT_COLOR)};
        }}
        """

    def get_primary_button_style(self):
        return f"""
        QPushButton {{
            background-color: {self.get_color(ACCENT_COLOR)};
            color: {self.get_color(WHITE_TEXT)};
            border: none;
            border-radius: {CONTROL_RADIUS}px;
            font-size: {BUTTON_TEXT_SIZE}px;
        }}

        QPushButton:hover {{
            background-color: {self.get_color(ACCENT_HOVER)};
        }}

        QPushButton:pressed {{
            background-color: {self.get_color(ACCENT_COLOR)};
        }}
        """

    def get_secondary_button_style(self):
        return f"""
        QPushButton {{
            background-color: {self.get_color(CARD_BG)};
            color: {self.get_color(TEXT_COLOR)};
            border: 1px solid {self.get_color(BORDER_COLOR)};
            border-radius: {CONTROL_RADIUS}px;
            font-size: {BUTTON_TEXT_SIZE}px;
        }}

        QPushButton:hover {{
            background-color: {self.get_color(CARD_HOVER)};
        }}

        QPushButton:pressed {{
            background-color: {self.get_color(CARD_BG)};
        }}
        """

    # =====================================================
    # WIDGET HELPERS
    # =====================================================

    def create_entry(self):
        entry = QLineEdit()

        entry.setFixedHeight(
            INPUT_HEIGHT
        )

        entry.setStyleSheet(
            self.get_entry_style()
        )

        self.entry_widgets.append(
            entry
        )

        return entry

    def create_primary_button(
        self,
        text,
    ):
        button = QPushButton(
            text
        )

        button.setFixedSize(
            BUTTON_WIDTH,
            BUTTON_HEIGHT,
        )

        button.setStyleSheet(
            self.get_primary_button_style()
        )

        self.primary_buttons.append(
            button
        )

        return button

    def create_secondary_button(
        self,
        text,
    ):
        button = QPushButton(
            text
        )

        button.setFixedSize(
            BUTTON_WIDTH,
            BUTTON_HEIGHT,
        )

        button.setStyleSheet(
            self.get_secondary_button_style()
        )

        self.secondary_buttons.append(
            button
        )

        return button

    # =====================================================
    # LIST HELPERS
    # =====================================================

    def populate_list(
        self,
        listbox,
        values,
    ):
        if not values:
            return

        for value in values:
            listbox.insert(
                "end",
                value,
            )

    # =====================================================
    # SIZE ACTIONS
    # =====================================================

    def add_size(self):
        value = (
            self.size_entry
            .text()
            .strip()
        )

        if not value:
            return

        dataset = (
            self.size_dataset_dropdown.currentText()
        )

        sizes = self.metadata.setdefault(
            "sizes",
            {},
        )

        if not isinstance(
            sizes,
            dict,
        ):
            sizes = {}
            self.metadata[
                "sizes"
            ] = sizes

        values = sizes.setdefault(
            dataset,
            [],
        )

        if value not in values:
            values.append(
                value
            )

            self.size_list.insert(
                "end",
                value,
            )

            self.size_entry.clear()

            self.save_metadata()

    # =====================================================
    # REMOVE SIZE
    # =====================================================

    def remove_size(self):
        selection = (
            self.size_list.curselection()
        )

        if not selection:
            return

        index = selection[0]

        dataset = (
            self.size_dataset_dropdown.currentText()
        )

        sizes = self.metadata.get(
            "sizes",
            {},
        )

        if not isinstance(
            sizes,
            dict,
        ):
            return

        values = sizes.get(
            dataset,
            [],
        )

        if 0 <= index < len(
            values
        ):
            values.pop(
                index
            )

            self.size_list.delete(
                index
            )

            self.save_metadata()

    # =====================================================
    # OPTION ACTIONS
    # =====================================================

    def add_option(self):
        focused = self.focusWidget()

        value = ""
        metadata_key = None
        listbox = None
        entry = None

        if focused is self.point_entry:
            value = (
                self.point_entry
                .text()
                .strip()
            )

            metadata_key = "point"
            listbox = self.point_list
            entry = self.point_entry

        elif focused is self.drive_entry:
            value = (
                self.drive_entry
                .text()
                .strip()
            )

            metadata_key = "drive"
            listbox = self.drive_list
            entry = self.drive_entry

        else:
            return

        if not value:
            return

        values = self.metadata.setdefault(
            metadata_key,
            [],
        )

        if value not in values:
            values.append(
                value
            )

            listbox.insert(
                "end",
                value,
            )

            entry.clear()

            self.save_metadata()

    # =====================================================
    # REMOVE OPTION
    # =====================================================

    def remove_option(self):
        focused = self.focusWidget()

        if focused is self.point_entry:
            metadata_key = "point"
            listbox = self.point_list

        elif focused is self.drive_entry:
            metadata_key = "drive"
            listbox = self.drive_list

        else:
            return

        selection = (
            listbox.curselection()
        )

        if not selection:
            return

        index = selection[0]

        values = self.metadata.get(
            metadata_key,
            [],
        )

        if 0 <= index < len(
            values
        ):
            values.pop(
                index
            )

            listbox.delete(
                index
            )

            self.save_metadata()
