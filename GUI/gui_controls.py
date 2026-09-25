import tkinter as tk
import tkinter.ttk as ttk
import cv2
import json
import os

from GUI.gui_constants import (
    CROP_MODE_EXPANDED,
    CROP_MODE_OBJECTS,
    CROP_MODE_PREVIEW,
    CROP_MODE_FULL,
    TRIGGER_MANUAL,
    TRIGGER_AUTOMATIC,
    TRIGGER_CONTINUOUS,
)

from config import SETTINGS_FILE
from config import DEFAULT_VIDEO_SOURCE


def get_available_video_sources(max_sources=10):
    available = []

    for index in range(max_sources):
        cap = cv2.VideoCapture(index)

        if cap.isOpened():
            success, frame = cap.read()

            if success and frame is not None:
                available.append(index)

        cap.release()

    return available

class ControlsMixin:

    def create_below_webcam_frame(self):
        self.below_webcam_container = tk.Frame(
            self.root,
            height=220,
        )

        self.below_webcam_container.pack(
            fill=tk.X,
            padx=10,
            pady=(0, 10),
        )

        self.below_webcam_container.pack_propagate(False)

        self.below_webcam_canvas = tk.Canvas(
            self.below_webcam_container,
            highlightthickness=0,
        )

        self.below_webcam_canvas.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True,
        )

        self.below_webcam_scrollbar = ttk.Scrollbar(
            self.below_webcam_container,
            orient=tk.VERTICAL,
            command=self.below_webcam_canvas.yview,
        )

        self.below_webcam_scrollbar.pack(
            side=tk.RIGHT,
            fill=tk.Y,
        )

        self.below_webcam_canvas.configure(
            yscrollcommand=self.below_webcam_scrollbar.set,
        )

        self.below_webcam_frame = tk.Frame(
            self.below_webcam_canvas,
            bd=2,
            relief=tk.GROOVE,
            padx=8,
            pady=8,
        )

        self.below_webcam_window = (
            self.below_webcam_canvas.create_window(
                (0, 0),
                window=self.below_webcam_frame,
                anchor="nw",
            )
        )

        self.below_webcam_frame.bind(
            "<Configure>",
            self.update_below_webcam_scroll_region,
        )

        self.below_webcam_canvas.bind(
            "<Configure>",
            self.resize_below_webcam_content,
        )

        self.below_webcam_canvas.bind(
            "<MouseWheel>",
            self.on_below_webcam_mousewheel,
        )

    def on_video_source_changed(self, event=None):
        if self.camera is None:
            return

        try:
            source = int(
                self.video_source_var.get()
            )
        except ValueError:
            return

        self.camera.set_video_source(
            source
        )

    def update_below_webcam_scroll_region(self, event=None):
        self.below_webcam_canvas.configure(
            scrollregion=self.below_webcam_canvas.bbox("all")
        )

    def resize_below_webcam_content(self, event):
        self.below_webcam_canvas.itemconfig(
            self.below_webcam_window,
            width=max(event.width, self.below_webcam_frame.winfo_reqwidth()),
        )

    def on_below_webcam_mousewheel(self, event):
        self.below_webcam_canvas.yview_scroll(
            int(-1 * (event.delta / 120)),
            "units",
        )

    def create_control_frame(self):
        self.control_frame = tk.Frame(
            self.below_webcam_frame,
            bd=2,
            relief=tk.GROOVE,
            padx=8,
            pady=6,
        )

        self.control_frame.pack(
            fill=tk.X,
            padx=10,
            pady=(0, 8),
        )

        self.control_canvas = tk.Canvas(
            self.control_frame,
            highlightthickness=0,
            bd=0,
            height=48,
        )

        self.control_canvas.pack(
            side=tk.TOP,
            fill=tk.BOTH,
            expand=True,
        )

        self.control_xscrollbar = ttk.Scrollbar(
            self.control_frame,
            orient=tk.HORIZONTAL,
            command=self.control_canvas.xview,
        )

        self.control_xscrollbar.pack(
            side=tk.BOTTOM,
            fill=tk.X,
        )

        self.control_canvas.configure(
            xscrollcommand=self.control_xscrollbar.set,
        )

        self.control_content = tk.Frame(
            self.control_canvas,
            padx=8,
            pady=2,
        )

        self.control_window = self.control_canvas.create_window(
            (0, 0),
            window=self.control_content,
            anchor="nw",
        )

        self.control_content.bind(
            "<Configure>",
            self.update_control_scroll_region,
        )

        self.control_canvas.bind(
            "<Configure>",
            self.resize_control_content,
        )

        self.require_red_var = tk.BooleanVar(
            value=True
        )

        self.require_red_check = tk.Checkbutton(
            self.control_content,
            text="Require Red Scan",
            variable=self.require_red_var,
            command=self.on_require_red_changed,
            font=("Arial", 11),
        )

        self.require_red_check.pack(
            side=tk.LEFT,
            padx=8,
        )

        tk.Label(
            self.control_content,
            text="Mode:",
            font=("Arial", 11, "bold"),
        ).pack(
            side=tk.LEFT,
            padx=(2, 5),
        )

        self.trigger_mode_var = tk.StringVar(
            value=TRIGGER_MANUAL
        )

        self.trigger_mode_dropdown = ttk.Combobox(
            self.control_content,
            textvariable=self.trigger_mode_var,
            values=[
                TRIGGER_MANUAL,
                TRIGGER_AUTOMATIC,
                TRIGGER_CONTINUOUS,
            ],
            state="readonly",
            width=20,
        )

        self.trigger_mode_dropdown.pack(
            side=tk.LEFT,
            padx=5,
        )

        self.trigger_mode_dropdown.bind(
            "<<ComboboxSelected>>",
            self.on_trigger_mode_changed,
        )

        tk.Label(
            self.control_content,
            text="Camera:",
            font=("Arial", 11, "bold"),
        ).pack(
            side=tk.LEFT,
            padx=(15, 5),
        )

        default_source = DEFAULT_VIDEO_SOURCE

        self.video_source_var = tk.StringVar(
            value=str(default_source)
        )

        self.video_source_dropdown = ttk.Combobox(
            self.control_content,
            textvariable=self.video_source_var,
            values=[
                "0",
                "1",
                "2",
                "3",
            ],
            state="readonly",
            width=8,
        )

        self.video_source_dropdown.pack(
            side=tk.LEFT,
            padx=5,
        )

        self.video_source_dropdown.bind(
            "<<ComboboxSelected>>",
            self.on_video_source_changed,
        )

        self.manual_capture_key = "space"

        if os.path.exists(SETTINGS_FILE):
            try:
                with open(
                    SETTINGS_FILE,
                    "r",
                    encoding="utf-8",
                ) as file:
                    settings = json.load(file)

                self.manual_capture_key = settings.get(
                    "manual_capture_key",
                    "space",
                )

            except (
                OSError,
                ValueError,
                TypeError,
                json.JSONDecodeError,
            ):
                pass

        self.manual_trigger_button = tk.Button(
            self.control_content,
            text=f"Capture [{self.manual_capture_key}]",
            command=self.manual_trigger,
            font=("Arial", 11, "bold"),
            width=18,
        )

        self.manual_trigger_button.pack(
            side=tk.LEFT,
            padx=8,
        )

        tk.Label(
            self.control_content,
            text="Crop:",
            font=("Arial", 11, "bold"),
        ).pack(
            side=tk.LEFT,
            padx=(15, 5),
        )

        self.crop_mode_var = tk.StringVar(
            value=CROP_MODE_FULL
        )

        self.crop_mode_dropdown = ttk.Combobox(
            self.control_content,
            textvariable=self.crop_mode_var,
            values=[
                CROP_MODE_FULL,
                CROP_MODE_PREVIEW,
                CROP_MODE_OBJECTS,
                CROP_MODE_EXPANDED,
            ],
            state="readonly",
            width=30,
        )

        self.crop_mode_dropdown.pack(
            side=tk.LEFT,
            padx=5,
        )

        self.crop_mode_dropdown.bind(
            "<<ComboboxSelected>>",
            self.on_crop_mode_changed,
        )

        self.update_manual_button_state()

        self.update_manual_capture_key(
            self.manual_capture_key
        )

    def update_control_scroll_region(self, event=None):
        self.control_canvas.configure(
            scrollregion=self.control_canvas.bbox("all")
        )

    def resize_control_content(self, event):
        self.control_canvas.itemconfigure(
            self.control_window,
            width=max(event.width, self.control_content.winfo_reqwidth()),
        )

    def update_manual_capture_key(self, key):
        if hasattr(self, "manual_capture_key"):
            self.root.unbind(
                f"<{self.manual_capture_key}>"
            )

        self.manual_capture_key = key

        self.root.bind(
            f"<{self.manual_capture_key}>",
            self.on_manual_key,
        )

        if hasattr(self, "manual_trigger_button"):
            self.manual_trigger_button.config(
                text=f"Capture [{self.manual_capture_key}]"
            )

    def on_inventory_type_changed(
        self,
        event=None,
    ):
        if self.camera is None:
            return

        self.camera.set_inventory_type(
            self.inventory_type_var.get()
        )

    def on_require_red_changed(self):
        if self.camera is None:
            return

        self.camera.set_require_red_for_automatic(
            self.require_red_var.get()
        )

    def on_trigger_mode_changed(self, event=None):
        if self.camera is None:
            return

        mode = self.trigger_mode_var.get()

        self.camera.set_trigger_mode(mode)

        self.update_manual_button_state()

    def update_manual_button_state(self):
        self.manual_trigger_button.config(
            state=tk.NORMAL
        )

    def on_crop_mode_changed(self, event=None):
        if self.camera is None:
            return

        self.camera.set_crop_mode(
            self.crop_mode_var.get()
        )

    def commit_metadata_entries(self):
        self.update_camera_metadata()

    def manual_trigger(self):
        if self.camera is None:
            return

        self.camera.request_manual_capture()

    def on_manual_key(self, event=None):
        if self.trigger_mode_var.get() == TRIGGER_MANUAL:
            self.manual_trigger()

    def create_status_display(self):
        self.status_label = tk.Label(
            self.below_webcam_frame,
            text="Waiting for objects...",
            font=("Arial", 14),
            anchor="w",
        )

        self.status_label.pack(
            fill=tk.X,
            pady=5,
        )

    def create_count_display(self):
        self.count_label = tk.Label(
            self.below_webcam_frame,
            text="Crops: 0",
            font=("Arial", 14),
            anchor="w",
        )

        self.count_label.pack(
            fill=tk.X,
            pady=5,
        )

    def create_box_display_controls(self, parent):
        self.crop_box_var = tk.BooleanVar(
            value=False
        )

        self.crop_box_check = tk.Checkbutton(
            parent,
            text="Preview Crop",
            variable=self.crop_box_var,
            command=self.update_box_display,
            font=("Arial", 11),
        )

        self.crop_box_check.pack(
            side=tk.LEFT,
            padx=5,
        )

        self.counting_box_var = tk.BooleanVar(
            value=False
        )

        self.counting_box_check = tk.Checkbutton(
            parent,
            text="Counting Box",
            variable=self.counting_box_var,
            command=self.update_box_display,
            font=("Arial", 11),
        )

        self.counting_box_check.pack(
            side=tk.LEFT,
            padx=5,
        )

    def update_box_display(self):
        self.show_crop_box = self.crop_box_var.get()
        self.show_counting_box = self.counting_box_var.get()

        if self.camera is not None:
            self.camera.set_box_display(
                self.show_crop_box,
                self.show_counting_box,
            )

    def create_action_buttons(self):
        frame = tk.Frame(
            self.below_webcam_frame
        )

        frame.pack(
            fill=tk.X,
            pady=(5, 0),
        )

        self.create_box_display_controls(frame)
        # self.create_analyze_button(frame)
        # self.create_logger_button(frame)
        self.create_stop_button(frame)

    # def create_analyze_button(self, parent):
    #     self.analyze_button = tk.Button(
    #         parent,
    #         text="Analyze Images",
    #         command=self.start_analyzer,
    #         font=("Arial", 12),
    #         width=18,
    #     )

    #     self.analyze_button.pack(
    #         side=tk.LEFT,
    #         padx=5,
    #     )

    # def create_logger_button(self, parent):
    #     self.logger_button = tk.Button(
    #         parent,
    #         text="Run Logger",
    #         command=self.run_logger,
    #         font=("Arial", 12),
    #         width=18,
    #     )

    #     self.logger_button.pack(
    #         side=tk.LEFT,
    #         padx=5,
    #     )

    def create_stop_button(self, parent):
        self.stop_button = tk.Button(
            parent,
            text="Stop",
            command=self.stop,
            font=("Arial", 12),
            width=12,
        )

        self.stop_button.pack(
            side=tk.RIGHT,
            padx=5,
        )