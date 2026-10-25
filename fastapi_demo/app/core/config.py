import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = BASE_DIR / "static"


class Settings:
    secret_key: str = os.getenv("APP_SECRET", "simaotea-demo-secret-change-me")
    base_url: str = os.getenv("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    access_token_ttl: int = 7 * 24 * 3600
    refresh_token_ttl: int = 30 * 24 * 3600
    idempotency_ttl: int = 600
    max_avatar_bytes: int = 2 * 1024 * 1024

    @property
    def image_url(self) -> str:
        return f"{self.base_url}/static/images"

    @property
    def avatar_dir(self) -> Path:
        return STATIC_DIR / "avatars"


settings = Settings()
