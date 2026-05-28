# face-recognition-edge

Edge service สำหรับตรวจจับใบหน้าแบบ real-time จาก RTSP/webcam ด้วย YOLOv8 แล้ว publish event ไป RabbitMQ

## Architecture

```
RTSP / Webcam → StreamService → DetectionService (YOLOv8) → QueueService → RabbitMQ
```

FastAPI ทำหน้าที่เป็น host สำหรับ health/status endpoint และ lifecycle management (lifespan)

## Quick Start

```bash
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Docker

```bash
docker compose up --build
```

RabbitMQ Management UI: http://localhost:15672 (guest/guest)

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/status` | Pipeline status |

## Config (.env)

| Key | Default | Description |
|-----|---------|-------------|
| `STREAM_SOURCE` | `0` | Webcam index หรือ RTSP URL |
| `STREAM_FPS_LIMIT` | `10` | FPS สูงสุดที่ process |
| `YOLO_MODEL_PATH` | `yolov8n-face.pt` | Path ของ model |
| `DETECTION_CONFIDENCE` | `0.5` | Confidence threshold |
| `RABBITMQ_URL` | `amqp://guest:guest@localhost:5672/` | RabbitMQ connection |
| `RABBITMQ_EXCHANGE` | `face_events` | Exchange name |
| `RABBITMQ_ROUTING_KEY` | `face.detected` | Routing key |
