import os
from typing import Any

import torch
from ultralytics import YOLO

from settings_menu.config import MODEL


# ==================================================
# Detection Settings
# ==================================================

MIN_FRAMES = 7

MIN_WIDTH = 30
MIN_HEIGHT = 30
MIN_AREA = 1000

CONFIDENCE = 0.35

TRACKER_CONFIG = "Camera/bytetrack_tools.yaml"

MAX_MISSED_FRAMES = 6


# ==================================================
# Device
# ==================================================

def get_model_device() -> str:
    """
    Determine the best available inference device.

    TOOL_SCANNER_DEVICE can be used to explicitly request:
        cpu
        cuda
        mps
    """

    requested = os.getenv(
        "TOOL_SCANNER_DEVICE",
        "",
    ).strip().lower()

    if requested:
        if requested in {"cpu", "cuda", "mps"}:
            # Fall back if the explicitly requested accelerator
            # is not actually available.
            if requested == "cuda":
                return (
                    "cuda"
                    if torch.cuda.is_available()
                    else "cpu"
                )

            if requested == "mps":
                if (
                    hasattr(torch.backends, "mps")
                    and torch.backends.mps.is_available()
                ):
                    return "mps"

                return "cpu"

            return "cpu"

        print(
            f"[ToolScanner] Invalid device "
            f"'{requested}', using automatic selection."
        )

    if torch.cuda.is_available():
        return "cuda"

    if (
        hasattr(torch.backends, "mps")
        and torch.backends.mps.is_available()
    ):
        return "mps"

    return "cpu"


# ==================================================
# Object Tracker
# ==================================================

