import json
import os
import tkinter as tk
from tkinter import ttk, messagebox

from settings_menu.tool_repository import ToolRepository
from settings_menu.settings_config import (
    DEFAULT_SAE_SIZES,
    DEFAULT_METRIC_SIZES,
    DEFAULT_OTHER,
)


class ToolSettings:

    SIZES_FILE = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
        ),
        "sizes.json",
    )

    def __init__(
        self,
        parent,
        tools,
        on_tools_changed,
    ):
        self.parent = parent
        self.tools = tools
        self.on_tools_changed = on_tools_changed

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

        self.create_add_section(
            main_frame
        )

        self.create_remove_section(
            main_frame
        )

        self.refresh_dropdowns()

    def create_add_section(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="Add General Tool",
            padx=15,
            pady=15,
        )

        frame.pack(
            fill=tk.X,
            pady=(0, 15),
        )

        tk.Label(
            frame,
            text="Tool Name:",
            font=("Arial", 11),
        ).pack(
            anchor="w"
        )

        self.tool_entry = tk.Entry(
            frame,
            font=("Arial", 12),
        )

        self.tool_entry.pack(
            fill=tk.X,
            pady=5,
        )

        tk.Button(
            frame,
            text="Add Tool",
            command=self.add_tool,
            width=12,
        ).pack(
            anchor="e",
            pady=5,
        )

    def create_remove_section(self, parent):
        frame = tk.LabelFrame(
            parent,
            text="Remove General Tool",
            padx=15,
            pady=15,
        )

        frame.pack(
            fill=tk.X,
        )

        tk.Label(
            frame,
            text="General Tool:",
            font=("Arial", 11),
        ).pack(
            anchor="w"
        )

        self.remove_tool_var = tk.StringVar()

        self.remove_tool_dropdown = ttk.Combobox(
            frame,
            textvariable=self.remove_tool_var,
            state="readonly",
        )

        self.remove_tool_dropdown.pack(
            fill=tk.X,
            pady=5,
        )

        tk.Button(
            frame,
            text="Remove Tool",
            command=self.remove_tool,
            width=12,
        ).pack(
            anchor="e",
            pady=5,
        )

    # =========================================================
    # Add Tool
    # =========================================================

    def add_tool(self):
        tool_name = self.tool_entry.get().strip().title()

        if not tool_name or tool_name == "NA":
            messagebox.showwarning(
                "Invalid Tool Name",
                "The reserved NA entry cannot be added as a tool.",
                parent=self.parent,
            )
            return

        if any(
            existing.casefold() == tool_name.casefold()
            for existing in self.tools
        ):
            messagebox.showwarning(
                "Tool Exists",
                f"{tool_name} already exists.",
                parent=self.parent,
            )
            return

        self.tools[tool_name] = ["NA"]
        self.tool_entry.delete(
            0,
            tk.END,
        )

        self.save_tools()
        self.refresh_dropdowns()

        self.on_tools_changed()

    # =========================================================
    # Remove Tool
    # =========================================================

    def remove_tool(self):
        tool_name = self.remove_tool_var.get()

        if not tool_name:
            messagebox.showwarning(
                "Select Tool",
                "Select a general tool to remove.",
                parent=self.parent,
            )
            return

        answer = messagebox.askyesno(
            "Remove Tool",
            (
                f"Remove '{tool_name}'?\n\n"
                "This will also remove all of its "
                "sizes."
            ),
            parent=self.parent,
        )

        if not answer:
            return

        del self.tools[tool_name]

        if not self.tools:
            self.tools = {"NA": ["NA"]}

        self.save_tools()
        self.refresh_dropdowns()

        self.on_tools_changed()

    # =========================================================
    # Refresh Tool Dropdown
    # =========================================================

    def refresh_dropdowns(self):
        tool_names = sorted(
            [name for name in self.tools.keys() if name != "NA"],
            key=str.casefold,
        )

        self.remove_tool_dropdown[
            "values"
        ] = tool_names

        if self.remove_tool_var.get() not in tool_names:
            if tool_names:
                self.remove_tool_var.set(
                    tool_names[0]
                )
            else:
                self.remove_tool_var.set("")

    # =========================================================
    # Tool Persistence
    # =========================================================

    def save_tools(self):
        if not ToolRepository.save_tools(
            self.tools
        ):
            messagebox.showerror(
                "Save Error",
                "Could not save tool settings.",
                parent=self.parent,
            )

    # =========================================================
    # General Size Persistence
    # =========================================================

    @classmethod
    def load_sizes_data(cls):
        default_sizes = {
            "SAE": list(
                DEFAULT_SAE_SIZES
            ),
            "Metric": list(
                DEFAULT_METRIC_SIZES
            ),
            "Other": list(
                DEFAULT_OTHER
            ),
            "DUAL": [],
        }

        if not os.path.exists(
            cls.SIZES_FILE
        ):
            return default_sizes

        try:
            with open(
                cls.SIZES_FILE,
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

            return {
                "SAE": data.get(
                    "SAE",
                    list(DEFAULT_SAE_SIZES),
                ),
                "Metric": data.get(
                    "Metric",
                    list(DEFAULT_METRIC_SIZES),
                ),
                "Other": data.get(
                    "Other",
                    list(DEFAULT_OTHER),
                ),
                "DUAL": data.get(
                    "DUAL",
                    [],
                ),
            }

        except (
            OSError,
            json.JSONDecodeError,
        ):
            return default_sizes

    @classmethod
    def save_sizes_data(cls, sizes):
        try:
            with open(
                cls.SIZES_FILE,
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    sizes,
                    file,
                    indent=4,
                )

            return True

        except OSError:
            return False