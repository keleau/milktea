# 四猫茶学园 · 后端对接前端文档

> 本文回答一件事：**`fastapi_demo` 如何把数据库里的数据稳定地交给 `fronted` 小程序**，包括启动、网络、鉴权、每个页面用到的接口契约、订单事务和联调排错。
>
> 配套文档：
>
> - 前端如何调用：[`../../fronted/docs/frontend-backend-integration.md`](../../fronted/docs/frontend-backend-integration.md)
> - 完整接口字段与示例：[`../../fronted/docs/backend-api.md`](../../fronted/docs/backend-api.md)
> - 表结构唯一契约：[`../../docs/data-dictionary.md`](../../docs/data-dictionary.md)
>
> 后端是数据的唯一权威：金额、库存、优惠券、积分、订单状态全部由 `app/services/` 计算和落库。前端提交的价格字段一律忽略。

---

## 1. 后端职责与目录

```
fastapi_demo/
├── main.py                     FastAPI 入口：CORS、异常、静态目录、路由挂载
├── requirements.txt            fastapi / uvicorn / pydantic / SQLAlchemy / PyMySQL
├── .env.example                环境变量示例（复制为 .env）
├── app/
│   ├── core/
│   │   ├── config.py           读取 .env；BASE_URL、DATABASE_URL、token TTL
│   │   ├── security.py         HMAC access/refresh token 签发与校验
│   │   └── response.py         {code,message,data} 与 BizError
│   ├── db.py                   Engine / SessionLocal / get_db
│   ├── models.py               SQLAlchemy 2.0 ORM（16 张表）
│   ├── schemas.py              Pydantic v2 请求/响应模型
│   ├── serializers.py          ORM → JSON（Decimal→float、路径→完整 URL）
│   ├── deps.py                 get_current_user / get_optional_user
│   ├── constants.py            冰/糖选项、状态/取餐方式文案、毫秒时间
│   ├── api/v1/
│   │   ├── auth.py             /auth/wx-login、/auth/refresh
│   │   ├── users.py            /users/me、头像、券、常点、收藏
│   │   ├── menu.py             /menu/lines|products|options|rank
│   │   ├── stores.py           /stores
│   │   ├── coupons.py          /coupons/templates|claim|usable
│   │   ├── orders.py           /orders 试算/创建/列表/详情/取消/完成/评价/再来一单
│   │   ├── payments.py         /payments/wechat/prepay|notify、/payments/{no}
│   │   ├── member.py           /member/profile|points/*
│   │   ├── addresses.py        /addresses CRUD
│   │   ├── tables.py           /tables/resolve（桌码解析）
│   │   └── staff.py            /staff/pickup/lookup|complete（店员核销）
│   ├── tables.py               门店桌位配置 + scene 解析（生成脚本共用）
│   └── services/
│       ├── pricing.py          商品快照、券校验、打包费、试算
│       ├── orders.py           建单、支付、取消、完成、评价、再来一单、计数
│       ├── pickup.py           取餐码定位、店员口令、核销状态校验
│       ├── coupons.py          券状态刷新、发放、可用数量
│       ├── member.py           等级、积分变更
│       └── catalog.py          常点商品排序
├── database/
│   ├── schema_sqlite.sql
│   ├── schema_mysql.sql
│   ├── build_sqlite.py
│   ├── build_table_qrcodes.py  生成桌码 PNG / print.html / manifest.csv
│   └── milktea.db              默认运行时库（含演示数据）
├── static/
│   ├── images/                 饮品图、默认头像
│   ├── avatars/                用户上传头像（gitignore）
│   └── qrcodes/                桌码 PNG、print.html、manifest.csv
└── docs/backend-frontend-integration.md
```

---

## 2. 启动与网络

### 2.1 启动命令

```bash
cd fastapi_demo

# 首次（如果没有 database/milktea.db）
python database/build_sqlite.py

# 安装依赖（已装过可跳过；segno 仅生成桌码时需要）
python -m pip install -r requirements.txt

# 生成/刷新桌码（22 张 PNG + print.html + manifest.csv）
python database/build_table_qrcodes.py

# 启动
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

> 已有库升级到桌码版本时**不要重建**（会清空用户和订单），只补列：
> `ALTER TABLE orders ADD COLUMN table_no TEXT;`（MySQL：`VARCHAR(8) NULL`）。
> 核销口令在 `.env` 设置 `STAFF_PIN`（演示用 6 位数字）；未配置时核销接口返回 9000/503，修改后需重启服务。

自检地址：

| 地址 | 用途 |
|---|---|
| `http://127.0.0.1:8000/` | 服务信息、演示登录提示 |
| `http://127.0.0.1:8000/docs` | Swagger UI |
| `http://127.0.0.1:8000/redoc` | ReDoc |
| `http://127.0.0.1:8000/static/images/drink_1.jpg` | 静态图片 |
| `http://127.0.0.1:8000/api/v1/menu/lines` | 第一条接口 |

启动时如果数据库表不存在，`main.py` 会在日志里警告：

