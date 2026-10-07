from PIL import Image

from PySide6.QtCore import (
    Qt,
    QEvent,
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


from GUI.tracker_tuning_tab import TrackerTuningTabMixin
from GUI.recent_crops_tab import RecentCropsTabMixin

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

class RightPanelMixin(
    RecentCropsTabMixin,
    TrackerTuningTabMixin,
):

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

        self.tracker_tuning_tab = QWidget()

        self.right_panel_notebook.addTab(
            self.tracker_tuning_tab,
            "Tracker",
        )

        self.create_tracker_tuning_tab(
            self.tracker_tuning_tab
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
        
        self.refresh_tracker_tuning_theme()

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
        # ---------------------------------------------------------

        elif isinstance(
            widget,
            QPushButton,
        ):

            # Tracker tuning buttons have their own styling.
            if widget in (
                getattr(
                    self,
                    "tracker_defaults_button",
                    None,
                ),
                getattr(
                    self,
                    "tracker_overwrite_defaults_button",
                    None,
                ),
                getattr(
                    self,
                    "tracker_reset_defaults_button",
                    None,
                ),
            ):

                self._style_tracker_button(
                    widget
                )

            elif widget is getattr(
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
            getattr(
                self,
                "tracker_tuning_tab",
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
            getattr(
                self,
                "tracker_tuning_tab",
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