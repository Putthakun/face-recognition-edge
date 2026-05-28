import cv2
import asyncio
import logging
from typing import AsyncGenerator
import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)


class StreamService:
    def __init__(self):
        self._cap: cv2.VideoCapture | None = None

    def open(self) -> None:
        source = settings.stream_source
        # Convert "0" string to int for webcam
        src = int(source) if source.isdigit() else source
        self._cap = cv2.VideoCapture(src)
        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open stream: {source}")
        logger.info("Stream opened: %s", source)

    def release(self) -> None:
        if self._cap:
            self._cap.release()
            self._cap = None
            logger.info("Stream released")

    async def frames(self) -> AsyncGenerator[np.ndarray, None]:
        if not self._cap:
            raise RuntimeError("Stream not opened. Call open() first.")

        interval = 1.0 / settings.stream_fps_limit

        while True:
            ret, frame = self._cap.read()
            if not ret:
                logger.warning("Failed to read frame, retrying...")
                await asyncio.sleep(1.0)
                continue

            yield frame
            await asyncio.sleep(interval)
