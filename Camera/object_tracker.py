import os

import torch
from ultralytics import YOLO

from settings_menu.config import MODEL

# ==================================================
# Detection Settings
# ==================================================

MIN_FRAMES = 10

MIN_WIDTH = 30
MIN_HEIGHT = 30
MIN_AREA = 1000

CONFIDENCE = 0.40

TRACKER_CONFIG = "Camera/bytetrack_tools.yaml"

MAX_MISSED_FRAMES = 6


def get_model_device():
    requested = os.getenv(
        "TOOL_SCANNER_DEVICE",
        "",
    ).strip().lower()

    if requested:
        if requested in {"cpu", "cuda", "mps"}:
            return requested

        return (
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

    if torch.cuda.is_available():
        return "cuda"

    if (
        hasattr(torch.backends, "mps")
        and torch.backends.mps.is_available()
    ):
        return "mps"

    return "cpu"


class ObjectTracker:

    def __init__(self):

        # -------------------------
        # YOLO model
        # -------------------------

        self.device = get_model_device()

        print(
            f"[ToolScanner] YOLO device: "
            f"{self.device}"
        )

        print(
            f"[ToolScanner] YOLO model: "
            f"{MODEL}"
        )

        self.model = YOLO(MODEL)
        self.model.to(self.device)

        # -------------------------
        # Tracked objects
        # -------------------------

        self.objects = {}


    # ==================================================
    # Detect + Track Objects
    # ==================================================

    def detect(
        self,
        frame,
    ):

        results = self.model.track(
            frame,
            conf=CONFIDENCE,
            tracker=TRACKER_CONFIG,
            persist=True,
            verbose=False,
            device=self.device,
        )
        
        detections = []

        model_names = self.model.names

        for result in results:

            if result.boxes is None:
                continue

            boxes = result.boxes

            for index, box in enumerate(boxes):

                # -------------------------
                # Bounding box
                # -------------------------

                x1, y1, x2, y2 = (
                    box.xyxy[0]
                    .cpu()
                    .numpy()
                    .astype(int)
                )

                x = int(x1)
                y = int(y1)

                w = int(x2 - x1)
                h = int(y2 - y1)

                area = w * h

                # -------------------------
                # Size filtering
                # -------------------------

                if w < MIN_WIDTH:
                    continue

                if h < MIN_HEIGHT:
                    continue

                if area < MIN_AREA:
                    continue

                center_x = x + w // 2
                center_y = y + h // 2

                # -------------------------
                # Confidence
                # -------------------------

                confidence = float(
                    box.conf[0]
                    .cpu()
                    .item()
                )

                # -------------------------
                # Class
                # -------------------------

                class_id = int(
                    box.cls[0]
                    .cpu()
                    .item()
                )

                class_name = model_names[
                    class_id
                ]

                # -------------------------
                # YOLO / ByteTrack ID
                # -------------------------

                if boxes.id is not None:

                    object_id = int(
                        boxes.id[index]
                        .cpu()
                        .item()
                    )

                else:

                    object_id = None

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

        # -------------------------
        # Update persistent tracker
        # -------------------------

        return detections

    # ==================================================
    # Update Objects
    # ==================================================

    def update(self, detections):
        visible_ids = set()

        for detection in detections:
            object_id = detection["id"]

            if object_id is None:
                continue

            visible_ids.add(object_id)

            if object_id in self.objects:
                obj = self.objects[object_id]

                obj["x"] = detection["x"]
                obj["y"] = detection["y"]
                obj["w"] = detection["w"]
                obj["h"] = detection["h"]

                obj["center_x"] = (
                    detection["center_x"]
                )

                obj["center_y"] = (
                    detection["center_y"]
                )

                obj["frames"] += 1
                obj["missed_frames"] = 0

                current_area = (
                    detection["w"]
                    * detection["h"]
                )

                best_area = (
                    obj["best_w"]
                    * obj["best_h"]
                )

                if current_area > best_area:
                    obj["best_x"] = detection["x"]
                    obj["best_y"] = detection["y"]
                    obj["best_w"] = detection["w"]
                    obj["best_h"] = detection["h"]

            else:
                self.objects[object_id] = {
                    "id": object_id,
                    "x": detection["x"],
                    "y": detection["y"],
                    "w": detection["w"],
                    "h": detection["h"],
                    "center_x": detection["center_x"],
                    "center_y": detection["center_y"],
                    "frames": 1,
                    "missed_frames": 0,
                    "captured": False,
                    "best_x": detection["x"],
                    "best_y": detection["y"],
                    "best_w": detection["w"],
                    "best_h": detection["h"],
                    "class_name": detection.get("class_name"),
                    "class_id": detection.get("class_id"),
                    "confidence": detection.get("confidence", 0),
                }

        # Only increment missed_frames when YOLO actually ran.
        for object_id in list(self.objects.keys()):

            if object_id in visible_ids:
                continue

            self.objects[object_id]["missed_frames"] += 1

            if (
                self.objects[object_id]["missed_frames"]
                > MAX_MISSED_FRAMES
            ):
                del self.objects[object_id]

        return self.objects

    def get_visible_objects(self):

        visible_objects = []

        for object_id, obj in self.objects.items():

            # -------------------------
            # Copy object so the
            # persistent state is not
            # accidentally modified
            # by the drawing code.
            # -------------------------

            visible_object = dict(obj)

            # -------------------------
            # If ByteTrack missed the
            # object, retain its last
            # known bounding box.
            # -------------------------

            if obj["missed_frames"] > 0:

                visible_object["x"] = obj[
                    "x"
                ]

                visible_object["y"] = obj[
                    "y"
                ]

                visible_object["w"] = obj[
                    "w"
                ]

                visible_object["h"] = obj[
                    "h"
                ]

                visible_object["center_x"] = (
                    obj["center_x"]
                )

                visible_object["center_y"] = (
                    obj["center_y"]
                )

            visible_objects.append(
                visible_object
            )

        return visible_objects


    # ==================================================
    # Reset
    # ==================================================

    def reset(self):

        self.objects = {}

        # -------------------------
        # Reset YOLO / ByteTrack
        # -------------------------

        self.model = YOLO(MODEL)

        self.model.to(
            self.device
        )