```
数据库表不存在，请先执行 database/build_sqlite.py 或导入 database/schema_mysql.sql
```

应用**不会自动建表**，表结构以 `database/schema_*.sql` 和 `docs/data-dictionary.md` 为准。

### 2.2 前端运行方式与地址

| 前端场景 | 后端启动 | 前端 `API_BASE_URL` | 后端 `.env` `BASE_URL` |
|---|---|---|---|
| H5 浏览器 | `--host 127.0.0.1` | `http://127.0.0.1:8000` | `http://127.0.0.1:8000` |
| 微信开发者工具 | `--host 127.0.0.1` | `http://127.0.0.1:8000` | `http://127.0.0.1:8000` |
| 手机真机预览 | `--host 0.0.0.0` | `http://192.168.x.x:8000` | `http://192.168.x.x:8000` |

`BASE_URL` 决定接口里 `image` / `avatar` 的完整地址。真机联调时如果只改了前端、不改后端 `.env`，会出现「接口有数据但图片 404 / 转圈」。

> Windows 防火墙可能拦截 8000 端口；真机联调时先允许 Python/uvicorn 的局域网访问。

### 2.3 CORS 与静态资源

`main.py` 已配置：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
```

- H5 跨域访问 `127.0.0.1:8000` 不需要额外代理。
- 鉴权用 `Authorization` 请求头，不依赖 Cookie，因此 `allow_credentials=False` 不影响登录。
- 小程序不走浏览器 CORS，但微信开发者工具需关闭域名校验（`manifest.json` 已设 `urlCheck: false`）；真机/正式版必须配置 request 合法域名。
- 静态目录：`/static/images/...`（饮品图、默认头像）、`/static/avatars/...`（用户上传）、`/static/qrcodes/...`（桌码 PNG 与打印页）。

---

## 3. 统一响应与异常

所有接口成功时：

```json
{ "code": 0, "message": "ok", "data": { ... } }
```

列表 / 分页：

```json
{ "data": { "items": [], "total": 0, "page": 1, "page_size": 20 } }
```

业务异常由 `BizError` 转成：

```json
{ "code": 3004, "message": "优惠券已被其他订单占用", "data": null }
```

- HTTP 状态码同时设置（400/401/403/404/409/410/500）。
- Pydantic 参数校验统一转 `1001`，`message` 带字段位置。
- 404/405 等框架错误也保持同一 envelope。
- 未捕获异常统一 `9000`，日志打印堆栈，不把内部细节返回前端。

前端 `common/api/request.js` 会把非 0 的 `code` 转成 `ApiError`，并针对 `1002` 尝试一次 refresh。

### 3.1 错误码

| code | HTTP | 含义 | 典型触发 |
|---|---|---|---|
| 0 | 200 | 成功 | — |
| 1001 | 400 | 参数校验失败 | 地址格式、冰糖值、空 items、外送缺地址 |
| 1002 | 401 | 未登录 / token 无效 | 无 Bearer、token 过期、刷新失败 |
| 1003 | 403 | 无权限 | 操作他人订单/地址 |
| 1004 | 404 | 资源不存在 | 商品/门店/订单/地址不存在 |
| 2001 | 400 | 商品已下架 | 支付时商品被下架 |
| 2002 | 409 | 库存不足 | 试算/支付时库存不够 |
| 2003 | 409 | 商品在该门店售罄 | 预留 |
| 2004 | 409 | 门店已打烊 | `store.status == closed` |
| 3001 | 400 | 券不可用 / 门槛不足 | 金额 < `min_amount` |
| 3002 | 409 | 券已使用或过期 | 支付时券状态异常 |
| 3003 | 409 | 券重复领取 | 同模板已领过 |
| 3004 | 409 | 券被其他订单占用 | 券 `locked_by` 非本单 |
| 4001 | 409 | 订单状态不允许该操作 | 已完成再取消、未完成评价 |
| 4002 | 409 | 订单已支付 | 对 making/completed 再 prepay |
| 4003 | 410 | 订单已取消 | 对 cancelled 支付 |
| 5002 | 400 | 支付结果失败 | notify `result_code != SUCCESS` |
| 6001 | 400 | 积分不足 | 兑换 |
| 9000 | 500 | 服务内部错误 | 未捕获异常 |

---

## 4. 鉴权生命周期

### 4.1 登录

`POST /api/v1/auth/wx-login`

```json
{ "code": "081abc", "mock_id": "device-1729-abc123", "nickname": "猫友1234", "avatar": "" }
```

- `.env` 配了 `WECHAT_APPID` + `WECHAT_SECRET` 且 `code != "demo"` → 后端调用微信 `jscode2session`，用返回的 `openid` 查找/注册用户。`session_key` 只留在服务端，不返回前端。
- `code == "demo"` → openid 固定 `mock-openid-demo` → 预置用户 1001（即使已配置真实微信登录也保留，方便演示）。
- 未配 AppSecret、传了 `mock_id` → `sha256("device:" + mock_id)` 前 24 位拼 `mock-` 作为 openid；不存在则自动注册 V1 / 0 积分 / 0 券。
- 未配 AppSecret、未传 `mock_id` → 退回 `sha256(code)` 前 24 位，行为与旧版一致。
- 昵称/头像可选，传了会更新已有用户。
- `mock_id` 由前端生成并持久化在本地，长度 1~64；只用于未接真实微信时的模拟身份。
- 真实微信返回错误（如 code 无效、AppID 与小程序不一致）→ `1001` + 微信错误信息；微信服务不可达 → `9000`。

响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "access_token": "...",
    "refresh_token": "...",
    "token_type": "Bearer",
    "expires_in": 604800,
    "user": {
      "id": 1001,
      "nickname": "猫友1234",
      "avatar": "http://127.0.0.1:8000/static/images/avatar.jpg",
      "level": "V2 银牌猫评员",
      "points": 320,
      "balance": 8.5,
      "coupon_count": 2,
      "created_at": 1788220800000
    }
  }
}
```

