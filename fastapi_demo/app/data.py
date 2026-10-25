from __future__ import annotations

import random
import threading
import time

from app.core.config import settings

DAY_MS = 24 * 3600 * 1000


def now_ms() -> int:
    return int(time.time() * 1000)


LINES = [
    {
        "id": "buchi",
        "name": "布奇·醇厚系列",
        "tag": "醇厚",
        "en": "Buchi's Rich Collection",
        "desc": "厚乳打底，浓郁治愈",
        "color": "#8B5E3C",
        "bg": "#F3EAE0",
    },
    {
        "id": "sakamoto",
        "name": "坂本·纯选系列",
        "tag": "纯选",
        "en": "Sakamoto's Pure Selection",
        "desc": "原叶直萃，低糖轻负担",
        "color": "#5A5A5A",
        "bg": "#EFEFEF",
    },
    {
        "id": "tom",
        "name": "汤姆·甜心角落",
        "tag": "甜心",
        "en": "Tom's Sweet Corner",
        "desc": "布丁芋泥，甜蜜暴击",
        "color": "#D9737F",
        "bg": "#FAEBED",
    },
    {
        "id": "tama",
        "name": "玉·清爽系列",
        "tag": "清爽",
        "en": "Tama's Refresh Line",
        "desc": "冷萃鲜果，一口回魂",
        "color": "#5C9E6E",
        "bg": "#EAF3EC",
    },
]


def _image(drink_id: int) -> str:
    return f"{settings.image_url}/drink_{drink_id}.jpg"


PRODUCTS = [
    {"id": 1, "line_id": "buchi", "name": "黑糖波波厚奶茶", "price": 14.0, "orig_price": 17.0, "paws": 5, "is_hot": True, "is_new": False, "desc": "手熬黑糖挂壁，波波Q弹，厚乳香浓", "image": _image(1), "stock": 50, "on_sale": True},
    {"id": 2, "line_id": "buchi", "name": "经典原味厚乳奶茶", "price": 12.0, "orig_price": 15.0, "paws": 4, "is_hot": True, "is_new": False, "desc": "锡兰红茶配厚牛乳，经典不翻车", "image": _image(2), "stock": 45, "on_sale": True},
    {"id": 3, "line_id": "buchi", "name": "提拉米苏厚乳茶", "price": 16.0, "orig_price": None, "paws": 4, "is_hot": False, "is_new": True, "desc": "可可粉轻撒，奶油顶配厚乳茶底", "image": _image(3), "stock": 30, "on_sale": True},
    {"id": 4, "line_id": "sakamoto", "name": "茉莉初雪轻乳茶", "price": 12.0, "orig_price": None, "paws": 4, "is_hot": False, "is_new": False, "desc": "茉莉雪芽打底，轻薄乳盖", "image": _image(4), "stock": 40, "on_sale": True},
    {"id": 5, "line_id": "sakamoto", "name": "四季春原叶纯茶", "price": 9.0, "orig_price": None, "paws": 4, "is_hot": False, "is_new": False, "desc": "原叶冷萃，零奶零糖也回甘", "image": _image(5), "stock": 60, "on_sale": True},
    {"id": 6, "line_id": "sakamoto", "name": "轻乳乌龙茶", "price": 11.0, "orig_price": None, "paws": 3, "is_hot": False, "is_new": True, "desc": "三分甜轻负担，乌龙回香", "image": _image(6), "stock": 35, "on_sale": True},
    {"id": 7, "line_id": "tom", "name": "布丁可可萌宠杯", "price": 15.0, "orig_price": 18.0, "paws": 4, "is_hot": True, "is_new": False, "desc": "整颗焦糖布丁沉底，可可香浓", "image": _image(7), "stock": 25, "on_sale": True},
    {"id": 8, "line_id": "tom", "name": "芋泥啵啵鲜奶茶", "price": 15.0, "orig_price": None, "paws": 5, "is_hot": False, "is_new": False, "desc": "手捣芋泥厚挂壁，芋圆软糯", "image": _image(8), "stock": 25, "on_sale": True},
    {"id": 9, "line_id": "tom", "name": "草莓芝士奶盖", "price": 16.0, "orig_price": None, "paws": 4, "is_hot": False, "is_new": True, "desc": "鲜草莓果肉，咸香芝士奶盖", "image": _image(9), "stock": 20, "on_sale": True},
    {"id": 10, "line_id": "tama", "name": "满杯百香果茶", "price": 12.0, "orig_price": None, "paws": 5, "is_hot": False, "is_new": False, "desc": "整颗百香果，冰爽维C满格", "image": _image(10), "stock": 40, "on_sale": True},
    {"id": 11, "line_id": "tama", "name": "手打香水柠檬茶", "price": 11.0, "orig_price": None, "paws": 5, "is_hot": False, "is_new": False, "desc": "现捶香水柠檬，酸爽解腻", "image": _image(11), "stock": 40, "on_sale": True},
    {"id": 12, "line_id": "tama", "name": "冷萃乌龙青提茶", "price": 14.0, "orig_price": None, "paws": 4, "is_hot": False, "is_new": True, "desc": "冷萃乌龙配青提，低糖果香", "image": _image(12), "stock": 30, "on_sale": True},
]
PRODUCTS_BY_ID = {p["id"]: p for p in PRODUCTS}
LINES_BY_ID = {line["id"]: line for line in LINES}

