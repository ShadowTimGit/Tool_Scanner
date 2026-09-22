from ultralytics import YOLO


class ToolDetector:
    def __init__(self, model_path, confidence=0.50):
        self.model = YOLO(model_path)
        self.confidence = confidence

    def detect(self, frame):
        """
        Run object detection on a single frame.

        Returns:
            list of dictionaries containing:
                - box
                - track_id
                - confidence
                - class_id
                - class_name
        """

        results = self.model.track(
            frame,
            persist=True,
            conf=self.confidence,
            tracker="bytetrack.yaml",
            verbose=False,
        )

        result = results[0]

        if result.boxes is None:
            return []

        boxes = result.boxes.xyxy.cpu().numpy()
        confidences = result.boxes.conf.cpu().numpy()
        class_ids = result.boxes.cls.cpu().numpy().astype(int)

        if result.boxes.id is not None:
            track_ids = result.boxes.id.cpu().numpy().astype(int)
        else:
            track_ids = [None] * len(boxes)

        detections = []

        for box, track_id, confidence, class_id in zip(
            boxes,
            track_ids,
            confidences,
            class_ids,
        ):
            detections.append(
                {
                    "box": tuple(map(int, box)),
                    "track_id": track_id,
                    "confidence": float(confidence),
                    "class_id": int(class_id),
                    "class_name": self.model.names[class_id],
                }
            )

        return detections