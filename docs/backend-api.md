# 四猫茶学园 · 后端接口文档（FastAPI）

> 依据当前小程序前端（`pages/` + `common/data/`）的数据模型与交互整理，用于替换本地 storage 演示数据。
> 所有接口默认返回 JSON，时间统一为 **毫秒时间戳**（与前端 `Date.now()` 一致），金额单位 **元（float，保留 2 位）**。

---

## 1. 基础约定

### 1.1 基础信息

| 项 | 值 |
|---|---|
| Base URL（开发） | `http://127.0.0.1:8000/api/v1` |
| Base URL（生产） | `https://api.simaotea.com/api/v1` |
| 文档 | `/docs`（Swagger UI）、`/redoc` |
| 编码 | `application/json; charset=utf-8` |
| 鉴权 | `Authorization: Bearer <access_token>` |
| 图片 | 后端返回完整 URL（CDN），前端不再拼接本地路径 |

### 1.2 统一响应

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

- `code = 0` 表示成功；非 0 见第 8 章错误码。
- 分页数据统一结构：

```json
{
  "code": 0,
  "message": "ok",
  "data": { "items": [], "total": 0, "page": 1, "page_size": 20 }
}
```

### 1.3 鉴权流程

1. 小程序 `uni.login()` 拿到 `code`
2. `POST /auth/wx-login`，后端调 `code2session` 换 `openid`
3. 返回 `access_token`（JWT，7 天）与 `refresh_token`（30 天）
4. 之后所有需登录接口带 `Authorization: Bearer <access_token>`
5. `401` 时前端用 `refresh_token` 换新 token

### 1.4 FastAPI 约定

- 每个模块一个 `APIRouter`，`prefix="/orders"` 等
- 统一响应用 `response_model=ApiResponse[OrderOut]`（泛型 Pydantic 模型）
- 鉴权用依赖：`current_user: User = Depends(get_current_user)`
- 金额计算全部在后端完成，前端传参只传「商品 ID + 规格 + 数量 + 券 ID」，**不信任前端价格**
- 下单接口支持 `Idempotency-Key` 请求头，防重复提交

---

## 2. 数据模型

### 2.1 User

| 字段 | 类型 | 说明 |
|---|---|---|
| id | int | 用户 ID |
| openid | string | 微信 openid（不下发前端） |
| nickname | string | 昵称，默认「猫友1234」 |
| avatar | string | 头像 URL |
| level | string | 等级，如 `V2 银牌猫评员` |
| points | int | 积分 |
| balance | float | 余额 |
| coupon_count | int | 可用券数量 |
| created_at | int | 注册时间 |

```json
{
  "id": 1001,
  "nickname": "猫友1234",
  "avatar": "https://cdn.simaotea.com/avatar/1001.jpg",
  "level": "V2 银牌猫评员",
  "points": 320,
  "balance": 8.5,
  "coupon_count": 2,
  "created_at": 1760000000000
}
```

### 2.2 Store

| 字段 | 类型 | 说明 |
|---|---|---|
| id | int | 门店 ID |
| name | string | 门店全名 |
| area | string | 位置描述，如 `星悦广场 1F` |
| address | string | 详细地址 |
| lat / lng | float | 经纬度 |
| distance | int | 距离（米，按用户坐标计算） |
| status | string | `open` / `resting` / `closed` |
| business_hours | string | `10:00-22:00` |
| making_cups | int | 当前制作中杯数（展示用） |
| pack_fee | float | 自取打包费 |
| delivery_fee | float | 配送费 |

### 2.3 ProductLine

| 字段 | 类型 | 说明 |
|---|---|---|
| id | string | `buchi` / `sakamoto` / `tom` / `tama` |
| name | string | 系列全名 |
| tag | string | 短标签（醇厚/纯选/甜心/清爽） |
| en | string | 英文名 |
| desc | string | 一句话描述 |
| color | string | 主题色 |
| bg | string | 浅色底 |

### 2.4 Product

| 字段 | 类型 | 说明 |
|---|---|---|
| id | int | 商品 ID |
| line_id | string | 所属产品线 |
| name | string | 名称 |
| price | float | 现价（会员价） |
| orig_price | float? | 原价，有值表示参与会员价 |
| paws | int | 猫评分 1~5 |
| is_hot | bool | 招牌 |
| is_new | bool | 新品 |
| desc | string | 描述 |
| image | string | 图片 URL |
| stock | int | 库存，`0` 表示售罄 |
| on_sale | bool | 是否上架 |