STORES = [
    {"id": 1, "name": "四猫茶学园·星悦广场店", "area": "星悦广场 1F", "address": "浦东新区世纪大道 100 号", "lat": 31.2320, "lng": 121.4750, "distance": 205, "status": "resting", "business_hours": "10:00-22:00", "making_cups": 4, "pack_fee": 1.0, "delivery_fee": 4.0},
    {"id": 2, "name": "四猫茶学园·万象城店", "area": "万象城 L2", "address": "闵行区吴中路 1599 号", "lat": 31.2250, "lng": 121.4650, "distance": 1200, "status": "open", "business_hours": "10:00-22:00", "making_cups": 6, "pack_fee": 1.0, "delivery_fee": 5.0},
    {"id": 3, "name": "四猫茶学园·大学城店", "area": "大学城美食街 B1", "address": "松江区文汇路 800 号", "lat": 31.2000, "lng": 121.4300, "distance": 2400, "status": "open", "business_hours": "09:30-21:30", "making_cups": 2, "pack_fee": 1.0, "delivery_fee": 3.0},
]
STORES_BY_ID = {s["id"]: s for s in STORES}

ICE_OPTIONS = ["正常冰", "少冰", "去冰", "热饮"]
SUGAR_OPTIONS = ["全糖", "七分糖", "五分糖", "三分糖", "不加糖"]
TOPPINGS = [
    {"id": 1, "name": "珍珠", "price": 1.0},
    {"id": 2, "name": "椰果", "price": 1.0},
    {"id": 3, "name": "布丁", "price": 2.0},
    {"id": 4, "name": "芋圆", "price": 2.0},
    {"id": 5, "name": "芝士奶盖", "price": 3.0},
]
TOPPINGS_BY_ID = {t["id"]: t for t in TOPPINGS}

COUPON_TEMPLATES = [
    {"id": 1, "title": "新猫见面礼", "desc": "满15减3", "cut": 3.0, "min_amount": 15.0, "valid_days": 30},
    {"id": 2, "title": "周二会员日", "desc": "满25减5", "cut": 5.0, "min_amount": 25.0, "valid_days": 30},
]
COUPON_TEMPLATES_BY_ID = {t["id"]: t for t in COUPON_TEMPLATES}

