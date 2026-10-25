from typing import Literal

from fastapi import APIRouter, Depends, Query

import app.data as db
from app.core.response import ApiResponse, BizError, ok
from app.deps import get_optional_user
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

router = APIRouter(prefix="/menu", tags=["菜单"])


def _public_products() -> list[dict]:
    return [product for product in db.PRODUCTS if product["on_sale"]]


@router.get("/lines", response_model=ApiResponse[ListData[LineOut]], summary="产品线列表")
def list_lines():
    return ok({"items": db.LINES})


@router.get("/products", response_model=ApiResponse[MenuData], summary="商品列表（支持筛选/分页/按产品线分组）")
def list_products(
    line_id: str | None = Query(None),
    tab: Literal["classic", "member", "new", "mine"] | None = Query(None),
    keyword: str | None = Query(None, max_length=50),
    store_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    group_by_line: bool = Query(False),
    user: dict | None = Depends(get_optional_user),
):
    if line_id is not None and line_id not in db.LINES_BY_ID:
        raise BizError(1004, "产品线不存在", 404)
    if store_id is not None and store_id not in db.STORES_BY_ID:
        raise BizError(1004, "门店不存在", 404)

    products = _public_products()
    if line_id:
        products = [p for p in products if p["line_id"] == line_id]

    if tab == "member":
        products = [p for p in products if p["orig_price"] is not None]
    elif tab == "new":
        products = [p for p in products if p["is_new"]]
    elif tab == "mine":
        if user is None:
            raise BizError(1002, "查看常点需要先登录", 401)
        frequent = db.frequent_product_ids(user["id"])
        positions = {product_id: index for index, product_id in enumerate(frequent)}
        products = [p for p in products if p["id"] in positions]
        products.sort(key=lambda p: positions[p["id"]])
    elif tab not in (None, "classic"):
        raise BizError(1001, "tab 参数不正确", 400)

    if keyword:
        needle = keyword.strip().lower()
        products = [p for p in products if needle in p["name"].lower()]

    if tab != "mine":
        products.sort(key=lambda p: p["id"])

    total = len(products)
    groups = None
    if group_by_line:
        groups = []
        for line in db.LINES:
            line_products = [p for p in products if p["line_id"] == line["id"]]
            if line_products:
                groups.append({"line": line, "products": line_products})
        items = products
        page = 1
        page_size = len(items)
    else:
        start = (page - 1) * page_size
        items = products[start : start + page_size]

    return ok(
        {
            "items": items,
            "groups": groups,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.get("/products/{product_id}", response_model=ApiResponse[ProductDetailOut], summary="商品详情")
def get_product(product_id: int):
    product = db.PRODUCTS_BY_ID.get(product_id)
    if product is None:
        raise BizError(1004, "商品不存在", 404)
    if not product["on_sale"]:
        raise BizError(2001, "商品已下架", 400)
    return ok(
        {
            **product,
            "line": db.LINES_BY_ID[product["line_id"]],
            "ice_options": db.ICE_OPTIONS,
            "sugar_options": db.SUGAR_OPTIONS,
            "toppings": db.TOPPINGS,
        }
    )


@router.get("/options", response_model=ApiResponse[OptionsOut], summary="全局冰/糖/小料选项")
def get_options():
    return ok(
        {
            "ice_options": db.ICE_OPTIONS,
            "sugar_options": db.SUGAR_OPTIONS,
            "toppings": db.TOPPINGS,
        }
    )


@router.get("/rank", response_model=ApiResponse[RankData], summary="猫爪人气榜")
def get_rank(period: RankPeriod = Query("week")):
    products = sorted(_public_products(), key=lambda p: (-p["paws"], -int(p["is_hot"]), p["id"]))
    items = [{"rank": index + 1, **product} for index, product in enumerate(products)]
    new_items = [product for product in products if product["is_new"]][:6]
    return ok({"period": period, "items": items, "new_items": new_items})
