# 四猫茶学园 · 后端接口文档（FastAPI）

> 依据当前小程序前端（`pages/` + `common/data/`）的数据模型与交互整理，用于替换本地 storage 演示数据。
> 所有接口默认返回 JSON，时间统一为 **毫秒时间戳**（与前端 `Date.now()` 一致），金额单位 **元（float，保留 2 位）**。
> 字段、枚举与表结构的唯一数据契约见根目录 [`docs/data-dictionary.md`](../../docs/data-dictionary.md)；数据库脚本在 [`fastapi_demo/database/`](../../fastapi_demo/database/)。

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
| 图片 | 后端返回完整 URL（生产用 CDN；demo 为 `http://127.0.0.1:8000/static/...`） |

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

- 404/405 等框架错误也保持同一结构，例如 `{"code": 1004, "message": "Not Found", "data": null}`。

### 1.3 鉴权流程

1. 小程序 `uni.login()` 拿到 `code`
2. `POST /auth/wx-login`，后端调 `code2session` 换 `openid`
3. 返回 `access_token`（7 天）与 `refresh_token`（30 天）
4. 之后所有需登录接口带 `Authorization: Bearer <access_token>`
5. `401` 时前端用 `refresh_token` 换新 token

> token 对前端是不透明字符串：生产建议 JWT，`fastapi_demo` 用 HMAC-SHA256 自签，用法完全一致。

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
| desc | string | 展示文案，如「满15减3」 |
| cut | float | 减免金额 |
| min_amount | float | 门槛金额 |
| status | string | `unused` / `used` / `expired` |
| expire_at | int | 过期时间 |

```json
{
  "id": 501,
  "template_id": 1,
  "title": "新猫见面礼",
  "desc": "满15减3",
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
| mode | string | `pickup`（自取）/ `delivery`（外送） |
| mode_text | string | 中文取餐方式，前端可直接展示 |
| items | OrderItem[] | 订单明细 |
| subtotal | float | 商品小计（含小料） |
| pack_fee | float | 打包费 / 配送费 |
| coupon_cut | float | 券抵扣 |
| total | float | 实付 |
| pick_code | string | 取餐码（自取时） |
| table_no | string? | 堂食桌号（扫码点餐时，如 `A01`；仅自取单可有） |
| address | Address? | 配送地址（外送时） |
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

### 2.10 Review

| 字段 | 类型 | 说明 |
|---|---|---|
| rating | int | 1~5 爪 |
| content | string | 评价内容，可为空 |
| created_at | int | 评价时间 |

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
{ "code": "081Kx...", "mock_id": "device-...", "nickname": "猫友1234", "avatar": "" }
// 响应 data
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 604800,
  "user": {
    "id": 1001,
    "nickname": "猫友1234",
    "avatar": "https://cdn.simaotea.com/avatar/1001.jpg",
    "level": "V1 见习猫评员",
    "points": 0,
    "balance": 0,
    "coupon_count": 0,
    "created_at": 1760000000000
  }
}
```

> 新用户默认 V1、0 积分、0 券，可到券包中心领取。演示环境支持用 `code = "demo"` 登录预置会员（id 1001、V2、320 积分、2 张券）。后端 `.env` 配好 `WECHAT_APPID` + `WECHAT_SECRET` 时调用微信 `code2session` 换真实 openid；未配置时按 `mock_id` 哈希生成稳定模拟 openid，不带 `mock_id` 才退回按 code 哈希。

**PATCH /users/me** 请求 `{ "nickname": "布奇头号粉丝" }`，响应 data 为更新后的 `User`。

**POST /users/me/avatar** 使用 `multipart/form-data`，字段名 `file`，支持 jpg/png/webp、最大 2MB；响应 data：

```json
{ "avatar": "http://127.0.0.1:8000/static/avatars/user_1001_1760000000000.jpg" }
```

### 3.2 门店

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| GET | `/stores?lat=&lng=` | 否 | 门店列表，按距离升序 |
| GET | `/stores/{store_id}` | 否 | 门店详情（含制作中杯数、营业状态） |

```json
// GET /stores?lat=31.23&lng=121.47
{
  "code": 0,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": 1,
        "name": "四猫茶学园·星悦广场店",
        "area": "星悦广场 1F",
        "address": "浦东新区世纪大道 100 号",
        "lat": 31.232,
        "lng": 121.475,
        "distance": 205,
        "status": "resting",
        "business_hours": "10:00-22:00",
        "making_cups": 4,
        "pack_fee": 1.0,
        "delivery_fee": 4.0
      }
    ]
  }
}
```

