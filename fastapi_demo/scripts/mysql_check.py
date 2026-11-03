"""MySQL 实库 smoke 检查。

用法：
    python scripts/mysql_check.py

前提：fastapi_demo/.env 配置了 mysql+pymysql 的 DATABASE_URL。
脚本会创建临时库 milktea_test_<时间戳>，导入 schema_mysql.sql，
跑完库存/取消/优惠券/积分检查后删除临时库，不改动现有 milktea 库。
"""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path
from urllib.parse import unquote, urlparse

import pymysql
from pymysql.constants import CLIENT

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
SCHEMA_PATH = BASE_DIR / "database" / "schema_mysql.sql"


def _mysql_config() -> dict:
    from app.core.config import settings

    parsed = urlparse(settings.database_url)
    if parsed.scheme not in ("mysql+pymysql", "mysql"):
        raise SystemExit(
            "当前 DATABASE_URL 不是 MySQL。请在 fastapi_demo/.env 配置 "
            "mysql+pymysql://用户:密码@127.0.0.1:3306/milktea?charset=utf8mb4"
        )
    if not parsed.hostname or not parsed.username:
        raise SystemExit("DATABASE_URL 缺少 host 或 user")
    return {
        "host": parsed.hostname,
        "port": parsed.port or 3306,
        "user": unquote(parsed.username),
        "password": unquote(parsed.password or ""),
    }


def _make_session_factory(test_url):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(
        test_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 5},
    )
    return engine, sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def main() -> int:
    if not SCHEMA_PATH.is_file():
        print(f"schema 不存在：{SCHEMA_PATH}")
        return 2

    config = _mysql_config()
    from sqlalchemy.engine import URL

    test_db = f"milktea_test_{int(time.time())}"
    if not re.fullmatch(r"[A-Za-z0-9_]+", test_db):
        print("临时库名不合法")
        return 2

    server = pymysql.connect(
        **config,
        charset="utf8mb4",
        autocommit=True,
        connect_timeout=5,
        client_flag=CLIENT.MULTI_STATEMENTS,
    )
    engine = None
    try:
        with server.cursor() as cur:
            cur.execute("SELECT VERSION()")
            version = cur.fetchone()[0]
            cur.execute(
                f"CREATE DATABASE `{test_db}` "
                "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        print(f"[OK] MySQL {version}，临时库 {test_db}")

        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        schema = schema.replace(
            "CREATE DATABASE IF NOT EXISTS milktea",
            f"CREATE DATABASE IF NOT EXISTS `{test_db}`",
        )
        schema = schema.replace("USE milktea;", f"USE `{test_db}`;")
        with server.cursor() as cur:
            cur.execute(schema)
            while cur.nextset():
                pass
        print("[OK] schema_mysql.sql 导入完成")

        test_url = URL.create(
            "mysql+pymysql",
            username=config["user"],
            password=config["password"],
            host=config["host"],
            port=config["port"],
            database=test_db,
            query={"charset": "utf8mb4"},
        )
        engine, session_factory = _make_session_factory(test_url)

        from sqlalchemy import inspect

        tables = inspect(engine).get_table_names()
        if len(tables) != 16:
            raise AssertionError(f"表数量应为 16，实际 {len(tables)}")

        from app.models import Product, User, UserCoupon
        from app.services.orders import cancel_order, create_order, pay_order
        from scripts.concurrency_check import (
            run_double_cancel_race,
            run_last_stock_race,
        )

        with session_factory() as db:
            product_count = db.query(Product).count()
            user_count = db.query(User).count()
        if product_count != 12 or user_count < 1:
            raise AssertionError("种子数据不完整")
        print(f"[OK] 16 张表，{product_count} 款饮品，{user_count} 个用户")

        last_stock = run_last_stock_race(session_factory)
        print(
            "[OK] 最后 1 件库存并发："
            f"成功 {last_stock['success']} 单，"
            f"库存不足 {last_stock['stock_insufficient']} 单，"
            f"库存 {last_stock['stock_after']}"
        )
        if last_stock["success"] != 1 or last_stock["stock_after"] != 0:
            raise AssertionError("MySQL 并发抢库存结果不正确")

        double_cancel = run_double_cancel_race(
            session_factory, 1001, last_stock["success_order_no"]
        )
        print(
            "[OK] 同一订单并发取消："
            f"取消成功 {double_cancel['success']} 次，"
            f"库存 {double_cancel['stock_before']} -> {double_cancel['stock_after']}"
        )
        if (
            double_cancel["success"] != 2
            or double_cancel["stock_after"] != double_cancel["stock_before"] + 1
        ):
            raise AssertionError("MySQL 重复取消结果不正确")

        coupon_payload = {
            "store_id": 1,
            "mode": "pickup",
            "coupon_id": 501,
            "items": [
                {
                    "product_id": 3,
                    "ice": "少冰",
                    "sugar": "五分糖",
                    "topping_ids": [],
                    "count": 1,
                }
            ],
        }
        with session_factory() as db:
            product = db.get(Product, 3)
            product.stock = 10
            db.commit()
            user = db.get(User, 1001)
            initial_points = user.points
            order = create_order(
                db, user, coupon_payload, idempotency_key="mysql-coupon-1"
            )
            pay_order(db, order.out_trade_no)
            db.expire_all()
            if db.get(UserCoupon, 501).status != "used":
                raise AssertionError("支付后优惠券未核销")
            cancel_order(db, db.get(User, 1001), order.out_trade_no)
            db.expire_all()
            if db.get(UserCoupon, 501).status != "unused":
                raise AssertionError("取消后优惠券未释放")
            if db.get(User, 1001).points != initial_points:
                raise AssertionError("取消后积分未回滚")
            if db.get(Product, 3).stock != 10:
                raise AssertionError("取消后库存未回补")
        print("[OK] 创建订单 / 支付 / 取消：库存、券、积分一致")

        print("RESULT: PASS")
        return 0
    except Exception as exc:
        print(f"RESULT: FAIL ({type(exc).__name__}: {exc})")
        return 1
    finally:
        if engine is not None:
            engine.dispose()
        try:
            from app.db import engine as app_engine

            app_engine.dispose()
        except Exception:
            pass
        try:
            with server.cursor() as cur:
                cur.execute("USE mysql")
                cur.execute(f"DROP DATABASE IF EXISTS `{test_db}`")
            print(f"[OK] 已删除临时库 {test_db}")
        except Exception as exc:
            print(f"[WARN] 临时库删除失败：{type(exc).__name__}: {exc}")
        server.close()


if __name__ == "__main__":
    sys.exit(main())
