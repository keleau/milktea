from fastapi import APIRouter, Depends
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.response import ApiResponse, BizError, ok
from app.db import get_db
from app.deps import get_current_user
from app.models import Address, User
from app.schemas import AddressIn, AddressOut, AddressUpdateIn, ListData
from app.serializers import serialize_address

router = APIRouter(prefix="/addresses", tags=["收货地址"])


def _owned_address(db: Session, user: User, address_id: int) -> Address:
    address = db.get(Address, address_id)
    if address is None:
        raise BizError(1004, "收货地址不存在", 404)
    if address.user_id != user.id:
        raise BizError(1003, "无权操作该地址", 403)
    return address


def _clear_default(db: Session, user_id: int, except_id: int | None = None) -> None:
    statement = update(Address).where(Address.user_id == user_id)
    if except_id is not None:
        statement = statement.where(Address.id != except_id)
    db.execute(statement.values(is_default=False))


@router.get("", response_model=ApiResponse[ListData[AddressOut]], summary="地址列表")
def list_addresses(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    addresses = db.scalars(
        select(Address)
        .where(Address.user_id == user.id)
        .order_by(Address.is_default.desc(), Address.id)
    ).all()
    return ok({"items": [serialize_address(address) for address in addresses]})


@router.post("", response_model=ApiResponse[AddressOut], summary="新增地址")
def create_address(
    payload: AddressIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = (
        db.scalar(
            select(func.count()).select_from(Address).where(Address.user_id == user.id)
        )
        or 0
    )
    is_default = payload.is_default or existing == 0
    if is_default:
        _clear_default(db, user.id)
    address = Address(
        user_id=user.id,
        name=payload.name,
        phone=payload.phone,
        detail=payload.detail,
        is_default=is_default,
    )
    db.add(address)
    db.commit()
    return ok(serialize_address(address))


@router.patch("/{address_id}", response_model=ApiResponse[AddressOut], summary="编辑地址")
def update_address(
    address_id: int,
    payload: AddressUpdateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    address = _owned_address(db, user, address_id)
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("is_default") is True:
        _clear_default(db, user.id, address_id)
    for key, value in changes.items():
        if value is not None:
            setattr(address, key, value)
    db.commit()
    return ok(serialize_address(address))


@router.delete("/{address_id}", response_model=ApiResponse[AddressOut], summary="删除地址")
def delete_address(
    address_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    address = _owned_address(db, user, address_id)
    was_default = address.is_default
    snapshot = serialize_address(address)
    db.delete(address)
    db.flush()
    if was_default:
        remaining = db.scalars(
            select(Address).where(Address.user_id == user.id).order_by(Address.id)
        ).all()
        if remaining:
            remaining[0].is_default = True
    db.commit()
    return ok(snapshot)


@router.patch("/{address_id}/default", response_model=ApiResponse[AddressOut], summary="设为默认地址")
def set_default(
    address_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    address = _owned_address(db, user, address_id)
    _clear_default(db, user.id, address_id)
    address.is_default = True
    db.commit()
    return ok(serialize_address(address))
