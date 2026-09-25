import json
import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

from master_conversion import convert_item_master

from config import (
    SETTINGS_FILE,
    OUTPUT_DIR,
)
from Camera.camera import SUPPORTED_RESOLUTIONS

from logger import rebuild_workbook_from_json, sync_json_from_workbook

class GeneralSettings:
    def __init__(
        self,
        parent,
        camera,
        main_gui,
    ):
        self.parent = parent
        self.camera = camera
        self.main_gui = main_gui

        self.crop_analyzed_images = tk.BooleanVar(
            value=False,
        )

        self.camera_resolution = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.log_dir = tk.StringVar()
        self.manual_capture_key = tk.StringVar(
            value="space"
        )

        self.load_settings()

        if hasattr(
            self.main_gui,
            "update_manual_capture_key",
        ):
            self.main_gui.update_manual_capture_key(
                self.manual_capture_key.get()
            )

        self.create_gui()

    def load_settings(self):

        self.output_dir.set(OUTPUT_DIR)

        if not os.path.exists(SETTINGS_FILE):
            self.camera_resolution.set(
                f"{self.camera.camera_width}x"
                f"{self.camera.camera_height}"
            )
            return

        try:
            with open(
                SETTINGS_FILE,
                "r",
                encoding="utf-8",
            ) as file:
                settings = json.load(file)

                self.output_dir.set(
                    settings.get(
                        "output_dir",
                        OUTPUT_DIR,
                    )
                )

            self.crop_analyzed_images.set(
                bool(
                    settings.get(
                        "crop_analyzed_images",
                        False,
                    )
                )
            )

            self.manual_capture_key.set(
                settings.get(
                    "manual_capture_key",
                    "space",
                )
            )
        
            resolution = settings.get(
                "camera_resolution"
            )

            if isinstance(
                resolution,
                dict,
            ):
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
                    self.camera_resolution.set(
                        f"{width}x{height}"
                    )
                else:
                    self.camera_resolution.set(
                        f"{self.camera.camera_width}x"
                        f"{self.camera.camera_height}"
                    )

            else:
                self.camera_resolution.set(
                    f"{self.camera.camera_width}x"
                    f"{self.camera.camera_height}"
                )

        except (
            OSError,
            ValueError,
            TypeError,
            json.JSONDecodeError,
        ):
            self.camera_resolution.set(
                f"{self.camera.camera_width}x"
                f"{self.camera.camera_height}"
            )

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

                if isinstance(
                    existing_settings,
                    dict,
                ):
                    settings = existing_settings

            except (
                OSError,
                ValueError,
                TypeError,
                json.JSONDecodeError,
            ):
                settings = {}

        settings["output_dir"] = self.output_dir.get()

        settings["crop_analyzed_images"] = (
            self.crop_analyzed_images.get()
        )

        settings["camera_resolution"] = {
            "width": self.camera.camera_width,
            "height": self.camera.camera_height,
        }

        settings["manual_capture_key"] = (
            self.manual_capture_key.get()
        )

        try:
            os.makedirs(
                os.path.dirname(SETTINGS_FILE),
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

        except OSError:
            pass

    def choose_output_dir(self):
        directory = filedialog.askdirectory(
            title="Select Output Directory",
            initialdir=self.output_dir.get(),
        )

        if directory:
            self.output_dir.set(directory)
            self.save_settings()


    def change_manual_capture_key(self, event=None):
        key = self.manual_capture_key.get()

        print("Selected key:", key)
        print("Main GUI:", self.main_gui)
        print(
            "Has update method:",
            hasattr(
                self.main_gui,
                "update_manual_capture_key",
            ),
        )

        if hasattr(
            self.main_gui,
            "update_manual_capture_key",
        ):
            self.main_gui.update_manual_capture_key(key)

        self.save_settings()

    def change_camera_resolution(self, event=None):
        value = self.camera_resolution.get()

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
            self.camera_resolution.set(
                f"{self.camera.camera_width}x"
                f"{self.camera.camera_height}"
            )

    def rebuild_logger(self):
        try:
            rebuild_workbook_from_json()
        except Exception as error:
            print(
                f"ERROR: Could not rebuild logger: "
                f"{error}"
            )

    def sync_logger(self):
        try:
            sync_json_from_workbook()
        except Exception as error:
            print(
                f"ERROR: Could not sync logger to json: "
                f"{error}"
            )

    def create_gui(self):
        frame = tk.Frame(
            self.parent,
            padx=20,
            pady=20,
        )

        frame.pack(
            fill=tk.BOTH,
            expand=True,
        )

        tk.Label(
            frame,
            text="General Settings",
            font=("Arial", 14, "bold"),
        ).pack(
            anchor="w",
            pady=(0, 20),
        )

        settings_frame = tk.Frame(
            frame,
            relief=tk.GROOVE,
            borderwidth=1,
            padx=15,
            pady=15,
        )

        settings_frame.pack(
            fill=tk.X,
            anchor="w",
        )

        # -------------------------
        # Output Settings
        # -------------------------

        tk.Label(
            settings_frame,
            text="Output Directory",
            font=("Arial", 10, "bold"),
        ).pack(
            anchor="w",
            pady=(0, 5),
        )

        output_frame = tk.Frame(
            settings_frame,
        )

        output_frame.pack(
            fill=tk.X,
            pady=(0, 15),
        )

        tk.Entry(
            output_frame,
            textvariable=self.output_dir,
            state="readonly",
        ).pack(
            side=tk.LEFT,
            fill=tk.X,
            expand=True,
        )

        tk.Button(
            output_frame,
            text="Browse...",
            command=self.choose_output_dir,
        ).pack(
            side=tk.LEFT,
            padx=(10, 0),
        )


        tk.Label(
            settings_frame,
            text="Log Directory",
            font=("Arial", 10, "bold"),
        ).pack(
            anchor="w",
            pady=(0, 5),
        )

        # -------------------------
        # Camera Resolution
        # -------------------------

        tk.Label(
            settings_frame,
            text="Camera Resolution",
            font=("Arial", 10, "bold"),
        ).pack(
            anchor="w",
            pady=(0, 5),
        )

        resolution_values = [
            f"{width}x{height}"
            for width, height in SUPPORTED_RESOLUTIONS
        ]

        resolution_dropdown = ttk.Combobox(
            settings_frame,
            textvariable=self.camera_resolution,
            values=resolution_values,
            state="readonly",
            width=18,
        )

        resolution_dropdown.pack(
            anchor="w",
            pady=(0, 20),
        )

        resolution_dropdown.bind(
            "<<ComboboxSelected>>",
            self.change_camera_resolution,
        )

        # -------------------------
        # Manual Capture Shortcut
        # -------------------------

        tk.Label(
            settings_frame,
            text="Manual Capture Shortcut",
            font=("Arial", 10, "bold"),
        ).pack(
            anchor="w",
            pady=(0, 5),
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

        manual_capture_dropdown = ttk.Combobox(
            settings_frame,
            textvariable=self.manual_capture_key,
            values=manual_capture_values,
            state="readonly",
            width=18,
        )

        manual_capture_dropdown.pack(
            anchor="w",
            pady=(0, 20),
        )

        manual_capture_dropdown.bind(
            "<<ComboboxSelected>>",
            self.change_manual_capture_key,
        )

        # -------------------------
        # OCR Settings
        # -------------------------

        tk.Checkbutton(
            settings_frame,
            text="Crop images before OCR analysis",
            variable=self.crop_analyzed_images,
            command=self.save_settings,
        ).pack(
            anchor="w",
        )

        # -------------------------
        # Rebuild and Sync Logs
        # -------------------------

        tk.Label(
            settings_frame,
            text="The Rebuilder will rebuild the excel spreadsheet from existing JSON files. Can be used to create a Backup.",
            font=("Arial", 10, "bold"),
        ).pack(
            anchor="w",
            pady=(10, 0),
        )

        tk.Button(
            settings_frame,
            text="Rebuild Logger",
            command=self.rebuild_logger,
        ).pack(
            anchor="w",
        )

        tk.Label(
            settings_frame,
            text="The Sync Logger will modify existing JSON data based on the Tool_Logger.xslx file. Dangerous.",
            font=("Arial", 10, "bold"),
        ).pack(
            anchor="w",
            pady=(10, 0),
        )

        tk.Button(
            settings_frame,
            text="Sync Logger",
            command=self.sync_logger,
        ).pack(
            anchor="w",
            pady=(10, 0),
        )



    def convert_item_master(self):
        file_path = filedialog.askopenfilename(
            title="Select Item Master Workbook",
            filetypes=[
                (
                    "Excel Files",
                    "*.xlsx *.xlsm *.xltx *.xltm",
                ),
                (
                    "All Files",
                    "*.*",
                ),
            ],
        )

        if not file_path:
            return

        try:
            convert_item_master(
                file_path
            )

        except Exception as error:
            print(
                f"ERROR: Could not convert Item Master: "
                f"{error}"
            )
