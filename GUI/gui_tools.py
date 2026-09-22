from settings_menu.settings import SettingsWindow
from settings_menu.brand_settings import BrandSettings
from settings_menu.metadata_settings import MetadataSettings
from settings_menu.tool_settings import ToolSettings


class ToolsMixin:

    # ---------------------------------------------------------
    # Metadata
    # ---------------------------------------------------------

    def update_camera_metadata(self):
        if self.camera is None:
            return

        self.camera.set_metadata(
            tool=self.tool_var.get(),
            size_1=self.size_var.get(),
            size_2=self.size_2_var.get(),
            brand=self.brand_var.get(),
            measurement=self.measurement_var.get(),
            drive=self.drive_var.get(),
            point=self.point_var.get(),
            specialty_socket=self.specialty_socket_var.get(),
            invoice=self.invoice_var.get(),
            ebay_id=self.ebay_id_var.get(),
            part_number=self.part_number_var.get(),
            #estimated_value=self.estimated_value_var.get(),
            invoice_price=self.invoice_price_var.get(),
        )

    # ---------------------------------------------------------
    # Metadata Changed
    # ---------------------------------------------------------

    def on_metadata_changed(self):
        self.metadata = MetadataSettings.load_metadata()

        self.refresh_metadata_dropdowns()
        self.update_camera_metadata()


    # ---------------------------------------------------------
    # Brand
    # ---------------------------------------------------------

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

        self.update_camera_metadata()

    def on_brand_selected(self, event=None):
        self.selected_brand = self.brand_var.get()

        self.update_camera_metadata()

    def brands_changed(self):
        self.brands = BrandSettings.load_brands()

        self.refresh_brand_dropdown()

    # ---------------------------------------------------------
    # Tool
    # ---------------------------------------------------------

    def on_tool_selected(self, event=None):
        self.update_camera_metadata()

    # ---------------------------------------------------------
    # Size
    # ---------------------------------------------------------

    def on_size_selected(self, event=None):
        self.update_camera_metadata()

    def refresh_size_dropdowns(self):
        sizes = ToolSettings.load_sizes_data()

        measurement = self.measurement_var.get()

        available_sizes = sizes.get(
            measurement,
            [],
        )

        self.size_dropdown["values"] = (
            available_sizes
        )

        self.size_2_dropdown["values"] = (
            available_sizes
        )

        if self.size_var.get() not in available_sizes:
            self.size_var.set("")

        if self.size_2_var.get() not in available_sizes:
            self.size_2_var.set("")

    # ---------------------------------------------------------
    # Metadata Dropdowns
    # ---------------------------------------------------------

    def on_measurement_selected(self, event=None):
        self.refresh_size_dropdowns()
        self.update_camera_metadata()

    def on_drive_selected(self, event=None):
        self.update_camera_metadata()

    def on_point_selected(self, event=None):
        self.update_camera_metadata()

    def on_specialty_socket_selected(self, event=None):
        self.update_camera_metadata()

    def refresh_metadata_dropdowns(self):
        metadata = MetadataSettings.load_metadata()

        self.measurement_dropdown["values"] = [
            "SAE",
            "Metric",
        ]

        self.drive_dropdown["values"] = (
            metadata.get("drive", [])
        )

        self.point_dropdown["values"] = (
            metadata.get("point", [])
        )

        self.specialty_socket_dropdown[
            "values"
        ] = metadata.get(
            "specialty_socket",
            [],
        )

        if self.measurement_var.get() not in (
            "SAE",
            "Metric",
        ):
            self.measurement_var.set("SAE")

        if (
            self.drive_var.get()
            not in self.drive_dropdown["values"]
        ):
            self.drive_var.set("")

        if (
            self.point_var.get()
            not in self.point_dropdown["values"]
        ):
            self.point_var.set("")

        if (
            self.specialty_socket_var.get()
            not in self.specialty_socket_dropdown[
                "values"
            ]
        ):
            self.specialty_socket_var.set("")

        self.refresh_size_dropdowns()

    # ---------------------------------------------------------
    # Metadata Text Inputs
    # ---------------------------------------------------------

    def on_invoice_changed(self, event=None):
        self.update_camera_metadata()

    def on_ebay_id_changed(self, event=None):
        self.update_camera_metadata()

    def on_invoice_price_changed(self, event=None):
        self.update_camera_metadata()

    def on_part_number_changed(self, event=None):
        self.update_camera_metadata()

    def on_inventory_changed(self, event=None):
        self.update_camera_metadata()
    # ---------------------------------------------------------
    # Main Settings Refresh
    # ---------------------------------------------------------

    def refresh_main_settings(self):
        self.tools = ToolSettings.load_tools_data()
        self.brands = BrandSettings.load_brands()
        self.metadata = MetadataSettings.load_metadata()
        self.sizes = ToolSettings.load_sizes_data()

        self.tools_changed()
        self.refresh_brand_dropdown()
        self.refresh_metadata_dropdowns()
        self.refresh_size_dropdowns()

    # ---------------------------------------------------------
    # Settings
    # ---------------------------------------------------------

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
            self,
            self.tools,
            self.tools_changed,
            self.camera,
            self.brands_changed,
            self.on_metadata_changed,
            self.on_inventory_changed,
        )

    # ---------------------------------------------------------
    # Tools Changed
    # ---------------------------------------------------------

    def tools_changed(self):
        tool_names = list(
            self.tools.keys()
        )

        self.tool_dropdown["values"] = (
            tool_names
        )

        current_tool = self.tool_var.get()

        if current_tool in self.tools:
            self.tool_dropdown.set(
                current_tool
            )

        elif tool_names:
            self.tool_dropdown.set(
                tool_names[0]
            )

        else:
            self.tool_dropdown.set("")

        self.update_camera_metadata()