### 4.2 Token

- HMAC-SHA256 自签，不是 JWT，但对前端同样是不透明字符串。
- `access_token` 7 天，`refresh_token` 30 天。
- 载荷含 `user_id`、类型、过期时间；密钥 `APP_SECRET`（默认值仅用于演示，生产必须改）。
- 所有需登录接口：`Authorization: Bearer <access_token>`。

### 4.3 刷新

`POST /api/v1/auth/refresh`

```json
{ "refresh_token": "..." }
```

返回新的 `{access_token, refresh_token, token_type, expires_in}`。

前端在收到 401 / 1002 时自动刷新并重放一次；刷新失败则清本地会话并 `reLaunch` 登录页。后端不维护 token 黑名单，退出登录只需前端清 token（演示项目）。

### 4.4 鉴权依赖

| 依赖 | 行为 |
|---|---|
| `get_current_user` | 无 token / token 无效 / 用户不存在 → 1002 |
| `get_optional_user` | 无 token 返回 `None`；有 token 但无效 → 1002 |

需要登录的接口：`/users/me*`、`/addresses*`、`/coupons/*/claim`、`/coupons/usable`、`/orders`（除试算）、`/payments/*`（除 notify）、`/member/*`。
可选登录：`/menu/products`（`tab=mine` 时必须有用户）、`/coupons/templates`、`/orders/price-preview`。

---

## 5. 前端页面 → 后端接口

### 5.1 首页 `pages/index`

| 调用 | 接口 | 后端行为 |
|---|---|---|
| 会员行 | `GET /users/me` | 查 `users` + `member_levels`，统计未使用券 |
| 推荐 | `GET /menu/products?tab=classic&page_size=100` | 只返回上架商品；前端筛 `is_hot` |
| 产品线 | `GET /menu/lines` | 按 `sort_order, id` |
| 门店 | `GET /stores` | 3 家门店，按距离排序 |
| 券模板 | `GET /coupons/templates` | 登录后带 `claimed` |

### 5.2 点单 `pages/menu`

| 调用 | 接口 | 说明 |
|---|---|---|
| 门店 | `GET /stores?lat=&lng=` | 传经纬度时后端用 Haversine 重算 `distance`（米） |
| 产品线 | `GET /menu/lines` | — |
| 规格 | `GET /menu/options` | 冰/糖固定选项 + `toppings`（含 ID） |
| 商品列表 | `GET /menu/products` | `tab=classic/member/new/mine`、`line_id`、`keyword`、`store_id`、分页 |
| 我的常点 | `GET /menu/products?tab=mine` | 必须登录；按历史下单次数 + 收藏排序 |
| 领券 | `POST /coupons/{template_id}/claim` | 重复领 3003 |

`tab` 语义：

| tab | 过滤 |
|---|---|
| 不传 / `classic` | 全部上架商品 |
| `member` | `orig_price IS NOT NULL` |
| `new` | `is_new = 1` |
| `mine` | 历史订单商品频次 + 收藏，需登录 |

`group_by_line=true` 时响应多一个 `data.groups = [{line, products}]`，并忽略分页；当前前端按本地 `lines` 分组，没有使用该模式。

### 5.3 详情 `pages/detail`

`GET /menu/products/{id}`：

- 商品不存在 1004；下架 2001。
- 响应 = 商品字段 + `line` + `ice_options` + `sugar_options` + `toppings`。
- 前端不再需要额外请求规格。

### 5.4 结算 `pages/checkout`

#### 试算

`POST /orders/price-preview`（可选登录）

```json
{
  "store_id": 1,
  "mode": "pickup",
  "coupon_id": 501,
  "items": [
    { "product_id": 1, "ice": "少冰", "sugar": "五分糖", "topping_ids": [1, 3], "count": 2 }
  ]
}
```

后端 `quote()` 做：

