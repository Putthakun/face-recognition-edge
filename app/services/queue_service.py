import base64
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import aio_pika
import cv2
import numpy as np
from aio_pika import ExchangeType

from app.core.config import settings
from app.services.detection_service import Detection

logger = logging.getLogger(__name__)

DEBUG_FACE_DIR = Path("debug_faces")


class QueueService:
    def __init__(self):
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._exchange: aio_pika.abc.AbstractExchange | None = None

    async def connect(self) -> None:
        self._connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        self._channel = await self._connection.channel()
        self._exchange = await self._channel.declare_exchange(
            settings.rabbitmq_exchange,
            ExchangeType.TOPIC,
            durable=True,
        )
        logger.info("Connected to RabbitMQ: %s", settings.rabbitmq_url)

    async def close(self) -> None:
        if self._connection:
            await self._connection.close()
            logger.info("RabbitMQ connection closed")

    async def publish(self, face_image: np.ndarray, detection: Detection) -> None:
        if not self._exchange:
            raise RuntimeError("Not connected. Call connect() first.")

        _, jpeg = cv2.imencode(".jpg", face_image)
        jpeg_bytes = jpeg.tobytes()
        image_base64 = base64.b64encode(jpeg_bytes).decode("ascii")

        if settings.debug:
            DEBUG_FACE_DIR.mkdir(exist_ok=True)
            filename = DEBUG_FACE_DIR / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%f')}.jpg"
            filename.write_bytes(jpeg_bytes)
            logger.debug("Saved debug face image: %s", filename)

        payload = {
            "camera_id": settings.camera_id,          # int e.g. 1
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "image_base64": image_base64,
            "confidence": round(detection.confidence, 4),
            "bbox": [detection.x1, detection.y1, detection.x2, detection.y2],
        }

        message = aio_pika.Message(
            body=json.dumps(payload).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )

        await self._exchange.publish(message, routing_key=settings.rabbitmq_routing_key)
        logger.debug("Published face image (camera_id=%s)", settings.camera_id)
