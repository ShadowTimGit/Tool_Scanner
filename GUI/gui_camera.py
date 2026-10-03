import threading

from PySide6.QtCore import QTimer

from Camera.camera import CameraProcessor


class CameraMixin:

    def initialize_camera(self):
        try:
            camera = CameraProcessor()

            self.camera_initialized_signal.emit(
                camera
            )

        except Exception as error:
            print(
                "CAMERA INITIALIZATION ERROR:"
            )
            print(error)

            self.camera_initialization_failed_signal.emit(
                error
            )

    def start_camera_initialization(self):
        self.camera_initialized_signal.connect(
            self.camera_initialized
        )

        self.camera_initialization_failed_signal.connect(
            self.camera_initialization_failed
        )

        self.camera_thread = threading.Thread(
            target=self.initialize_camera,
            daemon=True,
        )

        self.camera_thread.start()

    def camera_initialized(self, camera):
        if not self.running:
            camera.release()
            return

        self.camera = camera
        self.camera_ready = True

        self.camera.set_metadata_sync_callback(
            self.update_camera_metadata
        )

        self.camera.set_recent_crops_callback(
            self._on_recent_crops_changed
        )

        self.status_label.setText(
            "Camera ready."
        )

        self.camera.set_trigger_mode(
            self.trigger_mode_dropdown.currentText()
        )

        self.camera.set_crop_mode(
            self.crop_mode_dropdown.currentText()
        )

        self.camera.set_inventory_type(
            self.inventory_type
        )

        self.tools_changed()
        self.on_brand_selected()
        self.update_box_display()

        if not hasattr(self, "camera_timer"):
            self.camera_timer = QTimer(self)
            self.camera_timer.timeout.connect(
                self.update_frame
            )

        self.camera_timer.start(30)

        self.update_frame()

    def _on_recent_crops_changed(self):
        self.recent_crops_changed_signal.emit()

    def _refresh_recent_crops_from_camera(self):
        self._recent_crop_signature = None
        self.refresh_recent_crops()

    def camera_initialization_failed(self, error):
        self.camera = None
        self.camera_ready = False

        if hasattr(self, "camera_timer"):
            self.camera_timer.stop()

        self.status_label.setText(
            "Camera initialization failed."
        )

        print(
            f"Failed to initialize camera: {error}"
        )

    def stop_camera(self):
        if hasattr(self, "camera_timer"):
            self.camera_timer.stop()

        if self.camera is not None:
            self.camera.release()
            self.camera = None
            self.camera_ready = False