1. 门店存在、非 `closed`。
2. 每个商品存在、上架、冰糖合法、小料存在。
3. 按「商品价 + 小料价」× 数量生成快照。
4. 汇总同商品数量校验库存。
5. 打包费：自取 `store.pack_fee`，外送 `store.delivery_fee`。
6. 券：登录 + 归属 + 未使用 + 未过期 + 未被锁 + 金额达门槛。
7. `total = max(0, subtotal + pack_fee - coupon_cut)`。

响应：

```json
{
  "subtotal": 34.0,
  "pack_fee": 1.0,
  "coupon_cut": 3.0,
  "total": 32.0,
  "usable_coupons": [ { "id": 501, "cut": 3.0, "min_amount": 15.0, "...": "..." } ],
  "estimated_ready_minutes": 8
}
```

- 未登录也能试算，但没有 `usable_coupons`；传 `coupon_id` 会 1002。
- 试算**不锁券、不扣库存**。

#### 创建订单

`POST /orders`（必须登录，建议带 `Idempotency-Key`）

- 请求体 = 试算字段 + `address_id` + `table_no` + `remark`。
- 外送必须传自己的地址：缺失 1001，非本人 1004。
- 扫码点餐时传 `table_no`（≤8 字符，自动转大写）：桌号必须属于当前门店，否则 1004；堂食单只允许 `mode=pickup`，传外送返回 1001。`price-preview` 忽略该字段。
- 事务内写：
  - `orders`（快照门店名、金额、地址快照、`pending_pay`）
  - `order_items`（商品名/图/线/冰糖/单价/数量/金额快照）
  - `order_item_toppings`（小料快照）
  - `idempotency_keys`（同用户同 key 10 分钟内返回首单）
  - 选中券 `user_coupons.locked_by = out_trade_no`
- 商品库存此时**不扣**，支付成功才扣。
- 金额全部由后端重算，前端传的金额不参与。

`Idempotency-Key` 细节：

- 存储键 `(user_id, idem_key)`，TTL 600 秒。
- 重复 key 且订单还在 → 直接返回原订单；订单不存在/过期 → 清掉记录重新建单。
- 前端每次进入结算页生成一个 key，重试不换 key。

#### 支付

1. `POST /payments/wechat/prepay` `{out_trade_no}`（登录）
   - 待支付 → 返回模拟 `timeStamp/nonceStr/package/signType/paySign`。
   - 已支付 → 4002；已取消 → 4003。
2. `POST /payments/wechat/notify` `{out_trade_no, transaction_id, result_code:"SUCCESS"}`（公开）
   - 演示不验签；`result_code != SUCCESS` → 5002。
   - `pay_order()` 用 `SELECT ... FOR UPDATE` 锁订单：
     - 已 making/completed：直接返回（幂等）。
     - cancelled：4003。
     - 商品下架 2001；库存不足 2002。
     - 券状态校验；被其他订单锁 3004；已用/过期 3002。
     - 扣库存、券置 used、`locked_by` 清空。
     - 积分 `int(total)` 入账，写 `points_logs`。
     - 生成 5 位 `pick_code`，写 `pay_time` / `transaction_id`，状态 `pending_pay → making`。
3. `GET /payments/{out_trade_no}`（登录）查询 `paid/state/pay_time`。

> 真实微信支付：`prepay` 换成 APIv3 统一下单，`notify` 增加验签 + 解密，前端改用 `uni.requestPayment`。订单事务逻辑可以复用。

### 5.5 订单列表 / 详情

| 前端动作 | 接口 | 后端行为 |
|---|---|---|
| 列表 | `GET /orders?state=&page=&page_size=` | 只查当前用户；按 `create_time desc` |
| 角标 | `GET /orders/counts` | 按状态分组计数 |
| 详情 | `GET /orders/{no}` | 非本人 1003；不存在 1004；含 `table_no` |
| 取餐二维码 | `GET /orders/{no}/pickup-qr` | 仅本人；`making/completed` 且有 `pick_code`，否则 4001；返回 `{content: "PICK:单号:取餐码", image: "data:image/png;base64,..."}` |
| 取消 | `POST /orders/{no}/cancel` | 仅 `pending_pay/making`；making 回补库存、退积分 |
| 完成 | `POST /orders/{no}/complete` | 仅 `making` → `completed`，写 `finish_time` |
| 评价 | `POST /orders/{no}/review` | 仅 `completed` 且未评价；写 review 三字段 |
| 再来一单 | `POST /orders/{no}/repeat` | 返回门店/方式/地址/items 草稿；不创建订单 |

状态机：

```
pending_pay ──支付回调──> making ──complete──> completed
     │                       │
     └──用户取消──> cancelled └──用户取消（演示允许）──> cancelled
```

> `cancelled` 的支付会被拒绝（4003）；`completed` 不能取消（4001）。
> 后端未实现「15 分钟未支付自动取消」定时任务，演示时需手动取消。

### 5.6 我的 / 地址 / 券包

