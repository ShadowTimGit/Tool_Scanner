import json
import tkinter as tk
import os

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

from settings_menu.brand_settings import BrandSettings
from settings_menu.tool_repository import ToolRepository
from settings_menu.metadata_settings import MetadataSettings
from settings_menu.tool_settings import ToolSettings

from version import APP_VERSION
from tkinter import messagebox

from updater import (
    check_for_updates,
    download_update,
    start_update,
)
from config import SETTINGS_FILE

class ToolScannerGUI(
    VideoMixin,
    ControlsMixin,
    ToolsMixin,
    CameraMixin,
    ProcessMixin,
    RightPanelMixin,
):

    def __init__(self, root):
        self.root = root

        self.root.title(
            "Object Scanner"
        )

        saved_size = self.load_window_size()

        self.root.geometry(
            f"{saved_size[0]}x{saved_size[1]}"
        )

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.stop,
        )

        self.running = True

        self.tools = ToolRepository.load_tools()

        self.brands = BrandSettings.load_brands()

        self.metadata = MetadataSettings.load_metadata()

        self.sizes = ToolSettings.load_sizes_data()

        self.selected_brand = ""

        self.inventory_type_var = tk.StringVar(
            value=INVENTORY_PURCHASE
        )

        self.settings_window = None

        self.current_frame_width = 0
        self.current_frame_height = 0

        self.display_width = 0
        self.display_height = 0

        self.camera = None
        self.camera_ready = False

        self.show_crop_box = True
        self.show_counting_box = True

        self.trigger_mode_var = tk.StringVar(
            value=TRIGGER_MANUAL
        )

        self.crop_mode_var = tk.StringVar(
            value=CROP_MODE_PREVIEW
        )

        self.create_gui()

        self.check_for_updates()

        self.status_label.config(
            text="Loading camera..."
        )

        self.start_camera_initialization()

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
        self.root.after(
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
        result = messagebox.askyesno(
            "Update Available",
            (
                "A new version of Object Scanner "
                "is available.\n\n"
                f"Current version: {APP_VERSION}\n"
                f"Latest version: {latest_version}\n\n"
                "Would you like to update now?"
            ),
        )

        if not result:
            return

        self.download_and_install_update(
            zip_url
        )


    def download_and_install_update(
        self,
        zip_url,
    ):
        messagebox.showinfo(
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
        self.root.after(
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

            
    def create_gui(self):
        self.create_right_panel()

        self.create_video_display()

        self.create_below_webcam_frame()

        self.create_control_frame()

        self.create_status_display()

        self.create_count_display()

        self.create_action_buttons()

        self.refresh_main_settings()

    def on_inventory_type_changed(
        self,
        event=None,
    ):
        if self.camera is None:
            return

        self.camera.set_inventory_type(
            self.inventory_type_var.get()
        )

    def refresh_main_settings(self):
        self.tools = ToolRepository.load_tools()

        self.brands = BrandSettings.load_brands()

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

        self.measurement_dropdown["values"] = [
            "SAE",
            "Metric",
            "Other",
            "DUAL",
        ]
        self.drive_dropdown["values"] = metadata.get(
            "drive",
            [],
        )

        self.point_dropdown["values"] = metadata.get(
            "point",
            [],
        )

        self.specialty_socket_dropdown["values"] = metadata.get(
            "specialty_socket",
            [],
        )

        if self.measurement_var.get() not in (
            "SAE",
            "Metric",
            "Other",
            "DUAL",
        ):
            self.measurement_var.set("SAE")

        if self.drive_var.get() not in self.drive_dropdown["values"]:
            if self.drive_dropdown["values"]:
                self.drive_var.set(self.drive_dropdown["values"][0])
            else:
                self.drive_var.set("")

        if self.point_var.get() not in self.point_dropdown["values"]:
            if self.point_dropdown["values"]:
                self.point_var.set(self.point_dropdown["values"][0])
            else:
                self.point_var.set("")

        if self.specialty_socket_var.get() not in self.specialty_socket_dropdown["values"]:
            if self.specialty_socket_dropdown["values"]:
                self.specialty_socket_var.set(
                    self.specialty_socket_dropdown["values"][0]
                )
            else:
                self.specialty_socket_var.set("")

    def refresh_size_dropdowns(self):
        sizes = ToolSettings.load_sizes_data()

        measurement = self.measurement_var.get()

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

        if self.size_var.get() not in size_1_values:
            if size_1_values:
                self.size_var.set(
                    size_1_values[0]
                )
            else:
                self.size_var.set("")

        if self.size_2_var.get() not in size_2_values:
            if size_2_values:
                self.size_2_var.set(
                    size_2_values[0]
                )
            else:
                self.size_2_var.set("")

    def on_measurement_selected(self, event=None):
        self.refresh_size_dropdowns()
        self.update_camera_metadata()

    def load_window_size(self):
        try:
            if not os.path.exists(SETTINGS_FILE):
                return (1100, 900)

            with open(
                SETTINGS_FILE,
                "r",
                encoding="utf-8",
            ) as file:
                settings = json.load(file)

            if not isinstance(settings, dict):
                return (1100, 900)

            window_size = settings.get("window_size")

            if not isinstance(window_size, dict):
                return (1100, 900)

            width = int(window_size.get("width", 1100))
            height = int(window_size.get("height", 900))

            if width > 0 and height > 0:
                return (width, height)

        except (
            OSError,
            ValueError,
            TypeError,
            json.JSONDecodeError,
        ):
            pass

        return (1100, 900)

    def save_window_size(self):
        try:
            if not os.path.exists(SETTINGS_FILE):
                settings = {}
            else:
                with open(
                    SETTINGS_FILE,
                    "r",
                    encoding="utf-8",
                ) as file:
                    settings = json.load(file)

                if not isinstance(settings, dict):
                    settings = {}

            self.root.update_idletasks()
            settings["window_size"] = {
                "width": self.root.winfo_width(),
                "height": self.root.winfo_height(),
            }

            os.makedirs(
                os.path.dirname(SETTINGS_FILE),
                exist_ok=True,
            )

            with open(
                SETTINGS_FILE,
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(settings, file, indent=4)

        except (
            OSError,
            ValueError,
            TypeError,
            json.JSONDecodeError,
        ):
            pass

    def stop(self):
        if not self.running:
            return

        self.running = False

        self.save_window_size()
        self.stop_camera()

        if (
            self.settings_window is not None
            and self.settings_window.window.winfo_exists()
        ):
            self.settings_window.window.destroy()

        self.root.destroy()