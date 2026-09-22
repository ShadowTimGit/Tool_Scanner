import cv2
import tkinter as tk

from PIL import Image, ImageTk


class VideoMixin:

    def create_video_display(self):
        self.video_label = tk.Label(
            self.root,
            cursor="arrow",
        )

        self.video_label.pack(
            padx=10,
            pady=10,
            fill=tk.BOTH,
            expand=True,
        )

        self.video_label.bind(
            "<ButtonPress-1>",
            self.on_mouse_down,
        )

        self.video_label.bind(
            "<B1-Motion>",
            self.on_mouse_move,
        )

        self.video_label.bind(
            "<ButtonRelease-1>",
            self.on_mouse_up,
        )

        self.video_label.bind(
            "<Motion>",
            self.on_mouse_motion,
        )

    def update_frame(self):
        if not self.running:
            return

        if not self.camera_ready:
            self.root.after(
                50,
                self.update_frame,
            )
            return

        frame = self.camera.read_frame()

        if frame is None:
            self.status_label.config(
                text="Video ended."
            )
            return

        processed_frame, detection_count = (
            self.camera.process_frame(frame)
        )

        self.update_capture_count()
        self.display_frame(processed_frame)

        self.root.after(
            10,
            self.update_frame,
        )

    def update_capture_count(self):
        if self.camera is None:
            return

        self.count_label.config(
            text=(
                f"Crops: "
                f"{self.camera.crop_number - 1}"
            )
        )

    def display_frame(self, frame):
        frame_height, frame_width = frame.shape[:2]

        self.current_frame_width = frame_width
        self.current_frame_height = frame_height

        frame_rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB,
        )

        image = Image.fromarray(frame_rgb)

        image.thumbnail(
            (1050, 650),
            Image.Resampling.LANCZOS,
        )

        self.display_width = image.width
        self.display_height = image.height

        photo = ImageTk.PhotoImage(
            image=image
        )

        self.video_label.configure(
            image=photo
        )

        self.video_label.image = photo

    def display_to_frame_coordinates(self, event):
        if (
            self.current_frame_width <= 0
            or self.current_frame_height <= 0
            or self.display_width <= 0
            or self.display_height <= 0
        ):
            return None

        label_width = self.video_label.winfo_width()
        label_height = self.video_label.winfo_height()

        offset_x = (
            label_width - self.display_width
        ) // 2

        offset_y = (
            label_height - self.display_height
        ) // 2

        image_x = event.x - offset_x
        image_y = event.y - offset_y

        if (
            image_x < 0
            or image_y < 0
            or image_x >= self.display_width
            or image_y >= self.display_height
        ):
            return None

        scale_x = (
            self.current_frame_width
            / self.display_width
        )

        scale_y = (
            self.current_frame_height
            / self.display_height
        )

        frame_x = int(image_x * scale_x)
        frame_y = int(image_y * scale_y)

        frame_x = max(
            0,
            min(
                frame_x,
                self.current_frame_width - 1,
            ),
        )

        frame_y = max(
            0,
            min(
                frame_y,
                self.current_frame_height - 1,
            ),
        )

        return frame_x, frame_y

    def on_mouse_down(self, event):
        if self.camera is None:
            return

        coordinates = self.display_to_frame_coordinates(
            event
        )

        if coordinates is None:
            return

        x, y = coordinates

        self.camera.mouse_callback(
            cv2.EVENT_LBUTTONDOWN,
            x,
            y,
            0,
            None,
        )

    def on_mouse_move(self, event):
        if self.camera is None:
            return

        coordinates = self.display_to_frame_coordinates(
            event
        )

        if coordinates is None:
            return

        x, y = coordinates

        self.camera.mouse_callback(
            cv2.EVENT_MOUSEMOVE,
            x,
            y,
            cv2.EVENT_FLAG_LBUTTON,
            None,
        )

    def on_mouse_up(self, event):
        if self.camera is None:
            return

        coordinates = self.display_to_frame_coordinates(
            event
        )

        if coordinates is None:
            # Still release the mouse state.
            self.camera.mouse_callback(
                cv2.EVENT_LBUTTONUP,
                0,
                0,
                0,
                None,
            )
            return

        x, y = coordinates

        self.camera.mouse_callback(
            cv2.EVENT_LBUTTONUP,
            x,
            y,
            0,
            None,
        )

    def on_mouse_motion(self, event):
        coordinates = self.display_to_frame_coordinates(
            event
        )

        if coordinates is None:
            self.video_label.config(
                cursor="arrow"
            )
            return

        x, y = coordinates

        cursor = self.get_box_cursor(x, y)

        self.video_label.config(
            cursor=cursor
        )

    def get_box_cursor(self, x, y):
        if self.camera is None:
            return ""

        box_manager = self.camera.box_manager

        if (
            box_manager.show_scan_box
            and box_manager.scan_box is not None
        ):
            if (
                box_manager.get_resize_handle(
                    box_manager.scan_box,
                    x,
                    y,
                )
                is not None
            ):
                return "sizing"

            if box_manager.point_inside_box(
                box_manager.scan_box,
                x,
                y,
            ):
                return "fleur"

        if (
            box_manager.show_crop_box
            and box_manager.crop_box is not None
        ):
            if (
                box_manager.get_resize_handle(
                    box_manager.crop_box,
                    x,
                    y,
                )
                is not None
            ):
                return "sizing"

            if box_manager.point_inside_box(
                box_manager.crop_box,
                x,
                y,
            ):
                return "fleur"

        if (
            box_manager.show_counting_box
            and box_manager.counting_box is not None
        ):
            if (
                box_manager.get_resize_handle(
                    box_manager.counting_box,
                    x,
                    y,
                )
                is not None
            ):
                return "sizing"

            if box_manager.point_inside_box(
                box_manager.counting_box,
                x,
                y,
            ):
                return "fleur"

        return ""