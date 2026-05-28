import asyncio
import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.config import settings
from app.services.stream_service import StreamService
from app.services.detection_service import DetectionService
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


async def _run_pipeline() -> None:
    frame_id = 0
    async for frame in stream_svc.frames():
        detections = detection_svc.detect(frame)
        if detections:
            await queue_svc.publish(detections, frame_id)
        frame_id += 1


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