| 前端动作 | 接口 | 后端行为 |
|---|---|---|
| 用户资料 | `GET /users/me` | `level` 拼成 `"V2 银牌猫评员"`，头像转完整 URL |
| 改昵称 | `PATCH /users/me` | 去空格，1~20 字 |
| 上传头像 | `POST /users/me/avatar` | multipart 字段 `file`；jpg/png/webp ≤2MB；写 `static/avatars/` |
| 券列表 | `GET /users/me/coupons?status=` | `unused/used/expired/all`；先刷新过期状态 |
| 地址列表 | `GET /addresses` | 默认地址排前 |
| 新增地址 | `POST /addresses` | 第一条自动默认；设默认会清其他 |
| 编辑地址 | `PATCH /addresses/{id}` | 部分更新；`is_default=true` 清其他 |
| 删除地址 | `DELETE /addresses/{id}` | 默认地址删除后提升下一条；历史订单外键 SET NULL、快照保留 |
| 设默认 | `PATCH /addresses/{id}/default` | 清其他再置 true |
| 会员信息 | `GET /member/profile` | 等级、积分、余额、成长值、下一级、进度、券数 |
| 积分明细 | `GET /member/points/logs` | 分页，按时间倒序 |
| 兑换列表 | `GET /member/points/items` | 券/小料类兑换项 |
| 兑换 | `POST /member/points/exchange` | 积分不足 6001；券类发到券包 |

### 5.7 榜单 `pages/rank`

`GET /menu/rank?period=week`

- 全部上架商品按 `paws DESC, is_hot DESC, id` 排序。
- `items` = 完整商品字段 + `rank`；`new_items` = `is_new` 的前 6 个完整商品。
- `week/month` 当前排序一致。

### 5.8 桌码 / 店员核销

| 前端动作 | 接口 | 后端行为 |
|---|---|---|
| 扫码识别桌号 | `POST /tables/resolve` `{scene}` | 解析 `MILKTEA:<store_id>:<table_no>`；桌号须在 `app/tables.py` 配置内；门店打烊 2004；格式错误/桌号不存在 1004 |
| 店员查询 | `POST /staff/pickup/lookup` `{code, pin}` | 先校验 `STAFF_PIN`（未配置 9000/503，错误 1003/403）；`code` 可为 `PICK:单号:取餐码` 或 5 位取餐码；重复取餐码 4001；仅 `making` 可查 |
| 店员核销 | `POST /staff/pickup/complete` `{code, pin}` | 同上校验，`state → completed` 并写 `finish_time`；已核销/已取消/未支付 4001 |

桌位配置与生成：

- `app/tables.py`：`DINING_TABLES = {1: A01–A08, 2: B01–B06, 3: C01–C08}`（共 22 桌），`scene_of()` / `parse_scene()` / `table_exists()` 同时供接口与生成脚本使用。
- `database/build_table_qrcodes.py`：`segno` 生成 PNG（scale=20、border=4），输出 `static/qrcodes/store{id}_{table}.png`、`print.html`（4 列打印版）、`manifest.csv`；`--clean` 只删除本脚本生成的 `store*_*.png` / `print.html` / `manifest.csv`。
- 桌码是静态内容，不含签名与过期时间；门店/桌位变更后重新生成并重新打印即可。

> 演示边界：核销无店员账号体系，只有共享口令；生产应增加店员登录、角色权限与操作审计，并把口令换成服务端会话。

---

## 6. 数据序列化规则

### 6.1 金额

- ORM 用 `Numeric(10,2)`，Python `Decimal`。
- 响应统一 `float`（保留 2 位效果由 Decimal 保证）。
- 前端只展示，不参与最终计算。

### 6.2 时间

- 全部是**毫秒时间戳**（`BigInteger`），与前端 `Date.now()` 一致。
- 前端用 `formatTime()` 转 `YYYY-MM-DD HH:mm`。

### 6.3 图片 / 头像

- 数据库存相对路径：`/static/images/drink_1.jpg`、`/static/avatars/user_1001_...jpg`。
- `serialize_*` 用 `assets_url()` 拼 `settings.base_url`。
- 已是 `http(s)` 的地址原样返回。
- 数据库迁移/CDN 时只改 `BASE_URL`，无需改数据。
- 微信基础库已不允许 `<image>` 直接加载 HTTP：前端 `resolveImage()` 会把同名的 12 张商品图和默认头像映射到小程序包内 `static/resource/images`；上传头像仍返回 HTTP，正式部署需把 `BASE_URL` 换成 HTTPS 才能长期显示。

### 6.4 快照

| 快照 | 写入时机 | 作用 |
|---|---|---|
| 订单门店名 `orders.store_name` | 建单 | 门店改名不影响历史 |
| 商品名/图/线/单价 `order_items` | 建单 | 商品改价/下架不影响历史 |
| 小料名/价 `order_item_toppings` | 建单 | 同上 |
| 地址姓名/电话/详址 `orders.address_*` | 建单 | 删除地址后仍能展示配送信息 |
| 券标题/门槛/减免 `user_coupons` | 领券 | 模板下线不影响已领券 |

### 6.5 地址删除后的响应

`orders.address_id` 外键 `ON DELETE SET NULL`，快照字段保留。`GET /orders/{no}` 返回：

