import cv2
import os
import json

from tool_logger.logger_worker import submit_json

from datetime import datetime

from config import (
    DEFAULT_VIDEO_SOURCE,
    OUTPUT_DIR,
    SETTINGS_FILE,
    MIN_RED_PERCENT,
)

from Camera.camera_settings import (
    CameraSettings,
    SUPPORTED_RESOLUTIONS,
)

from Camera.object_tracker import (
    ObjectTracker,
    MIN_FRAMES,
)

from Camera.box_manager import (
    BoxManager,
)

from GUI.gui_constants import (
    INVENTORY_PURCHASE,
    INVENTORY_SALE,
)

def get_output_dir():
    try:
        with open(
            SETTINGS_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            settings = json.load(file)

        return settings.get(
            "output_dir",
            OUTPUT_DIR,
        )

    except (
        OSError,
        ValueError,
        TypeError,
        json.JSONDecodeError,
    ):
        return OUTPUT_DIR

# ==================================================
# Camera / Capture Settings
# ==================================================

CAPTURE_INTERVAL = 3.0

CROP_MODE_EXPANDED = "Expanded Object (25%)"
CROP_MODE_OBJECTS = "All Objects in Counting Box"
CROP_MODE_PREVIEW = "Preview Crop Box"
CROP_MODE_FULL = "Full Image"

TRIGGER_MANUAL = "Manual"
TRIGGER_AUTOMATIC = "Automatic"
TRIGGER_CONTINUOUS = "Continuous Counting"

REQUIRE_RED_FOR_AUTOMATIC = True

WINDOW_NAME = "Camera"


# Add near the top-level constants/imports

INVENTORY_SETTINGS_PATH = os.path.join(
    os.path.dirname(__file__),
    "inventory_settings.json",
)


def load_estimated_values():
    try:
        with open(
            INVENTORY_SETTINGS_PATH,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return {}

    return data.get(
        "estimated_values",
        {}
    )

class CameraProcessor:

    def __init__(self):

        # -------------------------
        # Output directory
        # -------------------------

        self.output_dir = get_output_dir()

        os.makedirs(
            self.output_dir,
            exist_ok=True,
        )

        # -------------------------
        # Settings
        # -------------------------
        self.metadata_sync_callback = None

        self.settings = (
            CameraSettings()
        )

        self.camera_width = (
            self.settings.camera_width
        )

        self.camera_height = (
            self.settings.camera_height
        )

        # -------------------------
        # Camera
        # -------------------------

        self.video_source = DEFAULT_VIDEO_SOURCE

        self.cap = cv2.VideoCapture(
            self.video_source
        )

        if not self.cap.isOpened():

            raise RuntimeError(
                f"Could not open video source: "
                f"{DEFAULT_VIDEO_SOURCE}"
            )

        self.apply_camera_resolution()

        # -------------------------
        # Box manager
        # -------------------------

        self.box_manager = (
            BoxManager(
                self.settings
            )
        )

        # -------------------------
        # Object tracker
        # -------------------------

        self.tracker = (
            ObjectTracker()
        )

        # -------------------------
        # Capture
        # -------------------------

        self.crop_number = 1
        self.last_capture_time = 0

        self.trigger_mode = TRIGGER_AUTOMATIC
        self.crop_mode = CROP_MODE_PREVIEW
        self.require_red_for_automatic = (
            REQUIRE_RED_FOR_AUTOMATIC
)

        # Objects that have already crossed
        # the counting box during the current
        # automatic/continuous run.
        self.processed_object_ids = set()

        # Objects currently inside the counting box.
        self.counting_object_ids = set()

        # Total continuous count.
        self.continuous_count = 0

        self.inventory_type = INVENTORY_PURCHASE
        # Manual trigger flag.
        self.manual_trigger_requested = False

        # -------------------------
        # Tool selection
        # -------------------------

        self.tool = None
        self.size_1 = None
        self.size_2 = None
        self.brand = None
        self.measurement = None
        self.drive = None
        self.point = None
        self.specialty_socket = None
        self.invoice = None
        self.ebay_id = None
        self.estimated_value = None
        self.number_sold = None
        self.part_number = None
        self.invoice_price = None
        self.profit = None

        # In __init__, after the tool-selection attributes

        self.estimated_values = (
            load_estimated_values()
        )

        # -------------------------
        # Box display settings
        # -------------------------

        self.show_crop_box = True
        self.show_counting_box = True


    # ==================================================
    # Box Properties
    # ==================================================

    @property
    def scan_box(self):
        return self.box_manager.scan_box


    @scan_box.setter
    def scan_box(self, value):
        self.box_manager.scan_box = value


    @property
    def crop_box(self):
        return self.box_manager.crop_box


    @crop_box.setter
    def crop_box(self, value):
        self.box_manager.crop_box = value


    @property
    def counting_box(self):
        return self.box_manager.counting_box


    @counting_box.setter
    def counting_box(self, value):
        self.box_manager.counting_box = value

    def get_available_video_sources(
        max_sources=10,
    ):
        available = []

        for index in range(max_sources):
            cap = cv2.VideoCapture(index)

            if cap.isOpened():
                success, frame = cap.read()

                if success and frame is not None:
                    available.append(index)

            cap.release()

        return available

    def set_video_source(self, source):
        try:
            source = int(source)
        except (TypeError, ValueError):
            return False

        if source == self.video_source:
            return True

        old_source = self.video_source

        if self.cap.isOpened():
            self.cap.release()

        self.cap = cv2.VideoCapture(source)

        if not self.cap.isOpened():
            print(
                f"Could not open video source: {source}"
            )

            self.cap = cv2.VideoCapture(
                old_source
            )

            if self.cap.isOpened():
                self.apply_camera_resolution()

            return False

        self.video_source = source

        self.apply_camera_resolution()

        success, frame = self.cap.read()

        if not success or frame is None:
            print(
                f"Could not read from video source: {source}"
            )

            self.cap.release()

            self.video_source = old_source

            self.cap = cv2.VideoCapture(
                old_source
            )

            if self.cap.isOpened():
                self.apply_camera_resolution()

            return False

        self.tracker.reset()

        self.processed_object_ids.clear()
        self.counting_object_ids.clear()

        return True

    def set_metadata_sync_callback(self, callback):
        self.metadata_sync_callback = callback

    def set_inventory_type(
        self,
        inventory_type,
    ):
        if inventory_type not in (
            INVENTORY_PURCHASE,
            INVENTORY_SALE,
        ):
            return

        self.inventory_type = inventory_type

    # Add this method to CameraProcessor

    def get_estimated_value(
        self,
        tool_name,
    ):
        if not tool_name:
            return 5.00

        value = self.estimated_values.get(
            str(tool_name).strip()
        )

        if value is None:
            return 5.00

        try:
            return float(value)

        except (
            TypeError,
            ValueError,
        ):
            return 5.00

    def set_metadata(
        self,
        tool=None,
        size_1=None,
        size_2=None,
        brand=None,
        measurement=None,
        drive=None,
        point=None,
        specialty_socket=None,
        invoice=None,
        ebay_id=None,
        estimated_value=None,
        number_sold=None,
        part_number=None,
        invoice_price=None,
        profit=None,
        image_date=None,
    ):
        self.tool = tool
        self.size_1 = size_1
        self.size_2 = size_2
        self.brand = brand
        self.measurement = measurement
        self.drive = drive
        self.point = point
        self.specialty_socket = specialty_socket
        self.invoice = invoice
        self.ebay_id = ebay_id
        self.estimated_value = (
            self.get_estimated_value(
                tool
            )
        )
        self.number_sold = number_sold
        self.invoice_price = invoice_price
        self.part_number = part_number
        self.profit = profit
        self.image_date = image_date

    # ==================================================
    # Settings
    # ==================================================

    def load_settings(self):
        self.settings.load()

        self.camera_width = (
            self.settings.camera_width
        )

        self.camera_height = (
            self.settings.camera_height
        )

        self.box_manager.scan_box = (
            self.settings.scan_box
        )

        self.box_manager.crop_box = list(
            self.settings.crop_box
        )

        self.box_manager.counting_box = (
            list(self.settings.counting_box)
            if self.settings.counting_box is not None
            else None
        )

    # ==================================================
    # Save Settings
    # ==================================================

    def save_settings(self):

        self.settings.camera_width = (
            self.camera_width
        )

        self.settings.camera_height = (
            self.camera_height
        )

        self.box_manager.save()


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

        self.box_manager.mouse_callback(
            event,
            x,
            y,
            flags,
            param,
        )


    # ==================================================
    # Read Frame
    # ==================================================

    def read_frame(self):

        success, frame = (
            self.cap.read()
        )

        if not success:
            return None

        return frame


    def set_require_red_for_automatic(self, enabled):
        self.require_red_for_automatic = bool(enabled)

    # ==================================================
    # Trigger / Crop Settings
    # ==================================================

    def set_trigger_mode(self, mode):
        if mode not in (
            TRIGGER_MANUAL,
            TRIGGER_AUTOMATIC,
            TRIGGER_CONTINUOUS,
        ):
            return

        self.trigger_mode = mode

        # Starting a new automatic/continuous session
        # should allow currently tracked objects to
        # trigger once.
        self.processed_object_ids.clear()
        self.counting_object_ids.clear()

        if mode != TRIGGER_CONTINUOUS:
            self.continuous_count = 0

    def set_crop_mode(self, mode):
        if mode not in (
            CROP_MODE_EXPANDED,
            CROP_MODE_OBJECTS,
            CROP_MODE_PREVIEW,
            CROP_MODE_FULL,
        ):
            return

        self.crop_mode = mode

    def request_manual_capture(self):
        self.manual_trigger_requested = True

    def get_object_type(self, obj):
        return (
            obj.get("class_name")
            or obj.get("label")
            or obj.get("class")
            or obj.get("type")
            or ""
        )

    def point_inside_counting_box(self, x, y):
        if self.counting_box is None:
            return False

        x1, y1, x2, y2 = self.counting_box

        return (
            x1 <= x <= x2
            and y1 <= y <= y2
        )

    def object_center_inside_counting_box(self, box):
        if box is None:
            return False

        x1, y1, x2, y2 = box

        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2

        return self.point_inside_counting_box(
            center_x,
            center_y,
        )

    def expanded_object_box(self, box, frame):
        if box is None:
            return None

        x1, y1, x2, y2 = box

        width = x2 - x1
        height = y2 - y1

        expand_x = width * 0.25
        expand_y = height * 0.25

        frame_height, frame_width = frame.shape[:2]

        return [
            max(0, int(x1 - expand_x)),
            max(0, int(y1 - expand_y)),
            min(frame_width, int(x2 + expand_x)),
            min(frame_height, int(y2 + expand_y)),
        ]

    def crop_from_box(self, frame, box):
        if frame is None or box is None:
            return None

        height, width = frame.shape[:2]

        x1, y1, x2, y2 = [
            int(value)
            for value in box
        ]

        x1 = max(0, min(x1, width))
        x2 = max(0, min(x2, width))
        y1 = max(0, min(y1, height))
        y2 = max(0, min(y2, height))

        if x2 <= x1 or y2 <= y1:
            return None

        crop = frame[y1:y2, x1:x2].copy()

        if crop.size == 0:
            return None

        return crop

    def get_capture_crop(
        self,
        frame,
        objects,
    ):
        """
        Return the image that should be saved according
        to the selected crop mode.
        """

        if self.crop_mode == CROP_MODE_FULL:
            return frame.copy()

        if self.crop_mode == CROP_MODE_PREVIEW:
            return self.crop_from_box(
                frame,
                self.crop_box,
            )

        if self.crop_mode == CROP_MODE_EXPANDED:
            # Use the first triggering object.
            for object_id, obj in objects.items():

                if obj["frames"] < MIN_FRAMES:
                    continue

                box = [
                    obj["x"],
                    obj["y"],
                    obj["x"] + obj["w"],
                    obj["y"] + obj["h"],
                ]

                if self.object_center_inside_counting_box(box):
                    expanded = self.expanded_object_box(
                        box,
                        frame,
                    )

                    return self.crop_from_box(
                        frame,
                        expanded,
                    )

            return None

        if self.crop_mode == CROP_MODE_OBJECTS:
            boxes = []

            for object_id, obj in objects.items():

                if obj["frames"] < MIN_FRAMES:
                    continue

                box = [
                    obj["x"],
                    obj["y"],
                    obj["x"] + obj["w"],
                    obj["y"] + obj["h"],
                ]

                if self.object_center_inside_counting_box(
                    box
                ):
                    boxes.append(box)

            if not boxes:
                return None

            x1 = min(box[0] for box in boxes)
            y1 = min(box[1] for box in boxes)
            x2 = max(box[2] for box in boxes)
            y2 = max(box[3] for box in boxes)

            return self.crop_from_box(
                frame,
                [x1, y1, x2, y2],
            )

        return None

    # ==================================================
    # Capture Current Counting Area
    # ==================================================

    def capture_counting_area(
        self,
        frame,
        objects,
        object_id=None,
    ):
        if not self.tool or not self.brand:
            print(
                "Tool and brand must be selected before capturing."
            )
            return None

        crop = self.get_capture_crop(
            frame,
            objects,
        )

        if crop is None:
            return None

        today = datetime.now()

        year = today.strftime("%Y")
        month = today.strftime("%m")
        day = today.strftime("%d")
        self.output_dir = get_output_dir()

        output_dir = os.path.join(
            self.output_dir,
            self.inventory_type,
            self.tool,
            self.brand,
            year,
            month,
            day,
        )

        os.makedirs(
            output_dir,
            exist_ok=True,
        )

        crop_number = self.get_next_tool_number()

        if crop_number is None:
            return None

        filename = (
            f"{self.tool}_{self.brand}_"
            f"{crop_number:03d}_Unlogged.jpg"
        )

        filepath = os.path.join(
            output_dir,
            filename,
        )

        if not cv2.imwrite(filepath, crop):
            return None

        # -------------------------
        # Save raw metadata JSON
        # -------------------------

        json_filename = (
            f"{self.tool}_{self.brand}_"
            f"{crop_number:03d}_Unlogged.json"
        )

        json_filename2 = (
            f"{self.tool}_{self.brand}_"
            f"{crop_number:03d}_Logged.json"
        )


        json_filepath = os.path.join(
            output_dir,
            json_filename,
        )

        json_filepath2 = os.path.join(
            output_dir,
            json_filename2,
        )

        absolute_image_path = os.path.abspath(
            filepath,
        )

        absolute_json2_path = os.path.abspath(
            json_filepath2,
        )

        metadata = {
            "Tool Name": self.tool,
            "Size-1": self.size_1,
            "Size-2": self.size_2,
            "Brand": self.brand,
            "Measurement": self.measurement,
            "Drive": self.drive,
            "Point": self.point,
            "Specialty Socket": self.specialty_socket,
            "Invoice": self.invoice,
            "eBay ID": self.ebay_id,
            "Part Number": self.part_number,            
            "Estimated Value": self.estimated_value,
            "Number Sold": len(objects),
            "Invoice Price": self.invoice_price,
            "Profit": self.profit,
            "Date": today.strftime("%Y-%m-%d"),
            "Inventory Type": self.inventory_type,
            "File Path to Image": absolute_image_path,
            "File Path to JSON": absolute_json2_path,
        }

        try:

            with open(
                json_filepath,
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    metadata,
                    file,
                    indent=4,
                    ensure_ascii=False,
                )

        except OSError as error:

            print(
                f"ERROR: Could not save metadata JSON: "
                f"{error}"
            )

            return None

        # -------------------------
        # Send JSON to logger
        # -------------------------

        submit_json(
            json_filepath
        )

        self.crop_number += 1

        self.last_capture_time = (
            cv2.getTickCount()
            / cv2.getTickFrequency()
        )

        print(
            f"Saved object: {filepath}"
        )

        return filepath


    # ==================================================
    # Process Frame
    # ==================================================

    def process_frame(
        self,
        frame,
    ):

        self.box_manager.initialize(frame)

        original_frame = frame.copy()

        detections = self.tracker.detect(frame)

        objects = self.tracker.update(
            detections
        )

        current_time = (
            cv2.getTickCount()
            / cv2.getTickFrequency()
        )

        objects_inside = set()

        # --------------------------------------------------
        # Process tracked objects
        # --------------------------------------------------

        for object_id, obj in objects.items():

            x = obj["x"]
            y = obj["y"]
            w = obj["w"]
            h = obj["h"]

            object_box = [
                x,
                y,
                x + w,
                y + h,
            ]

            center_inside = (
                self.object_center_inside_counting_box(
                    object_box
                )
            )

            if center_inside:
                objects_inside.add(object_id)

            # --------------------------------------------------
            # Draw object
            # --------------------------------------------------

            if obj["frames"] >= MIN_FRAMES:

                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    (0, 255, 0),
                    2,
                )

                center_x = x + (w // 2)
                center_y = y + (h // 2)

                cv2.circle(
                    frame,
                    (center_x, center_y),
                    5,
                    (0, 0, 255),
                    -1,
                )

                cv2.putText(
                    frame,
                    f"ID: {object_id}",
                    (
                        x,
                        max(y - 25, 20),
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )

                cv2.putText(
                    frame,
                    f"Frames: {obj['frames']}",
                    (
                        x,
                        max(y - 5, 40),
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 0),
                    1,
                )

            # --------------------------------------------------
            # Automatic capture
            #
            # Only capture when:
            # - automatic mode is active
            # - object has enough tracking frames
            # - object center is inside counting box
            # - red scan condition is satisfied
            # - object has not already been processed
            # - capture interval has elapsed
            # --------------------------------------------------

            if self.require_red_for_automatic:

                red_detected = (
                    self.has_red_in_scan_area(
                        original_frame
                    )
                )

            else:

                red_detected = True

            if (
                self.trigger_mode == TRIGGER_AUTOMATIC
                and obj["frames"] >= MIN_FRAMES
                and center_inside
                and red_detected
                and object_id not in self.processed_object_ids
            ):

                time_since_capture = (
                    current_time
                    - self.last_capture_time
                )

                if time_since_capture >= CAPTURE_INTERVAL:
                    if self.metadata_sync_callback:
                        self.metadata_sync_callback()

                    saved_filename = (
                        self.capture_counting_area(
                            original_frame,
                            objects,
                            object_id,
                        )
                    )

                    if saved_filename:

                        self.processed_object_ids.add(
                            object_id
                        )

                        obj["captured"] = True

            # --------------------------------------------------
            # Continuous counting
            #
            # Count an object exactly once when its center
            # enters the counting box.
            # --------------------------------------------------

            elif (
                self.trigger_mode == TRIGGER_CONTINUOUS
                and obj["frames"] >= MIN_FRAMES
                and center_inside
                and object_id not in self.processed_object_ids
            ):

                self.processed_object_ids.add(
                    object_id
                )

                self.continuous_count += 1

        # --------------------------------------------------
        # Manual capture
        #
        # Counts/captures every object whose center is
        # currently inside the counting box.
        # --------------------------------------------------

        if (
            self.trigger_mode == TRIGGER_MANUAL
            and self.manual_trigger_requested
        ):

            self.manual_trigger_requested = False

            manual_objects = {}

            for object_id, obj in objects.items():

                if obj["frames"] < MIN_FRAMES:
                    continue

                box = [
                    obj["x"],
                    obj["y"],
                    obj["x"] + obj["w"],
                    obj["y"] + obj["h"],
                ]

                if (
                    not self.show_counting_box
                    or self.object_center_inside_counting_box(box)
                ):
                    manual_objects[object_id] = obj

            if manual_objects:

                if self.metadata_sync_callback:
                    self.metadata_sync_callback()

                saved_filename = (
                    self.capture_counting_area(
                        original_frame,
                        manual_objects,
                    )
                )

                if saved_filename:

                    for object_id in manual_objects:

                        manual_objects[
                            object_id
                        ]["captured"] = True

        # --------------------------------------------------
        # Reset processed IDs after objects leave the
        # counting box.
        #
        # This allows an object to be processed again only
        # after it has actually left and then re-entered.
        # --------------------------------------------------

        objects_that_left = (
            self.counting_object_ids
            - objects_inside
        )

        self.processed_object_ids.difference_update(
            objects_that_left
        )

        self.counting_object_ids = objects_inside

        # --------------------------------------------------
        # Detection count
        # --------------------------------------------------

        cv2.putText(
            frame,
            f"Objects: {len(detections)}",
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2,
        )

        if self.trigger_mode == TRIGGER_CONTINUOUS:

            cv2.putText(
                frame,
                f"Count: {self.continuous_count}",
                (20, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2,
            )

        # --------------------------------------------------
        # Scan box
        # --------------------------------------------------

        if self.scan_box is not None:

            (
                box_x1,
                box_y1,
                box_x2,
                box_y2,
            ) = self.scan_box

            cv2.rectangle(
                frame,
                (box_x1, box_y1),
                (box_x2, box_y2),
                (255, 0, 255),
                2,
            )

            cv2.putText(
                frame,
                "Scan Dot",
                (
                    box_x1 - 10,
                    max(box_y1 - 10, 20),
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 0, 255),
                2,
            )

        # --------------------------------------------------
        # Preview Crop box
        # --------------------------------------------------

        if (
            self.crop_box is not None
            and self.show_crop_box
        ):

            (
                crop_x1,
                crop_y1,
                crop_x2,
                crop_y2,
            ) = self.crop_box

            cv2.rectangle(
                frame,
                (crop_x1, crop_y1),
                (crop_x2, crop_y2),
                (0, 255, 0),
                2,
            )

            cv2.putText(
                frame,
                "Preview Crop",
                (
                    crop_x1 - 10,
                    max(crop_y1 - 10, 20),
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )

        # --------------------------------------------------
        # Counting box
        # --------------------------------------------------

        if (
            self.counting_box is not None
            and self.show_counting_box
        ):

            (
                counting_x1,
                counting_y1,
                counting_x2,
                counting_y2,
            ) = self.counting_box

            cv2.rectangle(
                frame,
                (counting_x1, counting_y1),
                (counting_x2, counting_y2),
                (255, 0, 0),
                2,
            )

            cv2.putText(
                frame,
                "Counting Box",
                (
                    counting_x1 - 10,
                    max(counting_y1 - 10, 20),
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 0, 0),
                2,
            )

        return (
            frame,
            len(detections),
        )

    
    # ==================================================
    # Tool Number
    # ==================================================

    def get_next_tool_number(self):
        """Get the next sequential number for the current tool and brand."""
        if not self.tool or not self.brand:
            return None

        today = datetime.now()

        year = today.strftime("%Y")
        month = today.strftime("%m")
        day = today.strftime("%d")
        self.output_dir = get_output_dir()

        output_dir = os.path.join(
            self.output_dir,
            self.inventory_type,
            self.tool,
            self.brand,
            year,
            month,
            day,
        )

        os.makedirs(output_dir, exist_ok=True)

        prefix = f"{self.tool}_{self.brand}_"

        existing_files = [
            f for f in os.listdir(output_dir)
            if f.startswith(prefix) and f.endswith(".jpg")
        ]

        numbers = []

        for filename in existing_files:
            try:
                number_part = filename[len(prefix):].split("_")[0]
                numbers.append(int(number_part))
            except (ValueError, IndexError):
                continue

        return max(numbers, default=0) + 1


    # ==================================================
    # Set Box Display
    # ==================================================

    def set_box_display(
        self,
        show_crop_box,
        show_counting_box,
    ):

        self.show_crop_box = (
            show_crop_box
        )

        self.show_counting_box = (
            show_counting_box
        )

        self.box_manager.set_box_display(
            True,
            show_crop_box,
            show_counting_box,
        )

    # ==================================================
    # Crop Object
    # ==================================================

    def crop_object(
        self,
        frame,
        box,
    ):

        if frame is None:
            return None

        if self.crop_box is None:
            return None

        (
            x1,
            y1,
            x2,
            y2,
        ) = self.crop_box

        height, width = (
            frame.shape[:2]
        )

        # -------------------------
        # Clamp crop coordinates
        # -------------------------

        x1 = max(
            0,
            min(
                int(x1),
                width,
            ),
        )

        x2 = max(
            0,
            min(
                int(x2),
                width,
            ),
        )

        y1 = max(
            0,
            min(
                int(y1),
                height,
            ),
        )

        y2 = max(
            0,
            min(
                int(y2),
                height,
            ),
        )

        if (
            x2 <= x1
            or y2 <= y1
        ):
            return None

        # -------------------------
        # Crop frame
        # -------------------------

        crop = frame[
            y1:y2,
            x1:x2,
        ].copy()

        if crop.size == 0:
            return None

        return crop

    # ==================================================
    # Capture
    # ==================================================

    def capture_object(self, frame, box):
        """Capture and save the detected object image."""
        if not self.tool or not self.brand:
            print(
                "Tool and brand must be selected before capturing."
            )
            return None

        if frame is None:
            return None

        original = frame.copy()


        today = datetime.now()

        year = today.strftime("%Y")
        month = today.strftime("%m")
        day = today.strftime("%d")
        self.output_dir = get_output_dir()

        output_dir = os.path.join(
            self.output_dir,
            self.inventory_type,
            self.tool,
            self.brand,
            year,
            month,
            day,
        )

        os.makedirs(
            output_dir,
            exist_ok=True,
        )

        crop_number = self.get_next_tool_number()

        if crop_number is None:
            return None

        filename = (
            f"{self.tool}_{self.brand}_"
            f"{crop_number:03d}_Unlogged.jpg"
        )

        filepath = os.path.join(
            output_dir,
            filename,
        )

        if not cv2.imwrite(filepath, original):
            return None

        # -------------------------
        # Save raw metadata JSON
        # -------------------------

        json_filename = (
            f"{self.tool}_{self.brand}_"
            f"{crop_number:03d}_Unlogged.json"
        )

        json_filepath = os.path.join(
            output_dir,
            json_filename,
        )

        metadata = {
            "Tool Name": self.tool,
            "Size-1": self.size_1,
            "Size-2": self.size_2,
            "Brand": self.brand,
            "Measurement": self.measurement,
            "Drive": self.drive,
            "Point": self.point,
            "Specialty Socket": self.specialty_socket,
            "Invoice": self.invoice,
            "eBay ID": self.ebay_id,
            "Part Number": self.part_number,
            "Estimated Value": self.estimated_value,
            "Number Sold": self.number_sold,
            "Invoice Price": self.invoice_price,
            "Profit": self.profit,
            "Date": today.strftime("%Y-%m-%d"),
            "Inventory Type": self.inventory_type,
            "File Path to Image": os.path.abspath(
                filepath,
            ),
            "File Path to JSON": os.path.abspath(
                json_filepath,
            ),
        }

        try:
            with open(
                json_filepath,
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    metadata,
                    file,
                    indent=4,
                    ensure_ascii=False,
                )

        except OSError as error:
            print(
                f"ERROR: Could not save metadata JSON: "
                f"{error}"
            )
            return None

        # -------------------------
        # Send JSON to logger
        # -------------------------

        submit_json(
            json_filepath
        )

        self.crop_number += 1

        self.last_capture_time = (
            cv2.getTickCount()
            / cv2.getTickFrequency()
        )

        print(
            f"Saved object: {filepath}"
        )

        return filepath

    # ==================================================
    # Object Crop Validation
    # ==================================================

    def object_inside_crop_area(
        self,
        box,
    ):

        if (
            box is None
            or self.crop_box is None
        ):
            return False

        obj_x1, obj_y1, obj_x2, obj_y2 = box
        crop_x1, crop_y1, crop_x2, crop_y2 = (
            self.crop_box
        )

        # -------------------------
        # Object center point
        # -------------------------

        center_x = (
            obj_x1 + obj_x2
        ) / 2

        center_y = (
            obj_y1 + obj_y2
        ) / 2

        center_inside = (
            crop_x1 <= center_x <= crop_x2
            and
            crop_y1 <= center_y <= crop_y2
        )

        if not center_inside:
            return False

        # -------------------------
        # Intersection
        # -------------------------

        intersection_x1 = max(
            obj_x1,
            crop_x1,
        )

        intersection_y1 = max(
            obj_y1,
            crop_y1,
        )

        intersection_x2 = min(
            obj_x2,
            crop_x2,
        )

        intersection_y2 = min(
            obj_y2,
            crop_y2,
        )

        if (
            intersection_x2 <= intersection_x1
            or intersection_y2 <= intersection_y1
        ):
            return False

        intersection_area = (
            intersection_x2
            - intersection_x1
        ) * (
            intersection_y2
            - intersection_y1
        )

        # -------------------------
        # Object area
        # -------------------------

        object_area = (
            obj_x2 - obj_x1
        ) * (
            obj_y2 - obj_y1
        )

        if object_area <= 0:
            return False

        # -------------------------
        # Percentage inside crop
        # -------------------------

        percentage_inside = (
            intersection_area
            / object_area
        )

        return (
            percentage_inside >= 0.75
        )

    # ==================================================
    # Red Detection
    # ==================================================

    def has_red_in_scan_area(
        self,
        frame,
    ):

        if self.scan_box is None:
            return False

        (
            x1,
            y1,
            x2,
            y2,
        ) = self.scan_box

        height, width = (
            frame.shape[:2]
        )

        x1 = max(
            0,
            min(x1, width),
        )

        x2 = max(
            0,
            min(x2, width),
        )

        y1 = max(
            0,
            min(y1, height),
        )

        y2 = max(
            0,
            min(y2, height),
        )

        if (
            x2 <= x1
            or y2 <= y1
        ):
            return False

        scan_area = frame[
            y1:y2,
            x1:x2
        ]

        hsv = cv2.cvtColor(
            scan_area,
            cv2.COLOR_BGR2HSV,
        )

        # -------------------------
        # Red wraps around HSV
        # -------------------------

        lower_red_1 = (
            0,
            100,
            80,
        )

        upper_red_1 = (
            10,
            255,
            255,
        )

        lower_red_2 = (
            170,
            100,
            80,
        )

        upper_red_2 = (
            180,
            255,
            255,
        )

        mask1 = cv2.inRange(
            hsv,
            lower_red_1,
            upper_red_1,
        )

        mask2 = cv2.inRange(
            hsv,
            lower_red_2,
            upper_red_2,
        )

        red_mask = cv2.bitwise_or(
            mask1,
            mask2,
        )

        red_pixels = (
            cv2.countNonZero(
                red_mask
            )
        )

        total_pixels = (
            scan_area.shape[0]
            * scan_area.shape[1]
        )

        if total_pixels == 0:
            return False

        red_percent = (
            red_pixels
            / total_pixels
            * 100
        )

        return (
            red_percent
            >= MIN_RED_PERCENT
        )


    # ==================================================
    # Release Camera
    # ==================================================

    def release(self):

        self.save_settings()

        if self.cap.isOpened():

            self.cap.release()


    # ==================================================
    # Reopen Camera
    # ==================================================

    def reopen_camera(self):

        if self.cap.isOpened():

            self.cap.release()

        self.cap = cv2.VideoCapture(
            self.video_source
        )

        if not self.cap.isOpened():

            raise RuntimeError(
                f"Could not reopen video source: "
                f"{self.video_source}"
            )

        self.apply_camera_resolution()

        success, frame = (
            self.cap.read()
        )

        if (
            not success
            or frame is None
        ):

            print(
                "Warning: camera opened but "
                "could not read initial frame."
            )

            return False

        return True


    # ==================================================
    # Apply Camera Resolution
    # ==================================================

    def apply_camera_resolution(self):

        self.cap.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            self.camera_width,
        )

        self.cap.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            self.camera_height,
        )

        actual_width = int(
            self.cap.get(
                cv2.CAP_PROP_FRAME_WIDTH
            )
        )

        actual_height = int(
            self.cap.get(
                cv2.CAP_PROP_FRAME_HEIGHT
            )
        )

        if (
            actual_width
            != self.camera_width
            or actual_height
            != self.camera_height
        ):

            print(
                f"Warning: requested camera "
                f"resolution "
                f"{self.camera_width}x"
                f"{self.camera_height}, "
                f"but camera is using "
                f"{actual_width}x"
                f"{actual_height}"
            )

        else:

            print(
                f"Camera resolution: "
                f"{actual_width}x"
                f"{actual_height}"
            )


    # ==================================================
    # Set Camera Resolution
    # ==================================================

    def set_resolution(
        self,
        width,
        height,
    ):

        resolution = (
            int(width),
            int(height),
        )

        if (
            resolution
            not in SUPPORTED_RESOLUTIONS
        ):

            print(
                f"Unsupported camera resolution: "
                f"{width}x{height}"
            )

            return False

        if (
            resolution[0]
            == self.camera_width
            and resolution[1]
            == self.camera_height
        ):

            return True

        old_width = (
            self.camera_width
        )

        old_height = (
            self.camera_height
        )

        print(
            f"Changing camera resolution from "
            f"{old_width}x{old_height} to "
            f"{resolution[0]}x{resolution[1]}"
        )

        # -------------------------
        # Change resolution
        # -------------------------

        self.camera_width = (
            resolution[0]
        )

        self.camera_height = (
            resolution[1]
        )

        # -------------------------
        # Reopen camera
        # -------------------------

        if not self.reopen_camera():

            print(
                f"Camera failed to start at "
                f"{self.camera_width}x"
                f"{self.camera_height}."
            )

            self.camera_width = old_width
            self.camera_height = old_height

            self.reopen_camera()

            return False

        # -------------------------
        # Test stream
        # -------------------------

        success, test_frame = (
            self.cap.read()
        )

        if (
            not success
            or test_frame is None
        ):

            print(
                f"Camera failed to read a frame "
                f"at {self.camera_width}x"
                f"{self.camera_height}."
            )

            self.cap.release()

            self.cap = cv2.VideoCapture(
                self.video_source
            )

            if self.cap.isOpened():

                self.camera_width = (
                    old_width
                )

                self.camera_height = (
                    old_height
                )

                self.apply_camera_resolution()

            else:

                print(
                    "Could not restore previous "
                    "camera stream."
                )

            return False

        # -------------------------
        # Reset tracking
        # -------------------------

        self.tracker.reset()

        # -------------------------
        # Scale boxes
        # -------------------------

        self.box_manager.scale_boxes(
            old_width,
            old_height,
            self.camera_width,
            self.camera_height,
        )

        # -------------------------
        # Save settings
        # -------------------------

        self.save_settings()

        print(
            f"Camera resolution changed to "
            f"{self.camera_width}x"
            f"{self.camera_height}"
        )

        return True


    # ==================================================
    # Get Supported Resolutions
    # ==================================================

    def get_supported_resolutions(
        self,
    ):

        resolutions_to_test = (
            SUPPORTED_RESOLUTIONS
        )

        supported = []

        current_width = int(
            self.cap.get(
                cv2.CAP_PROP_FRAME_WIDTH
            )
        )

        current_height = int(
            self.cap.get(
                cv2.CAP_PROP_FRAME_HEIGHT
            )
        )

        print()
        print(
            "================================"
        )
        print(
            "TESTING CAMERA RESOLUTIONS"
        )
        print(
            "================================"
        )

        for (
            width,
            height,
        ) in resolutions_to_test:

            self.cap.set(
                cv2.CAP_PROP_FRAME_WIDTH,
                width,
            )

            self.cap.set(
                cv2.CAP_PROP_FRAME_HEIGHT,
                height,
            )

            actual_width = int(
                self.cap.get(
                    cv2.CAP_PROP_FRAME_WIDTH
                )
            )

            actual_height = int(
                self.cap.get(
                    cv2.CAP_PROP_FRAME_HEIGHT
                )
            )

            if (
                actual_width == width
                and actual_height == height
            ):

                supported.append(
                    (
                        width,
                        height,
                    )
                )

                print(
                    f"SUPPORTED: "
                    f"{width}x{height}"
                )

            else:

                print(
                    f"NOT SUPPORTED: "
                    f"{width}x{height}"
                    f" -> "
                    f"{actual_width}x"
                    f"{actual_height}"
                )

        # -------------------------
        # Restore resolution
        # -------------------------

        self.cap.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            current_width,
        )

        self.cap.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            current_height,
        )

        print(
            "================================"
        )

        print(
            f"Found {len(supported)} "
            f"supported resolutions."
        )

        print(
            "================================"
        )

        print()

        return supported