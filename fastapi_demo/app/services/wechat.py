"""微信服务端接口：access_token 缓存与小程序码生成。

access_token 有效期 2 小时，且每个小程序每天最多获取 2000 次，
所以这里做进程内缓存。多进程部署时应换成共享缓存（如 Redis）。
"""

from __future__ import annotations

import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.core.config import settings

TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
WXA_CODE_URL = "https://api.weixin.qq.com/wxa/getwxacodeunlimit"

# 提前 5 分钟过期，避免拿到临界 token
TOKEN_SAFETY_SECONDS = 300

_token: str = ""
_token_expires_at: float = 0.0


class WeChatError(RuntimeError):
    """微信接口调用失败，message 可直接展示给调用方。"""


def _request_json(url: str, payload: dict | None = None, timeout: int = 10) -> dict:
    data = None
    headers: dict[str, str] = {}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers, method="POST" if data else "GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read()
    except (HTTPError, URLError, OSError) as exc:
        raise WeChatError(f"微信接口不可用：{exc}") from exc
    try:
        return json.loads(body.decode("utf-8"))
    except ValueError as exc:
        raise WeChatError("微信接口返回了非 JSON 数据") from exc


def get_access_token(force: bool = False) -> str:
    """取 access_token；进程内缓存到过期前 5 分钟。"""
    global _token, _token_expires_at

    if not settings.wechat_login_enabled:
        raise WeChatError("未配置 WECHAT_APPID / WECHAT_SECRET")

    now = time.time()
    if not force and _token and now < _token_expires_at:
        return _token

    query = urlencode(
        {
            "grant_type": "client_credential",
            "appid": settings.wechat_appid,
            "secret": settings.wechat_secret,
        }
    )
    data = _request_json(f"{TOKEN_URL}?{query}")
    token = data.get("access_token")
    if not token:
        raise WeChatError(
            f"获取 access_token 失败：{data.get('errmsg') or '未知错误'}（{data.get('errcode')}）"
        )

    expires_in = int(data.get("expires_in") or 7200)
    _token = token
    _token_expires_at = now + max(expires_in - TOKEN_SAFETY_SECONDS, 60)
    return token


def fetch_wxa_code(
    scene: str,
    page: str = "pages/menu/index",
    env_version: str = "release",
    width: int = 430,
    check_path: bool = False,
    _retry: bool = True,
) -> bytes:
    """生成小程序码，返回图片二进制。

    - scene 最多 32 个可见字符（MILKTEA:1:A01 这种格式没问题）
    - page 不能以 / 开头
    - check_path=False 时页面未发布也能生成，适合体验版/开发版联调
    - env_version: release 正式版 / trial 体验版 / develop 开发版
    """
    payload = {
        "scene": scene,
        "page": page,
        "check_path": check_path,
        "env_version": env_version,
        "width": width,
    }
    token = get_access_token()
    request = Request(
        f"{WXA_CODE_URL}?access_token={token}",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            body = response.read()
    except (HTTPError, URLError, OSError) as exc:
        raise WeChatError(f"生成小程序码失败：{exc}") from exc

    # 成功返回图片二进制，失败返回 JSON
    if body[:1] != b"{":
        if len(body) < 100:
            raise WeChatError("生成小程序码失败：返回内容不是图片")
        return body

    try:
        data = json.loads(body.decode("utf-8"))
    except ValueError as exc:
        raise WeChatError("生成小程序码失败：返回数据无法解析") from exc

    errcode = data.get("errcode")
    if errcode in (40001, 42001) and _retry:
        # token 失效：强制刷新后重试一次
        get_access_token(force=True)
        return fetch_wxa_code(scene, page, env_version, width, check_path, _retry=False)
    raise WeChatError(f"生成小程序码失败：{data.get('errmsg') or '未知错误'}（{errcode}）")


def image_ext(data: bytes) -> str:
    """按文件头判断图片格式；微信目前默认返回 jpg。"""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    return "jpg"
