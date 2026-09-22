import tkinter as tk
import tkinter.ttk as ttk

from settings_menu.settings import SettingsWindow
from settings_menu.brand_settings import BrandSettings
from settings_menu.tool_settings import ToolSettings


class ToolsMixin:

    def create_tool_selection(self):
        frame = tk.Frame(
            self.below_webcam_frame
        )

        frame.pack(
            fill=tk.X,
            pady=5,
        )

        self.create_tool_dropdown(frame)
        self.create_specialization_dropdown(frame)
        self.create_brand_dropdown(frame)
        self.create_settings_button(frame)

    def create_tool_dropdown(self, parent):
        tk.Label(
            parent,
            text="Tool:",
            font=("Arial", 12),
        ).pack(
            side=tk.LEFT,
            padx=5,
        )

        self.tool_var = tk.StringVar()

        self.tool_dropdown = ttk.Combobox(
            parent,
            textvariable=self.tool_var,
            state="readonly",
            width=20,
        )

        self.tool_dropdown.pack(
            side=tk.LEFT,
            padx=5,
        )

        self.tool_dropdown.bind(
            "<<ComboboxSelected>>",
            self.on_tool_selected,
        )

    def create_specialization_dropdown(self, parent):
        tk.Label(
            parent,
            text="Specialization:",
            font=("Arial", 12),
        ).pack(
            side=tk.LEFT,
            padx=5,
        )

        self.specialization_var = tk.StringVar()

        self.specialization_dropdown = ttk.Combobox(
            parent,
            textvariable=self.specialization_var,
            state="readonly",
            width=25,
        )

        self.specialization_dropdown.pack(
            side=tk.LEFT,
            padx=5,
        )

        self.specialization_dropdown.bind(
            "<<ComboboxSelected>>",
            self.on_specialization_selected,
        )

    def create_brand_dropdown(self, parent):
        tk.Label(
            parent,
            text="Brand:",
            font=("Arial", 12),
        ).pack(
            side=tk.LEFT,
            padx=5,
        )

        self.brand_var = tk.StringVar()

        self.brand_dropdown = ttk.Combobox(
            parent,
            textvariable=self.brand_var,
            state="readonly",
            width=20,
        )

        self.brand_dropdown.pack(
            side=tk.LEFT,
            padx=5,
        )

        self.brand_dropdown.bind(
            "<<ComboboxSelected>>",
            self.on_brand_selected,
        )

        self.refresh_brand_dropdown()

    def refresh_brand_dropdown(self):
        brand_names = list(
            self.brands.keys()
        )

        self.brand_dropdown["values"] = brand_names

        if self.selected_brand in brand_names:
            self.brand_var.set(
                self.selected_brand
            )

        elif brand_names:
            self.selected_brand = brand_names[0]

            self.brand_var.set(
                self.selected_brand
            )

        else:
            self.selected_brand = ""
            self.brand_var.set("")

    def on_brand_selected(self, event=None):
        self.selected_brand = self.brand_var.get()

        if self.camera is not None:
            self.camera.set_brand_selection(
                self.selected_brand
            )

    def brands_changed(self):
        self.brands = BrandSettings.load_brands()

        self.refresh_brand_dropdown()

        if self.camera is not None:
            self.camera.set_brand_selection(
                self.selected_brand
            )

    def create_settings_button(self, parent):
        self.settings_button = tk.Button(
            parent,
            text="Settings",
            command=self.open_settings,
            font=("Arial", 12),
            width=12,
        )

        self.settings_button.pack(
            side=tk.RIGHT,
            padx=5,
        )

    def on_specialization_selected(self, event=None):
        if self.camera is None:
            return

        self.camera.set_tool_selection(
            self.tool_var.get(),
            self.specialization_var.get(),
        )

    def on_tool_selected(self, event=None):
        if self.camera is None:
            return

        tool_name = self.tool_var.get()

        if tool_name not in self.tools:
            self.specialization_dropdown["values"] = []
            self.specialization_dropdown.set("")

            self.camera.set_tool_selection(
                "",
                "",
            )

            return

        specializations = self.tools[tool_name]

        self.specialization_dropdown["values"] = (
            specializations
        )

        if specializations:
            self.specialization_dropdown.set(
                specializations[0]
            )

            self.camera.set_tool_selection(
                tool_name,
                specializations[0],
            )

        else:
            self.specialization_dropdown.set("")

            self.camera.set_tool_selection(
                tool_name,
                "",
            )

    def open_settings(self):
        if self.camera is None:
            self.status_label.config(
                text="Camera is still loading..."
            )
            return

        if (
            self.settings_window is not None
            and self.settings_window.window.winfo_exists()
        ):
            self.settings_window.window.lift()
            return

        self.settings_window = SettingsWindow(
            self.root,
            self.tools,
            self.tools_changed,
            self.camera,
            self.brands_changed,
        )

    def tools_changed(self):
        tool_names = list(
            self.tools.keys()
        )

        self.tool_dropdown["values"] = tool_names

        current_tool = self.tool_var.get()

        if current_tool in self.tools:
            self.tool_dropdown.set(
                current_tool
            )

            self.on_tool_selected()

        elif tool_names:
            self.tool_dropdown.set(
                tool_names[0]
            )

            self.on_tool_selected()

        else:
            self.tool_dropdown.set("")

            self.specialization_dropdown[
                "values"
            ] = []

            self.specialization_dropdown.set("")

            if self.camera is not None:
                self.camera.set_tool_selection(
                    "",
                    "",
                )