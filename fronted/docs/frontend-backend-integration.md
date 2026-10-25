# 四猫茶学园 · 前端接入后端联调文档

> 本文回答一件事：**小程序前端如何调用 `fastapi_demo` 的接口，并把返回数据写进 / 读出数据库**。
>
> 配套文档：
>
> - 接口字段与请求示例：[`backend-api.md`](./backend-api.md)
> - 后端如何配合前端：[`../../fastapi_demo/docs/backend-frontend-integration.md`](../../fastapi_demo/docs/backend-frontend-integration.md)
> - 数据库表结构唯一契约：[`../../docs/data-dictionary.md`](../../docs/data-dictionary.md)
>
> 资金计算、库存、优惠券核销、订单状态机全部在后端完成。前端只负责「收集商品 ID + 规格 + 数量 + 地址 + 券 ID」和展示结果，**不把前端算出来的金额提交给后端**。

---

## 1. 总体链路

```
┌──────────────────────────── uni-app 前端（fronted/） ────────────────────────────┐
│ pages/*.vue                                                                      │
│   │ 只读写“视图字段”（drink.img / order.state_text / coupon.min ...）             │
│   ▼                                                                              │
│ common/api/adapters.js     后端字段 → 视图字段（line_id→line、orig_price→orig）   │
│   ▲                                                                              │
│   │                                                                              │
│ common/api/*.js            业务接口（catalog / orders / users / member ...）      │
│   │                                                                              │
│   ▼                                                                              │
│ common/api/request.js      API_BASE_URL + /api/v1 + Bearer + 统一 envelope + 刷新 │
│   │                                                                              │
│   ▼                                                                              │
│ common/api/token.js        access_token / refresh_token / user 本地缓存           │
└───────────────────────────────────┬──────────────────────────────────────────────┘
                                    │ HTTP JSON
                                    ▼
┌──────────────────────────── fastapi_demo（FastAPI） ─────────────────────────────┐
│ app/api/v1/*.py            路由、鉴权依赖、参数校验                               │
│ app/services/*.py          价格、券、库存、积分、订单状态机                       │
│ app/models.py              SQLAlchemy ORM（16 张表）                              │
│ app/db.py                  SessionLocal → SQLite（默认）/ MySQL（DATABASE_URL）     │
└───────────────────────────────────┬──────────────────────────────────────────────┘
                                    ▼
                fastapi_demo/database/milktea.db（默认）
                或 Navicat 里的 MySQL `milktea` 库（切换 DATABASE_URL）
```

前端不再从 `common/data/*` 读取演示数据，也不再用 `uni.setStorageSync('milk_orders')` 存订单。`common/data` 里旧字段只保留在本文第 9 章的迁移对照表中。

---

## 2. 联调前配置

### 2.1 前端

新增 [`../common/config.js`](../common/config.js)：

```js
// 电脑本机运行后端：H5 / 微信开发者工具都用 127.0.0.1
export const API_BASE_URL = 'http://127.0.0.1:8000'
export const API_PREFIX = '/api/v1'

// 演示登录：后端把 code=demo 映射到预置会员 1001（V2、320 积分、2 张券、1 个地址）
export const DEMO_LOGIN_CODE = 'demo'
export const REQUEST_TIMEOUT = 15000
```

切换场景时只改 `API_BASE_URL`：

| 运行场景 | API_BASE_URL | 额外要求 |
|---|---|---|
| H5（浏览器） | `http://127.0.0.1:8000` | 后端已启动，CORS 已放开 |
| 微信开发者工具 | `http://127.0.0.1:8000` | `manifest.json` 已设 `urlCheck: false` |
| 手机真机 / 预览 | `http://电脑局域网IP:8000`（如 `http://192.168.1.8:8000`） | 后端用 `--host 0.0.0.0` 启动；手机与电脑同一 Wi-Fi；后端 `.env` 的 `BASE_URL` 也要改成同一地址，否则图片仍是 127.0.0.1 |

> 后端返回的 `image` / `avatar` 是**完整 URL**，前端不要再拼 `API_BASE_URL`。`common/api/adapters.js` 的 `resolveImage()` 会把与小程序包内同名的商品图映射为 `/static/resource/images/*`：新版微信基础库已不允许 `<image>` 加载 HTTP 图片，映射后本地商品图可正常显示；上传头像等未知 HTTP 图片在微信端返回空值，页面回退到本地默认头像。生产环境把 `API_BASE_URL` 与后端 `BASE_URL` 换成 HTTPS 域名，并把域名加入微信公众平台的 request 合法域名。

### 2.2 后端

```bash
cd fastapi_demo
.venv/Scripts/python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

- 默认使用 `fastapi_demo/database/milktea.db`。
- 用 MySQL 时先在 Navicat 导入 `database/schema_mysql.sql`，再在 `fastapi_demo/.env` 写 `DATABASE_URL=mysql+pymysql://root:密码@127.0.0.1:3306/milktea?charset=utf8mb4`。
- `.env` 已被 `.gitignore` 忽略，密码不写进前端、不提交仓库。
- 打开 `http://127.0.0.1:8000/docs` 确认服务正常。

