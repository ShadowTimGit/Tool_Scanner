import cv2
import json
import os
import threading
import time

from datetime import datetime

from settings_menu.config import (
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
)

from Camera.box_manager import (
    BoxManager,
)

from GUI.gui_constants import (
    INVENTORY_PURCHASE,
    INVENTORY_SALE,
)

from Camera.camera_processor_capture import (
    CameraCaptureMixin,
)

from Camera.camera_processor_detection import (
    CameraDetectionMixin,
)

from Camera.camera_constants import (
    CAPTURE_INTERVAL,
    TRIGGER_MANUAL,
    TRIGGER_AUTOMATIC,
    TRIGGER_CONTINUOUS,
    DEBUG_AUTO_CAPTURE,
    DEBUG_CAMERA,
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

WINDOW_NAME = "Camera"


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
        {},
    )


class CameraProcessor(
    CameraCaptureMixin,
    CameraDetectionMixin,
):

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

        self.recent_crops_callback = None
        self.metadata_sync_callback = None

        self.settings = CameraSettings()

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

        self.camera_lock = threading.Lock()

        self.apply_camera_resolution()

        # -------------------------
        # Box manager
        # -------------------------

        self.box_manager = BoxManager(
            self.settings
        )

        # -------------------------
        # Object tracker
        # -------------------------

        self.tracker = ObjectTracker()

        self.tracker_lock = threading.RLock()

        # -------------------------
        # Capture
        # -------------------------

        self.crop_number = 1
        self.last_capture_time = 0
        self.last_detection_time = 0.0
        self.recent_session_crops = []

        self.detection_interval = max(
            0.05,
            float(
                os.getenv(
                    "TOOL_SCANNER_DETECTION_INTERVAL",
                    "0.08",
                )
            ),
        )

        self.trigger_mode = TRIGGER_AUTOMATIC
        self.crop_mode = CROP_MODE_PREVIEW

        self.require_red_for_automatic = False

        self.processed_object_ids = set()
        self.counting_object_ids = set()

        self.continuous_count = 0

        self.inventory_type = INVENTORY_PURCHASE

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
        self.image_date = None

        self.estimated_values = (
            load_estimated_values()
        )

        # -------------------------
        # Box display settings
        # -------------------------

        self.show_crop_box = True
        self.show_counting_box = True

        # ==================================================
        # Background Processing
        # ==================================================

        self.processing_thread = None
        self.processing_running = True

        self.processing_condition = (
            threading.Condition()
        )

        self.pending_frame = None

        self.latest_processed_frame = None
        self.latest_detection_count = 0

        self.processing_thread = threading.Thread(
            target=self._processing_loop,
            name="CameraProcessing",
            daemon=True,
        )

        self.processing_thread.start()

    # ==================================================
    # Callbacks
    # ==================================================

    def set_recent_crops_callback(
        self,
        callback,
    ):
        self.recent_crops_callback = callback

    def set_metadata_sync_callback(
        self,
        callback,
    ):
        self.metadata_sync_callback = callback

    # ==================================================
    # Background Processing
    # ==================================================

    def _processing_loop(self):

        while self.processing_running:

            with self.processing_condition:

                while (
                    self.processing_running
                    and self.pending_frame is None
                ):
                    self.processing_condition.wait(
                        timeout=0.1
                    )

                if not self.processing_running:
                    return

                frame = self.pending_frame
                self.pending_frame = None

            if frame is None:
                continue

            try:

                (
                    processed_frame,
                    detection_count,
                ) = self._process_frame_sync(
                    frame
                )

                with self.processing_condition:

                    self.latest_processed_frame = (
                        processed_frame
                    )

                    self.latest_detection_count = (
                        detection_count
                    )

            except Exception:

                import traceback

                print(
                    "CAMERA PROCESSING ERROR:"
                )

                traceback.print_exc()

    def process_frame(self, frame):
        """
        Queue a frame for background processing.

        This method intentionally returns immediately so
        the Tkinter UI thread is not blocked by detection,
        tracking, image processing, or file operations.
        """

        if frame is None:
            return None, 0

        with self.processing_condition:

            self.pending_frame = frame.copy()

            self.processing_condition.notify()

            if self.latest_processed_frame is not None:

                return (
                    self.latest_processed_frame,
                    self.latest_detection_count,
                )

        return frame, 0

    def _process_frame_sync(self, frame):
        """
        Actual frame processing.

        This method runs exclusively on the
        CameraProcessing background thread.
        """

        self.box_manager.initialize(frame)

        original_frame = frame.copy()

        detections = self._detect_objects(
            frame
        )

        objects = self._update_tracked_objects(
            detections
        )

        current_time = (
            self._get_current_capture_time()
        )

        red_detected = self._check_red_scan(
            original_frame
        )

        objects_inside = (
            self._process_tracked_objects(
                frame=frame,
                original_frame=original_frame,
                objects=objects,
                red_detected=red_detected,
                current_time=current_time,
            )
        )

        self._handle_manual_capture(
            original_frame=original_frame,
            objects=objects,
        )

        self._update_counting_state(
            objects_inside
        )

        detection_count = (
            len(detections)
            if detections is not None
            else len(objects)
        )

        self._draw_frame_overlay(
            frame=frame,
            detection_count=detection_count,
        )

        return frame, detection_count

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

    # ==================================================
    # Video Sources
    # ==================================================

    @staticmethod
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

        except (
            TypeError,
            ValueError,
        ):
            return False

        if source == self.video_source:
            return True

        old_source = self.video_source

        with self.camera_lock:

            if self.cap.isOpened():
                self.cap.release()

            self.cap = cv2.VideoCapture(
                source
            )

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

            success, frame = (
                self.cap.read()
            )

            if (
                not success
                or frame is None
            ):

                print(
                    f"Could not read from video source: "
                    f"{source}"
                )

                self.cap.release()

                self.video_source = old_source

                self.cap = cv2.VideoCapture(
                    old_source
                )

                if self.cap.isOpened():
                    self.apply_camera_resolution()

                return False

        with self.tracker_lock:
            self.tracker.reset()

        self.processed_object_ids.clear()
        self.counting_object_ids.clear()

        return True

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
            list(
                self.settings.counting_box
            )
            if self.settings.counting_box
            is not None
            else None
        )

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

        with self.camera_lock:

            success, frame = (
                self.cap.read()
            )

        if not success:
            return None

        return frame

    # ==================================================
    # Trigger Settings
    # ==================================================

    def set_require_red_for_automatic(
        self,
        enabled,
    ):
        self.require_red_for_automatic = bool(
            enabled
        )

    def set_trigger_mode(
        self,
        mode,
    ):

        if mode not in (
            TRIGGER_MANUAL,
            TRIGGER_AUTOMATIC,
            TRIGGER_CONTINUOUS,
        ):
            return

        self.trigger_mode = mode

        self.processed_object_ids.clear()
        self.counting_object_ids.clear()

        if mode != TRIGGER_CONTINUOUS:
            self.continuous_count = 0

    def set_crop_mode(
        self,
        mode,
    ):

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
    # Release Camera
    # ==================================================

    def release(self):

        self.processing_running = False

        with self.processing_condition:

            self.processing_condition.notify_all()

        if (
            self.processing_thread
            is not None
            and self.processing_thread.is_alive()
        ):

            self.processing_thread.join(
                timeout=1.0
            )

        self.save_settings()

        with self.camera_lock:

            if self.cap.isOpened():
                self.cap.release()

    # ==================================================
    # Reopen Camera
    # ==================================================

    def reopen_camera(self):

        with self.camera_lock:

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

            if DEBUG_CAMERA:
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

            if DEBUG_CAMERA:
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

        old_width = self.camera_width
        old_height = self.camera_height

        print(
            f"Changing camera resolution from "
            f"{old_width}x{old_height} to "
            f"{resolution[0]}x"
            f"{resolution[1]}"
        )

        self.camera_width = resolution[0]
        self.camera_height = resolution[1]

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

            with self.camera_lock:

                self.cap.release()

                self.cap = cv2.VideoCapture(
                    self.video_source
                )

                if self.cap.isOpened():

                    self.camera_width = old_width
                    self.camera_height = old_height

                    self.apply_camera_resolution()

                else:

                    print(
                        "Could not restore previous "
                        "camera stream."
                    )

            return False

        with self.tracker_lock:
            self.tracker.reset()

        self.box_manager.scale_boxes(
            old_width,
            old_height,
            self.camera_width,
            self.camera_height,
        )

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

        supported = []

        with self.camera_lock:

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

            if DEBUG_CAMERA:
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
            ) in SUPPORTED_RESOLUTIONS:

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

                    if DEBUG_CAMERA:
                        print(
                            f"SUPPORTED: "
                            f"{width}x{height}"
                        )

                else:

                    if DEBUG_CAMERA:
                        print(
                            f"NOT SUPPORTED: "
                            f"{width}x{height}"
                            f" -> "
                            f"{actual_width}x"
                            f"{actual_height}"
                        )

            self.cap.set(
                cv2.CAP_PROP_FRAME_WIDTH,
                current_width,
            )

            self.cap.set(
                cv2.CAP_PROP_FRAME_HEIGHT,
                current_height,
            )

        if DEBUG_CAMERA:
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


    # ==================================================
    # Tracker Tuning
    # ==================================================

    def set_tracker_setting(
        self,
        name,
        value,
    ):
        with self.tracker_lock:
            self.tracker.set_tracker_setting(
                name,
                value,
            )

    def reset_tracker(self):
        with self.tracker_lock:
            self.tracker.reset()


