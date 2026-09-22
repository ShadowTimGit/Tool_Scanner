import tkinter as tk
from tkinter import ttk, messagebox

from settings_menu.settings_config import (
    DEFAULT_SAE_SIZES,
    DEFAULT_METRIC_SIZES,
    DEFAULT_OTHER
)


class SizeSettings:

    def __init__(
        self,
        parent,
        on_sizes_changed,
    ):
        self.parent = parent
        self.on_sizes_changed = on_sizes_changed

        self.sizes = {
            "SAE": list(DEFAULT_SAE_SIZES),
            "Metric": list(DEFAULT_METRIC_SIZES),
            "Other": list(DEFAULT_OTHER),
            "DUAL": [],
        }
        self.create_gui()

    # =========================================================
    # GUI
    # =========================================================

    def create_gui(self):
        main_frame = tk.Frame(
            self.parent,
            padx=15,
            pady=15,
        )

        main_frame.pack(
            fill=tk.BOTH,
            expand=True,
        )

        self.create_size_editor(
            main_frame
        )

    def create_size_editor(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="General Sizes",
            padx=15,
            pady=15,
        )

        frame.pack(
            fill=tk.BOTH,
            expand=True,
        )

        # -----------------------------------------------------
        # Measurement System
        # -----------------------------------------------------

        tk.Label(
            frame,
            text="Measurement System:",
            font=("Arial", 11),
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 5),
        )

        self.measurement_var = tk.StringVar(
            value="SAE"
        )

        self.measurement_dropdown = ttk.Combobox(
            frame,
            textvariable=self.measurement_var,
            state="readonly",
            values=[
                "SAE",
                "Metric",
                "Other",
                "DUAL",
            ],
            width=20,
        )

        self.measurement_dropdown.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(0, 15),
        )

        self.measurement_dropdown.bind(
            "<<ComboboxSelected>>",
            self.on_measurement_changed,
        )

        # -----------------------------------------------------
        # Size List
        # -----------------------------------------------------

        tk.Label(
            frame,
            text="Available Sizes:",
            font=("Arial", 11),
        ).grid(
            row=2,
            column=0,
            sticky="w",
            pady=(0, 5),
        )

        list_frame = tk.Frame(frame)

        list_frame.grid(
            row=3,
            column=0,
            sticky="nsew",
        )

        list_frame.grid_columnconfigure(
            0,
            weight=1,
        )

        list_frame.grid_rowconfigure(
            0,
            weight=1,
        )

        self.size_listbox = tk.Listbox(
            list_frame,
            height=15,
            exportselection=False,
            font=("Arial", 11),
        )

        self.size_listbox.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        scrollbar = ttk.Scrollbar(
            list_frame,
            orient=tk.VERTICAL,
            command=self.size_listbox.yview,
        )

        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        self.size_listbox.config(
            yscrollcommand=scrollbar.set
        )

        # -----------------------------------------------------
        # Controls
        # -----------------------------------------------------

        controls = tk.Frame(frame)

        controls.grid(
            row=4,
            column=0,
            sticky="ew",
            pady=(10, 0),
        )

        controls.grid_columnconfigure(
            0,
            weight=1,
        )

        self.size_entry = tk.Entry(
            controls,
            font=("Arial", 11),
        )

        self.size_entry.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 5),
        )

        tk.Button(
            controls,
            text="Add Size",
            width=12,
            command=self.add_size,
        ).grid(
            row=0,
            column=1,
            padx=2,
        )

        tk.Button(
            controls,
            text="Remove Size",
            width=12,
            command=self.remove_size,
        ).grid(
            row=0,
            column=2,
            padx=2,
        )

        frame.grid_columnconfigure(
            0,
            weight=1,
        )

        frame.grid_rowconfigure(
            3,
            weight=1,
        )

        self.refresh_size_list()

    # =========================================================
    # Measurement Selection
    # =========================================================

    def on_measurement_changed(self, event=None):
        self.refresh_size_list()

    # =========================================================
    # Add Size
    # =========================================================

    def add_size(self):
        measurement = self.measurement_var.get()

        if measurement in {"Other", "DUAL"}:
            return

        size = self.size_entry.get().strip()

        if not size:
            return

        sizes = self.sizes[measurement]

        if any(
            existing.casefold() == size.casefold()
            for existing in sizes
        ):
            messagebox.showwarning(
                "Size Exists",
                (
                    f"{size} already exists in "
                    f"{measurement} sizes."
                ),
                parent=self.parent,
            )
            return

        sizes.append(size)

        self.size_entry.delete(
            0,
            tk.END,
        )

        self.sort_sizes(
            measurement
        )

        self.save_sizes()

        self.refresh_size_list()

        self.on_sizes_changed()

    # =========================================================
    # Remove Size
    # =========================================================

    def remove_size(self):
        measurement = self.measurement_var.get()

        if measurement in {"Other", "DUAL"}:
            return

        selection = (
            self.size_listbox.curselection()
        )

        if not selection:
            messagebox.showwarning(
                "Select Size",
                "Select a size to remove.",
                parent=self.parent,
            )
            return

        size = self.size_listbox.get(
            selection[0]
        )

        answer = messagebox.askyesno(
            "Remove Size",
            (
                f"Remove '{size}' from "
                f"{measurement} sizes?"
            ),
            parent=self.parent,
        )

        if not answer:
            return

        self.sizes[measurement].remove(
            size
        )

        self.save_sizes()

        self.refresh_size_list()

        self.on_sizes_changed()

    # =========================================================
    # Refresh
    # =========================================================

    def refresh_size_list(self):
        measurement = self.measurement_var.get()

        self.size_listbox.delete(
            0,
            tk.END,
        )
        if measurement == "Other":
            sizes = self.sizes.get(
                "Other",
                [],
            )

        elif measurement == "DUAL":
            sizes = []

        else:
            sizes = self.sizes.get(
                measurement,
                [],
            )

        for size in sizes:
            self.size_listbox.insert(
                tk.END,
                size,
            )

    # =========================================================
    # Sorting
    # =========================================================

    def sort_sizes(self, measurement):
        self.sizes[measurement].sort(
            key=self.size_sort_key
        )

    @staticmethod
    def size_sort_key(size):
        value = size.strip().lower()

        # Metric
        if value.endswith("mm"):
            try:
                return (
                    1,
                    float(
                        value[:-2]
                    ),
                )
            except ValueError:
                pass

        # SAE fractions / mixed numbers
        try:
            if "-" in value:
                whole, fraction = value.split(
                    "-",
                    1,
                )

                numerator, denominator = (
                    fraction.split(
                        "/",
                        1,
                    )
                )

                numeric = (
                    float(whole)
                    + (
                        float(numerator)
                        / float(denominator)
                    )
                )

            elif "/" in value:
                numerator, denominator = (
                    value.split(
                        "/",
                        1,
                    )
                )

                numeric = (
                    float(numerator)
                    / float(denominator)
                )

            else:
                numeric = float(value)

            return (
                0,
                numeric,
            )

        except ValueError:
            return (
                2,
                value,
            )

    # =========================================================
    # Persistence
    # =========================================================

    def save_sizes(self):
        from settings_menu.tool_settings import (
            ToolSettings,
        )

        ToolSettings.save_sizes_data(
            self.sizes
        )