### 2.3 演示账号

`POST /api/v1/auth/wx-login`，请求体 `{"code":"demo"}`：

| 项目 | 预置值 |
|---|---|
| 用户 | `id=1001`，昵称「猫友1234」 |
| 等级 / 积分 / 余额 | V2 银牌猫评员 / 320 / 8.5 |
| 优惠券 | 501（满15减3）、502（满25减5），均已领取 |
| 收货地址 | 1 条默认地址（张女士，13800008888） |
| 门店 | 1 星悦广场店（resting）、2 万象城店（open）、3 大学城店（open） |

> 演示登录是**共享账号**：所有用 `code=demo` 的设备看到同一份订单/积分数据。需要独立账号时，把 `DEMO_LOGIN_CODE` 换成设备唯一且稳定的字符串（后端会按字符串哈希生成 openid 并自动注册），或接入真实微信 `uni.login()` 的 code。

---

## 3. 前端请求层

### 3.1 文件职责

| 文件 | 职责 |
|---|---|
| `common/config.js` | 后端地址、API 前缀、演示登录 code、超时 |
| `common/api/token.js` | 读写 `access_token` / `refresh_token` / 用户缓存，清理会话 |
| `common/api/request.js` | `uni.request` 封装：拼 URL、带 Bearer、拆 `{code,message,data}`、401 自动刷新、抛 `ApiError` |
| `common/api/auth.js` | 登录、静默登录 `ensureLogin()`、刷新用户、改昵称、上传头像 |
| `common/api/catalog.js` | 产品线、商品、规格、榜单、门店 |
| `common/api/coupons.js` | 券模板、领券、我的券、可用券 |
| `common/api/orders.js` | 试算、创建、列表、详情、取消、完成、再来一单、评价、支付 |
| `common/api/users.js` | `/users/me`、订单数量、我的常点、收藏 |
| `common/api/member.js` | 会员等级、积分明细、积分兑换 |
| `common/api/addresses.js` | 地址增删改查、设默认 |
| `common/api/adapters.js` | 后端字段 → 页面现有视图字段；金额/时间/距离格式化 |

### 3.2 统一响应与错误

后端所有接口（包括 404/405）都返回：

```json
{ "code": 0, "message": "ok", "data": {} }
```

`request.js` 的规则：

- `HTTP 2xx && code === 0` → 直接返回 `data`，页面不用再拆一层。
- `HTTP 非 2xx || code !== 0` → 抛 `ApiError`：
  ```js
  { code: 3004, message: '优惠券已被其他订单占用', statusCode: 409 }
  ```
- `code === 1002` / HTTP 401：
  1. 有 `refresh_token` 且本次请求不是刷新接口 → 调 `POST /auth/refresh`
  2. 成功后保存新 token，并**重放原请求一次**
  3. 刷新也失败 → 清空本地会话，抛 `1002`
- 网络失败 → `code = -1`，提示「网络请求失败，请检查后端是否启动」。
- 多个请求同时 401 时共用一个刷新 Promise，避免并发刷新把后一个 refresh_token 作废。

页面统一用 `showError(error)`：

```js
uni.showToast({ title: error.message || '请求失败', icon: 'none' })
```

### 3.3 登录与会话

```
App.vue onLaunch
  └─ ensureLogin()
       ├─ 本地有 access_token → 直接返回缓存用户
       └─ 没有 → POST /auth/wx-login {code:"demo"}
            └─ data: {access_token, refresh_token, token_type, expires_in, user}
                 ├─ token.js 保存 token 与 user
                 └─ 页面读取 user（我的页、首页会员行）

任意需登录接口 → Authorization: Bearer <access_token>
  └─ 401/1002 → refresh → 重放 → 仍失败则清会话
```

需登录的页面/动作在请求前调用 `await ensureLogin()`：

- 首页会员行（可失败，页面仍能展示公开菜单）
- 点单页「我的常点」、领券
- 详情页收藏（当前 UI 未放收藏按钮，接口已封装）
- 结算页试算（用券需要登录）、创建订单、支付
- 订单列表/详情
- 我的页、地址页、券包页

本地缓存键：

| key | 内容 | 用途 |
|---|---|---|
| `milk_access_token` | access token | 请求头 |
| `milk_refresh_token` | refresh token | 401 刷新 |
| `milk_user` | 当前用户对象 | 首页/我的页首屏、离线兜底 |
| `milk_store_id` | 当前选中门店 ID | 菜单 → 详情 → 结算 |
| `common/store/session.js` | 结算草稿、订单筛选、结算页选中的地址 ID | 页面间临时状态，不落盘 |

旧的 `milk_orders` 不再读取；接入后订单以服务端数据库为准。

---

## 4. 页面 → 接口 → 数据库

### 4.1 总表