> 传 `lat`/`lng` 时按坐标重新计算 `distance`（米）并按距离升序；不传则使用门店预置距离。

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
| group_by_line | bool? | 默认 `false`；为 `true` 时额外返回 `data.groups`，此时不分页 |

> 需要按产品线分组时传 `group_by_line=true`（对应点单页连续滚动结构）：
> `data.groups = [{ line: {...}, products: [...] }, ...]`；`data.items` 仍返回扁平列表，且忽略分页。
> `tab=mine` 需要登录，按历史下单频次 + 收藏返回。

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

> 示例中为生产 CDN 地址；`fastapi_demo` 返回 `http://127.0.0.1:8000/static/images/drink_{id}.jpg`，前端同样直接用于 `:src`。

**GET /menu/products/{id}** 额外返回：

```json
{
  "line": { "id": "buchi", "name": "布奇·醇厚系列", "tag": "醇厚", "color": "#8B5E3C", "bg": "#F3EAE0" },
  "ice_options": ["正常冰", "少冰", "去冰", "热饮"],
  "sugar_options": ["全糖", "七分糖", "五分糖", "三分糖", "不加糖"],
  "toppings": [{ "id": 1, "name": "珍珠", "price": 1.0 }]
}
```

**GET /menu/rank?period=week** 响应 data：

```json
{
  "period": "week",
  "items": [
    { "rank": 1, "id": 1, "name": "黑糖波波厚奶茶", "paws": 5, "price": 14.0, "image": "https://cdn.simaotea.com/products/1.jpg" }
  ],
  "new_items": [
    { "id": 3, "name": "提拉米苏厚乳茶", "is_new": true, "price": 16.0 }
  ]
}
```

> `items` 为商品字段（见 2.4）加 `rank`，按爪评分降序；`new_items` 为新品横向卡片数据。演示中 `week` / `month` 排序一致。

### 3.4 优惠券

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| GET | `/coupons/templates` | 否 | 券包中心可领券模板 |
| POST | `/coupons/{template_id}/claim` | 是 | 领取券 |
| GET | `/users/me/coupons?status=` | 是 | 我的券（unused/used/expired/all） |
| GET | `/coupons/usable?amount=&store_id=` | 是 | 当前金额可用券（结算页） |

**GET /coupons/templates**（可选登录；登录后返回 `claimed`）

```json
// data.items
[
  { "id": 1, "title": "新猫见面礼", "desc": "满15减3", "cut": 3.0, "min_amount": 15.0, "valid_days": 30, "claimed": false }
]
```

**GET /coupons/usable?amount=18**

```json
// data.items
[
  { "id": 501, "template_id": 1, "title": "新猫见面礼", "desc": "满15减3", "cut": 3.0, "min_amount": 15.0, "status": "unused", "expire_at": 1762592000000 }
]
```

> 只返回 `amount >= min_amount`、未使用、未过期的券；已被其他未完成订单锁定的券不会出现，重复使用会返回 `3004`。`claim` 成功返回单张 `Coupon`，同一模板重复领取返回 `3003`。

