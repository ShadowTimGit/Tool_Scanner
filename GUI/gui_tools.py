from settings_menu.settings import SettingsWindow
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
            tool=self.tool_dropdown.currentText(),
            size_1=self.size_dropdown.get(),
            size_2=self.size_2_dropdown.get(),
            brand=self.brand_dropdown.currentText(),
            measurement=self.measurement_dropdown.currentText(),
            drive=self.drive_dropdown.currentText(),
            point=self.point_dropdown.currentText(),
            specialty_socket=self.specialty_socket_dropdown.currentText(),
            invoice=self.invoice_entry.text(),
            ebay_id=self.ebay_id_entry.text(),
            part_number=self.part_number_entry.text(),
            invoice_price=self.invoice_price_entry.text(),
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

        current_brand = self.brand_dropdown.currentText()

        self.brand_dropdown.clear()
        self.brand_dropdown.addItems(brand_names)

        if self.selected_brand in brand_names:
            index = brand_names.index(
                self.selected_brand
            )

        elif current_brand in brand_names:
            index = brand_names.index(
                current_brand
            )
            self.selected_brand = current_brand

        elif brand_names:
            index = 0
            self.selected_brand = brand_names[0]

        else:
            index = -1
            self.selected_brand = ""

        if index >= 0:
            self.brand_dropdown.setCurrentIndex(index)

        self.update_camera_metadata()

    def on_brand_selected(self, index=None):
        self.selected_brand = self.brand_dropdown.currentText()

        self.update_camera_metadata()

    def brands_changed(self):
        self.brands = ToolSettings.load_brands()

        self.refresh_brand_dropdown()

    # ---------------------------------------------------------
    # Tool
    # ---------------------------------------------------------

    def on_tool_selected(self, index=None):
        self.update_camera_metadata()

    # ---------------------------------------------------------
    # Size
    # ---------------------------------------------------------

    def on_size_selected(self, index=None):
        self.update_camera_metadata()

    def refresh_tools_size_dropdowns(self):
        sizes = ToolSettings.load_sizes_data()

        measurement = self.size_dropdown.get()

        if measurement == "Other":
            size_1_measurement = "Other"
            size_2_measurement = "Other"

        elif measurement == "DUAL":
            size_1_measurement = "SAE"
            size_2_measurement = "Metric"

        else:
            size_1_measurement = measurement
            size_2_measurement = measurement

        size_1_values = sizes.get(
            size_1_measurement,
            [],
        )

        size_2_values = sizes.get(
            size_2_measurement,
            [],
        )

        self.size_dropdown.set_measurement(
            size_1_measurement
        )

        self.size_2_dropdown.set_measurement(
            size_2_measurement
        )

        self.size_dropdown.set_values(
            size_1_values
        )

        self.size_2_dropdown.set_values(
            size_2_values
        )

    # ---------------------------------------------------------
    # Metadata Dropdowns
    # ---------------------------------------------------------

    def on_measurement_selected(self, index=None):
        self.refresh_tools_size_dropdowns()
        self.update_camera_metadata()

    def on_drive_selected(self, index=None):
        self.update_camera_metadata()

    def on_point_selected(self, index=None):
        self.update_camera_metadata()

    def on_specialty_socket_selected(self, index=None):
        self.update_camera_metadata()

    def refresh_metadata_dropdowns(self):
        metadata = MetadataSettings.load_metadata()

        measurement_values = [
            "SAE",
            "Metric",
            "Other",
            "DUAL",
        ]

        drive_values = metadata.get(
            "drive",
            [],
        )

        point_values = metadata.get(
            "point",
            [],
        )

        specialty_socket_values = metadata.get(
            "specialty_socket",
            [],
        )

        self.measurement_dropdown.clear()
        self.measurement_dropdown.addItems(
            measurement_values
        )

        self.drive_dropdown.clear()
        self.drive_dropdown.addItems(
            drive_values
        )

        self.point_dropdown.clear()
        self.point_dropdown.addItems(
            point_values
        )

        self.specialty_socket_dropdown.clear()
        self.specialty_socket_dropdown.addItems(
            specialty_socket_values
        )

        if (
            self.measurement_dropdown.currentText()
            not in measurement_values
        ):
            self.measurement_dropdown.setCurrentText(
                "SAE"
            )

        self.refresh_tools_size_dropdowns()

    # ---------------------------------------------------------
    # Metadata Text Inputs
    # ---------------------------------------------------------

    def on_invoice_changed(self, text=None):
        self.update_camera_metadata()

    def on_ebay_id_changed(self, text=None):
        self.update_camera_metadata()

    def on_invoice_price_changed(self, text=None):
        self.update_camera_metadata()

    def on_part_number_changed(self, text=None):
        self.update_camera_metadata()

    def on_inventory_changed(self, text=None):
        self.update_camera_metadata()

    # ---------------------------------------------------------
    # Main Settings Refresh
    # ---------------------------------------------------------

    def refresh_main_settings(self):
        self.tools = ToolSettings.load_tools_data()
        self.brands = ToolSettings.load_brands()
        self.metadata = MetadataSettings.load_metadata()
        self.sizes = ToolSettings.load_sizes_data()

        self.tools_changed()
        self.refresh_brand_dropdown()
        self.refresh_metadata_dropdowns()

    # ---------------------------------------------------------
    # Settings
    # ---------------------------------------------------------

    def open_settings(self):
        if self.camera is None:
            self.status_label.setText(
                "Camera is still loading..."
            )
            return

        if (
            self.settings_window is not None
            and self.settings_window.is_open()
        ):
            self.settings_window.window.showNormal()
            self.settings_window.window.raise_()
            self.settings_window.window.activateWindow()
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

        current_tool = self.tool_dropdown.currentText()

        self.tool_dropdown.clear()
        self.tool_dropdown.addItems(
            tool_names
        )

        if current_tool in tool_names:
            self.tool_dropdown.setCurrentText(
                current_tool
            )

        elif tool_names:
            self.tool_dropdown.setCurrentIndex(0)

        self.update_camera_metadata()