| 页面 | 读取接口 | 写入接口 | 主要数据库表 |
|---|---|---|---|
| `App.vue` | — | `POST /auth/wx-login` | `users`、`member_levels` |
| 首页 `pages/index` | `GET /users/me`、`GET /menu/lines`、`GET /menu/products?tab=classic`、`GET /stores`、`GET /coupons/templates` | 静默登录 | `users`、`products`、`stores`、`coupon_templates` |
| 点单 `pages/menu` | `GET /stores`、`GET /menu/lines`、`GET /menu/options`、`GET /menu/products?tab=`、`GET /coupons/templates` | `POST /coupons/{id}/claim` | `stores`、`products`、`toppings`、`user_coupons` |
| 详情 `pages/detail` | `GET /menu/products/{id}`、`GET /menu/lines` | —（把草稿交给结算页） | `products`、`product_lines`、`toppings` |
| 结算 `pages/checkout` | `GET /stores/{id}`、`GET /addresses`、`POST /orders/price-preview` | `POST /orders`、`POST /payments/wechat/prepay`、`POST /payments/wechat/notify` | `orders`、`order_items`、`order_item_toppings`、`user_coupons`、`idempotency_keys`、`products` |
| 订单列表 `pages/order/index` | `GET /orders?state=` | — | `orders`、`order_items` |
| 订单详情 `pages/order/order` | `GET /orders/{no}`、`GET /payments/{no}`、`GET /menu/products/{id}`、`GET /menu/options` | `POST /orders/{no}/cancel`、`POST /orders/{no}/complete`、`POST /orders/{no}/review`、`POST /orders/{no}/repeat`、支付 | `orders`、`order_items`、`order_item_toppings`、`products`、`user_coupons`、`points_logs` |
| 我的 `pages/user` | `GET /users/me`、`GET /orders/counts`、`GET /member/profile` | `PATCH /users/me`、`POST /users/me/avatar` | `users`、`orders`、`user_coupons`、`points_logs` |
| 榜单 `pages/rank` | `GET /menu/rank?period=week`、`GET /menu/lines` | — | `products`、`product_lines` |
| 地址 `pages/address` | `GET /addresses` | `POST/PATCH/DELETE /addresses`、`PATCH /addresses/{id}/default` | `addresses` |
| 券包 `pages/coupon` | `GET /users/me/coupons?status=`、`GET /coupons/templates` | `POST /coupons/{id}/claim` | `user_coupons`、`coupon_templates` |

### 4.2 首页 `pages/index/index.vue`

| 区域 | 数据来源 | 视图字段 |
|---|---|---|
| 会员行 V2 / 银牌 / 券 / 积分 / 余额 | `GET /users/me` | `level` 拆成 `levelCode` + `levelName`；`coupon_count`、`points`、`balance` |
| 今日猫推荐 | `GET /menu/products?tab=classic` 后筛 `is_hot`，取前 3 | `toDrink()`：`img/name/line/paws/desc/price` |
| 产品线标签颜色 | `GET /menu/lines` | `lineOf()` 按 `line_id` 查 |
| 页脚门店标语 | 固定文案「今天的奶茶，由猫评分」 | 后端无此字段，不放接口 |
| 轮播海报 | 本地 `static/resource/images/banner_*.jpg` | 营销素材，不走接口 |

失败策略：用户信息失败不影响菜单展示；推荐为空时显示原空区，不弹错误。

### 4.3 点单页 `pages/menu/index.vue`

加载顺序：

1. `GET /stores`（可选带 `uni.getLocation` 经纬度）→ 门店行、选店弹层。
2. `GET /menu/lines` + `GET /menu/options` → 左侧分类、冰/糖/小料。
3. `GET /menu/products?tab=classic&store_id=当前门店&page_size=100` → 商品卡。
4. `GET /coupons/templates` → 券包特惠列表；已领取的显示「已领取」。
5. 切页签：`classic / member / new / mine` 传 `tab`。`mine` 前必须 `ensureLogin()`，返回 401 时显示空态并提示登录。

后端 → 视图字段：

| 后端 | 视图 | 说明 |
|---|---|---|
| `line_id` | `drink.line` | 用于 `lineOf()` 找颜色/标签 |
| `orig_price` | `drink.orig` | 有值显示会员价划线 |
| `is_hot` / `is_new` | `drink.hot` / `drink.isNew` | 标签、分节 |
| `image` | `drink.img` | 经 `resolveImage()` 映射为本地商品图；HTTPS 环境保留原 URL |
| `price` | `drink.price` | 展示价；最终价以后端试算为准 |
| `toppings[].id` | 购物车 `toppingIds` | 下单传 ID，不传价格 |

购物车与草稿：

```js
// 加入购物车
{ drink, ice, sugar, toppings: [{id,name,price}], count }

// 去结算 / 立即购买 → session.js
setCheckoutDraft({
  storeId,
  mode: 'pickup' | 'delivery',
  items: [{ product /* 视图 drink */, ice, sugar, toppings, count }]
})
uni.navigateTo({ url: '/pages/checkout/index' })
```

> 购物车的「预估」金额只做展示；结算页会用 `/orders/price-preview` 重新算。

领券：点击券卡 / 一键领取 → `POST /coupons/{template_id}/claim`。成功把本地 `claimed` 置 true；重复领取（3003）提示「已领取」；未登录先 `ensureLogin()`。演示账号两张券都已领取。

### 4.4 详情页 `pages/detail/index.vue`

