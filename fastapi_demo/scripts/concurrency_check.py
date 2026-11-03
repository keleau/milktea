"""可复现的订单并发检查。

用法：
    python scripts/concurrency_check.py

脚本会把 database/milktea.db 复制到临时目录，不修改项目数据库。
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
import threading
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
DEFAULT_SEED = BASE_DIR / "database" / "milktea.db"
USER_ID = 1001
PRODUCT_ID = 1


def _payload(product_id: int = PRODUCT_ID, count: int = 1) -> dict:
    return {
        "store_id": 1,
        "mode": "pickup",
        "coupon_id": None,
        "items": [
            {
                "product_id": product_id,
                "ice": "少冰",
                "sugar": "五分糖",
                "topping_ids": [],
                "count": count,
            }
        ],
    }


def run_last_stock_race(session_factory, user_id: int = USER_ID, product_id: int = PRODUCT_ID) -> dict:
    """两个线程同时抢最后 1 件库存。"""
    from app.core.response import BizError
    from app.models import Order, Product, User
    from app.services.orders import create_order

    with session_factory() as db:
        product = db.get(Product, product_id)
        product.stock = 1
        before_count = db.query(Order).count()
        db.commit()

    results: list[tuple] = []
    barrier = threading.Barrier(2)

    def worker(index: int) -> None:
        with session_factory() as db:
            user = db.get(User, user_id)
            barrier.wait()
            try:
                order = create_order(
                    db,
                    user,
                    _payload(product_id),
                    idempotency_key=f"last-stock-{index}",
                )
                results.append(("ok", order.out_trade_no))
            except BizError as exc:
                results.append(("biz_error", exc.code, exc.message))
            except Exception as exc:  # pragma: no cover - 只用于把异常打印出来
                results.append(("exception", type(exc).__name__, str(exc)))

    threads = [threading.Thread(target=worker, args=(index,)) for index in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    with session_factory() as db:
        stock_after = db.get(Product, product_id).stock
        after_count = db.query(Order).count()

    success_order_no = next((item[1] for item in results if item[0] == "ok"), None)
    return {
        "results": results,
        "success": sum(1 for item in results if item[0] == "ok"),
        "stock_insufficient": sum(
            1 for item in results if item[0] == "biz_error" and item[1] == 2002
        ),
        "stock_after": stock_after,
        "orders_created": after_count - before_count,
        "success_order_no": success_order_no,
    }


def run_double_cancel_race(session_factory, user_id: int, out_trade_no: str, product_id: int = PRODUCT_ID) -> dict:
    """两个线程同时取消同一笔订单。"""
    from app.core.response import BizError
    from app.models import Order, Product, User
    from app.services.orders import cancel_order

    with session_factory() as db:
        before_stock = db.get(Product, product_id).stock

    results: list[tuple] = []
    barrier = threading.Barrier(2)

    def worker() -> None:
        with session_factory() as db:
            user = db.get(User, user_id)
            barrier.wait()
            try:
                order = cancel_order(db, user, out_trade_no)
                results.append(("ok", order.state))
            except BizError as exc:
                results.append(("biz_error", exc.code, exc.message))
            except Exception as exc:  # pragma: no cover
                results.append(("exception", type(exc).__name__, str(exc)))

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    with session_factory() as db:
        stock_after = db.get(Product, product_id).stock
        state = db.get(Order, out_trade_no).state

    return {
        "results": results,
        "success": sum(1 for item in results if item[0] == "ok"),
        "stock_before": before_stock,
        "stock_after": stock_after,
        "state": state,
    }


def _make_factory(db_path: Path):
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(
        f"sqlite:///{db_path.as_posix()}",
        connect_args={"check_same_thread": False, "timeout": 15},
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine, sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="订单并发一致性检查")
    parser.add_argument("--seed", type=Path, default=DEFAULT_SEED, help="种子数据库路径")
    args = parser.parse_args()

    if not args.seed.is_file():
        print(f"种子数据库不存在：{args.seed}")
        return 2

    temp_dir = Path(tempfile.mkdtemp(prefix="milktea-concurrency-"))
    test_db = temp_dir / "milktea.db"
    shutil.copy(args.seed, test_db)
    os.environ["DATABASE_URL"] = f"sqlite:///{test_db.as_posix()}"
    engine, session_factory = _make_factory(test_db)

    try:
        last_stock = run_last_stock_race(session_factory)
        print(
            "[1/2] 最后 1 件库存并发："
            f"成功 {last_stock['success']} 单，"
            f"库存不足 {last_stock['stock_insufficient']} 单，"
            f"库存 {last_stock['stock_after']}，"
            f"新增订单 {last_stock['orders_created']} 笔"
        )
        for item in last_stock["results"]:
            print(f"      - {item}")

        if last_stock["success"] != 1 or last_stock["stock_after"] != 0:
            print("RESULT: FAIL（最后 1 件库存没有做到只有 1 单成功）")
            return 1

        double_cancel = run_double_cancel_race(
            session_factory, USER_ID, last_stock["success_order_no"]
        )
        print(
            "[2/2] 同一订单并发取消："
            f"取消成功 {double_cancel['success']} 次，"
            f"库存 {double_cancel['stock_before']} -> {double_cancel['stock_after']}，"
            f"订单状态 {double_cancel['state']}"
        )
        for item in double_cancel["results"]:
            print(f"      - {item}")

        expected_stock = double_cancel["stock_before"] + 1
        if (
            double_cancel["success"] != 2
            or double_cancel["stock_after"] != expected_stock
            or double_cancel["state"] != "cancelled"
        ):
            print("RESULT: FAIL（重复取消没有做到只回补一次库存）")
            return 1

        print("RESULT: PASS")
        return 0
    finally:
        engine.dispose()
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
