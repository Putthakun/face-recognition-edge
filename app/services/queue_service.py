import json
import logging
from datetime import datetime, timezone

import aio_pika
from aio_pika import ExchangeType

from app.core.config import settings
from app.services.detection_service import Detection

logger = logging.getLogger(__name__)


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

    async def publish(self, detections: list[Detection], frame_id: int) -> None:
        if not self._exchange:
            raise RuntimeError("Not connected. Call connect() first.")

        payload = {
            "frame_id": frame_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "face_count": len(detections),
            "detections": [
                {
                    "bbox": [d.x1, d.y1, d.x2, d.y2],
                    "confidence": round(d.confidence, 4),
                }
                for d in detections
            ],
        }

        message = aio_pika.Message(
            body=json.dumps(payload).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )

        await self._exchange.publish(message, routing_key=settings.rabbitmq_routing_key)
        logger.debug("Published frame_id=%d faces=%d", frame_id, len(detections))