- `onLoad` 读取 `id`、`mode`，并行 `GET /menu/products/{id}` 与 `GET /menu/lines`。
- 详情响应已经包含 `line`、`ice_options`、`sugar_options`、`toppings`，不再读 `common/data` 常量。
- 四猫联合评分仍是展示性算法（以商品 `paws` 为基准浮动），后端无评分明细接口。
- 「选好了，去结算」只写草稿：

```js
setCheckoutDraft({
  storeId: Number(uni.getStorageSync('milk_store_id')) || 1,
  mode: params.mode === 'delivery' ? 'delivery' : 'pickup',
  items: [{ product: drink, ice, sugar, toppings: picked, count }]
})
```

### 4.5 结算页 `pages/checkout/index.vue`

这是前后端联调的核心页面，所有金额以后端为准。

#### 读取

- `GET /stores/{storeId}`：门店名、营业时间、打包费/配送费展示。
- 外送时 `GET /addresses`：默认地址或用户选择的地址。
- `POST /orders/price-preview`：

```json
{
  "store_id": 1,
  "mode": "delivery",
  "coupon_id": 501,
  "items": [
    { "product_id": 1, "ice": "少冰", "sugar": "五分糖", "topping_ids": [1, 3], "count": 2 }
  ]
}
```

响应字段直接映射页面：

| 响应 | 页面 |
|---|---|
| `subtotal` | 小计 |
| `pack_fee` | 打包费 / 配送费 |
| `coupon_cut` | 优惠券抵扣 |
| `total` | 合计（底部栏） |
| `usable_coupons` | 优惠券卡片（`cut/title/desc`） |
| `estimated_ready_minutes` | 「出杯约 N 分钟」 |

切换 `mode`、勾选/取消券、修改地址后都重新试算；请求期间禁用提交按钮。

#### 写入

```js
const idempotencyKey = `CAT-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`

// 1. 创建订单
const order = await createOrder({
  store_id,
  mode,
  address_id: mode === 'delivery' ? address.id : null,
  coupon_id: couponId || null,
  remark: '',
  items: items.map(/* product_id / ice / sugar / topping_ids / count */)
}, idempotencyKey)

// 2. 统一下单（演示返回模拟参数）
await prepay(order.out_trade_no)

// 3. 演示支付回调：真实微信支付时改为 uni.requestPayment(prepayParams)
await payDemo(order.out_trade_no) // POST /payments/wechat/notify

// 4. 清理草稿并跳详情
clearCheckoutDraft()
uni.redirectTo({ url: `/pages/order/order?oid=${order.out_trade_no}` })
```

- `Idempotency-Key` 在同一结算页内保持不变；网络失败后用户再次点提交不会重复建单。
- 外送必须选地址，前端先拦一次；后端仍会校验 `address_id`（1001）。
- 创建成功后即使支付失败，也跳订单详情，不再回结算页重复建单；待支付订单可在详情页继续支付或取消（取消会释放券）。
- 试算 / 建单会校验商品上下架、库存、门店打烊、券门槛与占用，错误码见第 6 章。

### 4.6 订单列表 `pages/order/index.vue`

- 状态 Tab 内部值改为英文：`'' / pending_pay / making / completed / cancelled`，展示中文用映射表。
- `onShow`：`ensureLogin()` → `GET /orders?state=...&page=1&page_size=50`。
- `GET /orders` 不传 `state` 才是全部；**不要传空字符串**，后端 `Literal` 校验会报 1001。
- 列表卡片由第一件商品快照生成：

| 卡片字段 | 来源 |
|---|---|
| 单号后 8 位 | `out_trade_no.slice(-8)` |
| 状态文案/颜色 | `state_text` + `state` |
| 图片/名称/规格 | `items[0].image/name/ice/sugar/topping_names` |
| 件数 | `Σ items.count` |
| 取餐方式 | `mode_text` |
| 金额 | `total` |

> 本地 `milk_orders` 不再参与。订单状态由服务端支付回调/取消/完成驱动，列表每次 `onShow` 重新拉取。

### 4.7 订单详情 `pages/order/order.vue`

- `onLoad` 记下 `oid`；`onShow` 拉 `GET /orders/{no}`，从详情页返回时自动刷新。
- 状态文案：优先 `state_text`；横幅标题仍按 `state` 显示更口语化的文案。
- 清单改为 `v-for="item in order.items"`，展示快照字段。
- 信息区展示：订单号、`mode_text`、下单时间（`create_time` 格式化）、小计、打包费/配送费、券抵扣、实付、备注、外送地址快照。
- 按钮与接口：

| 状态 | 按钮 | 接口 | 后续 |
|---|---|---|---|
| `pending_pay` | 立即支付 | `prepay` → `notify` | 重新拉详情，状态变 `making`，出取餐码 |
| `pending_pay` / `making` | 取消订单 | `POST /orders/{no}/cancel` | 确认弹窗；`making` 取消会回补库存、退积分、释放券 |
| `making` | 模拟出杯 | `POST /orders/{no}/complete` | 演示用，状态变 `completed` |
| `completed` 且未评价 | 去评价 | `POST /orders/{no}/review` | `rating` 1~5 + `content` ≤200 字 |
| `completed` / `cancelled` | 再来一单 | `POST /orders/{no}/repeat` | 用返回草稿补齐商品视图后进结算页 |

