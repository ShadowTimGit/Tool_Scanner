import copy
import json
import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox

from master_conversion import convert_item_master

from config import (
    DEFAULT_BOX,
    DEFAULT_CROP,
    SETTINGS_FILE,
    OUTPUT_DIR,
)
from Camera.camera import SUPPORTED_RESOLUTIONS
from settings_menu.brand_settings import DEFAULT_BRANDS
from settings_menu.inventory_settings import DEFAULT_INVENTORY
from settings_menu.tool_repository import DEFAULT_TOOLS
from settings_menu.settings_config import DEFAULT_METADATA

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
        width = getattr(self.camera, "camera_width", 1920)
        height = getattr(self.camera, "camera_height", 1080)

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

    def reset_settings_file(self, include_window_size=True):
        settings = self._default_settings_dict()
        if include_window_size:
            settings["window_size"] = {
                "width": 1100,
                "height": 900,
            }
        else:
            settings.pop("window_size", None)

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

    def reset_modifiable_settings(self):
        if not messagebox.askyesno(
            "Full Wipe",
            "This will clear the custom option data so the stored lists are blank/NA and can be re-entered manually.\n\nIt does not overwrite the app base settings file.",
            parent=self.parent,
        ):
            return

        empty_brands = {}
        with open(
            os.path.join(
                os.path.dirname(__file__),
                "settings",
                "brands.json",
            ),
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(empty_brands, file, indent=4)

        empty_inventory = {"estimated_values": {}}
        inventory_path = os.path.join(
            os.path.dirname(__file__),
            "settings",
            "inventory_settings.json",
        )
        with open(inventory_path, "w", encoding="utf-8") as file:
            json.dump(empty_inventory, file, indent=4)

        empty_metadata = {
            "sizes": {
                "SAE": ["NA"],
                "Metric": ["NA"],
                "Other": ["NA"],
            },
            "drive": ["NA"],
            "point": ["NA"],
        }
        metadata_path = os.path.join(
            os.path.dirname(__file__),
            "settings",
            "metadata_options.json",
        )
        with open(metadata_path, "w", encoding="utf-8") as file:
            json.dump(empty_metadata, file, indent=4)

        empty_tools = {"NA": ["NA"]}
        tools_path = os.path.join(
            os.path.dirname(__file__),
            "settings",
            "tools.json",
        )
        with open(tools_path, "w", encoding="utf-8") as file:
            json.dump(empty_tools, file, indent=4)

        if hasattr(self.main_gui, "refresh_main_settings"):
            self.main_gui.refresh_main_settings()

        messagebox.showinfo(
            "Full Wipe Complete",
            "The custom option entries have been cleared to blank/NA values and can be re-entered manually.",
            parent=self.parent,
        )

    def reset_all_settings(self):
        if not messagebox.askyesno(
            "Reset All Default Settings",
            "This will restore all stored settings JSON files to their default values: brands.json, inventory_settings.json, metadata_options.json, tools.json, and settings.json.",
            parent=self.parent,
        ):
            return

        with open(
            os.path.join(
                os.path.dirname(__file__),
                "settings",
                "brands.json",
            ),
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(copy.deepcopy(DEFAULT_BRANDS), file, indent=4)

        inventory_path = os.path.join(
            os.path.dirname(__file__),
            "settings",
            "inventory_settings.json",
        )
        with open(inventory_path, "w", encoding="utf-8") as file:
            json.dump({"estimated_values": copy.deepcopy(DEFAULT_INVENTORY)}, file, indent=4)

        metadata_path = os.path.join(
            os.path.dirname(__file__),
            "settings",
            "metadata_options.json",
        )
        default_metadata = copy.deepcopy(DEFAULT_METADATA)
        default_metadata.pop("specialty_socket", None)
        with open(metadata_path, "w", encoding="utf-8") as file:
            json.dump(default_metadata, file, indent=4)

        tools_path = os.path.join(
            os.path.dirname(__file__),
            "settings",
            "tools.json",
        )
        with open(tools_path, "w", encoding="utf-8") as file:
            json.dump(copy.deepcopy(DEFAULT_TOOLS), file, indent=4)

        self.reset_settings_file(include_window_size=True)

        if hasattr(self.main_gui, "refresh_main_settings"):
            self.main_gui.refresh_main_settings()

        messagebox.showinfo(
            "Defaults Restored",
            "The stored JSON settings files have been restored to their default values.",
            parent=self.parent,
        )

    def create_gui(self):
        outer_frame = tk.Frame(
            self.parent,
            padx=20,
            pady=20,
        )

        outer_frame.pack(
            fill=tk.BOTH,
            expand=True,
        )

        canvas = tk.Canvas(
            outer_frame,
            highlightthickness=0,
        )
        scrollbar = ttk.Scrollbar(
            outer_frame,
            orient=tk.VERTICAL,
            command=canvas.yview,
        )

        canvas.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True,
        )
        scrollbar.pack(
            side=tk.RIGHT,
            fill=tk.Y,
        )

        canvas.configure(
            yscrollcommand=scrollbar.set,
        )

        content_frame = tk.Frame(
            canvas,
            padx=4,
            pady=4,
        )
        canvas_window = canvas.create_window(
            (0, 0),
            window=content_frame,
            anchor="nw",
        )

        def _update_scrollregion(event=None):
            canvas_width = max(
                canvas.winfo_width(),
                content_frame.winfo_reqwidth(),
            )
            canvas.itemconfigure(
                canvas_window,
                width=canvas_width,
            )
            canvas.configure(
                scrollregion=canvas.bbox("all"),
            )

        content_frame.bind(
            "<Configure>",
            _update_scrollregion,
        )
        canvas.bind(
            "<Configure>",
            _update_scrollregion,
        )

        tk.Label(
            content_frame,
            text="General Settings",
            font=("Arial", 14, "bold"),
        ).pack(
            anchor="w",
            pady=(0, 20),
        )

        settings_frame = tk.Frame(
            content_frame,
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
        # Camera Resolution + Manual Capture Shortcut
        # -------------------------

        chooser_row = tk.Frame(
            settings_frame,
        )
        chooser_row.pack(
            fill=tk.X,
            pady=(0, 20),
        )

        resolution_frame = tk.Frame(
            chooser_row,
            width=280,
        )
        resolution_frame.pack(
            side=tk.LEFT,
            fill=tk.Y,
            padx=(0, 12),
        )

        tk.Label(
            resolution_frame,
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
            resolution_frame,
            textvariable=self.camera_resolution,
            values=resolution_values,
            state="readonly",
            width=18,
        )

        resolution_dropdown.pack(
            anchor="w",
        )

        resolution_dropdown.bind(
            "<<ComboboxSelected>>",
            self.change_camera_resolution,
        )

        manual_capture_frame = tk.Frame(
            chooser_row,
            width=260,
        )
        manual_capture_frame.pack(
            side=tk.LEFT,
            fill=tk.Y,
        )

        tk.Label(
            manual_capture_frame,
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
            manual_capture_frame,
            textvariable=self.manual_capture_key,
            values=manual_capture_values,
            state="readonly",
            width=18,
        )

        manual_capture_dropdown.pack(
            anchor="w",
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

        tk.Label(
            settings_frame,
            text="Reset all saved custom options to the built-in defaults.",
            font=("Arial", 10, "bold"),
        ).pack(
            anchor="w",
            pady=(20, 0),
        )

        tk.Button(
            settings_frame,
            text="Reset All Default Settings",
            command=self.reset_all_settings,
            width=24,
        ).pack(
            anchor="w",
            pady=(6, 0),
        )

        tk.Button(
            settings_frame,
            text="Full Wipe",
            command=self.reset_modifiable_settings,
            width=24,
        ).pack(
            anchor="w",
            pady=(6, 0),
        )

        canvas.update_idletasks()
        _update_scrollregion()
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
