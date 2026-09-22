import json
import os
import tkinter as tk
from tkinter import ttk, messagebox


SETTINGS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "settings",
)

INVENTORY_FILE = os.path.join(
    SETTINGS_DIR,
    "inventory_settings.json",
)

DEFAULT_INVENTORY = {
    "Socket": 8.0,
    "Adapter": 7.0,
    "Crowfoot": 12.0,
    "Extension": 8.0,
    "Wrench": 10.0,
    "Pliers": 12.0,
    "Brake Tool": 15.0,
    "Screwdriver": 8.0,
    "Breaker Bar": 20.0,
    "Ratchet": 20.0,
    "Punch": 8.0,
    "Feeler Gauge": 7.00,
    "Tool Holder": 8.00,
    "Torque Wrench": 50,
    "Allen Key": 6.0,
    "Torx Key": 7.0,
    "Hammer": 15.0,
    "Pick": 7.0,
}


class InventorySettings:
    def __init__(
        self,
        parent,
        tools,
        on_inventory_changed=None,
    ):
        self.parent = parent
        self.tools = tools
        self.on_inventory_changed = on_inventory_changed

        self.inventory = self.load_inventory()

        self.create_gui()

    # ---------------------------------------------------------
    # Persistence
    # ---------------------------------------------------------

    @staticmethod
    def load_inventory():
        os.makedirs(SETTINGS_DIR, exist_ok=True)

        default_inventory = {
            "estimated_values": DEFAULT_INVENTORY.copy()
        }

        if not os.path.exists(INVENTORY_FILE):
            InventorySettings.save_inventory(
                default_inventory
            )
            return default_inventory

        try:
            with open(
                INVENTORY_FILE,
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

        except (json.JSONDecodeError, OSError):
            data = {}

        saved_values = data.get(
            "estimated_values",
            {},
        )

        if not isinstance(saved_values, dict):
            saved_values = {}

        # Defaults remain available.
        # Saved values override the defaults.
        estimated_values = DEFAULT_INVENTORY.copy()
        estimated_values.update(saved_values)

        inventory = {
            "estimated_values": estimated_values
        }

        # Keep the file synchronized with the merged defaults.
        InventorySettings.save_inventory(inventory)

        return inventory

    @staticmethod
    def save_inventory(inventory):
        os.makedirs(SETTINGS_DIR, exist_ok=True)

        with open(
            INVENTORY_FILE,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                inventory,
                file,
                indent=4,
            )

    def on_tools_changed(self):
        self.refresh_tool_dropdown()

    # ---------------------------------------------------------
    # GUI
    # ---------------------------------------------------------

    def create_gui(self):
        main_frame = ttk.Frame(
            self.parent,
            padding=15,
        )
        main_frame.pack(
            fill=tk.BOTH,
            expand=True,
        )

        title = ttk.Label(
            main_frame,
            text="Estimated Tool Values",
            font=("TkDefaultFont", 12, "bold"),
        )
        title.pack(
            anchor="w",
            pady=(0, 5),
        )

        description = ttk.Label(
            main_frame,
            text=(
                "Set the estimated value for each tool type. "
                "These values are used when calculating the "
                "estimated value of purchased invoices."
            ),
            wraplength=650,
        )
        description.pack(
            anchor="w",
            pady=(0, 15),
        )

        self.create_estimated_value_editor(
            main_frame
        )

    def create_estimated_value_editor(self, parent):
        frame = ttk.LabelFrame(
            parent,
            text="Estimated Value by Tool Type",
            padding=10,
        )
        frame.pack(
            fill=tk.BOTH,
            expand=True,
        )

        # -----------------------------------------------------
        # Input row
        # -----------------------------------------------------

        ttk.Label(
            frame,
            text="Tool Type",
        ).grid(
            row=0,
            column=0,
            padx=5,
            pady=5,
            sticky="w",
        )

        ttk.Label(
            frame,
            text="Estimated Value",
        ).grid(
            row=0,
            column=1,
            padx=5,
            pady=5,
            sticky="w",
        )

        self.tool_var = tk.StringVar()
        self.value_var = tk.StringVar()

        self.tool_dropdown = ttk.Combobox(
            frame,
            textvariable=self.tool_var,
            state="readonly",
            width=30,
        )
        self.tool_dropdown.grid(
            row=1,
            column=0,
            padx=5,
            pady=5,
            sticky="ew",
        )

        self.value_entry = ttk.Entry(
            frame,
            textvariable=self.value_var,
            width=15,
        )
        self.value_entry.grid(
            row=1,
            column=1,
            padx=5,
            pady=5,
            sticky="ew",
        )

        ttk.Button(
            frame,
            text="Add / Update",
            command=self.add_or_update_value,
        ).grid(
            row=1,
            column=2,
            padx=5,
            pady=5,
        )

        # -----------------------------------------------------
        # List
        # -----------------------------------------------------

        self.values_listbox = tk.Listbox(
            frame,
            height=15,
        )
        self.values_listbox.grid(
            row=2,
            column=0,
            columnspan=2,
            padx=5,
            pady=(15, 5),
            sticky="nsew",
        )

        self.values_listbox.bind(
            "<<ListboxSelect>>",
            self.on_value_selected,
        )

        ttk.Button(
            frame,
            text="Remove",
            command=self.remove_value,
        ).grid(
            row=2,
            column=2,
            padx=5,
            pady=(15, 5),
            sticky="n",
        )

        frame.columnconfigure(
            0,
            weight=1,
        )

        frame.columnconfigure(
            1,
            weight=1,
        )

        frame.rowconfigure(
            2,
            weight=1,
        )

        self.refresh_tool_dropdown()
        self.refresh_values_list()

    # ---------------------------------------------------------
    # Tool List
    # ---------------------------------------------------------

    def refresh_tool_dropdown(self):
        if hasattr(self.tools, "tools"):
            tools = list(self.tools.tools)

        elif isinstance(self.tools, dict):
            tools = list(self.tools.keys())

        elif isinstance(self.tools, (list, tuple)):
            tools = list(self.tools)

        else:
            tools = []

        tools = [
            str(tool)
            for tool in tools
            if tool
        ]

        tools.sort()

        self.tool_dropdown["values"] = tools

    # ---------------------------------------------------------
    # Estimated Values
    # ---------------------------------------------------------

    def add_or_update_value(self):
        tool = self.tool_var.get().strip()
        value = self.value_var.get().strip()

        if not tool:
            messagebox.showwarning(
                "Missing Tool Type",
                "Select a tool type.",
                parent=self.parent.winfo_toplevel(),
            )
            return

        try:
            numeric_value = float(value)
        except ValueError:
            messagebox.showwarning(
                "Invalid Value",
                "Estimated value must be a number.",
                parent=self.parent.winfo_toplevel(),
            )
            return

        if numeric_value < 0:
            messagebox.showwarning(
                "Invalid Value",
                "Estimated value cannot be negative.",
                parent=self.parent.winfo_toplevel(),
            )
            return

        self.inventory[
            "estimated_values"
        ][tool] = numeric_value

        self.save_and_notify()

        self.tool_var.set("")
        self.value_var.set("")

        self.refresh_values_list()

    def remove_value(self):
        selection = self.values_listbox.curselection()

        if not selection:
            return

        tool = self.values_listbox.get(
            selection[0]
        ).split(" = $", 1)[0]

        if tool in self.inventory["estimated_values"]:
            del self.inventory[
                "estimated_values"
            ][tool]

        self.save_and_notify()

        self.tool_var.set("")
        self.value_var.set("")

        self.refresh_values_list()

    def on_value_selected(self, event=None):
        selection = self.values_listbox.curselection()

        if not selection:
            return

        tool = self.values_listbox.get(
            selection[0]
        ).split(" = $", 1)[0]

        value = self.inventory[
            "estimated_values"
        ].get(
            tool,
            "",
        )

        self.tool_var.set(tool)
        self.value_var.set(str(value))

    def refresh_values_list(self):
        self.values_listbox.delete(
            0,
            tk.END,
        )

        for tool, value in sorted(
            self.inventory[
                "estimated_values"
            ].items()
        ):
            self.values_listbox.insert(
                tk.END,
                f"{tool} = ${value:.2f}",
            )

    # ---------------------------------------------------------
    # Notifications
    # ---------------------------------------------------------

    def save_and_notify(self):
        self.save_inventory(
            self.inventory
        )

        if self.on_inventory_changed:
            self.on_inventory_changed()