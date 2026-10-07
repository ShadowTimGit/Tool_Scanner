import cv2
import time

from Camera.camera_constants import (
    MIN_RED_PERCENT,
    TRIGGER_AUTOMATIC,
    TRIGGER_CONTINUOUS,
    CAPTURE_INTERVAL,
    DEBUG_AUTO_CAPTURE,
)

from Camera.object_tracker import (
    MAX_MISSED_FRAMES,
    MIN_FRAMES,
)


class CameraDetectionMixin:

    # ==================================================
    # Object Helpers
    # ==================================================

    def get_object_type(
        self,
        obj,
    ):

        return (
            obj.get("class_name")
            or obj.get("label")
            or obj.get("class")
            or obj.get("type")
            or ""
        )

    def point_inside_counting_box(
        self,
        x,
        y,
    ):

        if self.counting_box is None:
            return False

        x1, y1, x2, y2 = (
            self.counting_box
        )

        return (
            x1 <= x <= x2
            and y1 <= y <= y2
        )

    def object_center_inside_counting_box(
        self,
        box,
    ):

        if box is None:
            return False

        x1, y1, x2, y2 = box

        center_x = (
            x1 + x2
        ) / 2

        center_y = (
            y1 + y2
        ) / 2

        return self.point_inside_counting_box(
            center_x,
            center_y,
        )

    # ==================================================
    # Detection / Tracking
    # ==================================================

    def _detect_objects(self, frame):

        now = time.monotonic()

        with self.tracker_lock:

            should_detect = (
                now - self.last_detection_time
                >= self.detection_interval
                or not self.tracker.objects
            )

            if not should_detect:
                return None

            detections = self.tracker.detect(
                frame
            )

        self.last_detection_time = now

        return detections
    

    def _update_tracked_objects(
        self,
        detections,
    ):

        with self.tracker_lock:

            if detections is None:
                return dict(
                    self.tracker.objects
                )

            self.tracker.update(
                detections
            )

            return dict(
                self.tracker.objects
            )

    def _get_current_capture_time(
        self,
    ):

        return (
            cv2.getTickCount()
            / cv2.getTickFrequency()
        )

    # ==================================================
    # Automatic Scan / Red Detection
    # ==================================================

    def _check_red_scan(
        self,
        frame,
    ):

        if (
            self.trigger_mode
            != TRIGGER_AUTOMATIC
            or not self.require_red_for_automatic
            or self.scan_box is None
        ):
            return True

        return self.has_red_in_scan_area(
            frame
        )

    # ==================================================
    # Tracked Object Processing
    # ==================================================

    def _process_tracked_objects(
        self,
        frame,
        original_frame,
        objects,
        red_detected,
        current_time,
    ):

        if objects is None:
            objects = {}

        objects_inside = set()

        for object_id, obj in list(
            objects.items()
        ):

            if obj is None:
                continue

            object_box = (
                self._get_object_box(obj)
            )

            center_inside = (
                self.object_center_inside_counting_box(
                    object_box
                )
            )

            if center_inside:
                objects_inside.add(
                    object_id
                )

            object_entered = (
                center_inside
                and object_id
                not in self.counting_object_ids
            )

            self._draw_tracked_object(
                frame=frame,
                object_id=object_id,
                obj=obj,
            )

            self._handle_object_capture_or_count(
                original_frame=original_frame,
                objects=objects,
                object_id=object_id,
                obj=obj,
                center_inside=center_inside,
                object_entered=object_entered,
                red_detected=red_detected,
                current_time=current_time,
            )

        return objects_inside

    def _get_object_box(
        self,
        obj,
    ):

        return [
            obj["x"],
            obj["y"],
            obj["x"] + obj["w"],
            obj["y"] + obj["h"],
        ]

    def _draw_tracked_object(
        self,
        frame,
        object_id,
        obj,
    ):

        x = obj["x"]
        y = obj["y"]
        w = obj["w"]
        h = obj["h"]

        cv2.rectangle(
            frame,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2,
        )

        center_x = x + (
            w // 2
        )

        center_y = y + (
            h // 2
        )

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
                max(
                    y - 25,
                    20,
                ),
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )

        label = (
            f"Frames: {obj['frames']}"
            if obj["frames"] >= MIN_FRAMES
            else "Tracking"
        )

        cv2.putText(
            frame,
            label,
            (
                x,
                max(
                    y - 5,
                    40,
                ),
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 0),
            1,
        )

    # ==================================================
    # Automatic Capture / Continuous Counting
    # ==================================================

    def _handle_object_capture_or_count(
        self,
        original_frame,
        objects,
        object_id,
        obj,
        center_inside,
        object_entered,
        red_detected,
        current_time,
    ):

        if self.trigger_mode == TRIGGER_AUTOMATIC:

            self._handle_automatic_capture(
                original_frame=original_frame,
                objects=objects,
                object_id=object_id,
                obj=obj,
                center_inside=center_inside,
                object_entered=object_entered,
                red_detected=red_detected,
                current_time=current_time,
            )

            return

        if (
            self.trigger_mode
            == TRIGGER_CONTINUOUS
        ):

            self._handle_continuous_counting(
                original_frame=original_frame,
                objects=objects,
                object_id=object_id,
                obj=obj,
                center_inside=center_inside,
                object_entered=object_entered,
            )

    def _should_automatic_capture(
        self,
        object_id,
        obj,
        center_inside,
        object_entered,
        red_detected,
        current_time,
    ):

        time_since_capture = (
            current_time
            - self.last_capture_time
        )

        reason = None

        if not object_entered:
            reason = (
                "object has not entered counting box"
            )

        elif not center_inside:
            reason = (
                "object center outside counting box"
            )

        elif (
            self.require_red_for_automatic
            and not red_detected
        ):
            reason = (
                "red scan not detected"
            )

        elif object_id in self.processed_object_ids:
            reason = (
                "object already processed"
            )

        elif (
            time_since_capture
            < CAPTURE_INTERVAL
        ):
            reason = (
                f"capture interval not elapsed "
                f"({time_since_capture:.2f}s/"
                f"{CAPTURE_INTERVAL}s)"
            )

        previous_reason = getattr(
            self,
            "_auto_debug_reasons",
            {},
        ).get(object_id)

        if reason:

            if (
                DEBUG_AUTO_CAPTURE
                and previous_reason != reason
            ):
                print(
                    f"[AUTO DEBUG] ID={object_id}: "
                    f"REJECT - {reason}"
                )

            if not hasattr(
                self,
                "_auto_debug_reasons",
            ):
                self._auto_debug_reasons = {}

            self._auto_debug_reasons[
                object_id
            ] = reason

            return False

        if not hasattr(
            self,
            "_auto_debug_reasons",
        ):
            self._auto_debug_reasons = {}

        if (
            DEBUG_AUTO_CAPTURE
            and previous_reason != "READY"
        ):
            print(
                f"[AUTO DEBUG] ID={object_id}: "
                f"READY - all automatic capture "
                f"conditions passed"
            )

        self._auto_debug_reasons[
            object_id
        ] = "READY"

        return True

    def _handle_automatic_capture(
        self,
        original_frame,
        objects,
        object_id,
        obj,
        center_inside,
        object_entered,
        red_detected,
        current_time,
    ):

        if not self._should_automatic_capture(
            object_id=object_id,
            obj=obj,
            center_inside=center_inside,
            object_entered=object_entered,
            red_detected=red_detected,
            current_time=current_time,
        ):
            return

        if DEBUG_AUTO_CAPTURE:
            print(
                f"[AUTO DEBUG] "
                f"CAPTURE TRIGGERED for ID={object_id}"
            )

        if self.metadata_sync_callback:

            if DEBUG_AUTO_CAPTURE:
                print(
                    f"[AUTO DEBUG] "
                    f"Running metadata sync "
                    f"for ID={object_id}"
                )

            self.metadata_sync_callback()

        saved_filename = (
            self.capture_counting_area(
                original_frame,
                objects,
                object_id,
            )
        )

        if not saved_filename:

            if DEBUG_AUTO_CAPTURE:
                print(
                    f"[AUTO DEBUG] "
                    f"CAPTURE FAILED for ID={object_id}: "
                    f"capture_counting_area() "
                    f"returned None."
                )

            return

        if DEBUG_AUTO_CAPTURE:
            print(
                f"[AUTO DEBUG] "
                f"CAPTURE SUCCESS for ID={object_id}: "
                f"{saved_filename}"
            )

        self.processed_object_ids.add(
            object_id
        )

        obj["captured"] = True

    def _handle_continuous_counting(
        self,
        original_frame,
        objects,
        object_id,
        obj,
        center_inside,
        object_entered,
    ):

        if not object_entered:
            return

        if obj["frames"] < MIN_FRAMES:
            return

        if not center_inside:
            return

        if (
            object_id
            in self.processed_object_ids
        ):
            return

        if self.metadata_sync_callback:
            self.metadata_sync_callback()

        saved_filename = (
            self.capture_counting_area(
                original_frame,
                objects,
                object_id,
            )
        )

        if not saved_filename:
            return

        self.processed_object_ids.add(
            object_id
        )

        self.continuous_count += 1

        obj["captured"] = True

    # ==================================================
    # Manual Capture
    # ==================================================

    def _handle_manual_capture(
        self,
        original_frame,
        objects,
    ):

        if not self.manual_trigger_requested:
            return

        self.manual_trigger_requested = False

        manual_objects = (
            self._get_manual_capture_objects(
                objects
            )
        )

        if (
            manual_objects
            or not self.show_counting_box
        ):

            self._capture_manual_objects(
                original_frame=original_frame,
                manual_objects=manual_objects,
            )

    def _get_manual_capture_objects(
        self,
        objects,
    ):

        if not self.show_counting_box:
            return objects

        manual_objects = {}

        for object_id, obj in list(
            objects.items()
        ):

            if obj["frames"] < MIN_FRAMES:
                continue

            object_box = (
                self._get_object_box(obj)
            )

            if self.object_center_inside_counting_box(
                object_box
            ):

                manual_objects[
                    object_id
                ] = obj

        return manual_objects

    def _capture_manual_objects(
        self,
        original_frame,
        manual_objects,
    ):

        if self.metadata_sync_callback:
            self.metadata_sync_callback()

        saved_filename = (
            self.capture_counting_area(
                original_frame,
                manual_objects,
            )
        )

        if not saved_filename:
            return

        for obj in manual_objects.values():
            obj["captured"] = True

    # ==================================================
    # Counting State
    # ==================================================

    def _update_counting_state(
        self,
        objects_inside,
    ):

        objects_that_left = (
            self.counting_object_ids
            - objects_inside
        )

        self.processed_object_ids.difference_update(
            objects_that_left
        )

        self.counting_object_ids = (
            objects_inside
        )

    # ==================================================
    # Frame Overlay
    # ==================================================

    def _draw_frame_overlay(
        self,
        frame,
        detection_count,
    ):

        self._draw_detection_count(
            frame,
            detection_count,
        )

        self._draw_scan_box(frame)
        self._draw_crop_box(frame)
        self._draw_counting_box(frame)

    def _draw_detection_count(
        self,
        frame,
        detection_count,
    ):

        cv2.putText(
            frame,
            f"Objects: {detection_count}",
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2,
        )

        if (
            self.trigger_mode
            == TRIGGER_CONTINUOUS
        ):

            cv2.putText(
                frame,
                f"Count: {self.continuous_count}",
                (20, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2,
            )

    def _draw_scan_box(
        self,
        frame,
    ):

        if self.scan_box is None:
            return

        x1, y1, x2, y2 = (
            self.scan_box
        )

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (255, 0, 255),
            2,
        )

        cv2.putText(
            frame,
            "Scan Dot",
            (
                x1 - 10,
                max(
                    y1 - 10,
                    20,
                ),
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 0, 255),
            2,
        )

    def _draw_crop_box(
        self,
        frame,
    ):

        if (
            self.crop_box is None
            or not self.show_crop_box
        ):
            return

        x1, y1, x2, y2 = (
            self.crop_box
        )

        color_crop = (
            0,
            255,
            255,
        )

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            color_crop,
            2,
        )

        cv2.putText(
            frame,
            "Preview Crop",
            (
                x1 - 10,
                max(
                    y1 - 10,
                    20,
                ),
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color_crop,
            2,
        )

    def _draw_counting_box(
        self,
        frame,
    ):

        if (
            self.counting_box is None
            or not self.show_counting_box
        ):
            return

        x1, y1, x2, y2 = (
            self.counting_box
        )

        color_count = (
            255,
            255,
            0,
        )

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            color_count,
            2,
        )

        cv2.putText(
            frame,
            "Counting Box",
            (
                x1 - 10,
                max(
                    y1 - 10,
                    20,
                ),
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color_count,
            2,
        )

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

        (
            obj_x1,
            obj_y1,
            obj_x2,
            obj_y2,
        ) = box

        (
            crop_x1,
            crop_y1,
            crop_x2,
            crop_y2,
        ) = self.crop_box

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
            intersection_x2
            <= intersection_x1
            or intersection_y2
            <= intersection_y1
        ):
            return False

        intersection_area = (
            intersection_x2
            - intersection_x1
        ) * (
            intersection_y2
            - intersection_y1
        )

        object_area = (
            obj_x2
            - obj_x1
        ) * (
            obj_y2
            - obj_y1
        )

        if object_area <= 0:
            return False

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
            x1:x2,
        ]

        hsv = cv2.cvtColor(
            scan_area,
            cv2.COLOR_BGR2HSV,
        )

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

        red_pixels = cv2.countNonZero(
            red_mask
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