### 2.5 Spec / Topping

```json
{
  "ice_options": ["正常冰", "少冰", "去冰", "热饮"],
  "sugar_options": ["全糖", "七分糖", "五分糖", "三分糖", "不加糖"],
  "toppings": [
    { "id": 1, "name": "珍珠", "price": 1.0 },
    { "id": 2, "name": "椰果", "price": 1.0 },
    { "id": 3, "name": "布丁", "price": 2.0 },
    { "id": 4, "name": "芋圆", "price": 2.0 },
    { "id": 5, "name": "芝士奶盖", "price": 3.0 }
  ]
}
```

### 2.6 Coupon

| 字段 | 类型 | 说明 |
|---|---|---|
| id | int | 用户券实例 ID |
| template_id | int | 券模板 ID |
| title | string | 券名 |
| cut | float | 减免金额 |
| min_amount | float | 门槛金额 |
| status | string | `unused` / `used` / `expired` |
| expire_at | int | 过期时间 |

```json
{
  "id": 501,
  "template_id": 1,
  "title": "新猫见面礼",
  "cut": 3.0,
  "min_amount": 15.0,
  "status": "unused",
  "expire_at": 1762592000000
}
```

### 2.7 Order

| 字段 | 类型 | 说明 |
|---|---|---|
| out_trade_no | string | 订单号，`CAT + 时间戳 + 3 位随机` |
| state | string | `pending_pay` / `making` / `completed` / `cancelled` |
| state_text | string | 中文状态，前端直接展示 |
| store_id | int | 门店 ID |
| store_name | string | 门店名 |
| mode | string | `pickup`（自取）/ `delivery`（外卖） |
| items | OrderItem[] | 订单明细 |
| subtotal | float | 商品小计（含小料） |
| pack_fee | float | 打包费 / 配送费 |
| coupon_cut | float | 券抵扣 |
| total | float | 实付 |
| pick_code | string | 取餐码（自取时） |
| address | Address? | 配送地址（外卖时） |
| remark | string | 备注 |
| create_time | int | 下单时间 |
| pay_time | int? | 支付时间 |
| finish_time | int? | 完成时间 |
| review | Review? | 评价（完成后可选） |

### 2.8 OrderItem

| 字段 | 类型 | 说明 |
|---|---|---|
| product_id | int | 商品 ID |
| name | string | 商品快照名 |
| image | string | 商品快照图 |
| line_id | string | 产品线 |
| ice | string | 冰度 |
| sugar | string | 糖度 |
| topping_ids | int[] | 小料 ID |
| topping_names | string | `珍珠+椰果`（展示用） |
| count | int | 数量 |
| unit_price | float | 单价（含小料） |
| amount | float | 小计 |

### 2.9 Address

| 字段 | 类型 | 说明 |
|---|---|---|
| id | int | 地址 ID |
| name | string | 联系人 |
| phone | string | 手机号 |
| detail | string | 详细地址 |
| is_default | bool | 默认地址 |

---

## 3. 接口清单

### 3.1 认证 / 用户

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| POST | `/auth/wx-login` | 否 | 微信 code 登录，返回 token |
| POST | `/auth/refresh` | 否 | 刷新 access_token |
| GET | `/users/me` | 是 | 当前用户信息 |
| PATCH | `/users/me` | 是 | 修改昵称 |
| POST | `/users/me/avatar` | 是 | 上传头像（multipart） |

**POST /auth/wx-login**

```json
// 请求
{ "code": "081Kx...", "nickname": "猫友1234", "avatar": "" }
// 响应 data
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "expires_in": 604800,
  "user": { "id": 1001, "nickname": "猫友1234", "level": "V1 见习猫评员", "points": 0, "balance": 0, "coupon_count": 2 }
}
```

### 3.2 门店

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| GET | `/stores?lat=&lng=` | 否 | 门店列表，按距离升序 |
| GET | `/stores/{store_id}` | 否 | 门店详情（含制作中杯数、营业状态） |

```json
// GET /stores?lat=31.23&lng=121.47 → data.items
[
  {
    "id": 1,
    "name": "四猫茶学园·星悦广场店",
    "area": "星悦广场 1F",
    "address": "浦东新区世纪大道 100 号",
    "distance": 205,
    "status": "resting",
    "business_hours": "10:00-22:00",
    "making_cups": 4,
    "pack_fee": 1.0,
    "delivery_fee": 4.0
  }
]
```

