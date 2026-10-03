# Replace imports
import copy
import json
import os
import shutil

from PySide6.QtCore import Qt, QEvent
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QCheckBox,
    QMessageBox,
    QFileDialog,
    QScrollArea,
    QFrame,
    QSizePolicy,
)

from settings_menu.config import (
    DEFAULT_BOX,
    DEFAULT_CROP,
    SETTINGS_FILE,
    OUTPUT_DIR,
)

from Camera.camera import SUPPORTED_RESOLUTIONS

from settings_menu.tool_settings import ToolSettings
from settings_menu.inventory_settings import DEFAULT_INVENTORY
from settings_menu.tool_repository import DEFAULT_TOOLS
from settings_menu.settings_config import DEFAULT_METADATA

from logger import (
    rebuild_workbook_from_json,
    sync_json_from_workbook,
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
    WHITE_TEXT,
)
class GeneralSettings(QWidget):

    def __init__(
        self,
        parent,
        camera,
        main_gui,
    ):
        super().__init__(parent)

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.parent = parent
        self.camera = camera
        self.main_gui = main_gui

        self.crop_analyzed_images = False

        self.camera_resolution = (
            f"{self.camera.camera_width}x"
            f"{self.camera.camera_height}"
        )

        self.output_dir = OUTPUT_DIR

        self.log_dir = os.path.join(
            OUTPUT_DIR,
            "Logs",
        )

        self.manual_capture_key = "space"

        self.load_settings()

        if hasattr(
            self.main_gui,
            "update_manual_capture_key",
        ):
            self.main_gui.update_manual_capture_key(
                self.manual_capture_key
            )

        self.create_gui()

    def eventFilter(self, obj, event):
        if (
            isinstance(obj, QComboBox)
            and event.type() == QEvent.Wheel
        ):
            return True

        return super().eventFilter(obj, event)

    # =========================================================
    # Theme
    # =========================================================

    def update_appearance(self, mode):
        self._create_stylesheet()

        self.update()

        if hasattr(self, "content_widget"):
            self.content_widget.update()

        if hasattr(self, "settings_frame"):
            self.settings_frame.update()

    def apply_theme(self):
        self.update_appearance(
            self.main_gui.appearance_controller.get_mode()
        )

    def _color(self, color):
        return self.main_gui.appearance_controller.get_color(
            color,
            self.main_gui.appearance_controller.get_mode(),
        )
    
    # =========================================================
    # Settings Loading
    # =========================================================

    def load_settings(self):
        self.output_dir = OUTPUT_DIR

        self.log_dir = os.path.join(
            OUTPUT_DIR,
            "Logs",
        )

        self.camera_resolution = (
            f"{self.camera.camera_width}x"
            f"{self.camera.camera_height}"
        )

        if not os.path.exists(SETTINGS_FILE):
            return

        try:
            with open(
                SETTINGS_FILE,
                "r",
                encoding="utf-8",
            ) as file:
                settings = json.load(file)

            if not isinstance(settings, dict):
                settings = {}

            self.output_dir = settings.get(
                "output_dir",
                OUTPUT_DIR,
            )

            self.crop_analyzed_images = bool(
                settings.get(
                    "crop_analyzed_images",
                    False,
                )
            )

            self.manual_capture_key = settings.get(
                "manual_capture_key",
                "space",
            )

            resolution = settings.get(
                "camera_resolution"
            )

            if isinstance(resolution, dict):
                width = int(
                    resolution.get(
                        "width",
                        self.camera.camera_width,
                    )
                )

                height = int(
                    resolution.get(
                        "height",
                        self.camera.camera_height,
                    )
                )

                if (
                    width,
                    height,
                ) in SUPPORTED_RESOLUTIONS:
                    self.camera_resolution = (
                        f"{width}x{height}"
                    )

        except (
            OSError,
            ValueError,
            TypeError,
            json.JSONDecodeError,
        ):
            self.output_dir = OUTPUT_DIR
            self.crop_analyzed_images = False
            self.manual_capture_key = "space"

            self.camera_resolution = (
                f"{self.camera.camera_width}x"
                f"{self.camera.camera_height}"
            )

        self.log_dir = os.path.join(
            self.output_dir or OUTPUT_DIR,
            "Logs",
        )

    # =========================================================
    # Settings Saving
    # =========================================================

    def save_settings(self):
        settings = {}

        if os.path.exists(SETTINGS_FILE):
            try:
                with open(
                    SETTINGS_FILE,
                    "r",
                    encoding="utf-8",
                ) as file:
                    existing_settings = json.load(file)

                if isinstance(existing_settings, dict):
                    settings = existing_settings

            except (
                OSError,
                ValueError,
                TypeError,
                json.JSONDecodeError,
            ):
                settings = {}

        settings["output_dir"] = self.output_dir

        settings["crop_analyzed_images"] = (
            self.crop_analyzed_images
        )

        settings["camera_resolution"] = {
            "width": int(self.camera.camera_width),
            "height": int(self.camera.camera_height),
        }

        settings["manual_capture_key"] = (
            self.manual_capture_key
        )

        try:
            settings_directory = os.path.dirname(
                SETTINGS_FILE
            )

            if settings_directory:
                os.makedirs(
                    settings_directory,
                    exist_ok=True,
                )

            with open(
                SETTINGS_FILE,
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    settings,
                    file,
                    indent=4,
                )

        except OSError as error:
            print(
                f"ERROR: Could not save settings: {error}"
            )

    # =========================================================
    # Output Directory
    # =========================================================

    def choose_output_dir(self):
        directory = QFileDialog.getExistingDirectory(
            self.parent,
            "Select Output Directory",
            self.output_dir or OUTPUT_DIR,
        )

        if not directory:
            return

        self.output_dir = directory

        self.log_dir = os.path.join(
            directory,
            "Logs",
        )

        self.output_entry.setText(
            self.output_dir
        )

        self.log_entry.setText(
            self.log_dir
        )

        self.save_settings()

    # =========================================================
    # Tool Log Import
    # =========================================================

    def import_tool_log(self):
        source_file, _ = QFileDialog.getOpenFileName(
            self.parent,
            "Select Tool Log File",
            "",
            "Excel files (*.xlsx *.xls);;All files (*)",
        )

        if not source_file:
            return

        logs_dir = os.path.join(
            self.output_dir or OUTPUT_DIR,
            "Logs",
        )

        try:
            os.makedirs(
                logs_dir,
                exist_ok=True,
            )

            extension = os.path.splitext(
                source_file
            )[1]

            destination_file = os.path.join(
                logs_dir,
                f"Tool_Log{extension}",
            )

            shutil.copy2(
                source_file,
                destination_file,
            )

            QMessageBox.information(
                self.parent,
                "Tool Log Imported",
                (
                    "Tool Log imported successfully:"
                    f"\n\n{destination_file}"
                ),
            )

        except OSError as error:
            QMessageBox.critical(
                self.parent,
                "Import Failed",
                (
                    "Could not import the Tool Log file:"
                    f"\n\n{error}"
                ),
            )

    # =========================================================
    # Manual Capture Key
    # =========================================================

    def change_manual_capture_key(self, value):
        self.manual_capture_key = value

        if hasattr(
            self.main_gui,
            "update_manual_capture_key",
        ):
            self.main_gui.update_manual_capture_key(
                value
            )

        self.save_settings()

    # =========================================================
    # Camera Resolution
    # =========================================================

    def change_camera_resolution(self, value):
        try:
            width, height = value.split("x")

            width = int(width)
            height = int(height)

        except (
            ValueError,
            TypeError,
        ):
            return

        if self.camera.set_resolution(
            width,
            height,
        ):
            self.camera_resolution = (
                f"{self.camera.camera_width}x"
                f"{self.camera.camera_height}"
            )

            self.resolution_dropdown.setCurrentText(
                self.camera_resolution
            )

            self.save_settings()

    # =========================================================
    # Logger
    # =========================================================

    def rebuild_logger(self):
        try:
            rebuild_workbook_from_json()

            QMessageBox.information(
                self.parent,
                "Logger Rebuilt",
                "The Excel logger was rebuilt successfully.",
            )

        except Exception as error:
            print(
                "ERROR: Could not rebuild logger: "
                f"{error}"
            )

            QMessageBox.critical(
                self.parent,
                "Logger Error",
                (
                    "Could not rebuild the logger:"
                    f"\n\n{error}"
                ),
            )

    def sync_logger(self):
        try:
            sync_json_from_workbook()

            QMessageBox.information(
                self.parent,
                "Logger Synced",
                "The JSON logger data was synchronized successfully.",
            )

        except Exception as error:
            print(
                "ERROR: Could not sync logger to json: "
                f"{error}"
            )

            QMessageBox.critical(
                self.parent,
                "Logger Error",
                (
                    "Could not synchronize the logger:"
                    f"\n\n{error}"
                ),
            )

    # =========================================================
    # Reset Helpers
    # =========================================================

    @staticmethod
    def _box_dict(bounds):
        x1, y1, x2, y2 = bounds

        return {
            "x": int(x1),
            "y": int(y1),
            "width": int(x2 - x1),
            "height": int(y2 - y1),
        }

    def _default_settings_dict(self):
        width = getattr(
            self.camera,
            "camera_width",
            1920,
        )

        height = getattr(
            self.camera,
            "camera_height",
            1080,
        )

        return {
            "scan_box": self._box_dict(DEFAULT_BOX),
            "crop_box": self._box_dict(DEFAULT_CROP),
            "crop_analyzed_images": False,
            "camera_resolution": {
                "width": int(width),
                "height": int(height),
            },
            "counting_box": self._box_dict(DEFAULT_CROP),
            "output_dir": OUTPUT_DIR,
            "manual_capture_key": "space",
            "window_size": {
                "width": 1100,
                "height": 900,
            },
        }

    def reset_settings_file(
        self,
        include_window_size=True,
    ):
        settings = self._default_settings_dict()

        if include_window_size:
            settings["window_size"] = {
                "width": 1100,
                "height": 900,
            }
        else:
            settings.pop(
                "window_size",
                None,
            )

        settings_directory = os.path.dirname(
            SETTINGS_FILE
        )

        if settings_directory:
            os.makedirs(
                settings_directory,
                exist_ok=True,
            )

        with open(
            SETTINGS_FILE,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                settings,
                file,
                indent=4,
            )

    # =========================================================
    # Full Wipe
    # =========================================================

    def reset_modifiable_settings(self):
        result = QMessageBox.question(
            self.parent,
            "Full Wipe",
            (
                "This will clear the custom option data so "
                "the stored lists are blank/NA and can be "
                "re-entered manually.\n\n"
                "It does not overwrite the app base settings file."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if result != QMessageBox.Yes:
            return

        brands_path = getattr(
            ToolSettings,
            "BRANDS_FILE",
            os.path.join(
                os.path.dirname(__file__),
                "settings",
                "brands.json",
            ),
        )

        with open(
            brands_path,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump({}, file, indent=4)

        inventory_path = os.path.join(
            os.path.dirname(__file__),
            "settings",
            "inventory_settings.json",
        )

        with open(
            inventory_path,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                {"estimated_values": {}},
                file,
                indent=4,
            )

        metadata_path = os.path.join(
            os.path.dirname(__file__),
            "settings",
            "metadata_options.json",
        )

        empty_metadata = {
            "sizes": {
                "SAE": ["NA"],
                "Metric": ["NA"],
                "Other": ["NA"],
            },
            "drive": ["NA"],
            "point": ["NA"],
        }

        with open(
            metadata_path,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                empty_metadata,
                file,
                indent=4,
            )

        tools_path = os.path.join(
            os.path.dirname(__file__),
            "settings",
            "tools.json",
        )

        with open(
            tools_path,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                {"NA": ["NA"]},
                file,
                indent=4,
            )

        if hasattr(
            self.main_gui,
            "refresh_main_settings",
        ):
            self.main_gui.refresh_main_settings()

        QMessageBox.information(
            self.parent,
            "Full Wipe Complete",
            (
                "The custom option entries have been "
                "cleared to blank/NA values and can be "
                "re-entered manually."
            ),
        )

    # =========================================================
    # Reset All
    # =========================================================

    def reset_all_settings(self):
        result = QMessageBox.question(
            self.parent,
            "Reset All Default Settings",
            (
                "This will restore all stored settings JSON "
                "files to their default values: brands.json, "
                "inventory_settings.json, metadata_options.json, "
                "tools.json, and settings.json."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if result != QMessageBox.Yes:
            return

        brands_path = getattr(
            ToolSettings,
            "BRANDS_FILE",
            os.path.join(
                os.path.dirname(__file__),
                "settings",
                "brands.json",
            ),
        )

        default_brands = copy.deepcopy(
            getattr(
                ToolSettings,
                "DEFAULT_BRANDS",
                {},
            )
        )

        with open(
            brands_path,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                default_brands,
                file,
                indent=4,
            )

        inventory_path = os.path.join(
            os.path.dirname(__file__),
            "settings",
            "inventory_settings.json",
        )

        with open(
            inventory_path,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                {
                    "estimated_values": copy.deepcopy(
                        DEFAULT_INVENTORY
                    )
                },
                file,
                indent=4,
            )

        metadata_path = os.path.join(
            os.path.dirname(__file__),
            "settings",
            "metadata_options.json",
        )

        default_metadata = copy.deepcopy(
            DEFAULT_METADATA
        )

        default_metadata.pop(
            "specialty_socket",
            None,
        )

        with open(
            metadata_path,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                default_metadata,
                file,
                indent=4,
            )

        tools_path = os.path.join(
            os.path.dirname(__file__),
            "settings",
            "tools.json",
        )

        with open(
            tools_path,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                copy.deepcopy(DEFAULT_TOOLS),
                file,
                indent=4,
            )

        self.reset_settings_file(
            include_window_size=True
        )

        self.output_dir = OUTPUT_DIR

        self.log_dir = os.path.join(
            OUTPUT_DIR,
            "Logs",
        )

        self.camera_resolution = (
            f"{self.camera.camera_width}x"
            f"{self.camera.camera_height}"
        )

        self.manual_capture_key = "space"
        self.crop_analyzed_images = False

        self.output_entry.setText(
            self.output_dir
        )

        self.log_entry.setText(
            self.log_dir
        )

        self.resolution_dropdown.setCurrentText(
            self.camera_resolution
        )

        self.manual_capture_dropdown.setCurrentText(
            self.manual_capture_key
        )

        self.crop_checkbox.setChecked(False)

        if hasattr(
            self.main_gui,
            "update_manual_capture_key",
        ):
            self.main_gui.update_manual_capture_key(
                "space"
            )

        if hasattr(
            self.main_gui,
            "refresh_main_settings",
        ):
            self.main_gui.refresh_main_settings()

        QMessageBox.information(
            self.parent,
            "Defaults Restored",
            (
                "The stored JSON settings files have "
                "been restored to their default values."
            ),
        )

    # =========================================================
    # GUI
    # =========================================================

    def create_gui(self):
        outer_layout = QVBoxLayout(self)

        outer_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        outer_layout.setSpacing(0)

        self.content_frame = QScrollArea()

        self.content_frame.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.content_frame.setWidgetResizable(True)
        self.content_frame.setFrameShape(
            QFrame.NoFrame
        )

        self.content_widget = QWidget()

        self.content_widget.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        content_layout = QVBoxLayout(
            self.content_widget
        )

        content_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        content_layout.setSpacing(0)

        self.content_frame.setWidget(
            self.content_widget
        )

        outer_layout.addWidget(
            self.content_frame
        )

        # -----------------------------------------------------
        # Header
        # -----------------------------------------------------

        self.header_label = QLabel(
            "General Settings"
        )

        self.header_label.setObjectName(
            "pageTitle"
        )

        content_layout.addWidget(
            self.header_label
        )

        self.description_label = QLabel(
            "Configure output, camera, capture, logging, and reset options."
        )

        self.description_label.setObjectName(
            "pageDescription"
        )

        content_layout.addWidget(
            self.description_label
        )

        # -----------------------------------------------------
        # Main Card
        # -----------------------------------------------------

        self.settings_frame = QFrame()

        self.settings_frame.setObjectName(
            "settingsCard"
        )

        card_layout = QVBoxLayout(
            self.settings_frame
        )

        card_layout.setContentsMargins(
            20,
            20,
            20,
            20,
        )

        card_layout.setSpacing(0)

        content_layout.addWidget(
            self.settings_frame
        )

        # -----------------------------------------------------
        # Output
        # -----------------------------------------------------

        self._create_section_title(
            card_layout,
            "Output",
            "Configure where captured files and tool logs are stored.",
        )

        output_label = QLabel(
            "Output Directory"
        )

        output_label.setObjectName(
            "fieldLabel"
        )

        card_layout.addWidget(
            output_label
        )

        output_layout = QHBoxLayout()
        output_layout.setSpacing(10)

        self.output_entry = QLineEdit(
            self.output_dir
        )

        self.output_entry.setReadOnly(True)

        output_layout.addWidget(
            self.output_entry
        )

        self.browse_button = QPushButton(
            "Browse..."
        )

        self.browse_button.setFixedWidth(
            100
        )

        self.browse_button.clicked.connect(
            self.choose_output_dir
        )

        output_layout.addWidget(
            self.browse_button
        )

        card_layout.addLayout(
            output_layout
        )

        # -----------------------------------------------------
        # Log Directory
        # -----------------------------------------------------

        log_label = QLabel(
            "Log Directory"
        )

        log_label.setObjectName(
            "fieldLabel"
        )

        card_layout.addWidget(
            log_label
        )

        log_layout = QHBoxLayout()
        log_layout.setSpacing(10)

        self.log_entry = QLineEdit(
            self.log_dir
        )

        self.log_entry.setReadOnly(True)

        log_layout.addWidget(
            self.log_entry
        )

        self.import_log_button = QPushButton(
            "Import Tool Log..."
        )

        self.import_log_button.setFixedWidth(
            145
        )

        self.import_log_button.clicked.connect(
            self.import_tool_log
        )

        log_layout.addWidget(
            self.import_log_button
        )

        card_layout.addLayout(
            log_layout
        )

        # -----------------------------------------------------
        # Camera
        # -----------------------------------------------------

        self._create_section_title(
            card_layout,
            "Camera & Capture",
            "Configure camera resolution and the keyboard shortcut for manual capture.",
            top_margin=24,
        )

        chooser_row = QHBoxLayout()
        chooser_row.setSpacing(16)

        resolution_container = QWidget()
        resolution_layout = QVBoxLayout(
            resolution_container
        )

        resolution_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        resolution_label = QLabel(
            "Camera Resolution"
        )

        resolution_label.setObjectName(
            "fieldLabel"
        )

        resolution_layout.addWidget(
            resolution_label
        )

        resolution_values = [
            f"{width}x{height}"
            for width, height in SUPPORTED_RESOLUTIONS
        ]

        self.resolution_dropdown = QComboBox()
        self.resolution_dropdown.installEventFilter(self)

        self.resolution_dropdown.addItems(
            resolution_values
        )

        self.resolution_dropdown.setCurrentText(
            self.camera_resolution
        )

        self.resolution_dropdown.currentTextChanged.connect(
            self.change_camera_resolution
        )

        resolution_layout.addWidget(
            self.resolution_dropdown
        )

        chooser_row.addWidget(
            resolution_container
        )

        manual_container = QWidget()
        manual_layout = QVBoxLayout(
            manual_container
        )

        manual_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        manual_label = QLabel(
            "Manual Capture Shortcut"
        )

        manual_label.setObjectName(
            "fieldLabel"
        )

        manual_layout.addWidget(
            manual_label
        )

        manual_capture_values = [
            "space",
            "Return",
            "F1",
            "F2",
            "F3",
            "F4",
            "F5",
            "F6",
            "F7",
            "F8",
            "F9",
            "F10",
            "F11",
            "F12",
        ]

        self.manual_capture_dropdown = QComboBox()
        self.manual_capture_dropdown.installEventFilter(self)

        self.manual_capture_dropdown.addItems(
            manual_capture_values
        )

        self.manual_capture_dropdown.setCurrentText(
            self.manual_capture_key
        )

        self.manual_capture_dropdown.currentTextChanged.connect(
            self.change_manual_capture_key
        )

        manual_layout.addWidget(
            self.manual_capture_dropdown
        )

        chooser_row.addWidget(
            manual_container
        )

        card_layout.addLayout(
            chooser_row
        )

        # -----------------------------------------------------
        # OCR
        # -----------------------------------------------------

        self._create_section_title(
            card_layout,
            "OCR",
            "Control whether images are cropped before OCR analysis.",
            top_margin=24,
        )

        self.crop_checkbox = QCheckBox(
            "Crop images before OCR analysis"
        )

        self.crop_checkbox.setChecked(
            self.crop_analyzed_images
        )

        self.crop_checkbox.toggled.connect(
            self._crop_changed
        )

        card_layout.addWidget(
            self.crop_checkbox
        )

        # -----------------------------------------------------
        # Logger
        # -----------------------------------------------------

        self._create_section_title(
            card_layout,
            "Logger",
            "Rebuild or synchronize the Excel logger and its JSON data.",
            top_margin=24,
        )

        rebuild_description = QLabel(
            "Rebuild Logger recreates the Excel spreadsheet from existing JSON files and can be used as a backup."
        )

        rebuild_description.setObjectName(
            "fieldDescription"
        )

        rebuild_description.setWordWrap(
            True
        )

        card_layout.addWidget(
            rebuild_description
        )

        self.rebuild_logger_button = QPushButton(
            "Rebuild Logger"
        )

        self.rebuild_logger_button.setFixedWidth(
            140
        )

        self.rebuild_logger_button.clicked.connect(
            self.rebuild_logger
        )

        card_layout.addWidget(
            self.rebuild_logger_button
        )

        sync_description = QLabel(
            "Sync Logger modifies existing JSON data based on the Tool_Logger.xlsx file. This can overwrite data."
        )

        sync_description.setObjectName(
            "fieldDescription"
        )

        sync_description.setWordWrap(
            True
        )

        card_layout.addWidget(
            sync_description
        )

        self.sync_logger_button = QPushButton(
            "Sync Logger"
        )

        self.sync_logger_button.setFixedWidth(
            140
        )

        self.sync_logger_button.clicked.connect(
            self.sync_logger
        )

        card_layout.addWidget(
            self.sync_logger_button
        )

        # -----------------------------------------------------
        # Reset Settings
        # -----------------------------------------------------

        self._create_section_title(
            card_layout,
            "Reset Settings",
            "Restore defaults or clear custom option data.",
            top_margin=24,
        )

        reset_description = QLabel(
            "Reset All Default Settings restores every stored JSON settings file to its built-in defaults."
        )

        reset_description.setObjectName(
            "fieldDescription"
        )

        reset_description.setWordWrap(
            True
        )

        card_layout.addWidget(
            reset_description
        )

        self.reset_all_button = QPushButton(
            "Reset All Default Settings"
        )

        self.reset_all_button.setFixedWidth(
            220
        )

        self.reset_all_button.clicked.connect(
            self.reset_all_settings
        )

        card_layout.addWidget(
            self.reset_all_button
        )

        wipe_description = QLabel(
            "Full Wipe clears custom brands, tools, inventory, and metadata entries to blank/NA values."
        )

        wipe_description.setObjectName(
            "fieldDescription"
        )

        wipe_description.setWordWrap(
            True
        )

        card_layout.addWidget(
            wipe_description
        )

        self.full_wipe_button = QPushButton(
            "Full Wipe"
        )

        self.full_wipe_button.setFixedWidth(
            140
        )

        self.full_wipe_button.setObjectName(
            "dangerButton"
        )

        self.full_wipe_button.clicked.connect(
            self.reset_modifiable_settings
        )

        card_layout.addWidget(
            self.full_wipe_button
        )


        self._create_stylesheet()

    # =========================================================
    # UI Helpers
    # =========================================================

    def _create_section_title(
        self,
        layout,
        title,
        description,
        top_margin=0,
    ):
        container = QWidget()

        section_layout = QVBoxLayout(
            container
        )

        section_layout.setContentsMargins(
            0,
            top_margin,
            0,
            0,
        )

        section_layout.setSpacing(2)

        title_label = QLabel(title)

        title_label.setObjectName(
            "sectionTitle"
        )

        section_layout.addWidget(
            title_label
        )

        description_label = QLabel(
            description
        )

        description_label.setObjectName(
            "sectionDescription"
        )

        description_label.setWordWrap(
            True
        )

        section_layout.addWidget(
            description_label
        )

        layout.addWidget(
            container
        )

    def _crop_changed(self, checked):
        self.crop_analyzed_images = checked
        self.save_settings()

    def _create_stylesheet(self):

        panel_bg = self._color(PANEL_BG)
        card_bg = self._color(CARD_BG)
        card_hover = self._color(CARD_HOVER)
        input_bg = self._color(INPUT_BG)
        border = self._color(BORDER_COLOR)
        text = self._color(TEXT_COLOR)
        muted = self._color(MUTED_TEXT)
        accent = self._color(ACCENT_COLOR)
        accent_hover = self._color(ACCENT_HOVER)
        danger = self._color(DANGER_COLOR)
        danger_hover = self._color(DANGER_HOVER)
        control_bg = self._color(CONTROL_BG)
        white = self._color(WHITE_TEXT)

        self.setStyleSheet(
            f"""
            QWidget {{
                color: {text};
                background: transparent;
            }}

            QLabel#pageTitle {{
                color: {text};
                font-size: 20px;
                font-weight: 700;
            }}

            QLabel#pageDescription {{
                color: {muted};
                font-size: 12px;
                margin-bottom: 18px;
            }}

            QFrame#settingsCard {{
                background-color: {card_bg};
                border: 1px solid {border};
                border-radius: 10px;
            }}

            QLabel#sectionTitle {{
                color: {text};
                font-size: 14px;
                font-weight: 700;
            }}

            QLabel#sectionDescription {{
                color: {muted};
                font-size: 11px;
            }}

            QLabel#fieldLabel {{
                color: {text};
                font-size: 12px;
                font-weight: 600;
                margin-top: 14px;
                margin-bottom: 6px;
            }}

            QLabel#fieldDescription {{
                color: {muted};
                font-size: 12px;
                margin-top: 14px;
                margin-bottom: 6px;
            }}

            QLineEdit {{
                min-height: 34px;
                background-color: {input_bg};
                color: {text};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 0 10px;
                font-size: 12px;
            }}

            QLineEdit:focus {{
                border: 1px solid {accent};
            }}

            QComboBox {{
                min-height: 34px;
                background-color: {input_bg};
                color: {text};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 0 10px;
                font-size: 12px;
            }}

            QComboBox:hover {{
                border-color: {accent};
            }}

            QComboBox QAbstractItemView {{
                background-color: {panel_bg};
                color: {text};
                border: 1px solid {border};
                selection-background-color: {card_hover};
                selection-color: {text};
            }}

            QPushButton {{
                min-height: 34px;
                background-color: {card_bg};
                color: {text};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 0 12px;
                font-size: 12px;
                font-weight: 600;
            }}

            QPushButton:hover {{
                background-color: {card_hover};
            }}

            QPushButton:pressed {{
                background-color: {control_bg};
            }}

            QPushButton#dangerButton {{
                background-color: {danger};
                color: {white};
                border: none;
            }}

            QPushButton#dangerButton:hover {{
                background-color: {danger_hover};
            }}

            QCheckBox {{
                color: {text};
                font-size: 12px;
                spacing: 8px;
                margin-top: 14px;
            }}

            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid {border};
                background-color: {input_bg};
            }}

            QCheckBox::indicator:checked {{
                background-color: {accent};
                border-color: {accent};
            }}

            QScrollArea {{
                border: none;
                background: transparent;
            }}

            QScrollBar:vertical {{
                background: transparent;
                width: 10px;
                margin: 2px;
            }}

            QScrollBar::handle:vertical {{
                background: {border};
                border-radius: 5px;
                min-height: 30px;
            }}

            QScrollBar::handle:vertical:hover {{
                background: {accent_hover};
            }}

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            """
        )