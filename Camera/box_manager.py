import cv2

from config import (
    DEFAULT_SCAN_WIDTH,
    DEFAULT_SCAN_HEIGHT,
    DEFAULT_HEIGHT_DISPLACEMENT,
)

from Camera.camera_settings import (
    MIN_BOX_WIDTH,
    MIN_BOX_HEIGHT,
)


# ==================================================
# Scan Area
# ==================================================

SCAN_WIDTH = DEFAULT_SCAN_WIDTH
SCAN_HEIGHT = DEFAULT_SCAN_HEIGHT
HEIGHT_DISPLACEMENT = DEFAULT_HEIGHT_DISPLACEMENT


# ==================================================
# Interactive Box Settings
# ==================================================

BOX_RESIZE_MARGIN = 15


class BoxManager:

    def __init__(self, settings):

        self.settings = settings

        # -------------------------
        # Boxes
        # -------------------------

        self.scan_box = (
            self.settings.scan_box
        )

        self.crop_box = list(
            self.settings.crop_box
        )

        self.counting_box = (
            list(
                self.settings.counting_box
            )
            if self.settings.counting_box
            is not None
            else None
        )

        self.show_scan_box = True
        self.show_crop_box = True
        self.show_counting_box = True

        # -------------------------
        # Interactive state
        # -------------------------

        self.active_box = None

        self.dragging = False
        self.resizing = False

        self.resize_handle = None

        self.drag_offset_x = 0
        self.drag_offset_y = 0

        # -------------------------
        # Current frame
        # -------------------------

        self.current_frame_shape = None


    # ==================================================
    # Initialize Boxes
    # ==================================================

    def initialize(
        self,
        frame,
    ):

        self.current_frame_shape = (
            frame.shape[:2]
        )

        height, width = (
            self.current_frame_shape
        )

        # -------------------------
        # Initialize scan box
        # -------------------------

        if self.scan_box is None:

            box_x1 = (
                width - SCAN_WIDTH
            ) // 2

            box_y1 = (
                HEIGHT_DISPLACEMENT
            )

            box_x2 = (
                box_x1
                + SCAN_WIDTH
            )

            box_y2 = (
                box_y1
                + SCAN_HEIGHT
            )

            self.scan_box = [
                box_x1,
                box_y1,
                box_x2,
                box_y2,
            ]

        # -------------------------
        # Clamp scan box
        # -------------------------

        self.scan_box = (
            self.settings.clamp_box(
                self.scan_box,
                width,
                height,
            )
        )

        # -------------------------
        # Clamp crop box
        # -------------------------

        self.crop_box = (
            self.settings.clamp_box(
                self.crop_box,
                width,
                height,
            )
        )

        # -------------------------
        # Clamp counting box
        # -------------------------

        if self.counting_box is not None:

            self.counting_box = (
                self.settings.clamp_box(
                    self.counting_box,
                    width,
                    height,
                )
            )


    # ==================================================
    # Set Box Display
    # ==================================================

    def set_box_display(
        self,
        show_scan_box,
        show_crop_box,
        show_counting_box,
    ):

        self.show_scan_box = (
            show_scan_box
        )

        self.show_crop_box = (
            show_crop_box
        )

        self.show_counting_box = (
            show_counting_box
        )

        # -------------------------
        # Cancel hidden box interaction
        # -------------------------

        if (
            self.active_box == "scan"
            and not self.show_scan_box
        ):

            self.active_box = None
            self.dragging = False
            self.resizing = False
            self.resize_handle = None

        elif (
            self.active_box == "crop"
            and not self.show_crop_box
        ):

            self.active_box = None
            self.dragging = False
            self.resizing = False
            self.resize_handle = None

        elif (
            self.active_box == "counting"
            and not self.show_counting_box
        ):

            self.active_box = None
            self.dragging = False
            self.resizing = False
            self.resize_handle = None

    # ==================================================
    # Mouse Callback
    # ==================================================

    def mouse_callback(
        self,
        event,
        x,
        y,
        flags,
        param,
    ):

        # -------------------------
        # Mouse button released
        # -------------------------

        if (
            event
            == cv2.EVENT_LBUTTONUP
        ):

            was_adjusting = (
                self.dragging
                or self.resizing
            )

            self.dragging = False
            self.resizing = False

            self.resize_handle = None
            self.active_box = None

            if was_adjusting:
                self.save()

            return

        # -------------------------
        # Mouse button pressed
        # -------------------------

        if (
            event
            == cv2.EVENT_LBUTTONDOWN
        ):

            # -------------------------
            # Scan box
            # -------------------------

            if (
                self.show_scan_box
                and self.scan_box is not None
            ):

                handle = (
                    self.get_resize_handle(
                        self.scan_box,
                        x,
                        y,
                    )
                )

                if handle is not None:

                    self.active_box = "scan"
                    self.resizing = True
                    self.dragging = False
                    self.resize_handle = handle

                    return

                if self.point_inside_box(
                    self.scan_box,
                    x,
                    y,
                ):

                    self.active_box = "scan"
                    self.dragging = True
                    self.resizing = False

                    self.drag_offset_x = (
                        x - self.scan_box[0]
                    )

                    self.drag_offset_y = (
                        y - self.scan_box[1]
                    )

                    return

            # -------------------------
            # Crop box
            # -------------------------

            if (
                self.show_crop_box
                and self.crop_box is not None
            ):

                handle = (
                    self.get_resize_handle(
                        self.crop_box,
                        x,
                        y,
                    )
                )

                if handle is not None:

                    self.active_box = "crop"
                    self.resizing = True
                    self.dragging = False
                    self.resize_handle = handle

                    return

                if self.point_inside_box(
                    self.crop_box,
                    x,
                    y,
                ):

                    self.active_box = "crop"
                    self.dragging = True
                    self.resizing = False

                    self.drag_offset_x = (
                        x - self.crop_box[0]
                    )

                    self.drag_offset_y = (
                        y - self.crop_box[1]
                    )

                    return

            # -------------------------
            # Counting box
            # -------------------------

            if (
                self.show_counting_box
                and self.counting_box is not None
            ):

                handle = (
                    self.get_resize_handle(
                        self.counting_box,
                        x,
                        y,
                    )
                )

                if handle is not None:

                    self.active_box = "counting"
                    self.resizing = True
                    self.dragging = False
                    self.resize_handle = handle

                    return

                if self.point_inside_box(
                    self.counting_box,
                    x,
                    y,
                ):

                    self.active_box = "counting"
                    self.dragging = True
                    self.resizing = False

                    self.drag_offset_x = (
                        x
                        - self.counting_box[0]
                    )

                    self.drag_offset_y = (
                        y
                        - self.counting_box[1]
                    )

                    return

            return

        # -------------------------
        # Mouse movement
        # -------------------------

        if (
            event
            == cv2.EVENT_MOUSEMOVE
        ):

            if self.active_box is None:
                return

            if (
                not self.dragging
                and not self.resizing
            ):
                return

            # -------------------------
            # Determine active box
            # -------------------------

            if (
                self.active_box
                == "scan"
            ):

                if (
                    not self.show_scan_box
                    or self.scan_box is None
                ):
                    self.dragging = False
                    self.resizing = False
                    self.active_box = None
                    self.resize_handle = None
                    return

                box = self.scan_box

            elif (
                self.active_box
                == "crop"
            ):

                if (
                    not self.show_crop_box
                    or self.crop_box is None
                ):
                    self.dragging = False
                    self.resizing = False
                    self.active_box = None
                    self.resize_handle = None
                    return

                box = self.crop_box

            elif (
                self.active_box
                == "counting"
            ):

                if (
                    not self.show_counting_box
                    or self.counting_box is None
                ):
                    self.dragging = False
                    self.resizing = False
                    self.active_box = None
                    self.resize_handle = None
                    return

                box = self.counting_box

            else:

                return

            # -------------------------
            # Resize
            # -------------------------

            if self.resizing:

                new_box = list(box)

                if (
                    self.resize_handle
                    is None
                ):
                    return

                if (
                    "left"
                    in self.resize_handle
                ):

                    new_box[0] = min(
                        x,
                        new_box[2]
                        - MIN_BOX_WIDTH,
                    )

                if (
                    "right"
                    in self.resize_handle
                ):

                    new_box[2] = max(
                        x,
                        new_box[0]
                        + MIN_BOX_WIDTH,
                    )

                if (
                    "top"
                    in self.resize_handle
                ):

                    new_box[1] = min(
                        y,
                        new_box[3]
                        - MIN_BOX_HEIGHT,
                    )

                if (
                    "bottom"
                    in self.resize_handle
                ):

                    new_box[3] = max(
                        y,
                        new_box[1]
                        + MIN_BOX_HEIGHT,
                    )

                if self.current_frame_shape is None:
                    return

                height, width = (
                    self.current_frame_shape
                )

                new_box = (
                    self.settings.clamp_box(
                        new_box,
                        width,
                        height,
                    )
                )

                # -------------------------
                # Save resized box
                # -------------------------

                if (
                    self.active_box
                    == "scan"
                ):

                    self.scan_box = new_box

                elif (
                    self.active_box
                    == "crop"
                ):

                    self.crop_box = new_box

                elif (
                    self.active_box
                    == "counting"
                ):

                    self.counting_box = new_box

            # -------------------------
            # Move
            # -------------------------

            elif self.dragging:

                box_width = (
                    box[2] - box[0]
                )

                box_height = (
                    box[3] - box[1]
                )

                new_x1 = (
                    x
                    - self.drag_offset_x
                )

                new_y1 = (
                    y
                    - self.drag_offset_y
                )

                new_box = [
                    new_x1,
                    new_y1,
                    new_x1 + box_width,
                    new_y1 + box_height,
                ]

                if self.current_frame_shape is None:
                    return

                height, width = (
                    self.current_frame_shape
                )

                new_box = (
                    self.settings.clamp_box(
                        new_box,
                        width,
                        height,
                    )
                )

                # -------------------------
                # Save moved box
                # -------------------------

                if (
                    self.active_box
                    == "scan"
                ):

                    self.scan_box = new_box

                elif (
                    self.active_box
                    == "crop"
                ):

                    self.crop_box = new_box

                elif (
                    self.active_box
                    == "counting"
                ):

                    self.counting_box = new_box


    # ==================================================
    # Point Inside Box
    # ==================================================

    def point_inside_box(
        self,
        box,
        x,
        y,
    ):

        if box is None:
            return False

        x1, y1, x2, y2 = box

        return (
            x1 <= x <= x2
            and y1 <= y <= y2
        )


    # ==================================================
    # Resize Handle Detection
    # ==================================================

    def get_resize_handle(
        self,
        box,
        x,
        y,
    ):

        if box is None:
            return None

        x1, y1, x2, y2 = box

        margin = BOX_RESIZE_MARGIN

        near_left = (
            abs(x - x1)
            <= margin
        )

        near_right = (
            abs(x - x2)
            <= margin
        )

        near_top = (
            abs(y - y1)
            <= margin
        )

        near_bottom = (
            abs(y - y2)
            <= margin
        )

        inside_horizontal = (
            y1 - margin
            <= y
            <= y2 + margin
        )

        inside_vertical = (
            x1 - margin
            <= x
            <= x2 + margin
        )

        # -------------------------
        # Corners
        # -------------------------

        if (
            near_left
            and near_top
        ):
            return "left_top"

        if (
            near_right
            and near_top
        ):
            return "right_top"

        if (
            near_left
            and near_bottom
        ):
            return "left_bottom"

        if (
            near_right
            and near_bottom
        ):
            return "right_bottom"

        # -------------------------
        # Edges
        # -------------------------

        if (
            near_left
            and inside_horizontal
        ):
            return "left"

        if (
            near_right
            and inside_horizontal
        ):
            return "right"

        if (
            near_top
            and inside_vertical
        ):
            return "top"

        if (
            near_bottom
            and inside_vertical
        ):
            return "bottom"

        return None


    # ==================================================
    # Save
    # ==================================================

    def save(self):

        self.settings.scan_box = (
            self.scan_box
        )

        self.settings.crop_box = list(
            self.crop_box
        )

        self.settings.counting_box = (
            list(
                self.counting_box
            )
            if self.counting_box is not None
            else None
        )

        self.settings.save()


    # ==================================================
    # Scale Boxes
    # ==================================================

    def scale_boxes(
        self,
        old_width,
        old_height,
        new_width,
        new_height,
    ):

        if (
            old_width <= 0
            or old_height <= 0
        ):
            return

        scale_x = (
            new_width
            / old_width
        )

        scale_y = (
            new_height
            / old_height
        )

        # -------------------------
        # Scan box
        # -------------------------

        if self.scan_box is not None:

            self.scan_box = [
                int(
                    self.scan_box[0]
                    * scale_x
                ),
                int(
                    self.scan_box[1]
                    * scale_y
                ),
                int(
                    self.scan_box[2]
                    * scale_x
                ),
                int(
                    self.scan_box[3]
                    * scale_y
                ),
            ]

        # -------------------------
        # Crop box
        # -------------------------

        if self.crop_box is not None:

            self.crop_box = [
                int(
                    self.crop_box[0]
                    * scale_x
                ),
                int(
                    self.crop_box[1]
                    * scale_y
                ),
                int(
                    self.crop_box[2]
                    * scale_x
                ),
                int(
                    self.crop_box[3]
                    * scale_y
                ),
            ]

        # -------------------------
        # Counting box
        # -------------------------

        if self.counting_box is not None:

            self.counting_box = [
                int(
                    self.counting_box[0]
                    * scale_x
                ),
                int(
                    self.counting_box[1]
                    * scale_y
                ),
                int(
                    self.counting_box[2]
                    * scale_x
                ),
                int(
                    self.counting_box[3]
                    * scale_y
                ),
            ]

        # -------------------------
        # Clamp scan box
        # -------------------------

        self.scan_box = (
            self.settings.clamp_box(
                self.scan_box,
                new_width,
                new_height,
            )
        )

        # -------------------------
        # Clamp crop box
        # -------------------------

        self.crop_box = (
            self.settings.clamp_box(
                self.crop_box,
                new_width,
                new_height,
            )
        )

        # -------------------------
        # Clamp counting box
        # -------------------------

        if self.counting_box is not None:

            self.counting_box = (
                self.settings.clamp_box(
                    self.counting_box,
                    new_width,
                    new_height,
                )
            )