class ObjectTracker:

    def __init__(self) -> None:

        # -------------------------
        # Device
        # -------------------------

        self.tracker_settings = {
            "track_high_thresh": 0.60,
            "track_low_thresh": 0.10,
            "new_track_thresh": 0.50,
            "track_buffer": 50,
            "match_thresh": 0.65,
            "fuse_score": True,
        }

        self.device = get_model_device()

        print(
            f"[ToolScanner] YOLO device: "
            f"{self.device}"
        )

        print(
            f"[ToolScanner] YOLO model: "
            f"{MODEL}"
        )

        # -------------------------
        # YOLO model
        # -------------------------

        self.model = YOLO(MODEL)

        self.model.to(
            self.device
        )

        # -------------------------
        # Model class names
        # -------------------------

        self.model_names = self.model.names

        # -------------------------
        # Tracked objects
        # -------------------------

        self.objects: dict[int, dict[str, Any]] = {}

    # ==================================================
    # Runtime Tracker Settings
    # ==================================================

    def set_tracker_setting(
        self,
        name: str,
        value,
    ) -> None:

        if name not in self.tracker_settings:
            return

        self.tracker_settings[name] = value

        # Apply to the currently active ByteTrack instance.
        predictor = getattr(
            self.model,
            "predictor",
            None,
        )

        if predictor is None:
            return

        trackers = getattr(
            predictor,
            "trackers",
            None,
        )

        if not trackers:
            return

        for tracker in trackers:

            args = getattr(
                tracker,
                "args",
                None,
            )

            if args is not None:
                setattr(
                    args,
                    name,
                    value,
                )

            # ByteTrack caches track_buffer separately.
            if name == "track_buffer":
                tracker.max_time_lost = int(value)


    def _apply_tracker_settings(self) -> None:

        predictor = getattr(
            self.model,
            "predictor",
            None,
        )

        if predictor is None:
            return

        trackers = getattr(
            predictor,
            "trackers",
            None,
        )

        if not trackers:
            return

        for tracker in trackers:

            args = getattr(
                tracker,
                "args",
                None,
            )

            if args is not None:
                for name, value in self.tracker_settings.items():
                    setattr(
                        args,
                        name,
                        value,
                    )

            if hasattr(
                tracker,
                "max_time_lost",
            ):
                tracker.max_time_lost = int(
                    self.tracker_settings[
                        "track_buffer"
                    ]
                )

    # ==================================================
    # Detect + Track Objects
    # ==================================================

    def detect(
        self,
        frame,
    ) -> list[dict[str, Any]]:

        if frame is None:
            return []

        results = self.model.track(
            frame,
            conf=CONFIDENCE,
            tracker=TRACKER_CONFIG,
            persist=True,
            verbose=False,
            device=self.device,
        )

        self._apply_tracker_settings()

        detections: list[dict[str, Any]] = []

        for result in results:

            boxes = result.boxes

            if boxes is None or len(boxes) == 0:
                continue

            # -------------------------
            # Extract tensors once
            # -------------------------

            xyxy = (
                boxes.xyxy
                .detach()
                .cpu()
                .numpy()
            )

            confidences = (
                boxes.conf
                .detach()
                .cpu()
                .numpy()
                if boxes.conf is not None
                else None
            )

            class_ids = (
                boxes.cls
                .detach()
                .cpu()
                .numpy()
                if boxes.cls is not None
                else None
            )

            track_ids = None

            if boxes.id is not None:
                track_ids = (
                    boxes.id
                    .detach()
                    .cpu()
                    .numpy()
                )

            # -------------------------
            # Process detections
            # -------------------------

            for index, coordinates in enumerate(xyxy):

                x1, y1, x2, y2 = coordinates

                x1 = int(x1)
                y1 = int(y1)
                x2 = int(x2)
                y2 = int(y2)

                x = x1
                y = y1

                w = x2 - x1
                h = y2 - y1

                # -------------------------
                # Size filtering
                # -------------------------

                if w < MIN_WIDTH:
                    continue

                if h < MIN_HEIGHT:
                    continue

                area = w * h

                if area < MIN_AREA:
                    continue

                # -------------------------
                # Center
                # -------------------------

                center_x = x + w // 2
                center_y = y + h // 2

                # -------------------------
                # Confidence
                # -------------------------

                if confidences is not None:
                    confidence = float(
                        confidences[index]
                    )
                else:
                    confidence = 0.0

                # -------------------------
                # Class
                # -------------------------

                if class_ids is not None:
                    class_id = int(
                        class_ids[index]
                    )
                else:
                    class_id = -1

                if isinstance(
                    self.model_names,
                    dict,
                ):
                    class_name = self.model_names.get(
                        class_id,
                        str(class_id),
                    )
                else:
                    try:
                        class_name = self.model_names[
                            class_id
                        ]
                    except (
                        IndexError,
                        KeyError,
                    ):
                        class_name = str(
                            class_id
                        )

                # -------------------------
                # Tracker ID
                # -------------------------

                object_id = None

                if (
                    track_ids is not None
                    and index < len(track_ids)
                ):
                    object_id = int(
                        track_ids[index]
                    )

                # -------------------------
                # Detection
                # -------------------------

                detections.append(
                    {
                        "id": object_id,
                        "x": x,
                        "y": y,
                        "w": w,
                        "h": h,
                        "center_x": center_x,
                        "center_y": center_y,
                        "confidence": confidence,
                        "class_id": class_id,
                        "class_name": class_name,
                    }
                )

        return detections


    # ==================================================
    # Update Objects
    # ==================================================

    def update(
        self,
        detections: list[dict[str, Any]],
    ) -> dict[int, dict[str, Any]]:

        visible_ids: set[int] = set()

        for detection in detections:

            object_id = detection.get("id")

            # -------------------------
            # Ignore untracked detections
            # -------------------------

            if object_id is None:
                continue

            object_id = int(object_id)

            visible_ids.add(object_id)

            # ==================================================
            # Existing Object
            # ==================================================

            if object_id in self.objects:

                obj = self.objects[
                    object_id
                ]

                # -------------------------
                # Update current detection
                # -------------------------

                obj.update(
                    detection
                )

                obj["frames"] += 1
                obj["missed_frames"] = 0

            # ==================================================
            # New Object
            # ==================================================

            else:

                self.objects[
                    object_id
                ] = {

                    **detection,

                    "frames": 1,

                    "missed_frames": 0,

                    "captured": False,
                }

        # ==================================================
        # Handle Missing Objects
        # ==================================================

        stale_ids = []

        for object_id, obj in self.objects.items():

            if object_id in visible_ids:
                continue

            obj["missed_frames"] += 1

            if (
                obj["missed_frames"]
                > MAX_MISSED_FRAMES
            ):
                stale_ids.append(
                    object_id
                )

        # -------------------------
        # Remove stale objects
        # -------------------------

        for object_id in stale_ids:

            del self.objects[
                object_id
            ]

        return self.objects



    # ==================================================
    # Get Valid Objects
    # ==================================================

    def get_confirmed_objects(
        self,
    ) -> dict[int, dict[str, Any]]:

        """
        Return objects that have been tracked for at
        least MIN_FRAMES frames.
        """

        return {
            object_id: obj
            for object_id, obj in self.objects.items()
            if obj["frames"] >= MIN_FRAMES
        }


    # ==================================================
    # Reset Tracker
    # ==================================================

    def reset(self) -> None:

        # -------------------------
        # Clear tracked objects
        # -------------------------

        self.objects.clear()

        # -------------------------
        # Reset YOLO tracking state
        #
        # Do NOT set predictor.trackers
        # to None. Ultralytics expects
        # this to be initialized before
        # model.track() is called.
        # -------------------------

        try:

            predictor = getattr(
                self.model,
                "predictor",
                None,
            )

            if predictor is None:
                return

            trackers = getattr(
                predictor,
                "trackers",
                None,
            )

            if not trackers:
                return

            for tracker in trackers:

                if hasattr(
                    tracker,
                    "reset",
                ):
                    tracker.reset()

            self._apply_tracker_settings()

        except Exception as error:

            print(
                f"[ToolScanner] Tracker reset error: "
                f"{error}"
            )