```json
{
  "address": {
    "id": null,
    "name": "张女士",
    "phone": "13800008888",
    "detail": "星悦广场 3 栋 502",
    "is_default": false
  }
}
```

`POST /orders/{no}/repeat` 对已删除地址返回 `address_id: null`。

---

## 7. 数据库运行时

### 7.1 默认 SQLite

- 路径：`fastapi_demo/database/milktea.db`
- `sqlite:///...`，`check_same_thread=False`，连接时 `PRAGMA foreign_keys=ON`。
- `build_sqlite.py` 从 `schema_sqlite.sql` 建表并写种子数据；已存在时会重建（以脚本实现为准）。
- 适合课程演示、单机联调；不适合多进程高并发写。

### 7.2 切换 MySQL

1. Navicat 连接本地 MySQL。
2. 打开并运行 `database/schema_mysql.sql`（创建 `milktea` 库、16 张表、种子数据）。
3. 复制 `.env.example` 为 `.env`（模板里的 `DATABASE_URL` 默认是注释状态，用 MySQL 时再取消注释）：

```ini
DATABASE_URL=mysql+pymysql://root:你的密码@127.0.0.1:3306/milktea?charset=utf8mb4
BASE_URL=http://127.0.0.1:8000
# SQL_ECHO=1  # 需要看 SQL 时打开
# APP_SECRET=换成一个足够长的随机串
# WECHAT_APPID=wx...      # 想用真实微信登录时填
# WECHAT_SECRET=...       # 只放后端，不提交
```

4. 重启 uvicorn。日志无建表警告、`/api/v1/menu/products` 有数据即成功。
5. `.env` 已在 `.gitignore` 中，密码与 AppSecret 不会进仓库。

驱动：`PyMySQL[rsa]`；`caching_sha2_password` 需要 `cryptography`，requirements 已含 `PyMySQL[rsa]`。

### 7.3 16 张表与模块

| 表 | 模块 |
|---|---|
| `member_levels` | 会员等级阈值 |
| `users` | 用户、积分、余额、等级 |
| `product_lines` | 四条产品线 |
| `products` | 商品、价格、库存、上下架 |
| `toppings` | 小料 |
| `stores` | 门店、打包/配送费、营业状态 |
| `coupon_templates` | 券模板 |
| `user_coupons` | 用户券实例、锁定、核销 |
| `addresses` | 收货地址 |
| `favorites` | 收藏 |
| `orders` | 订单主表、状态、金额、地址快照、评价 |
| `order_items` | 订单商品快照 |
| `order_item_toppings` | 订单小料快照 |
| `points_logs` | 积分流水 |
| `exchange_items` | 积分兑换项 |
| `idempotency_keys` | 下单幂等键 |

外键关系（简化）：

```
users 1─n orders 1─n order_items 1─n order_item_toppings
users 1─n addresses 1─n orders.address_id (SET NULL)
users 1─n user_coupons n─1 coupon_templates
users 1─n favorites n─1 products
users 1─n points_logs
orders.coupon_id ─1 user_coupons
orders 1─1 idempotency_keys.order_no (逻辑关联)
```

### 7.4 演示种子

| 数据 | 内容 |
|---|---|
| 用户 | 1001 猫友1234，V2，320 积分，8.5 余额 |
| 地址 | 1 条默认：张女士 / 13800008888 / 星悦广场 3 栋 502 |
| 券 | 501 满15减3、502 满25减5，均 unused |
| 门店 | 1 星悦广场（resting，205m，打包1/配送4）；2 万象城（open，1200m，1/5）；3 大学城（open，2400m，1/3） |
| 商品 | 12 款，四条产品线，价格 9~16，库存充足 |
| 小料 | 珍珠 1、椰果 1、布丁 2、芋圆 2、芝士奶盖 3 |

> `resting`（即将休息）仍允许下单；只有 `closed` 会返回 2004。前端把 `resting` 显示为「即将休息」。

---

## 8. 关键事务与一致性

### 8.1 创建订单

```
BEGIN
  幂等键命中？ → 返回原订单
  quote() 重算 + 校验库存/券
  INSERT orders / order_items / order_item_toppings
  UPDATE user_coupons.locked_by
  INSERT idempotency_keys
COMMIT
```

- `db.add(order)` 后先 `db.flush()` 再插幂等键，保证 `idempotency_keys.order_no` 外键能找到订单（这是之前修过的 FK bug）。
- 创建失败整体回滚，不锁券、不写幂等键。

### 8.2 支付回调

```
BEGIN
  SELECT orders ... FOR UPDATE
  已支付？ → 直接返回（幂等）
  校验商品/库存/券
  UPDATE products.stock
  UPDATE user_coupons.status='used', locked_by=NULL
  UPDATE users.points, INSERT points_logs
  UPDATE orders SET state='making', pick_code, pay_time, transaction_id
COMMIT
```

- SQLite 的 `FOR UPDATE` 会被忽略，但演示单进程够用；MySQL 生效。
- 重复 notify 不重复扣库存/加积分。

