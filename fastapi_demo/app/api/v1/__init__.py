from fastapi import APIRouter

from app.api.v1 import (
    addresses,
    ai,
    auth,
    coupons,
    member,
    menu,
    orders,
    payments,
    staff,
    stores,
    tables,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(stores.router)
api_router.include_router(menu.router)
api_router.include_router(coupons.router)
api_router.include_router(orders.router)
api_router.include_router(payments.router)
api_router.include_router(member.router)
api_router.include_router(addresses.router)
api_router.include_router(tables.router)
api_router.include_router(staff.router)
api_router.include_router(ai.router)
