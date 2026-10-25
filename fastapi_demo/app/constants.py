import time

DAY_MS = 24 * 3600 * 1000

ICE_OPTIONS = ["正常冰", "少冰", "去冰", "热饮"]
SUGAR_OPTIONS = ["全糖", "七分糖", "五分糖", "三分糖", "不加糖"]

STATE_TEXT = {
    "pending_pay": "待支付",
    "making": "制作中",
    "completed": "已完成",
    "cancelled": "已取消",
}
MODE_TEXT = {"pickup": "自取", "delivery": "外送"}


def now_ms() -> int:
    return int(time.time() * 1000)