再来一单的草稿只有 ID，需要补视图：

```js
const draft = await repeatOrder(orderNo)             // store_id/mode/address_id/items
const [options, ...products] = await Promise.all([
  getOptions(),
  ...draft.items.map(item => getProduct(item.product_id))
])
setCheckoutDraft({
  storeId: draft.store_id,
  mode: draft.mode,
  items: draft.items.map((item, index) => ({
    product: toDrink(products[index]),
    ice: item.ice,
    sugar: item.sugar,
    toppings: item.topping_ids.map(id => options.toppings.find(t => t.id === id)).filter(Boolean),
    count: item.count
  }))
})
```

> `repeat` 返回的 `address_id` 可能为 `null`（原地址已删除）。外送单进入结算页后需要重新选地址。

### 4.8 我的 `pages/user/index.vue`

- `onShow`：`ensureLogin()` → `GET /users/me` + `GET /orders/counts`（可再取 `/member/profile` 显示等级进度）。
- 昵称、头像、等级、积分、券数、余额全部来自用户对象，不再随机生成本地昵称。
- 订单四宫格键名改为英文：

```json
{ "pending_pay": 1, "making": 2, "completed": 8, "cancelled": 0 }
```

点击格子写入 `setOrdersFilter('pending_pay')` 后 `switchTab` 到订单页。

- 修改昵称：`PATCH /users/me`，请求 `{ "nickname": "布奇头号粉丝" }`。
- 修改头像：
  - `uni.chooseMedia` 选图，压缩后确认 ≤2MB。
  - `uni.uploadFile` 到 `/api/v1/users/me/avatar`，字段名 `file`，带 `Authorization`。
  - 响应 `data.avatar` 是完整 URL，写回用户缓存和页面。
  - 后端支持 jpg/png/webp；文件落在 `fastapi_demo/static/avatars/`（已 gitignore）。
- 「优惠券」入口进入券包页；「收货地址」入口进入地址页。

### 4.9 地址页 `pages/address/index.vue`（新增）

- `GET /addresses` 列表，默认地址置顶。
- 新增 `POST /addresses`；编辑 `PATCH /addresses/{id}`；删除 `DELETE /addresses/{id}`；设默认 `PATCH /addresses/{id}/default`。
- 表单校验与后端一致：姓名 1~20 字、手机号 `^1[3-9]\d{9}$`、地址 1~120 字。
- 第一条地址后端会自动设为默认。
- 结算页跳转时带 `?select=1`，点击某条地址后写入 `session.setSelectedAddressId(id)` 并返回；结算页 `onShow` 取一次并重新试算。
- 删除地址不会删除历史订单里的地址快照；订单详情中 `address.id` 可能为 `null`，但姓名/电话/地址仍在。

### 4.10 券包页 `pages/coupon/index.vue`（新增）

- 顶部 Tab：未使用 / 已使用 / 已过期 → `GET /users/me/coupons?status=unused|used|expired`。
- 下方「可领券包」→ `GET /coupons/templates`，已领取的禁用。
- 领取 → `POST /coupons/{template_id}/claim`，成功后刷新两个列表。
- 演示账号两张券都已领取，页面应显示「已领取」。

### 4.11 榜单 `pages/rank/index.vue`

- `Promise.all([getRank('week'), getLines()])`。
- `data.items` 是完整商品字段 + `rank`；`data.new_items` 也是完整商品字段。
- 视图字段用 `toDrink()`；榜单顺序直接用后端返回顺序（`paws desc, is_hot desc, id`），前端不再排序。

---

## 5. 字段适配表

`common/api/adapters.js` 统一做转换，页面模板保持原有字段名：

### 5.1 商品

| 后端 `Product` | 视图 `drink` |
|---|---|
| `id` | `id` |
| `line_id` | `line` |
| `name` | `name` |
| `price` | `price` |
| `orig_price` | `orig` |
| `paws` | `paws` |
| `is_hot` | `hot` |
| `is_new` | `isNew` |
| `desc` | `desc` |
| `image` | `img` |
| `stock` | `stock` |

### 5.2 订单

| 后端 | 列表卡片 / 详情 |
|---|---|
| `state` / `state_text` | 颜色用 `state`，文案用 `state_text` |
| `mode` / `mode_text` | 逻辑用 `mode`，展示用 `mode_text` |
| `items[]` | 快照数组；详情逐条渲染 |
| `total` | 实付 |
| `create_time` | 毫秒时间戳 → `YYYY-MM-DD HH:mm` |

### 5.3 券 / 门店 / 用户

| 后端 | 视图 |
|---|---|
| `min_amount` | `min` |
| `coupon_count` | `coupons` |
| `level = "V2 银牌猫评员"` | `levelCode = "V2"`，`levelName = "银牌猫评员"` |
| `distance`（米） | `dist`：`205m` / `1.2km` |
| `status = open/resting/closed` | `营业中` / `即将休息` / `已打烊` |