POINT_EXCHANGE_ITEMS = [
    {"id": 1, "title": "¥3 优惠券", "cost": 100, "type": "coupon", "template_id": 1},
    {"id": 2, "title": "¥5 优惠券", "cost": 200, "type": "coupon", "template_id": 2},
]
POINT_EXCHANGE_BY_ID = {item["id"]: item for item in POINT_EXCHANGE_ITEMS}

MEMBER_LEVELS = [
    ("V1 见习猫评员", 0),
    ("V2 银牌猫评员", 200),
    ("V3 金牌猫评员", 800),
    ("V4 黑金猫评员", 2000),
]

USERS: dict[int, dict] = {}
USER_ID_BY_OPENID: dict[str, int] = {}
COUPONS: dict[int, dict] = {}
ORDERS: dict[str, dict] = {}
ADDRESSES: dict[int, dict] = {}
FAVORITES: dict[int, list[int]] = {}
POINTS_LOGS: dict[int, list[dict]] = {}
IDEMPOTENCY: dict[str, tuple[int, str]] = {}

_lock = threading.Lock()
_next_user_id = 1001
_next_coupon_id = 501
_next_address_id = 2
_next_points_log_id = 2


def _new_user_id() -> int:
    global _next_user_id
    with _lock:
        value = _next_user_id
        _next_user_id += 1
        return value


def _new_coupon_id() -> int:
    global _next_coupon_id
    with _lock:
        value = _next_coupon_id
        _next_coupon_id += 1
        return value


def _new_address_id() -> int:
    global _next_address_id
    with _lock:
        value = _next_address_id
        _next_address_id += 1
        return value


new_address_id = _new_address_id


def _new_points_log_id() -> int:
    global _next_points_log_id
    with _lock:
        value = _next_points_log_id
        _next_points_log_id += 1
        return value


def refresh_coupon_status(coupon: dict) -> dict:
    if coupon["status"] == "unused" and coupon["expire_at"] <= now_ms():
        coupon["status"] = "expired"
    return coupon


def coupon_count(user_id: int) -> int:
    return sum(1 for c in COUPONS.values() if c["user_id"] == user_id and refresh_coupon_status(c)["status"] == "unused")


def user_coupons(user_id: int) -> list[dict]:
    return [refresh_coupon_status(c) for c in COUPONS.values() if c["user_id"] == user_id]


def add_coupon(user_id: int, template: dict, expire_at: int | None = None) -> dict:
    coupon_id = _new_coupon_id()
    coupon = {
        "id": coupon_id,
        "user_id": user_id,
        "template_id": template["id"],
        "title": template["title"],
        "desc": template["desc"],
        "cut": float(template["cut"]),
        "min_amount": float(template["min_amount"]),
        "status": "unused",
        "expire_at": expire_at if expire_at is not None else now_ms() + template["valid_days"] * DAY_MS,
        "locked_by": None,
    }
    COUPONS[coupon_id] = coupon
    return coupon


def add_points_log(user_id: int, title: str, points: int, log_type: str) -> dict:
    log = {
        "id": _new_points_log_id(),
        "title": title,
        "points": points,
        "type": log_type,
        "created_at": now_ms(),
    }
    POINTS_LOGS.setdefault(user_id, []).insert(0, log)
    return log


def level_for(points: int) -> str:
    level = MEMBER_LEVELS[0][0]
    for name, threshold in MEMBER_LEVELS:
        if points >= threshold:
            level = name
    return level


def change_points(user: dict, delta: int, title: str, log_type: str) -> int:
    user["points"] = max(0, user["points"] + delta)
    user["level"] = level_for(user["points"])
    add_points_log(user["id"], title, delta, log_type)
    return user["points"]


def user_out(user: dict) -> dict:
    return {
        "id": user["id"],
        "nickname": user["nickname"],
        "avatar": user["avatar"],
        "level": user["level"],
        "points": user["points"],
        "balance": user["balance"],
        "coupon_count": coupon_count(user["id"]),
        "created_at": user["created_at"],
    }