### 8.3 取消订单

- `pending_pay`：释放券（`locked_by=NULL`），不改库存/积分。
- `making`：释放券 + 回补库存 + 扣回 `earning_points` + 写退款流水。
- `completed/cancelled`：4001。

### 8.4 积分

- 支付成功：`int(total)`，例如实付 32.8 → +32。
- 等级由累计积分决定：V1 0 / V2 200 / V3 800 / V4 2000。
- 取消制作中订单扣回本单积分；积分不会低于 0（`change_points` 夹紧）。

---

## 9. 联调检查清单

### 9.1 后端

```bash
# 1. 服务与文档
curl -s http://127.0.0.1:8000/
curl -s http://127.0.0.1:8000/api/v1/menu/lines

# 2. 登录（演示会员）
curl -s -X POST http://127.0.0.1:8000/api/v1/auth/wx-login \
  -H "Content-Type: application/json" -d '{"code":"demo"}'

# 2.1 模拟微信登录：同一 mock_id 两次应返回同一个 user.id
curl -s -X POST http://127.0.0.1:8000/api/v1/auth/wx-login \
  -H "Content-Type: application/json" -d '{"code":"081aaa","mock_id":"device-test"}'
curl -s -X POST http://127.0.0.1:8000/api/v1/auth/wx-login \
  -H "Content-Type: application/json" -d '{"code":"092bbb","mock_id":"device-test"}'

# 3. 带 token
TOKEN=... # 上一步 data.access_token
curl -s http://127.0.0.1:8000/api/v1/users/me -H "Authorization: Bearer $TOKEN"
curl -s http://127.0.0.1:8000/api/v1/addresses -H "Authorization: Bearer $TOKEN"
curl -s http://127.0.0.1:8000/api/v1/users/me/coupons -H "Authorization: Bearer $TOKEN"

# 4. 试算
curl -s -X POST http://127.0.0.1:8000/api/v1/orders/price-preview \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"store_id":2,"mode":"pickup","items":[{"product_id":1,"ice":"少冰","sugar":"五分糖","topping_ids":[1],"count":1}]}'

# 5. 下单 + 支付
curl -s -X POST http://127.0.0.1:8000/api/v1/orders \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -H "Idempotency-Key: test-$(date +%s)" \
  -d '{"store_id":2,"mode":"pickup","items":[{"product_id":1,"ice":"少冰","sugar":"五分糖","topping_ids":[1],"count":1}]}'
# 用返回的 out_trade_no：
curl -s -X POST http://127.0.0.1:8000/api/v1/payments/wechat/prepay \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"out_trade_no":"CAT..."}'
curl -s -X POST http://127.0.0.1:8000/api/v1/payments/wechat/notify \
  -H "Content-Type: application/json" \
  -d '{"out_trade_no":"CAT...","transaction_id":"MOCK-TEST"}'
```

### 9.2 前端

- `API_BASE_URL` 与后端 `BASE_URL` 一致。
- 冷启动后 `milk_access_token` 有值；`GET /users/me` 的昵称/积分显示在首页、我的页。
- 菜单接口返回 `http://127.0.0.1:8000/static/images/...`，微信端由 `resolveImage()` 映射成本地商品图。
- 结算金额与试算完全一致；自取/外送切换后 `pack_fee` 变化。
- 支付成功后订单变「制作中」、出现取餐码；`orders`、`products.stock`、`user_coupons`、`users.points`、`points_logs` 同时变化。
- 取消待支付订单后券解锁；取消制作中订单后库存/积分回滚。
- 地址删除后历史订单地址仍显示姓名/电话/详址。

---

