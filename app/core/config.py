from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Stream
    stream_source: str = "0"  # "0" = webcam, or rtsp://...
    stream_fps_limit: int = 10

    # Detection
    yolo_model_path: str = "yolov8n.pt"
    detection_confidence: float = 0.5

    # RabbitMQ
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    rabbitmq_exchange: str = "face_events"
    rabbitmq_routing_key: str = "face.detected"

    # App
    app_name: str = "face-recognition-edge"
    debug: bool = False


settings = Settings()