### 3.5 订单

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| POST | `/orders/price-preview` | 可选 | 试算金额（小计/打包费/券/合计） |
| POST | `/orders` | 是 | 创建订单 |
| GET | `/orders?state=` | 是 | 订单列表（分页） |
| GET | `/orders/counts` | 是 | 各状态数量（我的页角标） |
| GET | `/orders/{out_trade_no}` | 是 | 订单详情 |
| POST | `/orders/{out_trade_no}/cancel` | 是 | 取消订单（仅待支付/制作中可取消） |
| POST | `/orders/{out_trade_no}/complete` | 是 | 完成订单（演示用：模拟门店出杯） |
| POST | `/orders/{out_trade_no}/repeat` | 是 | 再来一单（返回可直接下单的草稿） |
| POST | `/orders/{out_trade_no}/review` | 是 | 评价（完成后） |
| GET | `/orders/{out_trade_no}/pickup-qr` | 是 | 取餐二维码（data URI，制作中/已完成可取） |

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
  "subtotal": 34.0,
  "pack_fee": 1.0,
  "coupon_cut": 3.0,
  "total": 32.0,
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
  "address_id": 1,
  "coupon_id": 501,
  "remark": "少放冰块",
  "items": [
    { "product_id": 1, "ice": "少冰", "sugar": "五分糖", "topping_ids": [1], "count": 1 }
  ]
}
// 响应 data（完整订单对象，字段见 2.7 / 2.8）
{
  "out_trade_no": "CAT1760000000000123",
  "state": "pending_pay",
  "state_text": "待支付",
  "store_id": 1,
  "store_name": "四猫茶学园·星悦广场店",
  "mode": "delivery",
  "mode_text": "外送",
  "items": [
    {
      "product_id": 1,
      "name": "黑糖波波厚奶茶",
      "image": "http://127.0.0.1:8000/static/images/drink_1.jpg",
      "line_id": "buchi",
      "ice": "少冰",
      "sugar": "五分糖",
      "topping_ids": [1],
      "topping_names": "珍珠",
      "count": 1,
      "unit_price": 15.0,
      "amount": 15.0
    }
  ],
  "subtotal": 15.0,
  "pack_fee": 4.0,
  "coupon_cut": 3.0,
  "total": 16.0,
  "pick_code": null,
  "address": { "id": 1, "name": "猫友", "phone": "13800000000", "detail": "XX 路 1 号", "is_default": true },
  "remark": "少放冰块",
  "create_time": 1760000000000,
  "pay_time": null,
  "finish_time": null,
  "review": null
}
```

> 请求头 `Idempotency-Key` 可选，建议结算页生成 UUID；同一用户 10 分钟内重复提交相同 key 会直接返回首单，不会重复建单/锁券。
> `pick_code` 在支付成功、进入制作中时生成（5 位数字：`10~99` + 时间戳后 3 位）。
> 配送单（`mode=delivery`）必须传 `address_id`，否则返回 `1001`。
> 桌码点餐时请求加 `"table_no": "A01"`：桌号必须属于该门店且只允许自取单，否则返回 `1004`（桌号不存在）/`1001`（堂食单选了外送）。`price-preview` 不需要传 `table_no`。
> 订单中的 `address` 是下单时的快照。若用户之后删除该地址，`address.id` 返回 `null`，但 `name/phone/detail` 仍保留；`repeat` 也不会再带回已删除的 `address_id`。

**GET /orders** 支持 `state=pending_pay|making|completed|cancelled`，不传返回全部。响应项结构见 2.7。

**GET /orders/counts**

```json
{ "pending_pay": 1, "making": 2, "completed": 8, "cancelled": 0 }
```

**POST /orders/{out_trade_no}/repeat** 响应 data（可直接用于结算页草稿）：

```json
{
  "store_id": 1,
  "store_name": "四猫茶学园·星悦广场店",
  "mode": "pickup",
  "mode_text": "自取",
  "address_id": null,
  "remark": "",
  "items": [
    { "product_id": 1, "ice": "少冰", "sugar": "五分糖", "topping_ids": [1], "count": 1 }
  ]
}
```

**POST /orders/{out_trade_no}/review**

```json
// 请求（仅 completed 状态可评价）
{ "rating": 5, "content": "猫爪拉花很可爱" }
// 响应 data
{ "rating": 5, "content": "猫爪拉花很可爱", "created_at": 1760000000000 }
```

> `cancel` / `complete` 均返回完整订单对象；`review` 返回评价对象。非 `completed` 订单评价返回 `4001`。

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

**GET /payments/{out_trade_no}** 响应 data：

```json
{
  "out_trade_no": "CAT1760000000000123",
  "state": "making",
  "state_text": "制作中",
  "paid": true,
  "transaction_id": "MOCK1760000005000",
  "pay_time": 1760000005000
}
```

> 回调成功后：订单 `pending_pay → making`，生成 `pick_code`，写入 `pay_time`，给用户加积分；对已支付订单重复回调不报错。
> **演示环境**：`prepay` 只返回模拟支付参数，`notify` 不验签、直接置为支付成功（请求体 `{ "out_trade_no": "...", "transaction_id": "..." }`）。未接入真实微信支付时，可让前端在 `uni.requestPayment` 后直接调用该回调。

### 3.7 会员

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| GET | `/member/profile` | 是 | 等级、积分、余额、成长值、升级进度 |
| GET | `/member/points/logs` | 是 | 积分明细（分页） |
| GET | `/member/points/items` | 是 | 积分兑换商品列表 |
| POST | `/member/points/exchange` | 是 | 积分兑换（券/小料） |

**GET /member/profile** 响应 data：

```json
{
  "level": "V2 银牌猫评员",
  "points": 320,
  "balance": 8.5,
  "growth": 320,
  "next_level": "V3 金牌猫评员",
  "next_level_growth": 800,
  "progress": 0.2,
  "coupon_count": 2
}
```

> 等级阈值：V1 `0` / V2 `200` / V3 `800` / V4 `2000`；`growth` 当前等于累计积分，`progress` 为当前等级到下一等级的进度（0~1，最高等级为 1）。

**GET /member/points/logs?page=1&page_size=20** 响应 data：

```json
{
  "items": [
    { "id": 1, "title": "新会员注册礼", "points": 20, "type": "system", "created_at": 1760000000000 }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

**GET /member/points/items** 响应 data：

```json
{
  "items": [
    { "id": 1, "title": "¥3 优惠券", "cost": 100, "type": "coupon" },
    { "id": 2, "title": "¥5 优惠券", "cost": 200, "type": "coupon" }
  ]
}
```

**POST /member/points/exchange**

```json
// 请求
{ "item_id": 1 }
// 响应 data
{
  "points": 220,
  "coupon": { "id": 503, "template_id": 1, "title": "新猫见面礼", "desc": "满15减3", "cut": 3.0, "min_amount": 15.0, "status": "unused", "expire_at": 1762592000000 },
  "message": "兑换成功"
}
```

> 积分不足返回 `6001`；兑换券会同时发放到用户券包。

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

```json
// GET /users/me/favorites → data.items（Product 数组，按常点频次排序）
[
  { "id": 1, "line_id": "buchi", "name": "黑糖波波厚奶茶", "price": 14.0, "orig_price": 17.0, "paws": 5, "is_hot": true, "is_new": false, "desc": "手熬黑糖挂壁，波波Q弹，厚乳香浓", "image": "http://127.0.0.1:8000/static/images/drink_1.jpg", "stock": 50, "on_sale": true }
]
// POST / DELETE /users/me/favorites/{id} → data
{ "product_id": 1, "favorited": true }
```

### 3.10 桌码点餐 / 取餐核销

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| POST | `/tables/resolve` | 否 | 解析桌码内容，返回门店 + 桌号 |
| GET | `/orders/{out_trade_no}/pickup-qr` | 是 | 取餐二维码（见 3.5） |
| POST | `/staff/pickup/lookup` | 否 | 店员核销前查询订单（需店员口令） |
| POST | `/staff/pickup/complete` | 否 | 店员确认取餐 |

桌码为静态二维码，内容格式固定为 `MILKTEA:<store_id>:<table_no>`，由 `fastapi_demo/database/build_table_qrcodes.py` 生成到 `static/qrcodes/`（含 `print.html` 打印页与 `manifest.csv`）。门店桌位配置在 `fastapi_demo/app/tables.py`。

**POST /tables/resolve**

```json
// 请求
{ "scene": "MILKTEA:1:A01" }
// 响应 data
{ "store_id": 1, "store_name": "四猫茶学园·星悦广场店", "table_no": "A01" }
```

> 内容格式错误、桌号不存在返回 `1004`；门店已打烊返回 `2004`。

**GET /orders/{out_trade_no}/pickup-qr** 响应 data：

```json
{
  "content": "PICK:CAT1760000000000123:48213",
  "image": "data:image/png;base64,iVBORw0KGgo..."
}
```

> 仅 `making` / `completed` 且有 `pick_code` 的订单可取，否则 `4001`。`image` 为 PNG data URI，前端直接放入 `<image :src>`。

**POST /staff/pickup/lookup / complete** 请求：

```json
{ "code": "PICK:CAT1760000000000123:48213", "pin": "店员口令" }
// code 也可以只传 5 位取餐码，如 "48213"；重复取餐码返回 4001
// 响应 data 为完整 Order（见 2.7），complete 成功后 state 变为 completed
```

> 店员口令来自后端 `.env` 的 `STAFF_PIN`，未配置返回 `9000`（503），口令错误返回 `1003`（403）。演示版没有店员账号体系，生产应改为店员登录 + 角色权限。订单必须处于 `making` 才能核销；已核销/已取消/未支付返回 `4001`。

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
> 演示后端没有门店出杯系统，可用 `POST /orders/{out_trade_no}/complete` 手动把 `making` 置为 `completed`，便于验证评价/再来一单。

---

## 5. 计费规则

```
商品单价 = 饮品价 + Σ 小料价
小计     = Σ(商品单价 × 数量)
打包费   = 自取 1 元 / 外送 4 元（按门店配置，外送实为配送费）
券抵扣   = 满足门槛的券中用户选中的一张（不叠加）
合计     = max(0, 小计 + 打包费 - 券抵扣)
```

- 会员价：`orig_price` 存在即展示划线价，`price` 为会员实付价。
- 券门槛按 **小计** 判断（不含打包费）。
- 下单时把商品名/图/价写入订单快照，后续商品改价不影响历史订单。

---

## 6. FastAPI 建议实现

### 6.1 目录结构

> 仓库内的 `fastapi_demo/` 是本节的**可运行简化版**：SQLAlchemy 2.0 ORM 持久化（默认 SQLite，可通过 `DATABASE_URL` 切换 MySQL）、HMAC 签名 token、模拟微信登录/支付；未使用 Redis。生产环境再按下面结构补充缓存、队列与真实微信接口。

```
backend/
├── app/
│   ├── main.py                 # FastAPI 实例、CORS、异常处理、路由注册
│   ├── core/
│   │   ├── config.py           # pydantic-settings 读取 .env
│   │   ├── security.py         # token 签发/校验（生产可用 JWT，demo 为 HMAC）
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
│   │       ├── member.py
│   │       └── addresses.py
│   ├── models/                 # SQLAlchemy 2.0 ORM
│   ├── schemas/                # Pydantic v2
│   └── services/               # 价格计算、库存、订单状态机、微信支付
├── alembic/
└── pyproject.toml
```

`fastapi_demo/` 实际结构：

```
fastapi_demo/
├── main.py                     # 应用入口、异常处理、CORS、静态目录挂载
├── requirements.txt
├── .env.example                # 数据库连接示例（复制为 .env 后填写）
├── app/
│   ├── core/{config,response,security}.py
│   ├── api/v1/{auth,users,stores,menu,coupons,orders,payments,member,addresses,tables,staff}.py
│   ├── constants.py            # 冰/糖选项、订单状态文案、时间工具
│   ├── db.py                   # Engine / SessionLocal / get_db
│   ├── models.py               # SQLAlchemy 2.0 ORM（16 张表）
│   ├── schemas.py              # 全部 Pydantic 模型
│   ├── serializers.py          # ORM 对象 → 接口 JSON（金额转 float、路径转完整 URL）
│   ├── tables.py               # 门店桌位配置 + 桌码 scene 解析
│   ├── deps.py
│   └── services/{pricing,orders,coupons,member,catalog,pickup}.py
├── database/
│   ├── schema_sqlite.sql
│   ├── schema_mysql.sql
│   ├── build_sqlite.py
│   ├── build_table_qrcodes.py  # 生成桌码 PNG / 打印页 / manifest
│   └── milktea.db              # 默认运行时数据库
└── static/
    ├── images/                 # 12 款饮品图 + 默认头像（复用前端资源）
    └── qrcodes/                # 桌码 PNG、print.html、manifest.csv
```

启动（默认使用 `database/milktea.db`）：

```bash
cd fastapi_demo
python database/build_sqlite.py           # 首次运行，生成 SQLite 库（会覆盖现有数据）
python database/build_table_qrcodes.py    # 生成 22 张桌码（segno，纯 Python）
python -m uvicorn main:app --reload       # 依赖已装在 .venv 中
# 接口文档 http://127.0.0.1:8000/docs
# 演示登录 POST /api/v1/auth/wx-login  {"code": "demo"}
```

> 已有数据库升级到桌码版本时，**不要**重建库（会清空用户/订单），执行一次：
> `ALTER TABLE orders ADD COLUMN table_no TEXT;`（MySQL 用 `VARCHAR(8) NULL`）。
> 核销口令在 `.env` 配置 `STAFF_PIN=6位数字`，修改后需重启服务。

切换到 MySQL：

1. 在 Navicat 中运行 `database/schema_mysql.sql`（会创建 `milktea` 库并写入种子数据）。
2. 复制 `.env.example` 为 `.env`，填写 `DATABASE_URL=mysql+pymysql://root:你的密码@127.0.0.1:3306/milktea?charset=utf8mb4`。
3. 重启服务。`.env` 已被 `.gitignore` 忽略，不会提交密码。

> 环境变量：`DATABASE_URL` 切换数据库，`APP_SECRET` 覆盖签名密钥，`BASE_URL` 用于拼接图片/头像完整 URL，`SQL_ECHO=1` 可打印 SQL，`STAFF_PIN` 为店员核销口令（演示用）。

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
| 首页 `pages/index` | `/menu/lines`、`/menu/products?tab=classic`、`/coupons/templates`、`/stores`、`/tables/resolve`（扫码点餐） |
| 点单页 `pages/menu` | `/stores`、`/menu/products`、`/menu/options`、`/coupons/usable`、`/tables/resolve` |
| 详情页 `pages/detail` | `/menu/products/{id}`、`/users/me/favorites` |
| 结算页 `pages/checkout` | `/orders/price-preview`、`/coupons/usable`、`/orders`、`/addresses` |
| 订单列表 `pages/order/index` | `/orders/counts`、`/orders?state=` |
| 订单详情 `pages/order/order` | `/orders/{no}`、`/orders/{no}/pickup-qr`、`/payments/{no}`、`/orders/{no}/cancel`、`/orders/{no}/review` |
| 店员核销 `pages/staff/verify` | `/staff/pickup/lookup`、`/staff/pickup/complete` |
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
| 2004 | 409 | 门店已打烊 |
| 3001 | 400 | 优惠券不可用（门槛不足） |
| 3002 | 409 | 优惠券已使用或过期 |
| 3003 | 409 | 优惠券重复领取 |
| 3004 | 409 | 优惠券已被其他订单占用（锁定中） |
| 4001 | 409 | 订单状态不允许该操作 |
| 4002 | 409 | 订单已支付，请勿重复支付 |
| 4003 | 410 | 订单超时已取消 |
| 5001 | 500 | 微信支付下单失败 |
| 5002 | 400 | 支付回调验签失败 |
| 6001 | 400 | 积分不足 |
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

### 9.1 字段映射（前端本地数据 → 接口）

| 前端现状 | 接口字段 | 说明 |
|---|---|---|
| `drink.line` | `line_id` | 产品线 ID，值不变（`buchi` 等） |
| `drink.orig` | `orig_price` | 可为 `null` |
| `drink.img` | `image` | 接口返回完整 URL |
| `drink.hot` | `is_hot` | 布尔 |
| `drink.isNew` | `is_new` | 布尔 |
| `order.state`（中文） | `state` + `state_text` | 接口枚举英文；展示用 `state_text`，状态 Tab 传英文 |
| `order.mode`（`自取`/`外送`） | `mode` + `mode_text` | `pickup`/`delivery` + 中文展示 |
| `order.spec` | `items[]` 的 `ice`/`sugar`/`topping_names` | 拆成结构化字段 |
| `order.price` | `total` | 另有 `subtotal`/`pack_fee`/`coupon_cut` |
| `order.create_time` | `create_time` | 均为毫秒时间戳 |
| `coupon.min` | `min_amount` | 券门槛 |
| 券 `desc`（本地拼接） | `desc` | 后端直接返回「满15减3」 |
| `store.dist` | `distance` | 单位米，传经纬度时按坐标重算 |
| `TOPPINGS` 仅 name/price | `toppings[].id` | 下单改传 `topping_ids`，服务端按 ID 计价 |

### 9.2 行为差异

| 现状 | 接入后端后 |
|---|---|
| `common/data/drinks.js` 写死 12 款饮品 | 改为 `/menu/products` 拉取，缓存到 pinia |
| `common/data/shop.js` 静态会员/券 | `/users/me`、`/users/me/coupons`、`/member/profile` |
| `common/data/orders.js` storage 读写 | `/orders` 系列接口，保留本地草稿缓存 |
| 结算 `submitOrder` 直接生成订单 | `/orders`（带 `Idempotency-Key`）→ `/payments/wechat/prepay` → `uni.requestPayment` |
| 购物车每杯直接生成一单 | 一次下单可含多个 `items`，由服务端合并计价 |
| 订单状态仅前端本地修改 | 服务端状态机 + 支付回调驱动 |
| 金额/优惠在前端计算 | `/orders/price-preview` 与创建订单均由服务端重算，前端结果仅展示 |
| 券在本地静态存在 | 下单锁定（`3004` 冲突）、支付核销、取消释放 |
| 门店为页面内静态数组 | `/stores`，配合 `uni.getLocation` 传经纬度 |
| 图片为本地 `/static/...` | 后端/CDN 完整 URL，前端无需改模板（`:src` 直接用） |

> 接入顺序建议：门店 → 菜单 → 用户/登录 → 券 → 下单试算 → 支付 → 订单状态，先跑通「只读接口」，再替换写操作。
