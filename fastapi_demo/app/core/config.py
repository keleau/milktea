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
_USE_SQLITE = os.getenv("USE_SQLITE", "").strip().lower() in {"1", "true", "yes", "on"}
_ENV_DATABASE_URL = os.getenv("DATABASE_URL", "").strip()


class Settings:
    secret_key: str = os.getenv("APP_SECRET", "simaotea-demo-secret-change-me")
    base_url: str = os.getenv("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    database_url: str = _SQLITE_URL if _USE_SQLITE or not _ENV_DATABASE_URL else _ENV_DATABASE_URL
    wechat_appid: str = os.getenv("WECHAT_APPID", "").strip()
    wechat_secret: str = os.getenv("WECHAT_SECRET", "").strip()
    staff_pin: str = os.getenv("STAFF_PIN", "").strip()
    llm_api_key: str = os.getenv("DEEPSEEK_API_KEY", "").strip() or os.getenv("LLM_API_KEY", "").strip()
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1").strip()
    llm_model: str = os.getenv("LLM_MODEL", "deepseek-chat").strip()
    ai_min_interval_seconds: float = float(os.getenv("AI_MIN_INTERVAL_SECONDS", "2") or 2)
    order_expiry_minutes: int = int(os.getenv("ORDER_EXPIRY_MINUTES", "15") or 15)
    order_expiry_interval_seconds: int = int(os.getenv("ORDER_EXPIRY_INTERVAL_SECONDS", "60") or 60)
    sql_echo: bool = os.getenv("SQL_ECHO", "").strip().lower() in {"1", "true", "yes", "on"}
    access_token_ttl: int = 7 * 24 * 3600
    refresh_token_ttl: int = 30 * 24 * 3600
    idempotency_ttl: int = 600
    max_avatar_bytes: int = 2 * 1024 * 1024

    @property
    def wechat_login_enabled(self) -> bool:
        return bool(self.wechat_appid and self.wechat_secret)

    @property
    def ai_enabled(self) -> bool:
        return bool(self.llm_api_key)

    @property
    def image_url(self) -> str:
        return f"{self.base_url}/static/images"

    @property
    def avatar_dir(self) -> Path:
        return STATIC_DIR / "avatars"


settings = Settings()
