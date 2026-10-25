from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")

OrderState = Literal["pending_pay", "making", "completed", "cancelled"]
OrderMode = Literal["pickup", "delivery"]
CouponStatus = Literal["unused", "used", "expired", "all"]
RankPeriod = Literal["week", "month"]


class ListData(BaseModel, Generic[T]):
    items: list[T]


class PageData(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class LineOut(BaseModel):
    id: str
    name: str
    tag: str
    en: str
    desc: str
    color: str
    bg: str


class ProductOut(BaseModel):
    id: int
    line_id: str
    name: str
    price: float
    orig_price: float | None = None
    paws: int
    is_hot: bool
    is_new: bool
    desc: str
    image: str
    stock: int
    on_sale: bool


class MenuGroupOut(BaseModel):
    line: LineOut
    products: list[ProductOut]


class MenuData(PageData[ProductOut]):
    groups: list[MenuGroupOut] | None = None


class ToppingOut(BaseModel):
    id: int
    name: str
    price: float


class OptionsOut(BaseModel):
    ice_options: list[str]
    sugar_options: list[str]
    toppings: list[ToppingOut]


class ProductDetailOut(ProductOut):
    line: LineOut
    ice_options: list[str]
    sugar_options: list[str]
    toppings: list[ToppingOut]


class RankItemOut(ProductOut):
    rank: int


class RankData(BaseModel):
    period: RankPeriod
    items: list[RankItemOut]
    new_items: list[ProductOut]


class StoreOut(BaseModel):
    id: int
    name: str
    area: str
    address: str
    lat: float
    lng: float
    distance: int
    status: Literal["open", "resting", "closed"]
    business_hours: str
    making_cups: int
    pack_fee: float
    delivery_fee: float


class UserOut(BaseModel):
    id: int
    nickname: str
    avatar: str
    level: str
    points: int
    balance: float
    coupon_count: int
    created_at: int


class LoginIn(BaseModel):
    code: str = Field(min_length=1, max_length=128)
    nickname: str | None = Field(default=None, max_length=20)
    avatar: str | None = None


class RefreshIn(BaseModel):
    refresh_token: str = Field(min_length=1)


class TokenPairOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


class AuthData(TokenPairOut):
    user: UserOut


class UserPatchIn(BaseModel):
    nickname: str = Field(min_length=1, max_length=20)


class AvatarData(BaseModel):
    avatar: str


class CouponOut(BaseModel):
    id: int
    template_id: int
    title: str
    desc: str
    cut: float
    min_amount: float
    status: Literal["unused", "used", "expired"]
    expire_at: int


class CouponTemplateOut(BaseModel):
    id: int
    title: str
    desc: str
    cut: float
    min_amount: float
    valid_days: int
    claimed: bool = False


class AddressIn(BaseModel):
    name: str = Field(min_length=1, max_length=20)
    phone: str = Field(pattern=r"^1[3-9]\d{9}$")
    detail: str = Field(min_length=1, max_length=120)
    is_default: bool = False


class AddressUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=20)
    phone: str | None = Field(default=None, pattern=r"^1[3-9]\d{9}$")
    detail: str | None = Field(default=None, min_length=1, max_length=120)
    is_default: bool | None = None


class AddressOut(BaseModel):
    id: int
    name: str
    phone: str
    detail: str
    is_default: bool


class OrderItemIn(BaseModel):
    product_id: int
    ice: str
    sugar: str
    topping_ids: list[int] = Field(default_factory=list)
    count: int = Field(ge=1, le=99)


class PricePreviewIn(BaseModel):
    store_id: int
    mode: OrderMode
    coupon_id: int | None = None
    items: list[OrderItemIn] = Field(min_length=1)


class PricePreviewOut(BaseModel):
    subtotal: float
    pack_fee: float
    coupon_cut: float
    total: float
    usable_coupons: list[CouponOut]
    estimated_ready_minutes: int


class OrderCreateIn(PricePreviewIn):
    address_id: int | None = None
    remark: str = Field(default="", max_length=100)


class OrderItemOut(BaseModel):
    product_id: int
    name: str
    image: str
    line_id: str
    ice: str
    sugar: str
    topping_ids: list[int]
    topping_names: str
    count: int
    unit_price: float
    amount: float


class OrderAddressOut(BaseModel):
    id: int | None = None
    name: str
    phone: str
    detail: str
    is_default: bool


class ReviewIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    content: str = Field(default="", max_length=200)


class ReviewOut(BaseModel):
    rating: int
    content: str
    created_at: int


class OrderOut(BaseModel):
    out_trade_no: str
    state: OrderState
    state_text: str
    store_id: int
    store_name: str
    mode: OrderMode
    mode_text: str
    items: list[OrderItemOut]
    subtotal: float
    pack_fee: float
    coupon_cut: float
    total: float
    pick_code: str | None = None
    address: OrderAddressOut | None = None
    remark: str
    create_time: int
    pay_time: int | None = None
    finish_time: int | None = None
    review: ReviewOut | None = None


class OrderCountsOut(BaseModel):
    pending_pay: int
    making: int
    completed: int
    cancelled: int


class RepeatData(BaseModel):
    store_id: int
    store_name: str
    mode: OrderMode
    mode_text: str
    address_id: int | None = None
    remark: str
    items: list[OrderItemIn]


class PrepayIn(BaseModel):
    out_trade_no: str = Field(min_length=1)


class PrepayOut(BaseModel):
    timeStamp: str
    nonceStr: str
    package: str
    signType: str
    paySign: str


class PaymentNotifyIn(BaseModel):
    out_trade_no: str = Field(min_length=1)
    transaction_id: str | None = None
    result_code: str = "SUCCESS"


class PaymentNotifyData(BaseModel):
    out_trade_no: str
    state: OrderState
    state_text: str


class PaymentStatusOut(BaseModel):
    out_trade_no: str
    state: OrderState
    state_text: str
    paid: bool
    transaction_id: str | None = None
    pay_time: int | None = None


class MemberProfileOut(BaseModel):
    level: str
    points: int
    balance: float
    growth: int
    next_level: str | None = None
    next_level_growth: int | None = None
    progress: float
    coupon_count: int


class PointsLogOut(BaseModel):
    id: int
    title: str
    points: int
    type: str
    created_at: int


class ExchangeItemOut(BaseModel):
    id: int
    title: str
    cost: int
    type: str


class ExchangeIn(BaseModel):
    item_id: int


class ExchangeData(BaseModel):
    points: int
    coupon: CouponOut | None = None
    message: str


class FavoriteOut(BaseModel):
    product_id: int
    favorited: bool