## 10. 常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| 前端提示网络失败 | 后端没启动 / 端口不对 / 真机用了 127.0.0.1 | 启动 uvicorn；真机改 `API_BASE_URL` 为局域网 IP |
| H5 控制台 CORS 错误 | 请求打到了别的地址，或用了错误的协议 | 确认 `API_BASE_URL` 为后端地址；后端已 `allow_origins=["*"]` |
| 图片裂开 / 404 | `BASE_URL` 还是 127.0.0.1，真机访问不到；或文件名不对 | 改后端 `.env` 的 `BASE_URL`；检查 `static/images/` |
| 401 / 1002 循环 | refresh_token 失效；系统时间偏差；`APP_SECRET` 变了 | 清前端缓存重新登录；确认后端未改密钥 |
| 登录后还是空数据 | 用了新账号（换了 `mock_id` 或清了小程序缓存），新用户本来就没有历史数据 | 想共用演示数据就点「演示会员登录」；独立账号按用户 ID 查数据 |
| 同一设备重复微信登录却换号 | 小程序缓存被清，`milk_mock_id` 重新生成 | 演示环境可接受；需要绝对稳定就接入真实 `code2session` |
| 领券 3003 | 演示账号已领过两张券 | 退出后用「微信一键登录」注册新用户；或清库重来 |
| 结算提示券被占用 3004 | 有一笔待支付订单锁着券 | 到订单列表取消那笔待支付订单 |
| 外送建单 1001 | 没传 `address_id` | 结算页选地址；地址必须属于当前用户 |
| 支付 4002 | 订单已支付 | 刷新订单详情；重复 notify 是幂等的 |
| MySQL 连接失败 | 密码错误 / 库不存在 / 驱动缺失 | 检查 `.env` URL；导入 `schema_mysql.sql`；安装 requirements |
| 启动 warning 表不存在 | 没建库/导错库 | 运行 `build_sqlite.py` 或导入 MySQL 脚本 |
| 上传头像 404 | `static/avatars` 未创建 / 路径被清 | 应用启动会自动建目录；检查 `static/` 可写 |
| 真机接口通但图片不通 | 只改了前端 base，后端 `BASE_URL` 没改 | 两边都改成同一局域网 IP 并重启 |
| 扫码提示桌号无效 1004 | 二维码不是本系统桌码 / 门店或桌号未配置 | 用 `static/qrcodes/` 生成的码；新增桌位先改 `app/tables.py` 再重生成 |
| 核销返回 9000/503 | 后端 `.env` 未设置 `STAFF_PIN`，或改后未重启 | 配置 `STAFF_PIN` 并重启后端 |
| 核销返回 1003/403 | 店员口令输错 | 核对 `.env` 的 `STAFF_PIN` |
| 核销返回 4001 | 订单未支付 / 已核销 / 已取消，或取餐码重复 | 让顾客打开订单详情出示二维码；刷新订单状态 |

---

## 11. 安全与演示边界

- `APP_SECRET` 默认值只能用于本地演示，部署必须换随机长串。
- `.env` 不提交；聊天、文档、前端代码里不出现数据库密码。
- 微信支付、退款为模拟；notify 公开且不验签，**不能用于生产**。
- 登录分两种：配置 `WECHAT_APPID` + `WECHAT_SECRET` 后走真实 `code2session`，`openid` 由微信签发；未配置时才用 `mock_id` 模拟。`mock_id` 是前端本地标识，任何人都能伪造，**不能当作可信身份**。
- `WECHAT_SECRET` 只放后端 `.env`，不要写进前端、文档、聊天或提交仓库。
- `STAFF_PIN` 只放后端 `.env`；店员核销接口无登录态，靠共享口令，演示够用，生产必须换成店员账号 + 角色权限。
- CORS `*` 仅方便联调；生产收紧到具体域名。
- 上传头像只校验 MIME 与大小，演示够用；生产还应做图片重编码、病毒扫描、对象存储。
- 订单超时取消、券锁定超时释放未实现定时任务；演示结束请手动取消未支付订单。
- 演示账号共享，适合单人/课堂演示；多人同时操作会互相影响订单与积分。

---

## 12. 接口总表（速查）

| 方法 | 路径 | 鉴权 | 前端页面 |
|---|---|---|---|
| POST | `/auth/wx-login` | 否 | 登录页两个入口 |
| POST | `/auth/refresh` | 否 | 请求层 401 |
| GET/PATCH | `/users/me` | 是 | 首页、我的 |
| POST | `/users/me/avatar` | 是 | 我的 |
| GET | `/users/me/coupons` | 是 | 我的、券包 |
| GET/POST/DELETE | `/users/me/favorites` | 是 | 详情（预留）、我的常点 |
| GET | `/menu/lines` | 否 | 首页、点单、详情、榜单 |
| GET | `/menu/products` | 可选 | 首页、点单 |
| GET | `/menu/products/{id}` | 否 | 详情、再来一单 |
| GET | `/menu/options` | 否 | 点单、再来一单 |
| GET | `/menu/rank` | 否 | 榜单 |
| GET | `/stores` `/stores/{id}` | 否 | 点单、结算 |
| GET | `/coupons/templates` | 可选 | 点单、券包 |
| POST | `/coupons/{id}/claim` | 是 | 点单、券包 |
| GET | `/coupons/usable` | 是 | 结算（试算也可） |
| POST | `/orders/price-preview` | 可选 | 结算 |
| POST | `/orders` | 是 | 结算 |
| GET | `/orders` `/orders/counts` `/orders/{no}` | 是 | 订单列表/详情、我的 |
| GET | `/orders/{no}/pickup-qr` | 是 | 订单详情（取餐二维码） |
| POST | `/orders/{no}/cancel|complete|repeat|review` | 是 | 订单详情 |
| POST | `/tables/resolve` | 否 | 首页、点单（扫码识别桌号） |
| POST | `/staff/pickup/lookup|complete` | 否（店员口令） | 店员核销 |
| POST | `/payments/wechat/prepay` | 是 | 结算、订单详情 |
| POST | `/payments/wechat/notify` | 否 | 演示支付 |
| GET | `/payments/{no}` | 是 | 订单详情 |
| GET | `/member/profile` `/member/points/*` | 是 | 我的（预留） |
| GET/POST/PATCH/DELETE | `/addresses` | 是 | 地址页、结算 |
| PATCH | `/addresses/{id}/default` | 是 | 地址页 |
