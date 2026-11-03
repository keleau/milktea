from datetime import timedelta

import pytest
from sqlalchemy import select

from app.constants import now_ms
from app.core.response import BizError
from app.models import Order, PointsLog, Product, User, UserCoupon
from app.services import orders as order_service
from app.services.orders import (
    cancel_order,
    create_order,
    expire_pending_orders,
    pay_order,
)
from scripts.concurrency_check import run_double_cancel_race, run_last_stock_race


def _payload(product_id: int = 1, count: int = 1, coupon_id: int | None = None) -> dict:
    return {
        "store_id": 1,
        "mode": "pickup",
        "coupon_id": coupon_id,
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


def _stock(db, product_id: int = 1) -> int:
    db.expire_all()
    return db.get(Product, product_id).stock


def _user(db) -> User:
    db.expire_all()
    return db.get(User, 1001)


def test_create_order_reserves_stock_and_reuses_idempotency(db):
    product = db.get(Product, 1)
    product.stock = 5
    db.commit()

    first = create_order(db, _user(db), _payload(), idempotency_key="idem-1")
    assert first.stock_reserved is True
    assert _stock(db) == 4

    second = create_order(db, _user(db), _payload(), idempotency_key="idem-1")
    assert second.out_trade_no == first.out_trade_no
    assert _stock(db) == 4


def test_duplicate_idempotency_insert_returns_existing_order(db, monkeypatch):
    product = db.get(Product, 1)
    product.stock = 5
    db.commit()

    first = create_order(db, _user(db), _payload(), idempotency_key="dup-key")
    first_no = first.out_trade_no

    # 模拟并发窗口：两个请求都通过了“查幂等键”，后到者在写唯一键时才冲突。
    monkeypatch.setattr(order_service, "get_idempotent", lambda *args, **kwargs: None)
    second = order_service.create_order(
        db, _user(db), _payload(), idempotency_key="dup-key"
    )

    assert second.out_trade_no == first_no
    assert _stock(db) == 4
    assert db.query(Order).count() == 1


def test_last_stock_only_one_order_succeeds(session_factory):
    result = run_last_stock_race(session_factory)

    assert result["success"] == 1
    assert result["stock_insufficient"] == 1
    assert result["stock_after"] == 0
    assert result["orders_created"] == 1


def test_double_cancel_restores_stock_once(session_factory):
    with session_factory() as db:
        product = db.get(Product, 1)
        product.stock = 1
        db.commit()
        order = create_order(db, _user(db), _payload(), idempotency_key="cancel-1")

    result = run_double_cancel_race(session_factory, 1001, order.out_trade_no)

    assert result["success"] == 2
    assert result["stock_after"] == result["stock_before"] + 1
    assert result["state"] == "cancelled"


def test_cancel_is_idempotent(db):
    product = db.get(Product, 1)
    product.stock = 5
    db.commit()

    order = create_order(db, _user(db), _payload(), idempotency_key="cancel-idem-1")
    cancel_order(db, _user(db), order.out_trade_no)
    again = cancel_order(db, _user(db), order.out_trade_no)

    assert again.state == "cancelled"
    assert _stock(db, 1) == 5


def test_pay_twice_awards_points_once(db):
    product = db.get(Product, 3)
    product.stock = 10
    db.commit()

    user = _user(db)
    initial_points = user.points
    order = create_order(db, user, _payload(product_id=3), idempotency_key="pay-1")
    paid = pay_order(db, order.out_trade_no)

    db.expire_all()
    assert _user(db).points == initial_points + int(paid.total)
    assert db.get(Order, order.out_trade_no).state == "making"
    logs = db.scalars(
        select(PointsLog).where(PointsLog.user_id == 1001, PointsLog.type == "order")
    ).all()
    assert len(logs) == 1

    pay_order(db, order.out_trade_no)
    db.expire_all()
    assert _user(db).points == initial_points + int(paid.total)
    assert len(
        db.scalars(
            select(PointsLog).where(PointsLog.user_id == 1001, PointsLog.type == "order")
        ).all()
    ) == 1


def test_cancel_making_order_refunds_stock_points_and_coupon(db):
    product = db.get(Product, 3)
    product.stock = 10
    db.commit()

    user = _user(db)
    initial_points = user.points
    order = create_order(
        db,
        user,
        _payload(product_id=3, coupon_id=501),
        idempotency_key="cancel-making-1",
    )
    assert db.get(UserCoupon, 501).locked_by == order.out_trade_no
    paid = pay_order(db, order.out_trade_no)

    db.expire_all()
    assert db.get(UserCoupon, 501).status == "used"
    assert _user(db).points == initial_points + int(paid.total)

    cancel_order(db, _user(db), order.out_trade_no)

    db.expire_all()
    assert db.get(Order, order.out_trade_no).state == "cancelled"
    assert _stock(db, 3) == 10
    assert db.get(UserCoupon, 501).status == "unused"
    assert db.get(UserCoupon, 501).locked_by is None
    assert _user(db).points == initial_points


def test_expire_pending_order_releases_stock_and_coupon(db):
    product = db.get(Product, 3)
    product.stock = 10
    db.commit()

    order = create_order(
        db,
        _user(db),
        _payload(product_id=3, coupon_id=501),
        idempotency_key="expire-1",
    )
    order.create_time = now_ms() - int(timedelta(minutes=16).total_seconds() * 1000)
    db.commit()

    assert expire_pending_orders(db, timeout_minutes=15) == 1

    db.expire_all()
    assert db.get(Order, order.out_trade_no).state == "cancelled"
    assert _stock(db, 3) == 10
    assert db.get(UserCoupon, 501).status == "unused"
    assert db.get(UserCoupon, 501).locked_by is None


def test_coupon_cannot_be_locked_by_two_orders(db):
    product = db.get(Product, 3)
    product.stock = 10
    db.commit()

    first = create_order(
        db,
        _user(db),
        _payload(product_id=3, coupon_id=501),
        idempotency_key="coupon-1",
    )
    assert _stock(db, 3) == 9

    with pytest.raises(BizError) as exc:
        create_order(
            db,
            _user(db),
            _payload(product_id=3, coupon_id=501),
            idempotency_key="coupon-2",
        )

    assert exc.value.code == 3004
    assert _stock(db, 3) == 9
    assert db.get(UserCoupon, 501).locked_by == first.out_trade_no


def test_invalid_table_is_rejected_before_stock_change(db):
    product = db.get(Product, 1)
    product.stock = 5
    db.commit()

    payload = _payload()
    payload["table_no"] = "Z99"

    with pytest.raises(BizError) as exc:
        create_order(db, _user(db), payload, idempotency_key="table-1")

    assert exc.value.code == 1004
    assert _stock(db, 1) == 5
    assert db.query(Order).count() == 0


def test_delivery_requires_address_before_stock_change(db):
    product = db.get(Product, 1)
    product.stock = 5
    db.commit()

    payload = _payload()
    payload["mode"] = "delivery"

    with pytest.raises(BizError) as exc:
        create_order(db, _user(db), payload, idempotency_key="delivery-1")

    assert exc.value.code == 1001
    assert _stock(db, 1) == 5
    assert db.query(Order).count() == 0


def test_delivery_order_snapshots_address(db):
    product = db.get(Product, 3)
    product.stock = 10
    db.commit()

    payload = _payload(product_id=3)
    payload["mode"] = "delivery"
    payload["address_id"] = 1
    order = create_order(db, _user(db), payload, idempotency_key="delivery-2")

    assert order.mode == "delivery"
    assert order.address_id == 1
    assert order.address_detail
    assert order.table_no is None

    cancel_order(db, _user(db), order.out_trade_no)
    assert _stock(db, 3) == 10


def test_table_order_binds_table_no(db):
    product = db.get(Product, 1)
    product.stock = 5
    db.commit()

    payload = _payload()
    payload["table_no"] = "A01"
    order = create_order(db, _user(db), payload, idempotency_key="table-2")

    assert order.table_no == "A01"
    assert order.mode == "pickup"

    cancel_order(db, _user(db), order.out_trade_no)
    assert _stock(db, 1) == 5
