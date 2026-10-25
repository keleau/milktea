import math

from fastapi import APIRouter, Query

import app.data as db
from app.core.response import ApiResponse, BizError, ok
from app.schemas import ListData, StoreOut

router = APIRouter(prefix="/stores", tags=["门店"])


def _distance_m(lat1: float, lng1: float, lat2: float, lng2: float) -> int:
    radius = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return int(2 * radius * math.asin(math.sqrt(a)))


@router.get("", response_model=ApiResponse[ListData[StoreOut]], summary="门店列表（按距离升序）")
def list_stores(
    lat: float | None = Query(None, ge=-90, le=90),
    lng: float | None = Query(None, ge=-180, le=180),
):
    stores = [dict(store) for store in db.STORES]
    if lat is not None and lng is not None:
        for store in stores:
            store["distance"] = _distance_m(lat, lng, store["lat"], store["lng"])
    stores.sort(key=lambda store: store["distance"])
    return ok({"items": stores})


@router.get("/{store_id}", response_model=ApiResponse[StoreOut], summary="门店详情")
def get_store(store_id: int):
    store = db.STORES_BY_ID.get(store_id)
    if store is None:
        raise BizError(1004, "门店不存在", 404)
    return ok(store)
