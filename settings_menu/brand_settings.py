import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
import copy


SETTINGS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "settings",
)

BRANDS_FILE = os.path.join(
    SETTINGS_DIR,
    "brands.json",
)

DEFAULT_BRANDS = {
    "Snap-on": ["Snap-on"],
    "MAC": ["MAC"],
    "Matco": ["Matco"],
    "Cornwell": ["Cornwell"],
    "Craftsman": ["Craftsman"],
    "GearWrench": ["GearWrench"],
    "SK Tools": ["SK Tools"],
    "Proto": ["Proto"],
    "Kobalt": ["Kobalt"],
    "Husky": ["Husky"],
}

class BrandSettings:
    def __init__(self, parent, on_brands_changed=None,):
        self.parent = parent
        self.on_brands_changed = on_brands_changed
        self.brands = self.load_brands()

        self.create_gui()

    # =============================================================
    # GUI
    # =============================================================

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

        self.create_add_section(main_frame)
        self.create_remove_section(main_frame)

        self.refresh_brand_dropdowns()

    # =============================================================
    # Add Section
    # =============================================================

    def create_add_section(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="Add",
            padx=15,
            pady=15,
        )
        frame.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True,
            padx=(0, 10),
        )

        self.create_add_brand_section(frame)
        self.create_add_alias_section(frame)

    # =============================================================
    # Add Brand
    # =============================================================

    def create_add_brand_section(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="Add Brand",
            padx=10,
            pady=10,
        )
        frame.pack(
            fill=tk.X,
            pady=(0, 15),
        )

        tk.Label(
            frame,
            text="Brand Name:",
            font=("Arial", 11),
        ).pack(anchor="w")

        self.brand_name_entry = tk.Entry(
            frame,
            font=("Arial", 12),
        )
        self.brand_name_entry.pack(
            fill=tk.X,
            pady=5,
        )

        tk.Button(
            frame,
            text="Add Brand",
            command=self.add_brand,
            width=12,
        ).pack(
            anchor="e",
            pady=5,
        )

    # =============================================================
    # Add Brand Alias
    # =============================================================

    def create_add_alias_section(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="Add Brand Alias / Acronym",
            padx=10,
            pady=10,
        )
        frame.pack(
            fill=tk.X,
        )

        tk.Label(
            frame,
            text="Brand:",
            font=("Arial", 11),
        ).pack(anchor="w")

        self.add_alias_brand_var = tk.StringVar()

        self.add_alias_brand_dropdown = ttk.Combobox(
            frame,
            textvariable=self.add_alias_brand_var,
            state="readonly",
        )
        self.add_alias_brand_dropdown.pack(
            fill=tk.X,
            pady=5,
        )

        tk.Label(
            frame,
            text="Alias / Acronym:",
            font=("Arial", 11),
        ).pack(
            anchor="w",
            pady=(10, 0),
        )

        self.alias_entry = tk.Entry(
            frame,
            font=("Arial", 12),
        )
        self.alias_entry.pack(
            fill=tk.X,
            pady=5,
        )

        tk.Button(
            frame,
            text="Add Alias",
            command=self.add_alias,
            width=12,
        ).pack(
            anchor="e",
            pady=5,
        )

    # =============================================================
    # Remove Section
    # =============================================================

    def create_remove_section(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="Remove",
            padx=15,
            pady=15,
        )
        frame.pack(
            side=tk.RIGHT,
            fill=tk.BOTH,
            expand=True,
            padx=(10, 0),
        )

        self.create_remove_brand_section(frame)
        self.create_remove_alias_section(frame)

    # =============================================================
    # Remove Brand
    # =============================================================

    def create_remove_brand_section(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="Remove Brand",
            padx=10,
            pady=10,
        )
        frame.pack(
            fill=tk.X,
            pady=(0, 15),
        )

        tk.Label(
            frame,
            text="Brand:",
            font=("Arial", 11),
        ).pack(anchor="w")

        self.remove_brand_var = tk.StringVar()

        self.remove_brand_dropdown = ttk.Combobox(
            frame,
            textvariable=self.remove_brand_var,
            state="readonly",
        )
        self.remove_brand_dropdown.pack(
            fill=tk.X,
            pady=5,
        )

        tk.Button(
            frame,
            text="Remove Brand",
            command=self.remove_brand,
            width=15,
        ).pack(
            anchor="e",
            pady=5,
        )

    # =============================================================
    # Remove Brand Alias
    # =============================================================

    def create_remove_alias_section(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="Remove Brand Alias / Acronym",
            padx=10,
            pady=10,
        )
        frame.pack(
            fill=tk.X,
        )

        tk.Label(
            frame,
            text="Brand:",
            font=("Arial", 11),
        ).pack(anchor="w")

        self.remove_alias_brand_var = tk.StringVar()

        self.remove_alias_brand_dropdown = ttk.Combobox(
            frame,
            textvariable=self.remove_alias_brand_var,
            state="readonly",
        )
        self.remove_alias_brand_dropdown.pack(
            fill=tk.X,
            pady=5,
        )

        self.remove_alias_brand_dropdown.bind(
            "<<ComboboxSelected>>",
            self.on_remove_brand_selected,
        )

        tk.Label(
            frame,
            text="Alias / Acronym:",
            font=("Arial", 11),
        ).pack(
            anchor="w",
            pady=(10, 0),
        )

        self.remove_alias_var = tk.StringVar()

        self.remove_alias_dropdown = ttk.Combobox(
            frame,
            textvariable=self.remove_alias_var,
            state="readonly",
        )
        self.remove_alias_dropdown.pack(
            fill=tk.X,
            pady=5,
        )

        tk.Button(
            frame,
            text="Remove Alias",
            command=self.remove_alias,
            width=15,
        ).pack(
            anchor="e",
            pady=5,
        )

    # =============================================================
    # Add Brand
    # =============================================================

    def add_brand(self):
        brand_name = (
            self.brand_name_entry
            .get()
            .strip()
        )

        if not brand_name:
            return

        for existing_brand in self.brands:
            if existing_brand.casefold() == brand_name.casefold():
                messagebox.showwarning(
                    "Brand Exists",
                    f"{brand_name} already exists.",
                    parent=self.parent,
                )
                return

        self.brands[brand_name] = [
            brand_name
        ]

        self.brand_name_entry.delete(
            0,
            tk.END,
        )

        self.save_brands()
        self.refresh_brand_dropdowns()
        self.notify_brands_changed()

        self.add_alias_brand_var.set(
            brand_name
        )

        self.remove_brand_var.set(
            brand_name
        )

        self.remove_alias_brand_var.set(
            brand_name
        )

        self.on_remove_brand_selected()

    # =============================================================
    # Add Alias
    # =============================================================

    def add_alias(self):
        brand_name = self.add_alias_brand_var.get()

        alias = (
            self.alias_entry
            .get()
            .strip()
        )

        if not brand_name:
            messagebox.showwarning(
                "Select Brand",
                "Select a brand first.",
                parent=self.parent,
            )
            return

        if not alias:
            return

        aliases = self.brands[brand_name]

        if any(
            existing.casefold() == alias.casefold()
            for existing in aliases
        ):
            messagebox.showwarning(
                "Alias Exists",
                (
                    f"'{alias}' already exists "
                    f"for '{brand_name}'."
                ),
                parent=self.parent,
            )
            return

        aliases.append(alias)

        self.alias_entry.delete(
            0,
            tk.END,
        )

        self.save_brands()
        self.refresh_brand_dropdowns()
        self.notify_brands_changed()

        self.add_alias_brand_var.set(
            brand_name
        )

        self.remove_alias_brand_var.set(
            brand_name
        )

        self.on_remove_brand_selected()

    # =============================================================
    # Remove Brand Selection
    # =============================================================

    def on_remove_brand_selected(self, event=None):
        brand_name = self.remove_alias_brand_var.get()

        if brand_name not in self.brands:
            self.remove_alias_dropdown["values"] = []
            self.remove_alias_var.set("")
            return

        aliases = self.brands[brand_name]

        self.remove_alias_dropdown["values"] = aliases

        if aliases:
            self.remove_alias_var.set(
                aliases[0]
            )
        else:
            self.remove_alias_var.set("")

    # =============================================================
    # Remove Alias
    # =============================================================

    def remove_alias(self):
        brand_name = self.remove_alias_brand_var.get()
        alias = self.remove_alias_var.get()

        if not brand_name:
            messagebox.showwarning(
                "Select Brand",
                "Select a brand first.",
                parent=self.parent,
            )
            return

        if not alias:
            messagebox.showwarning(
                "Select Alias",
                "Select an alias to remove.",
                parent=self.parent,
            )
            return

        if alias.casefold() == brand_name.casefold():
            messagebox.showwarning(
                "Cannot Remove",
                "The main brand name cannot be removed.",
                parent=self.parent,
            )
            return

        answer = messagebox.askyesno(
            "Remove Alias",
            (
                f"Remove alias '{alias}' from "
                f"'{brand_name}'?"
            ),
            parent=self.parent,
        )

        if not answer:
            return

        self.brands[brand_name].remove(
            alias
        )

        self.save_brands()
        self.refresh_brand_dropdowns()
        self.notify_brands_changed()

        self.remove_alias_brand_var.set(
            brand_name
        )

        self.on_remove_brand_selected()

    # =============================================================
    # Remove Brand
    # =============================================================

    def remove_brand(self):
        brand_name = self.remove_brand_var.get()

        if not brand_name:
            messagebox.showwarning(
                "Select Brand",
                "Select a brand to remove.",
                parent=self.parent,
            )
            return

        if brand_name.casefold() == "none":
            messagebox.showwarning(
                "Cannot Remove",
                "The default brand cannot be removed.",
                parent=self.parent,
            )
            return

        answer = messagebox.askyesno(
            "Remove Brand",
            (
                f"Remove '{brand_name}'?\n\n"
                "This will also remove all of its "
                "aliases and acronyms."
            ),
            parent=self.parent,
        )

        if not answer:
            return

        del self.brands[brand_name]

        self.save_brands()
        self.refresh_brand_dropdowns()
        self.notify_brands_changed()
        
    # =============================================================
    # Dropdowns
    # =============================================================

    def refresh_brand_dropdowns(self):
        brand_names = list(
            self.brands.keys()
        )

        self.add_alias_brand_dropdown["values"] = brand_names
        self.remove_brand_dropdown["values"] = brand_names
        self.remove_alias_brand_dropdown["values"] = brand_names

        if self.add_alias_brand_var.get() not in brand_names:
            if brand_names:
                self.add_alias_brand_var.set(
                    brand_names[0]
                )
            else:
                self.add_alias_brand_var.set("")

        if self.remove_brand_var.get() not in brand_names:
            if brand_names:
                self.remove_brand_var.set(
                    brand_names[0]
                )
            else:
                self.remove_brand_var.set("")

        if self.remove_alias_brand_var.get() not in brand_names:
            if brand_names:
                self.remove_alias_brand_var.set(
                    brand_names[0]
                )
            else:
                self.remove_alias_brand_var.set("")

        self.on_remove_brand_selected()

    # =============================================================
    # Persistence
    # =============================================================

    def save_brands(self):
        try:
            os.makedirs(
                SETTINGS_DIR,
                exist_ok=True,
            )

            with open(
                BRANDS_FILE,
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    self.brands,
                    file,
                    indent=4,
                )

        except OSError as error:
            messagebox.showerror(
                "Save Error",
                (
                    "Could not save brand settings:\n"
                    f"{error}"
                ),
                parent=self.parent,
            )

    @staticmethod
    def load_brands():
        if not os.path.exists(BRANDS_FILE):
            try:
                os.makedirs(
                    SETTINGS_DIR,
                    exist_ok=True,
                )

                with open(
                    BRANDS_FILE,
                    "w",
                    encoding="utf-8",
                ) as file:
                    json.dump(
                        DEFAULT_BRANDS,
                        file,
                        indent=4,
                    )

                return copy.deepcopy(DEFAULT_BRANDS)

            except OSError:
                return {}

        try:
            with open(
                BRANDS_FILE,
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

            if not isinstance(data, dict):
                return {}

            normalized_brands = {}

            for brand_name, aliases in data.items():

                if not isinstance(
                    brand_name,
                    str,
                ):
                    continue

                if not isinstance(
                    aliases,
                    list,
                ):
                    continue

                if not all(
                    isinstance(alias, str)
                    for alias in aliases
                ):
                    continue

                brand_name = brand_name.strip()

                if not brand_name:
                    continue

                unique_aliases = [
                    brand_name
                ]

                seen = {
                    brand_name.casefold()
                }

                for alias in aliases:
                    alias = alias.strip()

                    if not alias:
                        continue

                    key = alias.casefold()

                    if key in seen:
                        continue

                    seen.add(key)
                    unique_aliases.append(alias)

                normalized_brands[
                    brand_name
                ] = unique_aliases

            return normalized_brands

        except (
            OSError,
            json.JSONDecodeError,
        ):
            return {}

    def notify_brands_changed(self):
        if self.on_brands_changed is not None:
            self.on_brands_changed()