def create_user(openid: str, nickname: str | None = None, avatar: str | None = None) -> dict:
    user_id = _new_user_id()
    user = {
        "id": user_id,
        "openid": openid,
        "nickname": nickname or "猫友1234",
        "avatar": avatar or f"{settings.image_url}/avatar.jpg",
        "level": "V1 见习猫评员",
        "points": 0,
        "balance": 0.0,
        "created_at": now_ms(),
    }
    USERS[user_id] = user
    USER_ID_BY_OPENID[openid] = user_id
    FAVORITES.setdefault(user_id, [])
    POINTS_LOGS.setdefault(user_id, [])
    return user


def get_user_by_openid(openid: str) -> dict | None:
    user_id = USER_ID_BY_OPENID.get(openid)
    return USERS.get(user_id) if user_id else None


def new_order_no() -> str:
    stamp = now_ms()
    for _ in range(1000):
        order_no = f"CAT{stamp}{random.randint(100, 999)}"
        if order_no not in ORDERS:
            return order_no
    return f"CAT{stamp}{random.randint(1000, 9999)}"


def new_pick_code() -> str:
    return f"{random.randint(10, 99)}{now_ms() % 1000:03d}"


def order_frequency(user_id: int) -> dict[int, int]:
    counter: dict[int, int] = {}
    user_orders = [o for o in ORDERS.values() if o["user_id"] == user_id]
    for order in sorted(user_orders, key=lambda o: o["create_time"]):
        for item in order["items"]:
            counter[item["product_id"]] = counter.get(item["product_id"], 0) + item["count"]
    return counter


def frequent_product_ids(user_id: int) -> list[int]:
    counter = order_frequency(user_id)
    ordered = sorted(counter, key=lambda pid: counter[pid], reverse=True)
    result = list(ordered)
    for pid in FAVORITES.get(user_id, []):
        if pid not in result:
            result.append(pid)
    return result


def get_idempotent(user_id: int, key: str) -> str | None:
    scoped = f"{user_id}:{key}"
    cached = IDEMPOTENCY.get(scoped)
    if not cached:
        return None
    expires_at, order_no = cached
    if expires_at <= now_ms() or order_no not in ORDERS:
        IDEMPOTENCY.pop(scoped, None)
        return None
    return order_no


def set_idempotent(user_id: int, key: str, order_no: str) -> None:
    IDEMPOTENCY[f"{user_id}:{key}"] = (now_ms() + settings.idempotency_ttl * 1000, order_no)


def reset() -> None:
    """清空运行时数据，仅测试使用。"""
    global _next_user_id, _next_coupon_id, _next_address_id, _next_points_log_id
    USERS.clear()
    USER_ID_BY_OPENID.clear()
    COUPONS.clear()
    ORDERS.clear()
    ADDRESSES.clear()
    FAVORITES.clear()
    POINTS_LOGS.clear()
    IDEMPOTENCY.clear()
    _next_user_id = 1001
    _next_coupon_id = 501
    _next_address_id = 2
    _next_points_log_id = 2
    seed()


def seed() -> None:
    demo = create_user("mock-openid-demo", "猫友1234")
    demo.update(
        {
            "level": "V2 银牌猫评员",
            "points": 320,
            "balance": 8.5,
            "created_at": now_ms() - 60 * DAY_MS,
        }
    )
    add_coupon(demo["id"], COUPON_TEMPLATES_BY_ID[1], expire_at=now_ms() + 30 * DAY_MS)
    add_coupon(demo["id"], COUPON_TEMPLATES_BY_ID[2], expire_at=now_ms() + 30 * DAY_MS)
    add_points_log(demo["id"], "历史积分", 320, "history")
    FAVORITES[demo["id"]] = [1, 8]
    ADDRESSES[1] = {
        "id": 1,
        "user_id": demo["id"],
        "name": "张女士",
        "phone": "13800008888",
        "detail": "星悦广场 3 栋 502",
        "is_default": True,
    }
    _next_address_id = 2


seed()
