import logging
import threading
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import api_router
from app.core.config import STATIC_DIR, settings
from app.core.response import BizError, biz_error_handler
from app.db import SessionLocal, engine
from app.services import orders as order_service

logger = logging.getLogger("simaotea")
STATIC_DIR.mkdir(parents=True, exist_ok=True)
settings.avatar_dir.mkdir(parents=True, exist_ok=True)

_expiry_stop = threading.Event()


def _expire_orders_loop() -> None:
    interval = max(5, settings.order_expiry_interval_seconds)
    while not _expiry_stop.wait(interval):
        try:
            with SessionLocal() as db:
                expired = order_service.expire_pending_orders(db)
            if expired:
                logger.info("已自动取消 %s 笔超时未支付订单", expired)
        except Exception:
            logger.exception("自动取消超时订单失败")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("数据库连接: %s", engine.url.render_as_string(hide_password=True))
    if not inspect(engine).has_table("users"):
        logger.warning(
            "数据库表不存在，请先执行 database/build_sqlite.py 或导入 database/schema_mysql.sql"
        )
    expiry_thread = None
    if settings.order_expiry_minutes > 0:
        _expiry_stop.clear()
        expiry_thread = threading.Thread(
            target=_expire_orders_loop,
            name="order-expiry",
            daemon=True,
        )
        expiry_thread.start()
    yield
    _expiry_stop.set()
    if expiry_thread is not None:
        expiry_thread.join(timeout=2)
    engine.dispose()


app = FastAPI(
    title="四猫茶学园 API",
    version="1.0.0",
    description=(
        "奶茶点单小程序演示后端。数据存储于数据库（默认 SQLite，可通过 DATABASE_URL 切换 MySQL）；"
        "支付与微信登录均为模拟实现。调用 `POST /api/v1/auth/wx-login` 且 body 为 "
        '`{"code": "demo"}` 可登录预置会员（V2、320 积分、2 张券）。'
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)
app.add_exception_handler(BizError, biz_error_handler)


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException):
    code = {400: 1001, 401: 1002, 403: 1003, 404: 1004}.get(exc.status_code)
    if code is None:
        code = 9000 if exc.status_code >= 500 else 1001
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": code, "message": str(exc.detail), "data": None},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    first = errors[0] if errors else {}
    location = ".".join(str(part) for part in first.get("loc", ())[1:])
    message = first.get("msg", "参数校验失败")
    if location:
        message = f"{location}: {message}"
    return JSONResponse(status_code=400, content={"code": 1001, "message": message, "data": None})


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logger.exception("未处理异常: %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"code": 9000, "message": "服务内部错误", "data": None})


app.include_router(api_router, prefix="/api/v1")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
def index():
    return {
        "name": "四猫茶学园 API",
        "docs": "/docs",
        "api_prefix": "/api/v1",
        "demo_login": 'POST /api/v1/auth/wx-login with {"code": "demo"}',
    }


if __name__ == "__main__":
    # 真机调试需要监听局域网；只在本机调试可改回 127.0.0.1
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
