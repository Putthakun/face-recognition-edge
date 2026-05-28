import logging
from dataclasses import dataclass

import numpy as np
from ultralytics import YOLO

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class Detection:
    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float


class DetectionService:
    def __init__(self):
        self._model: YOLO | None = None

    def load(self) -> None:
        self._model = YOLO(settings.yolo_model_path)
        logger.info("YOLO model loaded: %s", settings.yolo_model_path)

    def detect(self, frame: np.ndarray) -> list[Detection]:
        if not self._model:
            raise RuntimeError("Model not loaded. Call load() first.")

        # classes=0 → person (yolov8n.pt); face-specific models ignore this filter
        is_face_model = "face" in settings.yolo_model_path
        cls_filter = None if is_face_model else [0]

        results = self._model(frame, conf=settings.detection_confidence, classes=cls_filter, verbose=False)
        detections: list[Detection] = []

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = float(box.conf[0])
                detections.append(Detection(x1=x1, y1=y1, x2=x2, y2=y2, confidence=conf))

        return detections
