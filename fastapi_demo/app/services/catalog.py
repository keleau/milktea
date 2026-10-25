from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Favorite, Order, OrderItem


def frequent_product_ids(db: Session, user_id: int) -> list[int]:
    rows = db.execute(
        select(OrderItem.product_id, OrderItem.count)
        .join(Order, Order.out_trade_no == OrderItem.order_no)
        .where(Order.user_id == user_id)
        .order_by(Order.create_time, OrderItem.id)
    ).all()

    counter: dict[int, int] = {}
    for product_id, count in rows:
        counter[product_id] = counter.get(product_id, 0) + count

    result = sorted(counter, key=lambda product_id: counter[product_id], reverse=True)
    favorites = db.scalars(
        select(Favorite.product_id)
        .where(Favorite.user_id == user_id)
        .order_by(Favorite.created_at, Favorite.product_id)
    ).all()
    for product_id in favorites:
        if product_id not in result:
            result.append(product_id)
    return result