### 3.3 菜单

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| GET | `/menu/lines` | 否 | 四条产品线 |
| GET | `/menu/products` | 可选 | 商品列表，支持筛选 |
| GET | `/menu/products/{id}` | 否 | 商品详情 + 规格选项 |
| GET | `/menu/options` | 否 | 全局冰/糖/小料选项 |
| GET | `/menu/rank?period=week` | 否 | 人气榜（对应 rank 页） |

**GET /menu/products** Query：

| 参数 | 类型 | 说明 |
|---|---|---|
| line_id | string? | 按产品线过滤 |
| tab | string? | `classic` / `member` / `new` / `mine`（我的常点） |
| keyword | string? | 名称模糊搜索 |
| store_id | int? | 按门店过滤售罄状态 |
| page / page_size | int | 默认 1 / 20 |

> 无 `line_id` 时返回按产品线分组的完整菜单（对应前端连续滚动结构）：
> `data.items = [{ line: {...}, products: [...] }, ...]`

```json
// GET /menu/products?tab=new 简化响应
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": 3,
        "line_id": "buchi",
        "name": "提拉米苏厚乳茶",
        "price": 16.0,
        "orig_price": null,
        "paws": 4,
        "is_hot": false,
        "is_new": true,
        "desc": "可可粉轻撒，奶油顶配厚乳茶底",
        "image": "https://cdn.simaotea.com/products/3.jpg",
        "stock": 50,
        "on_sale": true
      }
    ],
    "total": 3,
    "page": 1,
    "page_size": 20
  }
}
```

**GET /menu/products/{id}** 额外返回：

```json
{
  "line": { "id": "buchi", "name": "布奇·醇厚系列", "tag": "醇厚", "color": "#8B5E3C", "bg": "#F3EAE0" },
  "ice_options": ["正常冰", "少冰", "去冰", "热饮"],
  "sugar_options": ["全糖", "七分糖", "五分糖", "三分糖", "不加糖"],
  "toppings": [{ "id": 1, "name": "珍珠", "price": 1.0 }]
}
```

### 3.4 优惠券

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| GET | `/coupons/templates` | 否 | 券包中心可领券模板 |
| POST | `/coupons/{template_id}/claim` | 是 | 领取券 |
| GET | `/users/me/coupons?status=` | 是 | 我的券（unused/used/expired/all） |
| GET | `/coupons/usable?amount=&store_id=` | 是 | 当前金额可用券（结算页） |

```json
// GET /coupons/usable?amount=18 → data.items
[
  { "id": 501, "template_id": 1, "title": "新猫见面礼", "cut": 3.0, "min_amount": 15.0, "status": "unused", "expire_at": 1762592000000 }
]
```

### 3.5 订单

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| POST | `/orders/price-preview` | 可选 | 试算金额（小计/打包费/券/合计） |
| POST | `/orders` | 是 | 创建订单 |
| GET | `/orders?state=` | 是 | 订单列表（分页） |
| GET | `/orders/counts` | 是 | 各状态数量（我的页角标） |
| GET | `/orders/{out_trade_no}` | 是 | 订单详情 |
| POST | `/orders/{out_trade_no}/cancel` | 是 | 取消订单（仅待支付/制作中可取消） |
| POST | `/orders/{out_trade_no}/repeat` | 是 | 再来一单（返回可直接下单的草稿） |
| POST | `/orders/{out_trade_no}/review` | 是 | 评价（完成后） |

**POST /orders/price-preview**

```json
// 请求
{
  "store_id": 1,
  "mode": "pickup",
  "coupon_id": 501,
  "items": [
    { "product_id": 1, "ice": "少冰", "sugar": "五分糖", "topping_ids": [1, 3], "count": 2 }
  ]
}
// 响应 data
{
  "subtotal": 38.0,
  "pack_fee": 1.0,
  "coupon_cut": 3.0,
  "total": 36.0,
  "usable_coupons": [],
  "estimated_ready_minutes": 8
}
```

**POST /orders**

