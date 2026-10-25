import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = BASE_DIR / "static"


def _load_env(path: Path) -> None:
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key:
            os.environ.setdefault(key, value.strip().strip("'\""))


_load_env(BASE_DIR / ".env")

_SQLITE_URL = f"sqlite:///{(BASE_DIR / 'database' / 'milktea.db').as_posix()}"


class Settings:
    secret_key: str = os.getenv("APP_SECRET", "simaotea-demo-secret-change-me")
    base_url: str = os.getenv("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    database_url: str = os.getenv("DATABASE_URL", _SQLITE_URL)
    wechat_appid: str = os.getenv("WECHAT_APPID", "").strip()
    wechat_secret: str = os.getenv("WECHAT_SECRET", "").strip()
    sql_echo: bool = os.getenv("SQL_ECHO", "").strip().lower() in {"1", "true", "yes", "on"}
    access_token_ttl: int = 7 * 24 * 3600
    refresh_token_ttl: int = 30 * 24 * 3600
    idempotency_ttl: int = 600
    max_avatar_bytes: int = 2 * 1024 * 1024

    @property
    def wechat_login_enabled(self) -> bool:
        return bool(self.wechat_appid and self.wechat_secret)

    @property
    def image_url(self) -> str:
        return f"{self.base_url}/static/images"

    @property
    def avatar_dir(self) -> Path:
        return STATIC_DIR / "avatars"


settings = Settings()
