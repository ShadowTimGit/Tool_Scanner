import json
import os

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
)

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from GUI.appearance_controller import (
    AppearanceController,
    PANEL_BG,
    CARD_BG,
    CARD_HOVER,
    INPUT_BG,
    BORDER_COLOR,
    TEXT_COLOR,
    MUTED_TEXT,
)

from GUI.gui_camera import CameraMixin
from GUI.gui_constants import (
    CROP_MODE_PREVIEW,
    TRIGGER_MANUAL,
    INVENTORY_PURCHASE,
)
from GUI.gui_controls import ControlsMixin
from GUI.gui_processes import ProcessMixin
from GUI.gui_tools import ToolsMixin
from GUI.gui_video import VideoMixin
from GUI.gui_panel import RightPanelMixin

from PySide6.QtCore import QTimer, Signal, Qt

from settings_menu.tool_repository import ToolRepository
from settings_menu.metadata_settings import MetadataSettings
from settings_menu.tool_settings import ToolSettings

from version import APP_VERSION

from updater import (
    check_for_updates,
    download_update,
    start_update,
)

from settings_menu.config import SETTINGS_FILE


class ToolScannerGUI(
    CameraMixin,
    VideoMixin,
    ControlsMixin,
    ToolsMixin,
    ProcessMixin,
    RightPanelMixin,
    QMainWindow,
):
    finish_remove_recent_crop = Signal(object, object)
    camera_initialized_signal = Signal(object)
    camera_initialization_failed_signal = Signal(object)
    recent_crops_changed_signal = Signal()

    def __init__(self):
        super().__init__()

        self.recent_crops_changed_signal.connect(
            self._refresh_recent_crops_from_camera
        )

        self.finish_remove_recent_crop.connect(
            self._finish_remove_recent_crop
        )

        self.root = self

        # ------------------------------------------------------------------
        # Application appearance
        # ------------------------------------------------------------------

        self.setWindowTitle(
            "Object Scanner"
        )

        saved_size = self.load_window_size()

        self.resize(
            saved_size[0],
            saved_size[1],
        )

        self.setMinimumSize(
            900,
            700,
        )

        self.closeEvent = self.handle_close_event

        self.running = True

        # ------------------------------------------------------------------
        # Application data
        # ------------------------------------------------------------------

        self.tools = ToolRepository.load_tools()

        self.brands = ToolSettings.load_brands()

        self.metadata = MetadataSettings.load_metadata()

        self.sizes = MetadataSettings.load_metadata().get(
            "sizes",
            {},
        )

        self.selected_brand = ""

        # ------------------------------------------------------------------
        # Application variables
        # ------------------------------------------------------------------

        self.inventory_type = INVENTORY_PURCHASE

        self.trigger_mode = TRIGGER_MANUAL

        self.crop_mode = CROP_MODE_PREVIEW

        # ------------------------------------------------------------------
        # Window state
        # ------------------------------------------------------------------

        self.settings_window = None

        self.current_frame_width = 0
        self.current_frame_height = 0

        self.display_width = 0
        self.display_height = 0

        self.camera = None
        self.camera_ready = False

        self.show_crop_box = True
        self.show_counting_box = True

        # ------------------------------------------------------------------
        # GUI
        # ------------------------------------------------------------------

        self.create_gui()

        self.check_for_updates()

        self.status_label.setText(
            "Loading camera..."
        )

        self.start_camera_initialization()

    # ======================================================================
    # Updates
    # ======================================================================

    def check_for_updates(self):
        check_for_updates(
            APP_VERSION,
            self.show_update,
        )

    def show_update(
        self,
        latest_version,
        release_url,
        zip_url,
    ):
        QTimer.singleShot(
            0,
            lambda: self.show_update_dialog(
                latest_version,
                release_url,
                zip_url,
            ),
        )

    def show_update_dialog(
        self,
        latest_version,
        release_url,
        zip_url,
    ):
        result = QMessageBox.question(
            self,
            "Update Available",
            (
                "A new version of Object Scanner "
                "is available.\n\n"
                f"Current version: {APP_VERSION}\n"
                f"Latest version: {latest_version}\n\n"
                "Would you like to update now?"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if result != QMessageBox.Yes:
            return

        self.download_and_install_update(
            zip_url
        )

    def download_and_install_update(
        self,
        zip_url,
    ):
        QMessageBox.information(
            self,
            "Updating",
            (
                "The update is being downloaded.\n\n"
                "Object Scanner will restart "
                "automatically when finished."
            ),
        )

        download_update(
            zip_url,
            self.update_download_finished,
        )

    def update_download_finished(
        self,
        temp_dir,
        zip_path,
    ):
        QTimer.singleShot(
            0,
            lambda: self.finish_update(
                temp_dir,
                zip_path,
            ),
        )

    def finish_update(
        self,
        temp_dir,
        zip_path,
    ):
        project_dir = os.path.dirname(
            os.path.abspath(__file__)
        )

        success = start_update(
            zip_path,
            project_dir,
        )

        if success:
            self.stop()

    # ======================================================================
    # GUI creation
    # ======================================================================

    def create_gui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # ==============================================================
        # ROOT
        #
        # ┌──────────────────────────────────────┬───────────────┐
        # │                                      │               │
        # │             CAMERA AREA              │               │
        # │                                      │   RIGHT       │
        # ├──────────────────────────────────────┤   PANEL       │
        # │                                      │               │
        # │          CAMERA CONTROLS             │               │
        # │                                      │               │
        # └──────────────────────────────────────┴───────────────┘
        # ==============================================================

        self.main_layout = QHBoxLayout(
            self.central_widget
        )

        self.main_layout.setContentsMargins(
            8,
            8,
            8,
            8,
        )

        self.main_layout.setSpacing(8)

        # ==============================================================
        # LEFT SIDE
        # ==============================================================

        self.left_widget = QWidget()

        self.left_layout = QVBoxLayout(
            self.left_widget
        )

        self.left_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.left_layout.setSpacing(8)

        # ==============================================================
        # CAMERA AREA
        # ==============================================================

        self.camera_area = QWidget()

        self.camera_layout = QVBoxLayout(
            self.camera_area
        )

        self.camera_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.camera_layout.setSpacing(0)

        self.create_video_display()

        self.left_layout.addWidget(
            self.camera_area,
            1,
        )

        self.create_below_webcam_frame()

        self.appearance_controller = AppearanceController(
            self.below_webcam_container,
            on_changed=self.on_appearance_changed,
        )

        self.create_count_display()
        
        self.create_status_display()
        self.create_action_buttons()

        self.create_control_frame()

        self.apply_theme(
            self.appearance_controller.get_mode()
        )

        self.left_layout.addWidget(
            self.below_webcam_container,
            0,
        )

        # ==============================================================
        # RIGHT PANEL
        # ==============================================================

        self.right_panel_container = QWidget()

        self.right_panel_layout = QVBoxLayout(
            self.right_panel_container
        )

        self.right_panel_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.right_panel_layout.setSpacing(0)

        self.create_right_panel()

        # ==============================================================
        # ROOT SPLIT
        # ==============================================================

        self.main_layout.addWidget(
            self.left_widget,
            1,
        )

        self.main_layout.addWidget(
            self.right_panel_container,
            0,
        )

        # Keep the panel usable while allowing it to resize.
        self.right_panel_container.setMinimumWidth(
            280
        )

        self.right_panel_container.setMaximumWidth(
            400
        )

        # ==============================================================
        # SETTINGS
        # ==============================================================

        self.refresh_main_settings()

    def on_appearance_changed(self, mode):
        self.appearance_mode = mode

        self.apply_theme(mode)

        if (
            self.settings_window is not None
            and self.settings_window.is_open()
        ):
            self.settings_window.update_appearance(
                mode
            )

    # ======================================================================
    # Appearance
    # ======================================================================

    def apply_theme(self, mode):
        self.appearance_mode = mode

        panel_bg = AppearanceController.get_color(
            PANEL_BG,
            mode,
        )

        card_bg = AppearanceController.get_color(
            CARD_BG,
            mode,
        )

        input_bg = AppearanceController.get_color(
            INPUT_BG,
            mode,
        )

        border = AppearanceController.get_color(
            BORDER_COLOR,
            mode,
        )

        text = AppearanceController.get_color(
            TEXT_COLOR,
            mode,
        )

        self.setStyleSheet(
            f"""
            QMainWindow {{
                background-color: {panel_bg};
                color: {text};
            }}

            QWidget {{
                color: {text};
            }}

            QFrame {{
                background-color: {panel_bg};
                color: {text};
            }}

            QLabel {{
                color: {text};
                background: transparent;
            }}

            QLineEdit,
            QComboBox,
            QSpinBox,
            QDoubleSpinBox {{
                background-color: {input_bg};
                color: {text};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 6px 8px;
            }}

            QPushButton {{
                background-color: {card_bg};
                color: {text};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 7px 12px;
            }}

            QPushButton:hover {{
                background-color: {AppearanceController.get_color(
                    CARD_HOVER,
                    mode,
                )};
            }}

            QScrollArea {{
                background-color: {panel_bg};
                border: none;
            }}
            """
        )

        if hasattr(self, "refresh_right_panel_theme"):
            self.refresh_right_panel_theme()

        if hasattr(
            self,
            "refresh_control_theme",
        ):
            self.refresh_control_theme()

        if hasattr(
            self,
            "refresh_video_theme",
        ):
            self.refresh_video_theme()



    # ======================================================================
    # Inventory
    # ======================================================================

    def on_inventory_type_changed(
        self,
        value=None,
    ):
        if value is not None:
            self.inventory_type = value

        if self.camera is None:
            return

        self.camera.set_inventory_type(
            self.inventory_type
        )

    # ======================================================================
    # Settings
    # ======================================================================

    def refresh_main_settings(self):
        self.tools = ToolRepository.load_tools()

        self.brands = ToolSettings.load_brands()

        self.metadata = MetadataSettings.load_metadata()

        self.sizes = ToolSettings.load_sizes_data()

        self.tools_changed()

        self.refresh_brand_dropdown()

        self.refresh_metadata_dropdowns()

        self.refresh_size_dropdowns()

    def on_settings_changed(self):
        self.refresh_main_settings()

    def refresh_metadata_dropdowns(self):
        metadata = MetadataSettings.load_metadata()

        self.measurement_dropdown.clear()

        self.measurement_dropdown.addItems(
            [
                "SAE",
                "Metric",
                "Other",
                "DUAL",
            ]
        )

        self.drive_dropdown.clear()

        self.drive_dropdown.addItems(
            metadata.get(
                "drive",
                [],
            )
        )

        self.point_dropdown.clear()

        self.point_dropdown.addItems(
            metadata.get(
                "point",
                [],
            )
        )

        self.specialty_socket_dropdown.clear()

        self.specialty_socket_dropdown.addItems(
            metadata.get(
                "specialty_socket",
                [],
            )
        )

        if (
            self.measurement_dropdown.currentText()
            not in (
                "SAE",
                "Metric",
                "Other",
                "DUAL",
            )
        ):
            self.measurement_dropdown.setCurrentText(
                "SAE"
            )

        drive_values = [
            self.drive_dropdown.itemText(index)
            for index in range(
                self.drive_dropdown.count()
            )
        ]

        if (
            self.drive_dropdown.currentText()
            not in drive_values
        ):
            if drive_values:
                self.drive_dropdown.setCurrentIndex(0)
            else:
                self.drive_dropdown.setCurrentText("")

        point_values = [
            self.point_dropdown.itemText(index)
            for index in range(
                self.point_dropdown.count()
            )
        ]

        if (
            self.point_dropdown.currentText()
            not in point_values
        ):
            if point_values:
                self.point_dropdown.setCurrentIndex(0)
            else:
                self.point_dropdown.setCurrentText("")

        specialty_values = [
            self.specialty_socket_dropdown.itemText(index)
            for index in range(
                self.specialty_socket_dropdown.count()
            )
        ]

        if (
            self.specialty_socket_dropdown.currentText()
            not in specialty_values
        ):
            if specialty_values:
                self.specialty_socket_dropdown.setCurrentIndex(0)
            else:
                self.specialty_socket_dropdown.setCurrentText("")

    def refresh_size_dropdowns(self):
        metadata = MetadataSettings.load_metadata()

        sizes = metadata.get(
            "sizes",
            {},
        )

        measurement = self.measurement_dropdown.currentText()

        if measurement == "Other":
            size_1_measurement = "Other"
            size_2_measurement = "Other"

        elif measurement == "DUAL":
            size_1_measurement = "SAE"
            size_2_measurement = "Metric"

        else:
            size_1_measurement = measurement
            size_2_measurement = measurement

        size_1_values = sizes.get(
            size_1_measurement,
            [],
        )

        size_2_values = sizes.get(
            size_2_measurement,
            [],
        )

        # Save current selections before rebuilding the dropdowns.
        current_size_1 = self.size_dropdown.get()
        current_size_2 = self.size_2_dropdown.get()

        self.size_dropdown.set_measurement(
            size_1_measurement
        )

        self.size_2_dropdown.set_measurement(
            size_2_measurement
        )

        self.size_dropdown.set_values(
            size_1_values
        )

        self.size_2_dropdown.set_values(
            size_2_values
        )

        # Restore the previous selection if it still exists.
        if current_size_1 in size_1_values:
            self.size_dropdown.set(current_size_1)
        elif size_1_values:
            self.size_dropdown.set(size_1_values[0])
        else:
            self.size_dropdown.set("")

        if current_size_2 in size_2_values:
            self.size_2_dropdown.set(current_size_2)
        elif size_2_values:
            self.size_2_dropdown.set(size_2_values[0])
        else:
            self.size_2_dropdown.set("")

    def on_measurement_selected(
        self,
        value=None,
    ):
        if value:
            self.measurement_dropdown.setCurrentText(
                value
            )

        self.refresh_size_dropdowns()

        self.update_camera_metadata()

    # ======================================================================
    # Window size
    # ======================================================================

    def load_window_size(self):
        try:
            if not os.path.exists(
                SETTINGS_FILE
            ):
                return (
                    1100,
                    900,
                )

            with open(
                SETTINGS_FILE,
                "r",
                encoding="utf-8",
            ) as file:
                settings = json.load(file)

            if not isinstance(
                settings,
                dict,
            ):
                return (
                    1100,
                    900,
                )

            window_size = settings.get(
                "window_size"
            )

            if not isinstance(
                window_size,
                dict,
            ):
                return (
                    1100,
                    900,
                )

            width = int(
                window_size.get(
                    "width",
                    1100,
                )
            )

            height = int(
                window_size.get(
                    "height",
                    900,
                )
            )

            if width > 0 and height > 0:
                return (
                    width,
                    height,
                )

        except (
            OSError,
            ValueError,
            TypeError,
            json.JSONDecodeError,
        ):
            pass

        return (
            1100,
            900,
        )

    def save_window_size(self):
        try:
            if not os.path.exists(
                SETTINGS_FILE
            ):
                settings = {}

            else:
                with open(
                    SETTINGS_FILE,
                    "r",
                    encoding="utf-8",
                ) as file:
                    settings = json.load(file)

                if not isinstance(
                    settings,
                    dict,
                ):
                    settings = {}

            settings["window_size"] = {
                "width": self.width(),
                "height": self.height(),
            }

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

        except (
            OSError,
            ValueError,
            TypeError,
            json.JSONDecodeError,
        ):
            pass

    # ======================================================================
    # Shutdown
    # ======================================================================

    def handle_close_event(self, event):
        self.stop()

        event.accept()

    def stop(self):
        if not self.running:
            return

        self.running = False

        self.save_window_size()

        self.stop_camera()

        self.close_recent_crop_previews()

        if (
            self.settings_window is not None
            and self.settings_window.is_open()
        ):
            self.settings_window.close()

        self.close()