---

## 6. 错误码与前端处理

| code | 前端处理 |
|---|---|
| `0` | 正常 |
| `-1` | 网络失败，Toast「网络请求失败，请检查后端是否启动」 |
| `1001` | 直接展示后端 `message`（参数/地址/冰糖不合法） |
| `1002` | 自动刷新一次；仍失败清会话并提示重新登录 |
| `1003` | 提示「无权操作」 |
| `1004` | 提示资源不存在，返回上一页 |
| `2001` | 商品已下架，刷新菜单 |
| `2002` | 库存不足，减少数量/取消该商品 |
| `2003` | 当前门店售罄，换门店 |
| `2004` | 门店打烊，换门店 |
| `3001` | 券门槛不足，展示 `message`（如「还差 ¥2 可用」） |
| `3002` | 券已用/过期，清空所选券并重新试算 |
| `3003` | 券已领取，按钮置灰 |
| `3004` | 券被其他待支付订单占用，取消旧单或换券 |
| `4001` | 当前状态不允许该操作，刷新订单详情 |
| `4002` | 订单已支付，刷新详情 |
| `4003` | 订单已取消，刷新详情 |
| `6001` | 积分不足 |
| `9000` | 服务内部错误，提示稍后重试 |

---

## 7. 数据库读写边界

前端**永远不直连数据库**，只通过后端接口。下表用于联调时确认「这个操作到底改了哪张表」：

| 前端动作 | 后端接口 | 数据库变化 |
|---|---|---|
| 启动 / 登录 | `POST /auth/wx-login` | 首次登录插入 `users`；不新增券 |
| 看菜单 | `GET /menu/*` | 只读 `products`、`product_lines`、`toppings` |
| 领券 | `POST /coupons/{id}/claim` | 插入 `user_coupons`（快照标题/门槛/减免/过期时间） |
| 试算 | `POST /orders/price-preview` | 只读；不改券、不锁库存 |
| 提交订单 | `POST /orders` | 插入 `orders`、`order_items`、`order_item_toppings`、`idempotency_keys`；`user_coupons.locked_by` 置订单号 |
| 支付回调 | `POST /payments/wechat/notify` | `orders` → making、写 `pay_time/pick_code/transaction_id`；扣 `products.stock`；`user_coupons.status` → used；`users.points` 增加；插入 `points_logs` |
| 取消（待支付） | `POST /orders/{no}/cancel` | `orders.state` → cancelled；释放 `user_coupons.locked_by` |
| 取消（制作中） | `POST /orders/{no}/cancel` | 同上，并回补 `products.stock`、扣回积分、插 `points_logs` |
| 模拟出杯 | `POST /orders/{no}/complete` | `orders.state` → completed、写 `finish_time` |
| 评价 | `POST /orders/{no}/review` | 写 `orders.review_rating/review_content/review_created_at` |
| 新增/编辑/删除地址 | `/addresses` | 写 `addresses`；删除默认地址会提升下一条为默认；历史订单 `orders.address_id` 由外键置 NULL，快照字段保留 |
| 上传头像 | `POST /users/me/avatar` | 写 `users.avatar_path`，文件写 `static/avatars/` |
| 改昵称 | `PATCH /users/me` | 写 `users.nickname` |
| 积分兑换 | `POST /member/points/exchange` | `users.points` 减少、插 `points_logs`；券类兑换插 `user_coupons` |
| 收藏 | `/users/me/favorites` | 写 `favorites` |

订单金额、券抵扣、库存、积分都不要在前端直接改数据库或在本地伪造。

---

## 8. 联调步骤（按顺序）

1. **起后端**：`uvicorn main:app --reload`，打开 `/docs`。
2. **验证登录**：`POST /api/v1/auth/wx-login`，body `{"code":"demo"}`，拿到 token。
3. **验证只读**：菜单、门店、榜单、券模板。
4. **验证登录态**：`GET /users/me`、`GET /addresses`、`GET /users/me/coupons`。
5. **验证试算**：`POST /orders/price-preview`，对比小计/打包费/券/合计。
6. **验证下单支付**：`POST /orders` → `POST /payments/wechat/prepay` → `POST /payments/wechat/notify`，再查订单应为 `making`，商品库存减少，积分增加。
7. **验证取消**：另建一单不支付，取消后券应释放；已支付订单取消后库存/积分回滚。
8. **验证地址**：新增/设默认/删除；删除后回看历史配送单，地址快照仍在。
9. **跑前端页面**：H5 或微信开发者工具，按「首页 → 点单 → 详情 → 结算 → 支付 → 订单 → 我的」走一遍。
10. **切 MySQL**：导入脚本、改 `.env`、重启后重复第 2~9 步，确认不是 SQLite 特例。

### 8.1 用 curl 快速自检

