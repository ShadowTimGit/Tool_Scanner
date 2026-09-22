import threading

from Camera.camera import CameraProcessor


class CameraMixin:

    def initialize_camera(self):
        try:
            camera = CameraProcessor()

            self.root.after(
                0,
                self.camera_initialized,
                camera,
            )

        except Exception as error:
            print(
                "CAMERA INITIALIZATION ERROR:"
            )

            print(error)

            self.root.after(
                0,
                self.camera_initialization_failed,
                error,
            )

    def start_camera_initialization(self):
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

        self.status_label.config(
            text="Camera ready."
        )

        self.camera.set_trigger_mode(
            self.trigger_mode_var.get()
        )

        self.camera.set_crop_mode(
            self.crop_mode_var.get()
        )

        self.camera.set_inventory_type(
            self.inventory_type_var.get()
        )

        self.tools_changed()
        self.on_brand_selected()
        self.update_box_display()

        self.update_frame()

    def camera_initialization_failed(self, error):
        self.camera = None
        self.camera_ready = False

        self.status_label.config(
            text="Camera initialization failed."
        )

        print(
            f"Failed to initialize camera: {error}"
        )

    def stop_camera(self):
        if self.camera is not None:
            self.camera.release()
            self.camera = None
            self.camera_ready = False