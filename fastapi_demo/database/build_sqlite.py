"""用 Python 标准库生成 SQLite 数据库，并校验结构、种子数据与外键。

用法：
    python database/build_sqlite.py
    python database/build_sqlite.py --force
    python database/build_sqlite.py --db other.db --schema schema_sqlite.sql
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DATABASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB = DATABASE_DIR / "milktea.db"
DEFAULT_SCHEMA = DATABASE_DIR / "schema_sqlite.sql"

EXPECTED_TABLES = {
    "member_levels": 4,
    "users": 1,
    "product_lines": 4,
    "products": 12,
    "toppings": 5,
    "stores": 3,
    "coupon_templates": 2,
    "user_coupons": 2,
    "addresses": 1,
    "favorites": 2,
    "points_logs": 1,
    "exchange_items": 2,
    "orders": 0,
    "order_items": 0,
    "order_item_toppings": 0,
    "idempotency_keys": 0,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成四猫茶学园 SQLite 数据库")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="输出数据库路径")
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA, help="建表脚本路径")
    parser.add_argument("--force", action="store_true", help="覆盖已存在的数据库文件")
    return parser.parse_args()


def build(db_path: Path, schema_path: Path, force: bool) -> None:
    if not schema_path.is_file():
        raise SystemExit(f"建表脚本不存在：{schema_path}")

    if db_path.exists():
        if not force:
            raise SystemExit(
                f"数据库已存在：{db_path}\n如需重建请加 --force（会删除现有文件）"
            )
        db_path.unlink()
        print(f"已删除旧数据库：{db_path}")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    schema = schema_path.read_text(encoding="utf-8")

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(schema)
        conn.commit()

        conn.execute("PRAGMA foreign_keys = ON")
        check(conn)
    finally:
        conn.close()

    print(f"\n生成完成：{db_path}")
    print(f"文件大小：{db_path.stat().st_size} 字节")


def check(conn: sqlite3.Connection) -> None:
    print("自检开始")

    tables = [
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]
    expected = set(EXPECTED_TABLES)
    missing = expected - set(tables)
    extra = set(tables) - expected
    if missing or extra:
        raise SystemExit(f"表清单不一致：缺少 {sorted(missing)}，多出 {sorted(extra)}")
    print(f"[OK] 表数量 {len(tables)}")

    for table, expected_rows in EXPECTED_TABLES.items():
        actual = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        if actual != expected_rows:
            raise SystemExit(
                f"种子行数不一致：{table} 期望 {expected_rows}，实际 {actual}"
            )
    print("[OK] 种子行数")

    demo = conn.execute(
        "SELECT nickname, level_code, points, balance FROM users WHERE id = 1001"
    ).fetchone()
    if demo != ("猫友1234", "V2", 320, 8.5):
        raise SystemExit(f"演示用户数据异常：{demo}")
    print("[OK] 演示用户 1001")

    coupons = conn.execute(
        "SELECT id, status, locked_by FROM user_coupons ORDER BY id"
    ).fetchall()
    if coupons != [(501, "unused", None), (502, "unused", None)]:
        raise SystemExit(f"演示优惠券数据异常：{coupons}")
    print("[OK] 演示优惠券 501 / 502")

    fk_errors = conn.execute("PRAGMA foreign_key_check").fetchall()
    if fk_errors:
        raise SystemExit(f"外键校验失败：{fk_errors}")
    print("[OK] 外键完整性")

    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        raise SystemExit(f"数据库完整性异常：{integrity}")
    print("[OK] 数据库完整性")

    fk_enabled = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    print(f"[INFO] 当前连接 foreign_keys={fk_enabled}（后端连接时需再次开启）")


def main() -> int:
    args = parse_args()
    build(args.db.resolve(), args.schema.resolve(), args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
