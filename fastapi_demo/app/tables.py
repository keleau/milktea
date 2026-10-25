"""桌码配置与解析。

桌码内容约定：MILKTEA:<门店id>:<桌号>
生成脚本 database/build_table_qrcodes.py 与后端共用这份配置。
"""

SCENE_PREFIX = "MILKTEA"

# 门店 id → 桌号
DINING_TABLES: dict[int, list[str]] = {
    1: [f"A{i:02d}" for i in range(1, 9)],
    2: [f"B{i:02d}" for i in range(1, 7)],
    3: [f"C{i:02d}" for i in range(1, 9)],
}


def scene_of(store_id: int, table_no: str) -> str:
    return f"{SCENE_PREFIX}:{store_id}:{table_no}"


def table_exists(store_id: int, table_no: str) -> bool:
    return table_no in DINING_TABLES.get(store_id, [])


def parse_scene(scene: str) -> tuple[int, str] | None:
    """合法返回 (门店 id, 桌号)，否则返回 None"""
    parts = scene.strip().split(":")
    if len(parts) != 3 or parts[0] != SCENE_PREFIX:
        return None
    try:
        store_id = int(parts[1])
    except ValueError:
        return None
    table_no = parts[2].strip().upper()
    if not table_exists(store_id, table_no):
        return None
    return store_id, table_no
