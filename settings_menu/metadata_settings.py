import json
import os
import copy
import tkinter as tk
from tkinter import ttk, messagebox

from settings_menu.settings_config import DEFAULT_METADATA



SETTINGS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "settings",
)

METADATA_FILE = os.path.join(
    SETTINGS_DIR,
    "metadata_options.json",
)


class MetadataSettings:

    def __init__(
        self,
        parent,
        on_metadata_changed=None,
    ):
        self.parent = parent
        self.on_metadata_changed = (
            on_metadata_changed
        )

        self.metadata = self.load_metadata()
        self.option_widgets = {}
        self.create_gui()

    # =========================================================
    # GUI
    # =========================================================

    def create_gui(self):
        main_frame = tk.Frame(
            self.parent,
            padx=20,
            pady=20,
        )

        main_frame.pack(
            fill=tk.BOTH,
            expand=True,
        )

        # -----------------------------------------------------
        # Header
        # -----------------------------------------------------

        header = tk.Frame(main_frame)

        header.pack(
            fill=tk.X,
            pady=(0, 15),
        )

        tk.Label(
            header,
            text="Product Attributes",
            font=("Arial", 14, "bold"),
        ).pack(
            anchor="w",
        )

        tk.Label(
            header,
            text=(
                "Add or remove options used by the product "
                "attribute dropdowns."
            ),
            font=("Arial", 10),
            anchor="w",
            justify=tk.LEFT,
        ).pack(
            anchor="w",
            pady=(4, 0),
        )

        self.create_option_sections(
            main_frame
        )


    def create_option_sections(self, parent):
        options_frame = tk.Frame(parent)

        options_frame.pack(
            fill=tk.BOTH,
            expand=True,
        )

        options_frame.grid_columnconfigure(
            0,
            weight=1,
        )

        options_frame.grid_columnconfigure(
            1,
            weight=1,
        )

        options_frame.grid_rowconfigure(
            0,
            weight=1,
        )

        options_frame.grid_rowconfigure(
            1,
            weight=1,
        )

        # -----------------------------------------------------
        # Size Dataset
        # -----------------------------------------------------

        self.create_size_editor(
            options_frame
        )

        # -----------------------------------------------------
        # Other Metadata
        # -----------------------------------------------------

        self.create_option_editor(
            options_frame,
            "Point",
            "point",
            1,
            0,
        )

        self.create_option_editor(
            options_frame,
            "Drive",
            "drive",
            0,
            1,
        )

    def create_size_editor(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="Sizes",
            padx=12,
            pady=12,
            font=("Arial", 10, "bold"),
        )

        frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=6,
            pady=6,
        )

        frame.grid_columnconfigure(
            0,
            weight=1,
        )

        frame.grid_rowconfigure(
            2,
            weight=1,
        )

        tk.Label(
            frame,
            text="Dataset:",
            font=("Arial", 10),
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 5),
        )

        self.size_dataset_var = tk.StringVar(
            value="SAE"
        )

        self.size_dataset_dropdown = ttk.Combobox(
            frame,
            textvariable=self.size_dataset_var,
            state="readonly",
            values=[
                "SAE",
                "Metric",
                "Other",
            ],
        )

        self.size_dataset_dropdown.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(0, 10),
        )

        self.size_dataset_dropdown.bind(
            "<<ComboboxSelected>>",
            lambda event: self.refresh_size_list(),
        )

        list_frame = tk.Frame(frame)

        list_frame.grid(
            row=2,
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
            height=7,
            exportselection=False,
            font=("Arial", 10),
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

        controls = tk.Frame(frame)

        controls.grid(
            row=3,
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
            font=("Arial", 10),
        )

        self.size_entry.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 6),
        )

        tk.Button(
            controls,
            text="Add",
            width=10,
            command=self.add_size,
        ).grid(
            row=0,
            column=1,
            padx=(0, 4),
        )

        tk.Button(
            controls,
            text="Remove",
            width=10,
            command=self.remove_size,
        ).grid(
            row=0,
            column=2,
        )

        self.refresh_size_list()

    def refresh_size_list(self):
        dataset = self.size_dataset_var.get()

        self.size_listbox.delete(
            0,
            tk.END,
        )

        for size in self.metadata["sizes"].get(
            dataset,
            [],
        ):
            self.size_listbox.insert(
                tk.END,
                size,
            )

    def add_size(self):
        dataset = self.size_dataset_var.get()

        value = (
            self.size_entry
            .get()
            .strip()
        )

        if not value:
            return

        sizes = self.metadata["sizes"][dataset]

        if any(
            existing.casefold() == value.casefold()
            for existing in sizes
        ):
            messagebox.showwarning(
                "Size Exists",
                f"'{value}' already exists in {dataset} sizes.",
                parent=self.parent,
            )
            return

        sizes.append(value)

        self.size_entry.delete(
            0,
            tk.END,
        )

        self.save_metadata()

        self.refresh_size_list()

        self.notify_metadata_changed()

    def remove_size(self):
        dataset = self.size_dataset_var.get()

        selection = self.size_listbox.curselection()

        if not selection:
            messagebox.showwarning(
                "Select Size",
                "Select a size to remove.",
                parent=self.parent,
            )
            return

        value = self.size_listbox.get(
            selection[0]
        )

        answer = messagebox.askyesno(
            "Remove Size",
            f"Remove '{value}' from {dataset} sizes?",
            parent=self.parent,
        )

        if not answer:
            return

        self.metadata["sizes"][dataset].remove(
            value
        )

        self.save_metadata()

        self.refresh_size_list()

        self.notify_metadata_changed()

    # =========================================================
    # Reusable Option Editor
    # =========================================================

    def create_option_editor(
        self,
        parent,
        label,
        key,
        row,
        column,
    ):
        frame = tk.LabelFrame(
            parent,
            text=label,
            padx=12,
            pady=12,
            font=("Arial", 10, "bold"),
        )

        frame.grid(
            row=row,
            column=column,
            sticky="nsew",
            padx=6,
            pady=6,
        )

        frame.grid_columnconfigure(
            0,
            weight=1,
        )

        frame.grid_rowconfigure(
            0,
            weight=1,
        )

        # -----------------------------------------------------
        # Current Options
        # -----------------------------------------------------

        list_frame = tk.Frame(frame)

        list_frame.grid(
            row=0,
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

        listbox = tk.Listbox(
            list_frame,
            height=7,
            exportselection=False,
            font=("Arial", 10),
        )

        listbox.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        scrollbar = ttk.Scrollbar(
            list_frame,
            orient=tk.VERTICAL,
            command=listbox.yview,
        )

        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        listbox.config(
            yscrollcommand=scrollbar.set
        )

        # -----------------------------------------------------
        # Controls
        # -----------------------------------------------------

        controls = tk.Frame(frame)

        controls.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(10, 0),
        )

        controls.grid_columnconfigure(
            0,
            weight=1,
        )

        entry = tk.Entry(
            controls,
            font=("Arial", 10),
        )

        entry.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 6),
        )

        add_button = tk.Button(
            controls,
            text="Add",
            width=10,
            command=lambda: self.add_option(
                key,
                entry,
            ),
        )

        add_button.grid(
            row=0,
            column=1,
            padx=(0, 4),
        )

        remove_button = tk.Button(
            controls,
            text="Remove",
            width=10,
            command=lambda: self.remove_option(
                key,
                listbox,
            ),
        )

        remove_button.grid(
            row=0,
            column=2,
        )

        # -----------------------------------------------------
        # Store Widgets
        # -----------------------------------------------------

        self.option_widgets[key] = {
            "listbox": listbox,
            "entry": entry,
        }

        self.refresh_option_list(
            key
        )

    # =========================================================
    # Add Option
    # =========================================================

    def add_option(
        self,
        key,
        entry,
    ):
        value = (
            entry
            .get()
            .strip()
        )

        if not value:
            return

        options = self.metadata[key]

        if any(
            existing.casefold() == value.casefold()
            for existing in options
        ):
            messagebox.showwarning(
                "Option Exists",
                f"'{value}' already exists.",
                parent=self.parent,
            )
            return

        options.append(value)

        entry.delete(
            0,
            tk.END,
        )

        self.save_metadata()

        self.refresh_option_list(
            key
        )

        self.notify_metadata_changed()

    # =========================================================
    # Remove Option
    # =========================================================

    def remove_option(
        self,
        key,
        listbox,
    ):
        selection = listbox.curselection()

        if not selection:
            messagebox.showwarning(
                "Select Option",
                "Select an option to remove.",
                parent=self.parent,
            )
            return

        index = selection[0]

        value = listbox.get(index)

        answer = messagebox.askyesno(
            "Remove Option",
            f"Remove '{value}'?",
            parent=self.parent,
        )

        if not answer:
            return

        self.metadata[key].remove(
            value
        )

        self.save_metadata()

        self.refresh_option_list(
            key
        )

        self.notify_metadata_changed()

    # =========================================================
    # Refresh
    # =========================================================

    def refresh_option_list(
        self,
        key,
    ):
        widgets = self.option_widgets[key]

        listbox = widgets["listbox"]

        listbox.delete(
            0,
            tk.END,
        )

        for value in self.metadata[key]:
            listbox.insert(
                tk.END,
                value,
            )

    # =========================================================
    # Persistence
    # =========================================================

    def save_metadata(self):
        try:
            serializable_metadata = {
                key: copy.deepcopy(value)
                for key, value in self.metadata.items()
                if key != "specialty_socket"
            }

            os.makedirs(
                SETTINGS_DIR,
                exist_ok=True,
            )

            with open(
                METADATA_FILE,
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    serializable_metadata,
                    file,
                    indent=4,
                )

        except OSError as error:
            messagebox.showerror(
                "Save Error",
                (
                    "Could not save metadata "
                    "settings:\n"
                    f"{error}"
                ),
                parent=self.parent,
            )

    @staticmethod
    def load_metadata():
        default_metadata = copy.deepcopy(DEFAULT_METADATA)
        default_metadata.pop("specialty_socket", None)

        if not os.path.exists(METADATA_FILE):
            try:
                os.makedirs(
                    SETTINGS_DIR,
                    exist_ok=True,
                )

                with open(
                    METADATA_FILE,
                    "w",
                    encoding="utf-8",
                ) as file:
                    json.dump(
                        default_metadata,
                        file,
                        indent=4,
                    )

            except OSError:
                pass

            normalized = copy.deepcopy(DEFAULT_METADATA)
            normalized.pop("specialty_socket", None)
            normalized["specialty_socket"] = [
                value.strip()
                for value in DEFAULT_METADATA.get("specialty_socket", [])
                if isinstance(value, str) and value.strip()
            ]
            return normalized

        try:
            with open(
                METADATA_FILE,
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

            if not isinstance(data, dict):
                raise ValueError("Invalid metadata file")

            if "specialty_socket" in data:
                data.pop("specialty_socket", None)
                with open(
                    METADATA_FILE,
                    "w",
                    encoding="utf-8",
                ) as output_file:
                    json.dump(data, output_file, indent=4)

            normalized = {
                "sizes": {},
            }

            saved_sizes = data.get("sizes", {})
            if not isinstance(saved_sizes, dict):
                saved_sizes = {}

            for dataset in ("SAE", "Metric", "Other"):
                values = saved_sizes.get(dataset, [])
                if not isinstance(values, list):
                    values = []

                normalized["sizes"][dataset] = [
                    value.strip()
                    for value in values
                    if isinstance(value, str) and value.strip()
                ]

            for key in ("drive", "point"):
                values = data.get(key, [])
                if not isinstance(values, list):
                    values = []

                normalized[key] = [
                    value.strip()
                    for value in values
                    if isinstance(value, str) and value.strip()
                ]

            normalized["specialty_socket"] = [
                value.strip()
                for value in DEFAULT_METADATA.get("specialty_socket", [])
                if isinstance(value, str) and value.strip()
            ]

            return normalized

        except (
            OSError,
            ValueError,
            TypeError,
            json.JSONDecodeError,
        ):
            return copy.deepcopy(DEFAULT_METADATA)
    # =========================================================
    # Notification
    # =========================================================

    def notify_metadata_changed(self):
        if (
            self.on_metadata_changed
            is not None
        ):
            self.on_metadata_changed()