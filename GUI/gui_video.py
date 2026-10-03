import cv2

from PySide6.QtCore import (
    Qt,
    QTimer,
)
from PySide6.QtGui import (
    QImage,
    QPixmap,
)
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
)

from GUI.appearance_controller import (
    CONTROL_BG,
    BORDER_COLOR,
    TEXT_COLOR,
)


# ==================================================================
# Video Label
# ==================================================================

class VideoLabel(QLabel):

    def __init__(self, parent=None, controller=None):
        super().__init__(parent)

        self.controller = controller

        self.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.setMouseTracking(True)

        self.setCursor(
            Qt.CursorShape.ArrowCursor
        )

    # --------------------------------------------------------------
    # Mouse
    # --------------------------------------------------------------

    def mousePressEvent(self, event):
        if self.controller is not None:
            self.controller.on_mouse_down(event)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.controller is not None:
            self.controller.on_mouse_move(event)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.controller is not None:
            self.controller.on_mouse_up(event)

        super().mouseReleaseEvent(event)

    def enterEvent(self, event):
        if self.controller is not None:
            self.controller.on_mouse_motion(
                None
            )

        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setCursor(
            Qt.CursorShape.ArrowCursor
        )

        super().leaveEvent(event)


# ==================================================================
# Video Mixin
# ==================================================================

