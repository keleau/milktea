from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import ApiResponse, BizError, ok
from app.db import get_db
from app.models import Store
from app.schemas import TableResolveIn, TableResolveOut
from app.tables import parse_scene

router = APIRouter(prefix="/tables", tags=["桌码"])


@router.post("/resolve", response_model=ApiResponse[TableResolveOut], summary="解析桌码")
def resolve_table(payload: TableResolveIn, db: Session = Depends(get_db)):
    parsed = parse_scene(payload.scene)
    if parsed is None:
        raise BizError(1004, "桌码无效，请扫描店内桌码", 404)
    store_id, table_no = parsed

    store = db.get(Store, store_id)
    if store is None:
        raise BizError(1004, "门店不存在", 404)
    if store.status == "closed":
        raise BizError(2004, "门店已打烊", 409)

    return ok({"store_id": store_id, "store_name": store.name, "table_no": table_no})