```bash
# Windows Git Bash / macOS / Linux
BASE=http://127.0.0.1:8000/api/v1
TOKEN=$(curl -s -X POST $BASE/auth/wx-login \
  -H "Content-Type: application/json" \
  -d '{"code":"demo"}' | python -c "import sys,json;print(json.load(sys.stdin)['data']['access_token'])")

curl -s $BASE/users/me -H "Authorization: Bearer $TOKEN"
curl -s "$BASE/menu/products?tab=classic&page_size=100"
curl -s "$BASE/orders?state=pending_pay" -H "Authorization: Bearer $TOKEN"
```

### 8.2 前端侧检查点

- 冷启动自动登录成功，`milk_access_token` / `milk_user` 已写入。
- 菜单图片能加载：后端 `image` 是 HTTP URL，但页面实际渲染 `/static/resource/images/drink_*.jpg` 本地图，控制台不应再出现 HTTP 图片警告。
- 切换「经典 / 会员专享价 / 新品 / 我的常点」时商品变化；「我的常点」未登录时会先登录。
- 领券后按钮变「已领取」，我的页券数 +1（演示账号本身已领完，需换新账号验证）。
- 结算页金额与 `/orders/price-preview` 完全一致；切换自取/外送时打包费变化。
- 外送未选地址时不能提交；选择地址后能提交。
- 支付成功后订单状态变为「制作中」，出现取餐码；我的页积分增加。
- 取消待支付订单后，原券重新出现在结算页。
- 订单完成后可评价；再来一单能带回商品与规格。
- 删除默认地址后，另一条地址自动变默认；历史订单地址快照不丢。

---

## 9. 旧静态数据迁移对照

| 旧位置 | 旧用途 | 接入后 |
|---|---|---|
| `common/data/drinks.js` `LINES` | 四条产品线 | `GET /menu/lines` |
| `common/data/drinks.js` `DRINKS` | 12 款饮品 | `GET /menu/products` |
| `common/data/drinks.js` `ICE_OPTS/SUGAR_OPTS/TOPPINGS` | 规格 | `GET /menu/options` / 商品详情 |
| `common/data/shop.js` `STORE` | 会员统计 | `GET /users/me` |
| `common/data/shop.js` `COUPONS` | 券模板 | `GET /coupons/templates` + `POST claim` |
| `common/data/orders.js` | storage 订单增删改查 | `/orders` 系列接口 |
| `common/data/orders.js` `saveOrder` | 前端算价建单 | `/orders/price-preview` + `/orders` |
| `common/data/orders.js` `countByState` | 我的页角标 | `GET /orders/counts` |
| `common/utils/image.js` `genImg/genBanner` | 远程生成图 | 后端静态图 / 本地 banner，不再需要 |
| `pages/user` 本地随机昵称、base64 头像 | 假用户 | `/users/me`、`PATCH /users/me`、头像上传 |
| `pages/checkout` 静态地址 | 假地址 | `/addresses` + 地址页 |
| `pages/order/*` 中文状态 | 前端改状态 | 后端状态机 + `state/state_text` |

---

## 10. 演示环境边界

1. **支付是模拟的**：`prepay` 返回假参数，`notify` 不验签、直接置成功。真实接入时前端改 `uni.requestPayment`，后端补 APIv3 验签与解密。
2. **微信登录是模拟的**：`code=demo` 固定映射到 1001；其他 code 按哈希生成 openid。真实接入需 `code2session`。
3. **demo 账号共享**：订单、积分、券的修改会写进默认 `milktea.db`，多人同时演示会互相影响。需要隔离时复制一份数据库或换独立登录 code。
4. **待支付订单不会自动超时取消**：后端的 15 分钟超时策略未实现定时任务；券会一直锁定，需手动取消订单释放。演示完请取消未支付订单。
5. **库存在支付时扣减**：创建订单只校验库存，支付回调才扣库存；高并发下真实项目需要更严格的锁与超时释放。
6. **图片域名**：12 张商品图已随小程序打包，`resolveImage()` 会优先使用本地图，因此不再依赖后端图床；上传头像仍以 HTTP 地址保存，微信开发者工具/真机需 HTTPS 才能显示，开发期刷新后会回退到本地默认头像。真机调用接口时 `BASE_URL` 与 `API_BASE_URL` 仍需同步改成电脑局域网 IP。
7. **搜索入口**：后端 `GET /menu/products?keyword=` 已支持，当前点单页搜索按钮仍是占位交互，未接 UI。

---

## 11. 实现与联调记录（2026-10-25）

### 11.1 已落地范围

- 请求层：`common/config.js`、`common/api/request.js`（统一解包、Bearer、401/1002 自动刷新并重放、上传）、`common/api/token.js`（会话缓存）、`common/api/auth.js`（静默登录、资料、昵称、头像）。
- 业务接口层：`catalog`、`coupons`、`addresses`、`orders`、`users`、`member`、`adapters`；页面只消费视图字段，价格与状态以服务端为准。
- 页面：首页、点单、详情、榜单、结算、订单列表、订单详情、我的均已改为接口数据；新增 `pages/coupon/index.vue`（券包）和 `pages/address/index.vue`（收货地址），并已注册到 `pages.json`。
- 启动：`App.vue` 调用 `ensureLogin()` 静默登录；`pages/user` 支持昵称修改、头像上传、订单角标、券包/地址入口。
- 结算：创建订单使用稳定 `Idempotency-Key`，随后执行演示支付；支付失败时保留订单并跳转详情页继续支付。
- 订单详情：支持多商品快照、取消、模拟出杯、评价、再来一单；地址被删除时仍显示历史快照。

