<div align="center">

# Face Recognition Edge

**Real-time face detection pipeline running at the edge**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-FF6F00?style=flat)](https://ultralytics.com)
[![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3.13-FF6600?style=flat&logo=rabbitmq&logoColor=white)](https://rabbitmq.com)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat&logo=docker&logoColor=white)](https://docker.com)

A lightweight edge service that reads video streams from RTSP cameras or webcams,
detects faces using YOLOv8, and publishes detection events to RabbitMQ in real time —
designed to run close to the camera with minimal latency.

</div>

---

## Overview

This service sits at the **edge layer** of a computer vision pipeline. Instead of sending raw video to a central server, it processes frames locally and only forwards structured detection events — reducing bandwidth and enabling near-instant response times.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Edge Device                              │
│                                                                 │
│   RTSP / Webcam                                                 │
│        │                                                        │
│        ▼                                                        │
│  ┌─────────────┐    ┌──────────────────┐    ┌───────────────┐  │
│  │   Stream    │───▶│    Detection     │───▶│     Queue     │  │
│  │   Service   │    │    Service       │    │    Service    │  │
│  │  (OpenCV)   │    │   (YOLOv8)      │    │   (aio-pika)  │  │
│  └─────────────┘    └──────────────────┘    └───────┬───────┘  │
│                                                     │          │
└─────────────────────────────────────────────────────┼──────────┘
                                                      │
                                                      ▼
                                              ┌───────────────┐
                                              │   RabbitMQ    │
                                              │  (Backend)    │
                                              └───────────────┘
```

---

## Features

- **Real-time detection** — async pipeline processes frames continuously with configurable FPS cap
- **RTSP & webcam support** — works with IP cameras over RTSP or any local webcam (index-based)
- **YOLOv8 inference** — runs on CPU or GPU, swappable to any `.pt` model including face-specific variants
- **Event-driven output** — publishes structured JSON payloads to RabbitMQ topic exchange, persistent delivery
- **FastAPI lifecycle** — pipeline starts/stops cleanly with the server via `lifespan` context manager
- **Health & status API** — `/health` and `/status` endpoints for monitoring and orchestration
- **Docker ready** — single `docker compose up --build` for containerized deployment

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI + Uvicorn |
| Computer Vision | OpenCV + Ultralytics YOLOv8 |
| Message Queue | RabbitMQ via aio-pika (async) |
| Config | pydantic-settings (`.env` based) |
| Container | Docker + Docker Compose |

---

## Getting Started

### Prerequisites

- Python 3.11+
- A webcam **or** an RTSP stream URL
- RabbitMQ instance (local or remote)

### Run locally

```bash
# 1. Clone the repo
git clone https://github.com/Putthakun/face-recognition-edge.git
cd face-recognition-edge

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env to set your stream source and RabbitMQ URL

# 5. Start the service
uvicorn app.main:app --reload
```

The service will auto-download the YOLO model on first run.

### Run with Docker

```bash
cp .env.example .env
# Edit .env as needed

docker compose up --build
```

> **Note:** Webcam passthrough in Docker requires a Linux host (`/dev/video0`). On macOS, use an RTSP stream instead. See [`mock/README.md`](mock/README.md) for local RTSP setup.

---

## Configuration

All configuration is managed via environment variables. Copy `.env.example` to `.env` and adjust:

| Variable | Default | Description |
|---|---|---|
| `STREAM_SOURCE` | `0` | Webcam index (`0`, `1`, ...) or RTSP URL |
| `STREAM_FPS_LIMIT` | `10` | Max frames per second to process |
| `YOLO_MODEL_PATH` | `yolov8n.pt` | Path to YOLO model file |
| `DETECTION_CONFIDENCE` | `0.5` | Minimum confidence threshold (0.0–1.0) |
| `RABBITMQ_URL` | `amqp://guest:guest@localhost:5672/` | RabbitMQ connection URL |
| `RABBITMQ_EXCHANGE` | `face_events` | Exchange name |
| `RABBITMQ_ROUTING_KEY` | `face.detected` | Routing key for published messages |
| `DEBUG` | `false` | Enable debug logging |

### Using a face-specific model

Swap `yolov8n.pt` for a face detection model (e.g. from the [`akanametov/yolo-face`](https://github.com/akanametov/yolo-face) community repo):

```env
YOLO_MODEL_PATH=yolov8n-face.pt
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check — returns `{"status": "ok"}` |
| `GET` | `/status` | Pipeline status, stream source, model info |
| `GET` | `/docs` | Auto-generated Swagger UI |

---

## Event Payload

Each detection publishes a JSON message to RabbitMQ:

```json
{
  "frame_id": 1042,
  "timestamp": "2026-05-28T15:04:05.123Z",
  "face_count": 2,
  "detections": [
    {
      "bbox": [120, 80, 240, 200],
      "confidence": 0.9312
    },
    {
      "bbox": [310, 95, 420, 205],
      "confidence": 0.8754
    }
  ]
}
```

---

## Project Structure

```
face-recognition-edge/
├── app/
│   ├── main.py                  # FastAPI app + lifespan pipeline
│   ├── core/
│   │   └── config.py            # pydantic-settings config
│   └── services/
│       ├── stream_service.py    # RTSP/webcam frame generator
│       ├── detection_service.py # YOLOv8 inference
│       └── queue_service.py     # RabbitMQ publisher
├── mock/
│   └── README.md                # Local RTSP stream setup guide
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Roadmap

- [ ] Face recognition (embedding + identity matching)
- [ ] Frame snapshot storage (S3 / Blob)
- [ ] Prometheus metrics endpoint
- [ ] GPU acceleration support (CUDA)
- [ ] Multi-camera support

---

## License

MIT
