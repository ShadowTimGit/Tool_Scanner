import json
import os
import tkinter as tk
import tkinter.ttk as ttk

from PIL import Image, ImageTk
from tkinter import messagebox

from GUI.gui_constants import (
    INVENTORY_PURCHASE,
    INVENTORY_SALE,
)
from GUI.gui_fraction_dropdown import FractionDropdown
from tool_logger.tool_logger_config import INPUT_ROOT
from tool_logger.tool_logger_spreadsheets import (
    rebuild_workbook_from_json,
)
from tool_logger.workbook import (
    remove_row_from_workbook_by_path,
)
from tool_logger.json_sync import sync_json_from_workbook


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
        # Notebook tabs
        # ---------------------------------------------------------

        style = ttk.Style(self.root)

        style.configure(
            "RightPanel.TNotebook",
            background="#dfe3ea",
            borderwidth=0,
            padding=0,
        )

        style.configure(
            "RightPanel.TNotebook.Tab",
            background="#c8ced8",
            foreground="#1f2937",
            padding=(14, 8),
            relief="flat",
            borderwidth=1,
            font=("Arial", 10, "bold"),
        )

        style.map(
            "RightPanel.TNotebook.Tab",
            background=[
                ("selected", "#ffffff"),
                ("active", "#e6ecff"),
            ],
            foreground=[
                ("selected", "#111827"),
                ("active", "#111827"),
            ],
            bordercolor=[
                ("selected", "#b8c0cc"),
                ("active", "#aab7c8"),
            ],
        )

        self.right_panel_notebook = ttk.Notebook(
            self.right_panel,
            style="RightPanel.TNotebook",
        )

        self.right_panel_notebook.pack(
            fill=tk.BOTH,
            expand=True,
        )

        self.selection_tab = ttk.Frame(
            self.right_panel_notebook,
        )

        self.right_panel_notebook.add(
            self.selection_tab,
            text="Selection",
        )

        # ---------------------------------------------------------
        # Canvas for selection tab
        # ---------------------------------------------------------

        self.right_panel_canvas = tk.Canvas(
            self.selection_tab,
            highlightthickness=0,
            bd=0,
            width=260,
        )

        self.right_panel_canvas.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True,
        )

        self.right_panel_scrollbar = ttk.Scrollbar(
            self.selection_tab,
            orient=tk.VERTICAL,
            command=self.right_panel_canvas.yview,
        )

        self.right_panel_scrollbar.pack(
            side=tk.RIGHT,
            fill=tk.Y,
        )

        self.right_panel_xscrollbar = ttk.Scrollbar(
            self.selection_tab,
            orient=tk.HORIZONTAL,
            command=self.right_panel_canvas.xview,
        )

        self.right_panel_xscrollbar.pack(
            side=tk.BOTTOM,
            fill=tk.X,
        )

        self.right_panel_canvas.configure(
            yscrollcommand=self.right_panel_scrollbar.set,
            xscrollcommand=self.right_panel_xscrollbar.set,
        )

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
        # Recent crop tab
        # ---------------------------------------------------------

        self.recent_crops_tab = ttk.Frame(
            self.right_panel_notebook,
        )

        self.right_panel_notebook.add(
            self.recent_crops_tab,
            text="Recent Crops",
        )

        self.create_recent_crops_tab(
            self.recent_crops_tab,
        )

        # ---------------------------------------------------------
        # Mouse wheel
        # ---------------------------------------------------------

        self._setup_right_panel_mousewheel()

        self.refresh_recent_crops()
        self.root.after(
            2000,
            self.refresh_recent_crops_loop,
        )

    # ---------------------------------------------------------
    # Recent Crops Tab
    # ---------------------------------------------------------

    def create_recent_crops_tab(self, parent):
        container = tk.Frame(
            parent,
            padx=10,
            pady=10,
        )

        container.pack(
            fill=tk.BOTH,
            expand=True,
        )

        tk.Label(
            container,
            text="Recently Cropped Items",
            font=("Arial", 11, "bold"),
        ).pack(
            anchor="w",
            pady=(0, 6),
        )

        refresh_button = tk.Button(
            container,
            text="Refresh",
            command=self.refresh_recent_crops,
        )

        refresh_button.pack(
            fill=tk.X,
            pady=(0, 8),
        )

        self.recent_crops_canvas = tk.Canvas(
            container,
            highlightthickness=0,
            bd=0,
            width=260,
        )

        self.recent_crops_canvas.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True,
        )

        self.recent_crops_scrollbar = ttk.Scrollbar(
            container,
            orient=tk.VERTICAL,
            command=self.recent_crops_canvas.yview,
        )

        self.recent_crops_scrollbar.pack(
            side=tk.RIGHT,
            fill=tk.Y,
        )

        self.recent_crops_canvas.configure(
            yscrollcommand=self.recent_crops_scrollbar.set,
        )

        self.recent_crops_list = tk.Frame(
            self.recent_crops_canvas,
            padx=6,
            pady=6,
        )

        self.recent_crops_window_id = self.recent_crops_canvas.create_window(
            (0, 0),
            window=self.recent_crops_list,
            anchor="nw",
            width=self.recent_crops_canvas.winfo_reqwidth(),
        )

        self.recent_crops_list.bind(
            "<Configure>",
            self._update_recent_crops_scrollregion,
        )

        self.recent_crops_canvas.bind(
            "<Configure>",
            self._resize_recent_crops_content,
        )

    def refresh_recent_crops_loop(self):
        if not getattr(self, "running", False):
            return

        self.refresh_recent_crops()

        self.root.after(
            2000,
            self.refresh_recent_crops_loop,
        )

    def _update_recent_crops_scrollregion(self, event=None):
        if not hasattr(self, "recent_crops_canvas"):
            return

        self.recent_crops_canvas.update_idletasks()

        canvas_width = max(self.recent_crops_canvas.winfo_width(), 220)
        content_width = max(
            self.recent_crops_list.winfo_reqwidth(),
            canvas_width,
        )
        content_height = max(
            self.recent_crops_list.winfo_reqheight(),
            1,
        )

        self.recent_crops_canvas.configure(
            scrollregion=(0, 0, content_width + 20, content_height + 20),
        )

    def _resize_recent_crops_content(self, event):
        if hasattr(self, "recent_crops_window_id"):
            self.recent_crops_canvas.itemconfigure(
                self.recent_crops_window_id,
                width=max(1, event.width),
            )
            self._update_recent_crops_scrollregion()

    def refresh_recent_crops(self):
        if not hasattr(self, "recent_crops_list"):
            return

        entries = self.get_recent_crop_entries()
        signature = tuple(
            (
                entry.get("image_path"),
                entry.get("json_path"),
                entry.get("display_name"),
                entry.get("tool_name"),
            )
            for entry in entries
        )

        if getattr(self, "_recent_crop_signature", None) == signature:
            self._update_recent_crops_scrollregion()
            return

        self._recent_crop_signature = signature

        for child in self.recent_crops_list.winfo_children():
            child.destroy()

        if not entries:
            tk.Label(
                self.recent_crops_list,
                text="No recent cropped images found.",
                justify=tk.LEFT,
                anchor="w",
            ).pack(
                anchor="w",
                pady=8,
            )
            self._update_recent_crops_scrollregion()
            return

        for entry in entries:
            row = tk.Frame(
                self.recent_crops_list,
                bd=1,
                relief=tk.GROOVE,
                padx=8,
                pady=8,
            )

            row.pack(
                fill=tk.X,
                pady=6,
            )

            body = tk.Frame(
                row,
            )
            body.pack(
                fill=tk.X,
            )

            image_path = entry.get("image_path")
            thumbnail = self.load_thumbnail(image_path)

            image_label = tk.Label(
                body,
                image=thumbnail,
                compound=tk.TOP,
                cursor="hand2",
            )

            image_label.image = thumbnail
            image_label.bind(
                "<Button-1>",
                lambda event, item=entry: self.open_recent_crop_image(item),
            )
            image_label.pack(
                side=tk.LEFT,
                padx=(0, 8),
            )

            info = tk.Label(
                body,
                text=(
                    f"{entry.get('display_name', os.path.basename(image_path or ''))}\n"
                    f"{entry.get('tool_name', 'Unknown')}\n"
                    f"{os.path.basename(entry.get('json_path', ''))}"
                ),
                justify=tk.LEFT,
                anchor="w",
            )

            info.pack(
                side=tk.LEFT,
                fill=tk.BOTH,
                expand=True,
            )

            remove_button = tk.Button(
                row,
                text="Remove JSON",
                command=lambda item=entry: self.remove_recent_crop(item),
                width=12,
            )

            remove_button.pack(
                fill=tk.X,
                pady=(6, 0),
            )

            self._right_panel_add_mousewheel_bindings(row)
            self._right_panel_add_mousewheel_bindings(body)
            self._right_panel_add_mousewheel_bindings(image_label)
            self._right_panel_add_mousewheel_bindings(info)
            self._right_panel_add_mousewheel_bindings(remove_button)

        self.recent_crops_list.update_idletasks()
        self._update_recent_crops_scrollregion()

    def get_recent_crop_entries(self):
        if self.camera is None:
            return []

        session_entries = getattr(
            self.camera,
            "recent_session_crops",
            [],
        )

        entries = []

        for entry in session_entries:
            json_path = entry.get("json_path")
            image_path = entry.get("image_path")

            if not json_path and not image_path:
                continue

            if image_path and os.path.exists(image_path):
                entries.append(entry)
                continue

            if json_path and os.path.exists(json_path):
                entries.append(entry)
                continue

        return entries[:25]

    def load_thumbnail(self, image_path):
        if not image_path or not os.path.exists(image_path):
            placeholder = Image.new(
                "RGB",
                (80, 80),
                color=(220, 220, 220),
            )
            return ImageTk.PhotoImage(placeholder)

        try:
            image = Image.open(image_path)
            image = image.convert("RGB")
            image.thumbnail((80, 80), Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(image)
        except Exception:
            placeholder = Image.new(
                "RGB",
                (80, 80),
                color=(240, 220, 220),
            )
            return ImageTk.PhotoImage(placeholder)

    def open_recent_crop_image(self, entry):
        image_path = entry.get("image_path")

        if not image_path or not os.path.exists(image_path):
            return

        preview = tk.Toplevel(self.root)
        preview.title(
            f"Recent Crop - {os.path.basename(image_path)}"
        )
        preview.geometry("900x700")

        try:
            image = Image.open(image_path)
            image = image.convert("RGB")
            image_width, image_height = image.size

            max_width = 850
            max_height = 650

            if image_width > max_width or image_height > max_height:
                scale = min(
                    max_width / image_width,
                    max_height / image_height,
                )
                image = image.resize(
                    (
                        max(1, int(image_width * scale)),
                        max(1, int(image_height * scale)),
                    ),
                    Image.Resampling.LANCZOS,
                )

            photo = ImageTk.PhotoImage(image)

            label = tk.Label(
                preview,
                image=photo,
                compound=tk.TOP,
            )
            label.image = photo
            label.pack(
                padx=10,
                pady=10,
            )

            close_button = tk.Button(
                preview,
                text="Close",
                command=preview.destroy,
            )
            close_button.pack(
                pady=(0, 10),
            )

        except Exception:
            tk.Label(
                preview,
                text="Unable to load preview for this image.",
                padx=20,
                pady=20,
            ).pack()

    def remove_recent_crop(self, entry):
        json_path = entry.get("json_path")
        image_path = entry.get("image_path")

        if not json_path and not image_path:
            return

        result = messagebox.askyesno(
            "Remove crop entry",
            (
                "This will remove the selected crop image and JSON.\n"
                "The spreadsheet will be rebuilt afterward.\n\n"
                f"{os.path.basename(json_path or image_path or '')}"
            ),
        )

        if not result:
            return

        for path in (json_path, image_path):
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

        if self.camera is not None:
            recent = getattr(
                self.camera,
                "recent_session_crops",
                [],
            )

            self.camera.recent_session_crops = [
                item
                for item in recent
                if item.get("json_path") != json_path
                and item.get("image_path") != image_path
            ]

        try:
            remove_row_from_workbook_by_path(
                json_path=json_path,
                image_path=image_path,
            )
        except Exception as error:
            print(
                f"ERROR: Could not remove crop row from workbook: {error}"
            )

        self.refresh_recent_crops()

    # ---------------------------------------------------------
    # Right panel scrolling
    # ---------------------------------------------------------

    def _setup_right_panel_mousewheel(self):
        """
        Bind mouse-wheel scrolling directly to the right panel and all of
        its descendants so hover anywhere in the panel scrolls correctly,
        including dynamically created crop items.
        """

        self._right_panel_mousewheel_tag = "RightPanelMouseWheel"
        self.root.bind_class(
            self._right_panel_mousewheel_tag,
            "<MouseWheel>",
            self._right_panel_mousewheel,
        )
        self.root.bind_class(
            self._right_panel_mousewheel_tag,
            "<Shift-MouseWheel>",
            self._right_panel_mousewheel,
        )

        self._right_panel_add_mousewheel_bindings(self.right_panel)

    def _right_panel_add_mousewheel_bindings(self, widget):
        """Attach scroll behavior to this widget and all child widgets."""
        try:
            bindtags = list(widget.bindtags())
        except Exception:
            return

        if self._right_panel_mousewheel_tag not in bindtags:
            bindtags.append(self._right_panel_mousewheel_tag)
            widget.bindtags(tuple(bindtags))

        try:
            widget.bind("<MouseWheel>", self._right_panel_mousewheel)
            widget.bind("<Shift-MouseWheel>", self._right_panel_mousewheel)
        except Exception:
            pass

        for child in widget.winfo_children():
            self._right_panel_add_mousewheel_bindings(child)

    def _right_panel_mousewheel(self, event):
        """Scroll the current active right-panel canvas."""
        widget = self.root.winfo_containing(event.x_root, event.y_root)
        if widget is None:
            return

        if not self._is_inside_right_panel(widget):
            return

        if self._is_dropdown_widget(widget):
            return

        target_canvas = self._get_active_right_panel_canvas(widget)
        if target_canvas is None:
            return

        target_canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
        return "break"

    def _get_active_right_panel_canvas(self, widget):
        current = widget
        while current is not None:
            if current == self.recent_crops_canvas:
                return self.recent_crops_canvas
            if current == self.right_panel_canvas:
                return self.right_panel_canvas
            current = getattr(current, "master", None)

        active_tab = self.right_panel_notebook.select()
        if active_tab == str(self.recent_crops_tab):
            return getattr(self, "recent_crops_canvas", None)
        return getattr(self, "right_panel_canvas", None)

    def _is_inside_right_panel(self, widget):
        current = widget
        while current is not None:
            if current == self.right_panel:
                return True
            if current == self.right_panel_notebook:
                return True
            current = getattr(current, "master", None)
        return False

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
        if not hasattr(self, "right_panel_canvas"):
            return

        self.right_panel_canvas.update_idletasks()
        canvas_width = max(self.right_panel_canvas.winfo_width(), 220)
        content_width = max(
            self.right_panel_content.winfo_reqwidth(),
            canvas_width,
        )
        content_height = max(
            self.right_panel_content.winfo_reqheight(),
            1,
        )

        self.right_panel_canvas.configure(
            scrollregion=(0, 0, content_width + 20, content_height + 20),
        )

    def _resize_right_panel_content(self, event):
        self.right_panel_canvas.itemconfigure(
            self.right_panel_window,
            width=max(event.width, self.right_panel_content.winfo_reqwidth()),
        )
        self._update_right_panel_scrollregion()

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