class VideoMixin:

    def create_video_display(self):
        self.video_frame = QFrame(
            self.root
        )

        self.video_frame.setObjectName(
            "videoFrame"
        )

        self.video_frame.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.video_layout = QVBoxLayout(
            self.video_frame
        )

        self.video_layout.setContentsMargins(
            4,
            4,
            4,
            4,
        )

        self.video_layout.setSpacing(0)

        self.video_label = VideoLabel(
            self.video_frame,
            controller=self,
        )

        self.video_layout.addWidget(
            self.video_label
        )

        # ----------------------------------------------------------
        # Theme
        # ----------------------------------------------------------

        self.refresh_video_theme()

        # ----------------------------------------------------------
        # Layout
        # ----------------------------------------------------------

        self.camera_layout.addWidget(
            self.video_frame,
            1,
        )

        # ----------------------------------------------------------
        # Video state
        # ----------------------------------------------------------

        self.current_frame_width = 0
        self.current_frame_height = 0

        self.display_width = 0
        self.display_height = 0

        self.video_pixmap = None

        # ----------------------------------------------------------
        # Timer
        # ----------------------------------------------------------

        self.video_timer = QTimer(
            self.root
        )

        self.video_timer.setInterval(
            33
        )

        self.video_timer.timeout.connect(
            self.update_frame
        )

    def refresh_video_theme(self):
        if not hasattr(
            self,
            "video_frame",
        ):
            return

        control_bg = self._get_color(
            CONTROL_BG
        )

        border = self._get_color(
            BORDER_COLOR
        )

        text = self._get_color(
            TEXT_COLOR
        )

        self.video_frame.setStyleSheet(
            f"""
            QFrame#videoFrame {{
                background-color: {control_bg};
                border: 1px solid {border};
                border-radius: 12px;
            }}
            """
        )

        if hasattr(
            self,
            "video_label",
        ):

            self.video_label.setStyleSheet(
                f"""
                QLabel {{
                    background-color: {control_bg};
                    color: {text};
                    border: none;
                }}
                """
            )

    # ==================================================================
    # Start / Stop
    # ==================================================================

    def start_video_update(self):
        if not self.video_timer.isActive():
            self.video_timer.start()

    def stop_video_update(self):
        if self.video_timer.isActive():
            self.video_timer.stop()

    # ==================================================================
    # Update Frame
    # ==================================================================

    def update_frame(self):
        if not self.running:
            return

        if not self.camera_ready:
            return

        frame = self.camera.read_frame()

        if frame is None:
            self.status_label.setText(
                "Video ended."
            )
            return

        processed_frame, detection_count = (
            self.camera.process_frame(frame)
        )

        self.update_capture_count()

        self.display_frame(
            processed_frame
        )

    # ==================================================================
    # Capture Count
    # ==================================================================

    def update_capture_count(self):
        if self.camera is None:
            return

        self.count_label.setText(
            f"Crops: "
            f"{self.camera.crop_number - 1}"
        )

    # ==================================================================
    # Display Frame
    # ==================================================================

    def display_frame(self, frame):
        frame_height, frame_width = (
            frame.shape[:2]
        )

        self.current_frame_width = (
            frame_width
        )

        self.current_frame_height = (
            frame_height
        )

        # --------------------------------------------------------------
        # OpenCV BGR -> RGB
        # --------------------------------------------------------------

        frame_rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB,
        )

        # --------------------------------------------------------------
        # QImage
        # --------------------------------------------------------------

        bytes_per_line = (
            frame_rgb.strides[0]
        )

        image = QImage(
            frame_rgb.data,
            frame_width,
            frame_height,
            bytes_per_line,
            QImage.Format.Format_RGB888,
        ).copy()

        # --------------------------------------------------------------
        # Calculate display size
        # --------------------------------------------------------------

        max_width = min(
            1050,
            max(
                1,
                self.video_label.width(),
            ),
        )

        max_height = min(
            650,
            max(
                1,
                self.video_label.height(),
            ),
        )

        scaled_image = image.scaled(
            max_width,
            max_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )

        self.display_width = (
            scaled_image.width()
        )

        self.display_height = (
            scaled_image.height()
        )

        # --------------------------------------------------------------
        # QPixmap
        # --------------------------------------------------------------

        pixmap = QPixmap.fromImage(
            scaled_image
        )

        self.video_pixmap = pixmap

        self.video_label.setPixmap(
            pixmap
        )

    # ==================================================================
    # Display -> Frame Coordinates
    # ==================================================================

    def display_to_frame_coordinates(self, event):
        if event is None:
            return None

        if (
            self.current_frame_width <= 0
            or self.current_frame_height <= 0
            or self.display_width <= 0
            or self.display_height <= 0
        ):
            return None

        label_width = (
            self.video_label.width()
        )

        label_height = (
            self.video_label.height()
        )

        offset_x = (
            label_width
            - self.display_width
        ) // 2

        offset_y = (
            label_height
            - self.display_height
        ) // 2

        position = event.position()

        image_x = (
            position.x()
            - offset_x
        )

        image_y = (
            position.y()
            - offset_y
        )

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

        frame_x = int(
            image_x * scale_x
        )

        frame_y = int(
            image_y * scale_y
        )

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

    # ==================================================================
    # Mouse Down
    # ==================================================================

    def on_mouse_down(self, event):
        if self.camera is None:
            return

        coordinates = (
            self.display_to_frame_coordinates(
                event
            )
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

    # ==================================================================
    # Mouse Move
    # ==================================================================

    def on_mouse_move(self, event):
        if self.camera is None:
            return

        coordinates = (
            self.display_to_frame_coordinates(
                event
            )
        )

        if coordinates is None:
            return

        x, y = coordinates

        buttons = event.buttons()

        if buttons & Qt.MouseButton.LeftButton:
            flags = cv2.EVENT_FLAG_LBUTTON
        else:
            flags = 0

        self.camera.mouse_callback(
            cv2.EVENT_MOUSEMOVE,
            x,
            y,
            flags,
            None,
        )

        self.update_mouse_cursor(
            x,
            y,
        )

    # ==================================================================
    # Mouse Up
    # ==================================================================

    def on_mouse_up(self, event):
        if self.camera is None:
            return

        coordinates = (
            self.display_to_frame_coordinates(
                event
            )
        )

        if coordinates is None:
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

    # ==================================================================
    # Mouse Motion
    # ==================================================================

    def on_mouse_motion(self, event):
        if event is None:
            self.video_label.setCursor(
                Qt.CursorShape.ArrowCursor
            )
            return

        coordinates = (
            self.display_to_frame_coordinates(
                event
            )
        )

        if coordinates is None:
            self.video_label.setCursor(
                Qt.CursorShape.ArrowCursor
            )
            return

        x, y = coordinates

        self.update_mouse_cursor(
            x,
            y,
        )

    # ==================================================================
    # Cursor
    # ==================================================================

    def update_mouse_cursor(self, x, y):
        cursor = self.get_box_cursor(
            x,
            y,
        )

        if cursor == "sizing":
            self.video_label.setCursor(
                Qt.CursorShape.SizeAllCursor
            )

        elif cursor == "fleur":
            self.video_label.setCursor(
                Qt.CursorShape.SizeAllCursor
            )

        else:
            self.video_label.setCursor(
                Qt.CursorShape.ArrowCursor
            )

    # ==================================================================
    # Box Cursor
    # ==================================================================

    def get_box_cursor(self, x, y):
        if self.camera is None:
            return ""

        box_manager = (
            self.camera.box_manager
        )

        # --------------------------------------------------------------
        # Scan Box
        # --------------------------------------------------------------

        if (
            box_manager.show_scan_box
            and box_manager.scan_box is not None
        ):
            if (
                box_manager.get_resize_handle(
                    box_manager.scan_box,
                    x,
                    y,
                ) is not None
            ):
                return "sizing"

            if box_manager.point_inside_box(
                box_manager.scan_box,
                x,
                y,
            ):
                return "fleur"

        # --------------------------------------------------------------
        # Crop Box
        # --------------------------------------------------------------

        if (
            box_manager.show_crop_box
            and box_manager.crop_box is not None
        ):
            if (
                box_manager.get_resize_handle(
                    box_manager.crop_box,
                    x,
                    y,
                ) is not None
            ):
                return "sizing"

            if box_manager.point_inside_box(
                box_manager.crop_box,
                x,
                y,
            ):
                return "fleur"

        # --------------------------------------------------------------
        # Counting Box
        # --------------------------------------------------------------

        if (
            box_manager.show_counting_box
            and box_manager.counting_box is not None
        ):
            if (
                box_manager.get_resize_handle(
                    box_manager.counting_box,
                    x,
                    y,
                ) is not None
            ):
                return "sizing"

            if box_manager.point_inside_box(
                box_manager.counting_box,
                x,
                y,
            ):
                return "fleur"

        return ""