### 11.2 本次实际验证

用真实后端 + stdlib `urllib` 跑通：登录/刷新、用户资料、订单角标、四条产品线、12 个商品、会员/新品/常点筛选、榜单、门店、券模板与我的券、地址增改删与设默认、试算、创建订单、模拟支付、支付后 `making` 与取餐码、取消后积分回滚、重复下单、重复领券 `3003`、三类门店试算。

另用 Node 模拟 `uni.request`，直接加载 `common/api/*` 跑同一套链路，验证了：

- `toDrink` / `toOrderSummary` / `toOrder` 字段映射；
- query 空值过滤、统一响应解包、`ApiError`；
- access_token 被篡改时，refresh_token 能自动换新并成功重放请求。

验证后已用 `database/build_sqlite.py --force` 重建种子库，当前演示库为初始状态（0 订单、用户 1001、优惠券 501/502 未使用）。

### 11.3 尚需在 HBuilderX 里做的检查

本仓库是 HBuilderX 工程，未提供可直接运行的 CLI/H5 构建依赖，因此页面级交互未在浏览器或微信开发者工具中实际点击验证。请按 8.2 检查点运行一遍；重点看头像上传（`uni.chooseMedia` + `uni.uploadFile`）和真实机型上的图片域名（`config.js` 的 `API_BASE_URL`、后端 `.env` 的 `BASE_URL` 需同时改为局域网 IP）。

### 11.4 让微信开发者工具加载后端真实图片（HTTPS）

微信 `<image>` 只接受 HTTPS；开发者工具里的「不校验合法域名」只放开 `uni.request` / `uni.uploadFile`，不会放开图片组件。所以想让小程序显示后端 `static/images` 里的图，必须让后端也走 HTTPS：

1. 生成自签名证书（Git Bash，在 `fastapi_demo` 目录执行）：
   ```bash
   mkdir -p certs
   MSYS_NO_PATHCONV=1 openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
     -keyout certs/key.pem -out certs/cert.pem \
     -subj "/CN=127.0.0.1" -addext "subjectAltName=IP:127.0.0.1,DNS:localhost"
   ```
2. 后端 `.env` 增加一行 `BASE_URL=https://127.0.0.1:8000`（已有 `DATABASE_URL` 不用动）。
3. 停掉原来的 HTTP 服务，改成 HTTPS 启动：
   ```bash
   .venv/Scripts/python -m uvicorn main:app --host 0.0.0.0 --port 8000 \
     --ssl-keyfile certs/key.pem --ssl-certfile certs/cert.pem
   ```
4. 前端 `common/config.js` 改成 `API_BASE_URL = 'https://127.0.0.1:8000'`。
5. 微信开发者工具：详情 → 本地设置 → 勾选「不校验合法域名、web-view（业务域名）、TLS 版本以及 HTTPS 证书」，然后重新编译。
6. 验证：`curl -k https://127.0.0.1:8000/static/images/drink_1.jpg` 返回 200；小程序内商品图地址应为 `https://...`。

`resolveImage()` 现在只把 HTTP 图片映射为本地图；HTTPS 地址会原样交给 `<image>`。`BASE_URL` 与 `API_BASE_URL` 必须协议、主机、端口完全一致，否则图片仍是另一个地址。自签名证书只用于本机开发，真要真机预览时建议换正式 HTTPS 域名或可信证书。不想配 HTTPS 就继续保持现状：商品图用小程序包内本地图，上传头像回退默认头像。

### 11.5 微信开发者工具控制台排障（2026-10-25）

- **ENOENT `common/data/index.js` / `common/data/shop.js` / `common/utils/image.js`**：旧增量构建缓存里的文件清单，源码和当前 `unpackage/dist` 都已经不再引用这些模块。重新运行到微信开发者工具（完整编译）即可；若仍出现，在开发者工具执行「工具 → 清缓存 → 全部清除」后重编。构建产物被运行中的 HBuilderX 占用时无法从外部删除，清理由重新编译完成。
- **`<wx-image> 图片链接 ... 不再支持 HTTP 协议`**：基础库 3.17.4 起 `<image>` 拒绝 HTTP。`adapters.js` 新增 `resolveImage()`，把后端 `http://.../static/images/drink_*.jpg`、`avatar.jpg` 映射为包内 `/static/resource/images/*`；订单详情 `items[].image` 同样映射。上传头像属于运行时文件，微信端先显示本地预览、重启后回退默认头像，正式部署需 HTTPS。
- **`wx.getSystemInfoSync is deprecated`**：首页和点单页改用 `uni.getWindowInfo()`；`manifest.json` 已关闭 `uniStatistics`，减少 uni 统计产生的同类调用。
- **仍会出现的日志**：`调试器日志回显 socket`、`preloaded ...`、`Subpackages: N/A`、`LazyCodeLoading` 属于微信开发者工具/uni 框架内部提示，不影响页面运行。
