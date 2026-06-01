import asyncio
import logging

import cv2
import numpy as np
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.services.stream_service import StreamService
from app.services.detection_service import DetectionService, Detection
from app.services.queue_service import QueueService

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

stream_svc = StreamService()
detection_svc = DetectionService()
queue_svc = QueueService()

_pipeline_task: asyncio.Task | None = None
_latest_frame: np.ndarray | None = None


def _draw_detections(frame: np.ndarray, detections: list[Detection]) -> np.ndarray:
    annotated = frame.copy()
    for d in detections:
        cv2.rectangle(annotated, (d.x1, d.y1), (d.x2, d.y2), (0, 255, 0), 2)
        label = f"{d.confidence:.2f}"
        cv2.putText(annotated, label, (d.x1, d.y1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 1)
    return annotated


async def _run_pipeline() -> None:
    global _latest_frame
    frame_id = 0
    async for frame in stream_svc.frames():
        detections = detection_svc.detect(frame)
        _latest_frame = _draw_detections(frame, detections)
        if detections:
            await queue_svc.publish(detections, frame_id)
        frame_id += 1


async def _mjpeg_generator():
    while True:
        if _latest_frame is not None:
            _, jpeg = cv2.imencode(".jpg", _latest_frame)
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + jpeg.tobytes()
                + b"\r\n"
            )
        await asyncio.sleep(1 / 30)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _pipeline_task

    detection_svc.load()
    stream_svc.open()
    await queue_svc.connect()

    _pipeline_task = asyncio.create_task(_run_pipeline())
    logger.info("Pipeline started")

    yield

    _pipeline_task.cancel()
    try:
        await _pipeline_task
    except asyncio.CancelledError:
        pass

    stream_svc.release()
    await queue_svc.close()
    logger.info("Pipeline stopped")


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.app_name}


@app.get("/status")
async def status():
    return {
        "pipeline_running": _pipeline_task is not None and not _pipeline_task.done(),
        "stream_source": settings.stream_source,
        "yolo_model": settings.yolo_model_path,
        "rabbitmq_exchange": settings.rabbitmq_exchange,
    }


@app.get("/stream")
async def stream():
    return StreamingResponse(
        _mjpeg_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
