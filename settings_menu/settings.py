from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QDialog,
    QVBoxLayout,
    QTabWidget,
    QPushButton,
    QSizePolicy,
)

import traceback

from GUI.appearance_controller import (
    PANEL_BG,
    CARD_BG,
    CARD_HOVER,
    BORDER_COLOR,
    TEXT_COLOR,
    ACCENT_COLOR,
    ACCENT_HOVER,
    WHITE_TEXT,
)

from settings_menu.tool_settings import ToolSettings
from settings_menu.general_settings import GeneralSettings
from settings_menu.metadata_settings import MetadataSettings
from settings_menu.inventory_settings import InventorySettings


class SettingsWindow(QDialog):

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def __init__(
        self,
        parent,
        tools,
        on_tools_changed,
        camera,
        on_brands_changed=None,
        on_metadata_changed=None,
        on_inventory_changed=None,
    ):

        super().__init__(parent)

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.parent = parent
        self.tools = tools
        self.on_tools_changed = on_tools_changed
        self.camera = camera
        self.on_brands_changed = on_brands_changed
        self.on_metadata_changed = on_metadata_changed
        self.on_inventory_changed = on_inventory_changed

        self.window = QDialog(
            parent.root
        )

        self.window.setWindowTitle(
            "Settings"
        )

        self.window.setFixedSize(
            800,
            600,
        )

        # Keep Settings associated with the main window.
        self.window.setWindowModality(
            Qt.WindowModality.NonModal
        )

        self.window.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowTitleHint
        )

        self.create_gui()

        self.update_appearance(
            self.parent.appearance_controller.get_mode()
        )

        self.window.finished.connect(
            self._on_window_closed
        )

        self.show()


    # ------------------------------------------------------------------
    # Window State
    # ------------------------------------------------------------------

    def is_open(self):
        return self.window is not None and self.window.isVisible()

    # ------------------------------------------------------------------
    # Window Focus
    # ------------------------------------------------------------------

    def _focus_window(self):
        if self.window is None:
            return

        try:
            self.window.show()
            self.window.raise_()
            self.window.activateWindow()

        except RuntimeError:
            self.parent.settings_window = None

    def show(self):
        if self.window is None:
            self.parent.settings_window = None
            return False

        try:
            self.window.show()
            self.window.raise_()
            self.window.activateWindow()

            return True

        except RuntimeError:
            self.parent.settings_window = None
            return False

    # ------------------------------------------------------------------
    # GUI
    # ------------------------------------------------------------------

    def create_gui(self):

        self.main_frame = QWidget(
            self.window
        )

        self.main_layout = QVBoxLayout(
            self.main_frame
        )

        self.main_layout.setContentsMargins(
            15,
            15,
            15,
            15,
        )

        self.main_layout.setSpacing(
            10
        )

        # --------------------------------------------------------------
        # Tabs
        # --------------------------------------------------------------

        self.notebook = QTabWidget(
            self.main_frame
        )

        self.notebook.setDocumentMode(
            True
        )


        self.notebook.setStyleSheet("")

        self.main_layout.addWidget(
            self.notebook,
            1,
        )

        # --------------------------------------------------------------
        # Create ALL tabs once
        # --------------------------------------------------------------

        self.tools_frame = QWidget()

        self.product_frame = QWidget()

        self.sales_frame = QWidget()

        self.general_frame = QWidget()

        self.notebook.addTab(
            self.tools_frame,
            "Tools",
        )

        self.notebook.addTab(
            self.product_frame,
            "Product Attributes",
        )

        self.notebook.addTab(
            self.sales_frame,
            "Sales / Inventory",
        )

        self.notebook.addTab(
            self.general_frame,
            "General",
        )

        # --------------------------------------------------------------
        # Tab Layouts
        # --------------------------------------------------------------

        self.tools_layout = QVBoxLayout(
            self.tools_frame
        )

        self.product_layout = QVBoxLayout(
            self.product_frame
        )

        self.sales_layout = QVBoxLayout(
            self.sales_frame
        )

        self.general_layout = QVBoxLayout(
            self.general_frame
        )

        for layout in (
            self.tools_layout,
            self.product_layout,
            self.sales_layout,
            self.general_layout,
        ):
            layout.setContentsMargins(
                0,
                0,
                0,
                0,
            )

            layout.setSpacing(0)

        # --------------------------------------------------------------
        # Inventory
        # --------------------------------------------------------------

        try:
            self.inventory_settings = InventorySettings(
                self.sales_frame,
                self.tools,
                self.on_inventory_changed,
            )

            self.sales_layout.addWidget(
                self.inventory_settings
            )

        except Exception as exc:
            print(
                "[SETTINGS DEBUG] InventorySettings creation FAILED:"
            )
            print(
                f"[SETTINGS DEBUG] {exc}"
            )
            traceback.print_exc()
            raise

        # --------------------------------------------------------------
        # Tools / Brands
        # --------------------------------------------------------------

        try:
            self.tool_settings = ToolSettings(
                self.tools_frame,
                self.tools,
                self.inventory_settings.on_tools_changed,
                on_brands_changed=self.on_brands_changed,
            )

            self.tools_layout.addWidget(
                self.tool_settings
            )

        except Exception as exc:
            print(
                "[SETTINGS DEBUG] ToolSettings creation FAILED:"
            )
            print(
                f"[SETTINGS DEBUG] {exc}"
            )
            traceback.print_exc()
            raise

        # --------------------------------------------------------------
        # Product Attributes
        # --------------------------------------------------------------

        try:
            self.metadata_settings = MetadataSettings(
                self.product_frame,
                self.on_metadata_changed,
            )

            self.product_layout.addWidget(
                self.metadata_settings
            )

        except Exception as exc:
            print(
                "[SETTINGS DEBUG] MetadataSettings creation FAILED:"
            )
            print(
                f"[SETTINGS DEBUG] {exc}"
            )
            traceback.print_exc()
            raise

        # --------------------------------------------------------------
        # General
        # --------------------------------------------------------------

        try:
            self.general_settings = GeneralSettings(
                self.general_frame,
                self.camera,
                self.parent,
            )

            self.general_layout.addWidget(
                self.general_settings
            )

        except Exception as exc:
            print(
                "[SETTINGS DEBUG] GeneralSettings creation FAILED:"
            )
            print(
                f"[SETTINGS DEBUG] {exc}"
            )
            traceback.print_exc()
            raise

        # --------------------------------------------------------------
        # Close button
        # --------------------------------------------------------------

        self.close_button = QPushButton(
            "Close",
            self.main_frame,
        )

        self.close_button.setFixedSize(
            110,
            36,
        )

        self.close_button.setStyleSheet("")

        self.close_button.clicked.connect(
            self.close
        )

        self.main_layout.addWidget(
            self.close_button,
            0,
            Qt.AlignmentFlag.AlignHCenter,
        )

        self.window.setLayout(
            self.main_layout
        )

    # ------------------------------------------------------------------
    # Appearance
    # ------------------------------------------------------------------

    def update_appearance(self, mode):

        if self.window is None:
            self.parent.settings_window = None
            return

        try:
            self.apply_theme(mode)

            self.inventory_settings.update_appearance(
                mode
            )

            self.tool_settings.update_appearance(
                mode
            )

            self.metadata_settings.update_appearance(
                mode
            )

            self.general_settings.update_appearance(
                mode
            )

            self._restore_window_visibility()

        except RuntimeError:
            self.parent.settings_window = None

    def apply_theme(self, mode):

        panel_bg = self.parent.appearance_controller.get_color(
            PANEL_BG,
            mode,
        )

        card_bg = self.parent.appearance_controller.get_color(
            CARD_BG,
            mode,
        )

        card_hover = self.parent.appearance_controller.get_color(
            CARD_HOVER,
            mode,
        )

        border = self.parent.appearance_controller.get_color(
            BORDER_COLOR,
            mode,
        )

        text = self.parent.appearance_controller.get_color(
            TEXT_COLOR,
            mode,
        )

        accent = self.parent.appearance_controller.get_color(
            ACCENT_COLOR,
            mode,
        )

        accent_hover = self.parent.appearance_controller.get_color(
            ACCENT_HOVER,
            mode,
        )

        white_text = self.parent.appearance_controller.get_color(
            WHITE_TEXT,
            mode,
        )

        self.window.setStyleSheet(
            f"""
            QDialog {{
                background-color: {panel_bg};
                color: {text};
            }}

            QWidget {{
                background-color: {panel_bg};
                color: {text};
            }}

            QTabWidget::pane {{
                background-color: {panel_bg};
                border: 1px solid {border};
                border-radius: 8px;
                top: -1px;
            }}

            QTabBar::tab {{
                background-color: {card_bg};
                color: {text};
                border: 1px solid {border};
                padding: 9px 16px;
                margin-right: 2px;
                border-top-left-radius: 7px;
                border-top-right-radius: 7px;
            }}

            QTabBar::tab:hover {{
                background-color: {card_hover};
            }}

            QTabBar::tab:selected {{
                background-color: {accent};
                color: {white_text};
                border-color: {accent};
            }}

            QPushButton {{
                background-color: {card_bg};
                color: {text};
                border: 1px solid {border};
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
                padding: 7px 12px;
            }}

            QPushButton:hover {{
                background-color: {card_hover};
            }}

            QPushButton:pressed {{
                background-color: {accent_hover};
            }}

            QLabel {{
                color: {text};
                background: transparent;
            }}

            QLineEdit,
            QComboBox,
            QSpinBox,
            QDoubleSpinBox {{
                background-color: {card_bg};
                color: {text};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 6px 8px;
            }}

            QCheckBox,
            QRadioButton {{
                color: {text};
                background: transparent;
            }}

            QGroupBox {{
                color: {text};
                border: 1px solid {border};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 8px;
            }}

            QScrollArea {{
                background-color: {panel_bg};
                border: none;
            }}
            """
        )

        self.window.update()

    # ------------------------------------------------------------------
    # Restore Settings Window Visibility
    # ------------------------------------------------------------------

    def _restore_window_visibility(self):
        if self.window is None:
            self.parent.settings_window = None
            return

        try:
            if not self.window.isVisible():
                self.window.show()

            self.window.raise_()
            self.window.activateWindow()

        except RuntimeError:
            self.parent.settings_window = None

    # ------------------------------------------------------------------
    # Debug
    # ------------------------------------------------------------------

    def _debug_window_state(self, source):
        if self.window is None:
            print(
                f"[WINDOW DEBUG] {source}: WINDOW DOES NOT EXIST"
            )
            return

        try:
            print(
                f"[WINDOW DEBUG] {source}: "
                f"visible={self.window.isVisible()}, "
                f"active={self.window.isActiveWindow()}, "
                f"geometry={self.window.geometry()}"
            )

        except RuntimeError:
            print(
                f"[WINDOW DEBUG] {source}: RuntimeError"
            )

    # ------------------------------------------------------------------
    # Window Closed
    # ------------------------------------------------------------------

    def _on_window_closed(self):
        self.parent.settings_window = None

        print(
            "[SETTINGS DEBUG] SettingsWindow closed"
        )

    # ------------------------------------------------------------------
    # Close
    # ------------------------------------------------------------------

    def close(self):
        if self.window is None:
            self.parent.settings_window = None
            return

        try:
            self.window.close()

        except RuntimeError:
            pass

        self.parent.settings_window = None
