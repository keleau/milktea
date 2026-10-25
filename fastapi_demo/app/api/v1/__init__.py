from fastapi import APIRouter

from app.api.v1 import addresses, auth, coupons, member, menu, orders, payments, stores, users

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
