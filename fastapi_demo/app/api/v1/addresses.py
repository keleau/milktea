from fastapi import APIRouter, Depends

import app.data as db
from app.core.response import ApiResponse, BizError, ok
from app.deps import get_current_user
from app.schemas import AddressIn, AddressOut, AddressUpdateIn, ListData

router = APIRouter(prefix="/addresses", tags=["收货地址"])


def _owned_address(user: dict, address_id: int) -> dict:
    address = db.ADDRESSES.get(address_id)
    if address is None:
        raise BizError(1004, "收货地址不存在", 404)
    if address["user_id"] != user["id"]:
        raise BizError(1003, "无权操作该地址", 403)
    return address


def _clear_default(user_id: int, except_id: int | None = None) -> None:
    for address in db.ADDRESSES.values():
        if address["user_id"] == user_id and address["id"] != except_id:
            address["is_default"] = False


@router.get("", response_model=ApiResponse[ListData[AddressOut]], summary="地址列表")
def list_addresses(user: dict = Depends(get_current_user)):
    addresses = [a for a in db.ADDRESSES.values() if a["user_id"] == user["id"]]
    addresses.sort(key=lambda a: (not a["is_default"], a["id"]))
    return ok({"items": addresses})


@router.post("", response_model=ApiResponse[AddressOut], summary="新增地址")
def create_address(payload: AddressIn, user: dict = Depends(get_current_user)):
    existing = [a for a in db.ADDRESSES.values() if a["user_id"] == user["id"]]
    is_default = payload.is_default or not existing
    if is_default:
        _clear_default(user["id"])
    address = {
        "id": db.new_address_id(),
        "user_id": user["id"],
        "name": payload.name,
        "phone": payload.phone,
        "detail": payload.detail,
        "is_default": is_default,
    }
    db.ADDRESSES[address["id"]] = address
    return ok(address)


@router.patch("/{address_id}", response_model=ApiResponse[AddressOut], summary="编辑地址")
def update_address(address_id: int, payload: AddressUpdateIn, user: dict = Depends(get_current_user)):
    address = _owned_address(user, address_id)
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("is_default") is True:
        _clear_default(user["id"], address_id)
    for key, value in changes.items():
        if value is not None:
            address[key] = value
    return ok(address)


@router.delete("/{address_id}", response_model=ApiResponse[AddressOut], summary="删除地址")
def delete_address(address_id: int, user: dict = Depends(get_current_user)):
    address = _owned_address(user, address_id)
    was_default = address["is_default"]
    db.ADDRESSES.pop(address_id)
    if was_default:
        remaining = [a for a in db.ADDRESSES.values() if a["user_id"] == user["id"]]
        if remaining:
            remaining.sort(key=lambda a: a["id"])
            remaining[0]["is_default"] = True
    return ok(address)


@router.patch("/{address_id}/default", response_model=ApiResponse[AddressOut], summary="设为默认地址")
def set_default(address_id: int, user: dict = Depends(get_current_user)):
    address = _owned_address(user, address_id)
    _clear_default(user["id"], address_id)
    address["is_default"] = True
    return ok(address)
