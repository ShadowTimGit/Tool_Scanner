import tkinter as tk
import tkinter.ttk as ttk

from GUI.gui_constants import (
    INVENTORY_PURCHASE,
    INVENTORY_SALE,
)
from GUI.gui_fraction_dropdown import FractionDropdown


class RightPanelMixin:

    def create_right_panel(self):
        # ---------------------------------------------------------
        # Outer panel
        # ---------------------------------------------------------

        self.right_panel = tk.Frame(
            self.root,
            width=300,
            bd=2,
            relief=tk.GROOVE,
        )

        self.right_panel.pack(
            side=tk.RIGHT,
            fill=tk.Y,
            padx=(5, 10),
            pady=10,
        )

        self.right_panel.pack_propagate(False)

        # ---------------------------------------------------------
        # Canvas
        # ---------------------------------------------------------

        self.right_panel_canvas = tk.Canvas(
            self.right_panel,
            highlightthickness=0,
            bd=0,
        )

        self.right_panel_canvas.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True,
        )

        # ---------------------------------------------------------
        # Scrollbar
        # ---------------------------------------------------------

        self.right_panel_scrollbar = ttk.Scrollbar(
            self.right_panel,
            orient=tk.VERTICAL,
            command=self.right_panel_canvas.yview,
        )

        self.right_panel_scrollbar.pack(
            side=tk.RIGHT,
            fill=tk.Y,
        )

        self.right_panel_canvas.configure(
            yscrollcommand=self.right_panel_scrollbar.set,
        )

        # ---------------------------------------------------------
        # Scrollable inner frame
        # ---------------------------------------------------------

        self.right_panel_content = tk.Frame(
            self.right_panel_canvas,
            padx=10,
            pady=10,
        )

        self.right_panel_window = (
            self.right_panel_canvas.create_window(
                (0, 0),
                window=self.right_panel_content,
                anchor="nw",
            )
        )

        # ---------------------------------------------------------
        # Update scroll region
        # ---------------------------------------------------------

        self.right_panel_content.bind(
            "<Configure>",
            self._update_right_panel_scrollregion,
        )

        self.right_panel_canvas.bind(
            "<Configure>",
            self._resize_right_panel_content,
        )

        # ---------------------------------------------------------
        # Existing controls
        # ---------------------------------------------------------

        self.create_inventory_selection(
            self.right_panel_content
        )

        self.create_tool_selection(
            self.right_panel_content
        )

        self.create_metadata_selection(
            self.right_panel_content
        )

        self.create_settings_button(
            self.right_panel_content
        )

        # ---------------------------------------------------------
        # Mouse wheel
        # ---------------------------------------------------------

        self._setup_right_panel_mousewheel()

    # ---------------------------------------------------------
    # Right panel scrolling
    # ---------------------------------------------------------

    def _setup_right_panel_mousewheel(self):
        """
        Install one mouse-wheel binding for the entire right panel.

        The binding uses bind_class() so we don't have to recursively
        bind every widget inside the scrollable frame.
        """

        self._right_panel_mousewheel_tag = (
            "RightPanelMouseWheel"
        )

        self.root.bind_class(
            self._right_panel_mousewheel_tag,
            "<MouseWheel>",
            self._right_panel_mousewheel,
        )

        self._right_panel_add_mousewheel_bindings(
            self.right_panel
        )

    def _right_panel_add_mousewheel_bindings(self, widget):
        """
        Add the right-panel mouse-wheel bindtag to every widget.

        This allows the panel to scroll regardless of which child
        widget the mouse is currently over.

        The widget's own bindings remain intact.
        """

        bindtags = list(widget.bindtags())

        if self._right_panel_mousewheel_tag not in bindtags:
            bindtags.append(
                self._right_panel_mousewheel_tag
            )

            widget.bindtags(tuple(bindtags))

        for child in widget.winfo_children():
            self._right_panel_add_mousewheel_bindings(
                child
            )

    def _right_panel_mousewheel(self, event):
        """
        Scroll the right panel.

        Dropdown widgets are deliberately ignored so their native
        mouse-wheel behavior remains untouched.
        """

        widget = self.root.winfo_containing(
            event.x_root,
            event.y_root,
        )

        if widget is None:
            return

        if not self._is_inside_right_panel(widget):
            return

        if self._is_dropdown_widget(widget):
            return

        self.right_panel_canvas.yview_scroll(
            -1 if event.delta > 0 else 1,
            "units",
        )

        return "break"

    def _is_inside_right_panel(self, widget):
        current = widget

        while current is not None:
            if current == self.right_panel:
                return True

            current = getattr(
                current,
                "master",
                None,
            )

        return False

    def _is_dropdown_widget(self, widget):
        dropdowns = (
            self.tool_dropdown,
            self.size_dropdown,
            self.size_2_dropdown,
            self.brand_dropdown,
            self.measurement_dropdown,
            self.drive_dropdown,
            self.point_dropdown,
            self.specialty_socket_dropdown,
        )

        current = widget

        while current is not None:
            if current in dropdowns:
                return True

            current = getattr(
                current,
                "master",
                None,
            )

        return False

    # ---------------------------------------------------------
    # Canvas / Scroll region
    # ---------------------------------------------------------

    def _update_right_panel_scrollregion(self, event=None):
        self.right_panel_canvas.configure(
            scrollregion=self.right_panel_canvas.bbox("all")
        )

    def _resize_right_panel_content(self, event):
        self.right_panel_canvas.itemconfigure(
            self.right_panel_window,
            width=event.width,
        )

    # ---------------------------------------------------------
    # Inventory
    # ---------------------------------------------------------

    def create_inventory_selection(self, parent):
        frame = tk.Frame(
            parent,
            bd=2,
            relief=tk.GROOVE,
            padx=8,
            pady=8,
        )

        frame.pack(
            fill=tk.X,
            pady=(0, 10),
        )

        self.inventory_purchase_radio = tk.Radiobutton(
            frame,
            text="Purchase / Incoming",
            variable=self.inventory_type_var,
            value=INVENTORY_PURCHASE,
            command=self.on_inventory_type_changed,
            font=("Arial", 11),
        )

        self.inventory_purchase_radio.pack(
            anchor="w",
            pady=2,
        )

        self.inventory_sale_radio = tk.Radiobutton(
            frame,
            text="Sale / Outgoing",
            variable=self.inventory_type_var,
            value=INVENTORY_SALE,
            command=self.on_inventory_type_changed,
            font=("Arial", 11),
        )

        self.inventory_sale_radio.pack(
            anchor="w",
            pady=2,
        )

    # ---------------------------------------------------------
    # Tool / Size / Brand
    # ---------------------------------------------------------

    def create_tool_selection(self, parent):
        frame = tk.Frame(
            parent,
            bd=2,
            relief=tk.GROOVE,
            padx=8,
            pady=8,
        )

        frame.pack(
            fill=tk.X,
            pady=(0, 10),
        )

        self.create_tool_dropdown(frame)
        self.create_size_dropdown(frame)
        self.create_size_2_dropdown(frame)
        self.create_brand_dropdown(frame)

    def create_tool_dropdown(self, parent):
        tk.Label(
            parent,
            text="Tool:",
            font=("Arial", 11, "bold"),
        ).pack(
            anchor="w",
            pady=(0, 3),
        )

        self.tool_var = tk.StringVar()

        self.tool_dropdown = ttk.Combobox(
            parent,
            textvariable=self.tool_var,
            state="readonly",
            width=25,
        )

        self.tool_dropdown.pack(
            fill=tk.X,
            pady=(0, 8),
        )

        self.tool_dropdown.bind(
            "<<ComboboxSelected>>",
            self.on_tool_selected,
        )

    def create_size_dropdown(self, parent):
        tk.Label(
            parent,
            text="Size-1:",
            font=("Arial", 11, "bold"),
        ).pack(
            anchor="w",
            pady=(0, 3),
        )

        self.size_var = tk.StringVar()

        self.size_dropdown = FractionDropdown(
            parent,
            textvariable=self.size_var,
            command=self.on_size_selected,
            width=25,
            dual_measurement="SAE",
        )

        self.size_dropdown.pack(
            fill=tk.X,
            pady=(0, 8),
        )

    def create_size_2_dropdown(self, parent):
        tk.Label(
            parent,
            text="Size-2:",
            font=("Arial", 11, "bold"),
        ).pack(
            anchor="w",
            pady=(0, 3),
        )

        self.size_2_var = tk.StringVar()

        self.size_2_dropdown = FractionDropdown(
            parent,
            textvariable=self.size_2_var,
            command=self.on_size_selected,
            width=25,
            dual_measurement="Metric",
        )

        self.size_2_dropdown.pack(
            fill=tk.X,
            pady=(0, 8),
        )

    def create_brand_dropdown(self, parent):
        tk.Label(
            parent,
            text="Brand:",
            font=("Arial", 11, "bold"),
        ).pack(
            anchor="w",
            pady=(0, 3),
        )

        self.brand_var = tk.StringVar()

        self.brand_dropdown = ttk.Combobox(
            parent,
            textvariable=self.brand_var,
            state="readonly",
            width=25,
        )

        self.brand_dropdown.pack(
            fill=tk.X,
            pady=(0, 3),
        )

        self.brand_dropdown.bind(
            "<<ComboboxSelected>>",
            self.on_brand_selected,
        )

        self.refresh_brand_dropdown()

    # ---------------------------------------------------------
    # Metadata
    # ---------------------------------------------------------

    def create_metadata_selection(self, parent):
        frame = tk.Frame(
            parent,
            bd=2,
            relief=tk.GROOVE,
            padx=8,
            pady=8,
        )

        frame.pack(
            fill=tk.X,
            pady=(0, 10),
        )

        self.create_measurement_dropdown(frame)
        self.create_drive_dropdown(frame)
        self.create_point_dropdown(frame)
        self.create_specialty_socket_dropdown(frame)

        self.create_invoice_entry(frame)
        self.create_ebay_id_entry(frame)
        self.create_part_number_entry(frame)
        self.create_invoice_price_entry(frame)

        self.refresh_metadata_dropdowns()

    # ---------------------------------------------------------
    # Metadata Dropdowns
    # ---------------------------------------------------------

    def create_measurement_dropdown(self, parent):
        tk.Label(
            parent,
            text="Measurement:",
            font=("Arial", 11, "bold"),
        ).pack(
            anchor="w",
            pady=(0, 3),
        )

        self.measurement_var = tk.StringVar()

        self.measurement_dropdown = ttk.Combobox(
            parent,
            textvariable=self.measurement_var,
            values=[
                "SAE",
                "Metric",
                "Other",
                "DUAL",
            ],
            state="readonly",
            width=25,
        )

        self.measurement_dropdown.pack(
            fill=tk.X,
            pady=(0, 8),
        )

        self.measurement_dropdown.bind(
            "<<ComboboxSelected>>",
            self.on_measurement_selected,
        )

    def create_drive_dropdown(self, parent):
        tk.Label(
            parent,
            text="Drive:",
            font=("Arial", 11, "bold"),
        ).pack(
            anchor="w",
            pady=(0, 3),
        )

        self.drive_var = tk.StringVar()

        self.drive_dropdown = ttk.Combobox(
            parent,
            textvariable=self.drive_var,
            state="readonly",
            width=25,
        )

        self.drive_dropdown.pack(
            fill=tk.X,
            pady=(0, 8),
        )

        self.drive_dropdown.bind(
            "<<ComboboxSelected>>",
            self.on_drive_selected,
        )

    def create_point_dropdown(self, parent):
        tk.Label(
            parent,
            text="Point:",
            font=("Arial", 11, "bold"),
        ).pack(
            anchor="w",
            pady=(0, 3),
        )

        self.point_var = tk.StringVar()

        self.point_dropdown = ttk.Combobox(
            parent,
            textvariable=self.point_var,
            state="readonly",
            width=25,
        )

        self.point_dropdown.pack(
            fill=tk.X,
            pady=(0, 8),
        )

        self.point_dropdown.bind(
            "<<ComboboxSelected>>",
            self.on_point_selected,
        )

    def create_specialty_socket_dropdown(self, parent):
        tk.Label(
            parent,
            text="Specialty Socket:",
            font=("Arial", 11, "bold"),
        ).pack(
            anchor="w",
            pady=(0, 3),
        )

        self.specialty_socket_var = tk.StringVar()

        self.specialty_socket_dropdown = ttk.Combobox(
            parent,
            textvariable=self.specialty_socket_var,
            state="readonly",
            width=25,
        )

        self.specialty_socket_dropdown.pack(
            fill=tk.X,
            pady=(0, 8),
        )

        self.specialty_socket_dropdown.bind(
            "<<ComboboxSelected>>",
            self.on_specialty_socket_selected,
        )

    # ---------------------------------------------------------
    # Metadata Text Inputs
    # ---------------------------------------------------------

    def commit_metadata_entries(self):
        self.on_invoice_changed()
        self.on_ebay_id_changed()
        self.on_part_number_changed()
        self.on_invoice_price_changed()

    def create_invoice_entry(self, parent):
        self.create_metadata_entry(
            parent,
            "Invoice #:",
            "invoice_var",
            "invoice_entry",
            self.on_invoice_changed,
        )

    def create_ebay_id_entry(self, parent):
        self.create_metadata_entry(
            parent,
            "eBay ID:",
            "ebay_id_var",
            "ebay_id_entry",
            self.on_ebay_id_changed,
        )

    def create_part_number_entry(self, parent):
        self.create_metadata_entry(
            parent,
            "Part Number:",
            "part_number_var",
            "part_number_entry",
            self.on_part_number_changed,
        )

    def create_invoice_price_entry(self, parent):
        self.create_metadata_entry(
            parent,
            "Invoice Price:",
            "invoice_price_var",
            "invoice_price_entry",
            self.on_invoice_price_changed,
        )

    def create_metadata_entry(
        self,
        parent,
        label_text,
        variable_name,
        entry_name,
        callback,
    ):
        tk.Label(
            parent,
            text=label_text,
            font=("Arial", 11, "bold"),
        ).pack(
            anchor="w",
            pady=(0, 3),
        )

        variable = tk.StringVar()

        setattr(
            self,
            variable_name,
            variable,
        )

        entry = ttk.Entry(
            parent,
            textvariable=variable,
            width=25,
        )

        setattr(
            self,
            entry_name,
            entry,
        )

        entry.pack(
            fill=tk.X,
            pady=(0, 8),
        )

        entry.bind(
            "<FocusOut>",
            callback,
        )

    # ---------------------------------------------------------
    # Settings
    # ---------------------------------------------------------

    def create_settings_button(self, parent):
        self.settings_button = tk.Button(
            parent,
            text="Settings",
            command=self.open_settings,
            font=("Arial", 12),
            width=12,
        )

        self.settings_button.pack(
            fill=tk.X,
            pady=(5, 0),
        )