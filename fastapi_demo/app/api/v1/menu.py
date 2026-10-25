from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import ICE_OPTIONS, SUGAR_OPTIONS
from app.core.response import ApiResponse, BizError, ok
from app.db import get_db
from app.deps import get_optional_user
from app.models import Product, ProductLine, Store, Topping, User
from app.schemas import (
    ListData,
    LineOut,
    MenuData,
    MenuGroupOut,
    OptionsOut,
    ProductDetailOut,
    ProductOut,
    RankData,
    RankItemOut,
    RankPeriod,
)
from app.serializers import (
    serialize_line,
    serialize_product,
    serialize_topping,
)
from app.services.catalog import frequent_product_ids

router = APIRouter(prefix="/menu", tags=["菜单"])


@router.get("/lines", response_model=ApiResponse[ListData[LineOut]], summary="产品线列表")
def list_lines(db: Session = Depends(get_db)):
    lines = db.scalars(
        select(ProductLine).order_by(ProductLine.sort_order, ProductLine.id)
    ).all()
    return ok({"items": [serialize_line(line) for line in lines]})


@router.get("/products", response_model=ApiResponse[MenuData], summary="商品列表（支持筛选/分页/按产品线分组）")
def list_products(
    line_id: str | None = Query(None),
    tab: Literal["classic", "member", "new", "mine"] | None = Query(None),
    keyword: str | None = Query(None, max_length=50),
    store_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    group_by_line: bool = Query(False),
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    if line_id is not None and db.get(ProductLine, line_id) is None:
        raise BizError(1004, "产品线不存在", 404)
    if store_id is not None and db.get(Store, store_id) is None:
        raise BizError(1004, "门店不存在", 404)
    if tab not in (None, "classic", "member", "new", "mine"):
        raise BizError(1001, "tab 参数不正确", 400)

    statement = select(Product).where(Product.on_sale.is_(True))
    if line_id:
        statement = statement.where(Product.line_id == line_id)
    if tab == "member":
        statement = statement.where(Product.orig_price.is_not(None))
    elif tab == "new":
        statement = statement.where(Product.is_new.is_(True))
    if keyword:
        statement = statement.where(Product.name.contains(keyword, autoescape=True))

    positions: dict[int, int] = {}
    if tab == "mine":
        if user is None:
            raise BizError(1002, "查看常点需要先登录", 401)
        product_ids = frequent_product_ids(db, user.id)
        positions = {product_id: index for index, product_id in enumerate(product_ids)}
        if not positions:
            products = []
        else:
            rows = db.scalars(
                statement.where(Product.id.in_(list(positions))).order_by(Product.id)
            ).all()
            products = sorted(rows, key=lambda product: positions[product.id])
    else:
        products = list(db.scalars(statement.order_by(Product.id)).all())

    total = len(products)
    groups = None
    if group_by_line:
        lines = db.scalars(
            select(ProductLine).order_by(ProductLine.sort_order, ProductLine.id)
        ).all()
        grouped = []
        for line in lines:
            line_products = [product for product in products if product.line_id == line.id]
            if line_products:
                grouped.append(
                    {
                        "line": serialize_line(line),
                        "products": [serialize_product(product) for product in line_products],
                    }
                )
        groups = grouped
        items = products
        page = 1
        page_size = len(items)
    else:
        start = (page - 1) * page_size
        items = products[start : start + page_size]

    return ok(
        {
            "items": [serialize_product(product) for product in items],
            "groups": groups,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.get("/products/{product_id}", response_model=ApiResponse[ProductDetailOut], summary="商品详情")
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if product is None:
        raise BizError(1004, "商品不存在", 404)
    if not product.on_sale:
        raise BizError(2001, "商品已下架", 400)
    toppings = db.scalars(
        select(Topping).order_by(Topping.sort_order, Topping.id)
    ).all()
    return ok(
        {
            **serialize_product(product),
            "line": serialize_line(product.line),
            "ice_options": ICE_OPTIONS,
            "sugar_options": SUGAR_OPTIONS,
            "toppings": [serialize_topping(topping) for topping in toppings],
        }
    )


@router.get("/options", response_model=ApiResponse[OptionsOut], summary="全局冰/糖/小料选项")
def get_options(db: Session = Depends(get_db)):
    toppings = db.scalars(
        select(Topping).order_by(Topping.sort_order, Topping.id)
    ).all()
    return ok(
        {
            "ice_options": ICE_OPTIONS,
            "sugar_options": SUGAR_OPTIONS,
            "toppings": [serialize_topping(topping) for topping in toppings],
        }
    )


@router.get("/rank", response_model=ApiResponse[RankData], summary="猫爪人气榜")
def get_rank(period: RankPeriod = Query("week"), db: Session = Depends(get_db)):
    products = db.scalars(
        select(Product)
        .where(Product.on_sale.is_(True))
        .order_by(Product.paws.desc(), Product.is_hot.desc(), Product.id)
    ).all()
    items = [
        {"rank": index + 1, **serialize_product(product)}
        for index, product in enumerate(products)
    ]
    new_items = [serialize_product(product) for product in products if product.is_new][:6]
    return ok({"period": period, "items": items, "new_items": new_items})