```json
// 请求（结构与 price-preview 相同，另加地址/备注/幂等键）
{
  "store_id": 1,
  "mode": "delivery",
  "address_id": 12,
  "coupon_id": 501,
  "remark": "少放冰块",
  "items": [
    { "product_id": 1, "ice": "少冰", "sugar": "五分糖", "topping_ids": [1], "count": 1 }
  ]
}
// 响应 data
{
  "out_trade_no": "CAT1760000000000123",
  "state": "pending_pay",
  "state_text": "待支付",
  "total": 17.0,
  "pick_code": null,
  "create_time": 1760000000000
}
```

> `pick_code` 在支付成功、进入制作中时生成（4 位，`10~99` + 后 3 位时间）。

**GET /orders** 支持 `state=pending_pay|making|completed|cancelled`，不传返回全部。响应项结构见 2.7。

**GET /orders/counts**

```json
{ "pending_pay": 1, "making": 2, "completed": 8, "cancelled": 0 }
```

### 3.6 支付

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| POST | `/payments/wechat/prepay` | 是 | 统一下单，返回小程序支付参数 |
| POST | `/payments/wechat/notify` | 否（微信回调） | 支付结果通知，验签后更新订单 |
| GET | `/payments/{out_trade_no}` | 是 | 查询支付状态 |

```json
// POST /payments/wechat/prepay 请求
{ "out_trade_no": "CAT1760000000000123" }
// 响应 data（直接传给 uni.requestPayment）
{
  "timeStamp": "1760000000",
  "nonceStr": "5K8264ILTKCH16CQ",
  "package": "prepay_id=wx201...",
  "signType": "RSA",
  "paySign": "..."
}
```

> 回调成功后：订单 `pending_pay → making`，生成 `pick_code`，写入 `pay_time`，给用户加积分。

### 3.7 会员

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| GET | `/member/profile` | 是 | 等级、积分、余额、成长值、升级进度 |
| GET | `/member/points/logs` | 是 | 积分明细 |
| POST | `/member/points/exchange` | 是 | 积分兑换（券/小料） |

### 3.8 收货地址

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| GET | `/addresses` | 是 | 地址列表 |
| POST | `/addresses` | 是 | 新增 |
| PATCH | `/addresses/{id}` | 是 | 编辑 |
| DELETE | `/addresses/{id}` | 是 | 删除 |
| PATCH | `/addresses/{id}/default` | 是 | 设为默认 |

### 3.9 常点 / 收藏

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| GET | `/users/me/favorites` | 是 | 我的常点（按历史下单频次推荐） |
| POST | `/users/me/favorites/{product_id}` | 是 | 收藏 |
| DELETE | `/users/me/favorites/{product_id}` | 是 | 取消收藏 |

---

## 4. 订单状态机

```
pending_pay ──支付成功──> making ──制作完成──> completed
     │                       │
     ├──15 分钟未支付──> cancelled
     └──用户取消──────> cancelled
```

| 状态 | 中文 | 前端展示 | 可操作 |
|---|---|---|---|
| pending_pay | 待支付 | 去支付 / 取消 | 支付、取消 |
| making | 制作中 | 取餐码、预计时间 | 取消（视门店） |
| completed | 已完成 | 取餐码、再来一单、评价 | 评价、再来一单 |
| cancelled | 已取消 | - | 再来一单 |

> 建议用定时任务（APScheduler / Celery beat）扫描 `pending_pay` 超时订单自动取消，并释放库存。

---

## 5. 计费规则

```
商品单价 = 饮品价 + Σ 小料价
小计     = Σ(商品单价 × 数量)
打包费   = 自取 1 元 / 外卖 4 元（按门店配置）
券抵扣   = 满足门槛的券中用户选中的一张（不叠加）
合计     = max(0, 小计 + 打包费 - 券抵扣)
```

- 会员价：`orig_price` 存在即展示划线价，`price` 为会员实付价。
- 券门槛按 **小计** 判断（不含打包费）。
- 下单时把商品名/图/价写入订单快照，后续商品改价不影响历史订单。

---

## 6. FastAPI 建议实现

### 6.1 目录结构

```
backend/
├── app/
│   ├── main.py                 # FastAPI 实例、CORS、异常处理、路由注册
│   ├── core/
│   │   ├── config.py           # pydantic-settings 读取 .env
│   │   ├── security.py         # JWT 签发/校验
│   │   └── response.py         # ApiResponse 泛型、业务异常
│   ├── api/
│   │   ├── deps.py             # get_db / get_current_user
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── stores.py
│   │       ├── menu.py
│   │       ├── coupons.py
│   │       ├── orders.py
│   │       ├── payments.py
│   │       └── addresses.py
│   ├── models/                 # SQLAlchemy 2.0 ORM
│   ├── schemas/                # Pydantic v2
│   └── services/               # 价格计算、库存、订单状态机、微信支付
├── alembic/
└── pyproject.toml
```

