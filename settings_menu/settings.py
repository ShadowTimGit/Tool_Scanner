import tkinter as tk
from tkinter import ttk

from settings_menu.tool_settings import ToolSettings
from settings_menu.brand_settings import BrandSettings
from settings_menu.general_settings import GeneralSettings
from settings_menu.metadata_settings import MetadataSettings
from settings_menu.inventory_settings import InventorySettings


class SettingsWindow:
    def __init__(
        self,
        parent,
        tools,
        on_tools_changed,
        camera,
        on_brands_changed=None,
        on_metadata_changed=None,
        on_inventory_changed=None,
    ):
        self.parent = parent
        self.tools = tools
        self.on_tools_changed = on_tools_changed
        self.camera = camera
        self.on_brands_changed = on_brands_changed
        self.on_metadata_changed = on_metadata_changed
        self.on_inventory_changed = on_inventory_changed


        self.window = tk.Toplevel(parent.root)
        self.window.title("Settings")
        self.window.geometry("800x600")
        self.window.resizable(False, False)

        self.window.protocol(
            "WM_DELETE_WINDOW",
            self.close,
        )

        self.create_gui()

    def create_gui(self):
        notebook = ttk.Notebook(
            self.window
        )

        notebook.pack(
            fill=tk.BOTH,
            expand=True,
            padx=15,
            pady=15,
        )

        tools_frame = ttk.Frame(
            notebook
        )

        brands_frame = ttk.Frame(
            notebook
        )

        product_frame = ttk.Frame(
            notebook
        )

        sales_frame = ttk.Frame(
            notebook
        )

        general_frame = ttk.Frame(
            notebook
        )

        notebook.add(
            tools_frame,
            text="Tools",
        )

        notebook.add(
            brands_frame,
            text="Brands",
        )

        notebook.add(
            product_frame,
            text="Product Attributes",
        )

        notebook.add(
            sales_frame,
            text="Sales / Inventory",
        )

        notebook.add(
            general_frame,
            text="General",
        )

        # Create InventorySettings first
        self.inventory_settings = InventorySettings(
            sales_frame,
            self.tools,
            self.on_inventory_changed,
        )

        ToolSettings(
            tools_frame,
            self.tools,
            self.inventory_settings.on_tools_changed,
        )

        BrandSettings(
            brands_frame,
            self.on_brands_changed,
        )

        MetadataSettings(
            product_frame,
            self.on_metadata_changed,
        )

        GeneralSettings(
            general_frame,
            self.camera,
            self.parent,
        )

        tk.Button(
            self.window,
            text="Close",
            command=self.close,
            width=12,
        ).pack(
            pady=(0, 15),
        )

    def close(self):
        self.window.destroy()