### 6.2 关键依赖

```python
class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "ok"
    data: T | None = None

# 统一业务异常
class BizError(Exception):
    def __init__(self, code: int, message: str, status_code: int = 400):
        ...

@app.exception_handler(BizError)
async def biz_error_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message, "data": None},
    )
```

### 6.3 下单事务建议

1. `SELECT ... FOR UPDATE` 锁定商品库存
2. 重新计算价格（不信任前端）
3. 校验券状态与门槛，标记券为「锁定」
4. 写订单 + 明细快照
5. 提交事务；支付回调中扣库存、核销券、加积分
6. 幂等：`Idempotency-Key` 存 Redis（TTL 10 分钟），重复请求直接返回首单结果

### 6.4 微信支付

- 使用微信支付 APIv3，`signType=RSA`
- 回调必须验签 + 解密 `resource`
- 回调处理要幂等（以 `out_trade_no` + `transaction_id` 去重）

---

## 7. 前端页面 → 接口映射

| 页面 | 主要接口 |
|---|---|
| 首页 `pages/index` | `/menu/lines`、`/menu/products?tab=classic`、`/coupons/templates`、`/stores` |
| 点单页 `pages/menu` | `/stores`、`/menu/products`、`/menu/options`、`/coupons/usable` |
| 详情页 `pages/detail` | `/menu/products/{id}`、`/users/me/favorites` |
| 结算页 `pages/checkout` | `/orders/price-preview`、`/coupons/usable`、`/orders`、`/addresses` |
| 订单列表 `pages/order/index` | `/orders/counts`、`/orders?state=` |
| 订单详情 `pages/order/order` | `/orders/{no}`、`/payments/{no}`、`/orders/{no}/cancel`、`/orders/{no}/review` |
| 我的 `pages/user` | `/users/me`、`/member/profile`、`/orders/counts`、`/users/me/coupons` |
| 排行榜 `pages/rank` | `/menu/rank?period=week` |

---

## 8. 错误码

| code | HTTP | 含义 |
|---|---|---|
| 0 | 200 | 成功 |
| 1001 | 400 | 参数校验失败 |
| 1002 | 401 | 未登录 / token 无效 |
| 1003 | 403 | 无权限（操作他人订单等） |
| 1004 | 404 | 资源不存在 |
| 2001 | 400 | 商品已下架 |
| 2002 | 409 | 库存不足 |
| 2003 | 409 | 商品在该门店售罄 |
| 3001 | 400 | 优惠券不可用（门槛不足） |
| 3002 | 409 | 优惠券已使用或过期 |
| 3003 | 409 | 优惠券重复领取 |
| 4001 | 409 | 订单状态不允许该操作 |
| 4002 | 409 | 订单已支付，请勿重复支付 |
| 4003 | 410 | 订单超时已取消 |
| 5001 | 500 | 微信支付下单失败 |
| 5002 | 400 | 支付回调验签失败 |
| 9000 | 500 | 服务内部错误 |

### 请求示例（校验失败）

```json
{
  "code": 1001,
  "message": "items 不能为空",
  "data": null
}
```

---

## 9. 与当前前端的差异说明

| 现状 | 接入后端后 |
|---|---|
| `common/data/drinks.js` 写死 12 款饮品 | 改为 `/menu/products` 拉取，缓存到 pinia |
| `common/data/shop.js` 静态会员/券 | `/users/me`、`/users/me/coupons` |
| `common/data/orders.js` storage 读写 | `/orders` 系列接口，保留本地草稿缓存 |
| 结算 `submitOrder` 直接生成订单 | `/orders` → `/payments/wechat/prepay` → `uni.requestPayment` |
| 订单状态仅前端本地修改 | 服务端状态机 + 支付回调驱动 |
| 门店为页面内静态数组 | `/stores`，配合 `uni.getLocation` 传经纬度 |
| 图片为本地 `/static/...` | 后端/CDN 完整 URL，前端无需改模板（`:src` 直接用） |

> 建议接入顺序：门店 → 菜单 → 用户/登录 → 券 → 下单试算 → 支付 → 订单状态，先做到「只读接口」跑通，再替换写操作。
