# 四猫茶学园 · 统一数据字典

> 版本：v1.0（2026-10-25）
> 适用范围：`fronted/`（uni-app + Vue3）、`fastapi_demo/`（FastAPI）、数据库脚本（SQLite / MySQL）
> 配套文件：
> - 接口定义：[`fronted/docs/backend-api.md`](../fronted/docs/backend-api.md)
> - SQLite 建表：[`fastapi_demo/database/schema_sqlite.sql`](../fastapi_demo/database/schema_sqlite.sql)
> - MySQL 建表：[`fastapi_demo/database/schema_mysql.sql`](../fastapi_demo/database/schema_mysql.sql)
> - SQLite 生成脚本：[`fastapi_demo/database/build_sqlite.py`](../fastapi_demo/database/build_sqlite.py)

本文档是前端、接口、数据库三者之间的**唯一数据契约**。任何字段改名、枚举增减、表结构调整，都必须同步修改本文档和两份 SQL。

---

## 1. 分层与命名约定

### 1.1 三层数据形态

| 层 | 风格 | 枚举值 | 金额 | 图片 |
|---|---|---|---|---|
| 前端本地数据 | camelCase / 中文 | 中文（`待支付`、`自取`） | `number`（元） | 本地路径 `/static/resource/images/...` |
| API（FastAPI） | snake_case | 英文（`pending_pay`、`pickup`）+ 中文展示字段 | `float`（元，两位小数） | 完整 URL（`BASE_URL` + 相对路径） |
| 数据库 | snake_case | 英文，带 `CHECK` 约束 | `DECIMAL(10,2)`（MySQL）/ `NUMERIC(10,2)`（SQLite） | 相对路径 `/static/images/...` |

### 1.2 通用类型

| 逻辑类型 | 数据库 | API | 前端 | 说明 |
|---|---|---|---|---|
| 金额 | `DECIMAL(10,2)` / `NUMERIC(10,2)` | `float` | `number` | 单位元，保留两位；计算后 `round(x, 2)` |
| 时间 | `BIGINT` | `int` | `number` | Unix 毫秒时间戳（UTC），前端按本地时区展示 |
| 布尔 | `TINYINT(1)` / `INTEGER` `0/1` | `bool` | `boolean` | SQLite 无原生布尔 |
| 图片 | `*_path` 相对路径 | `image` / `avatar` 完整 URL | `img` / `avatar` | 数据库不存域名，便于换 CDN |
| 主键 | `INT ... AUTO_INCREMENT` / `INTEGER PRIMARY KEY AUTOINCREMENT` | `int` | `number` | 用户从 1001 起，券从 501 起 |
| 业务单号 | `TEXT` / `VARCHAR(32)` | `string` | `string` | `CAT` + 毫秒时间戳 + 3 位随机数 |

### 1.3 枚举总表

| 枚举 | 取值 | 中文 | 使用位置 |
|---|---|---|---|
| 门店状态 `stores.status` | `open` / `resting` / `closed` | 营业中 / 休息中 / 已打烊 | 菜单页门店行、选店弹层 |
| 订单状态 `orders.state` | `pending_pay` / `making` / `completed` / `cancelled` | 待支付 / 制作中 / 已完成 / 已取消 | 订单列表 Tab、详情页 |
| 取餐方式 `orders.mode` | `pickup` / `delivery` | 自取 / 外送 | 结算页、订单页 |
| 优惠券状态 `user_coupons.status` | `unused` / `used` / `expired` | 未使用 / 已使用 / 已过期 | 我的优惠券 |
| 积分流水类型 `points_logs.type` | `order` / `refund` / `exchange` / `history` | 下单奖励 / 取消退回 / 积分兑换 / 历史积分 | 积分明细 |
| 兑换商品类型 `exchange_items.item_type` | `coupon` | 优惠券 | 积分兑换 |
| 猫评分 `products.paws` | `1` ~ `5` | 1~5 爪 | 排行榜、详情页 |

### 1.4 不落库的固定选项

冰度和糖度是全局固定常量，由 API `/menu/options` 下发，不建表：

```text
ice_options   = ["正常冰", "少冰", "去冰", "热饮"]
sugar_options = ["全糖", "七分糖", "五分糖", "三分糖", "不加糖"]
```

小料（`toppings`）有价格，必须建表；前端目前只有 `name/price`，接入后统一使用数据库 `id` 下单。

---

## 2. 实体总览

| # | 表 | 对应 API 模型 | 前端数据来源 | 说明 |
|---|---|---|---|---|
| 1 | `member_levels` | `MemberProfileOut` 的等级计算 | `shop.js` 的 `user.level` | 会员等级阈值 |
| 2 | `users` | `UserOut` | `shop.js` `user` + 本地昵称/头像 | 用户账户 |
| 3 | `product_lines` | `LineOut` | `drinks.js` `LINES` | 四条产品线 |
| 4 | `products` | `ProductOut` | `drinks.js` `DRINKS` | 12 款饮品 |
| 5 | `toppings` | `ToppingOut` | `drinks.js` `TOPPINGS` | 小料 |
| 6 | `stores` | `StoreOut` | `pages/menu` 门店数组 | 3 家门店 |
| 7 | `coupon_templates` | `CouponTemplateOut` | `shop.js` `COUPONS` | 可领取券模板 |
| 8 | `user_coupons` | `CouponOut` | 结算页可用券、我的券 | 用户券实例 |
| 9 | `addresses` | `AddressOut` | 结算页地址 | 收货地址 |
| 10 | `favorites` | `FavoriteOut` | 详情页收藏、我的常点 | 用户收藏 |
| 11 | `orders` | `OrderOut` | `localStorage: milk_orders` | 订单主表 + 快照 |
| 12 | `order_items` | `OrderItemOut` | 本地订单的 `drink_id/spec/count` | 订单明细快照 |
| 13 | `order_item_toppings` | `OrderItemOut.topping_ids` | 本地订单 `spec` 中的小料 | 明细小料快照 |
| 14 | `points_logs` | `PointsLogOut` | 会员积分明细 | 积分流水 |
| 15 | `exchange_items` | `ExchangeItemOut` | 积分兑换列表 | 积分兑换商品 |
| 16 | `idempotency_keys` | 无（内部） | 无 | 下单幂等 |

---

## 3. 字段字典

### 3.1 `member_levels` 会员等级

| 数据库字段 | API / 前端 | 类型 | 约束 | 说明 |
|---|---|---|---|---|
| `code` | `level` 的前半段 | TEXT | PK | `V1` ~ `V4` |
| `name` | `level` 的后半段 | TEXT | NOT NULL | `见习猫评员` 等 |
| `min_points` | 等级计算 | INTEGER | `>= 0` | 达到该积分即升级 |
| `sort_order` | — | INTEGER | NOT NULL | 展示顺序 |

- API 的 `level` 由 `${code} ${name}` 拼接，例如 `V2 银牌猫评员`，保证与现有前端文案一致。
- 等级阈值：V1 = 0、V2 = 200、V3 = 800、V4 = 2000。

### 3.2 `users` 用户

| 数据库字段 | API | 前端 | 类型 | 约束 | 说明 |
|---|---|---|---|---|---|
| `id` | `id` | — | INTEGER | PK | 演示用户 1001 |
| `openid` | 不下发 | — | TEXT | UNIQUE, NOT NULL | 微信 openid |
| `nickname` | `nickname` | `cat_nickname`（本地覆盖） | TEXT | 1~20 字 | 默认 `猫友1234` |
| `avatar_path` | `avatar` | `local_avatar`（本地覆盖） | TEXT | 相对路径 | 默认 `/static/images/avatar.jpg` |
| `level_code` | `level` | `user.level` | TEXT | FK → `member_levels.code` | 写积分时同步更新 |
| `points` | `points` | `user.points` | INTEGER | `>= 0` | 当前积分 |
| `balance` | `balance` | `user.balance` | DECIMAL/NUMERIC | `>= 0` | 当前余额（元） |
| `created_at` | `created_at` | — | BIGINT | NOT NULL | 注册时间 |

- `coupon_count` 不存表，由 `user_coupons` 中 `status='unused'` 且未过期的数量实时统计。
- 本地 `cat_nickname`、`local_avatar` 是接入前的临时覆盖，接入后分别改为 `PATCH /users/me` 与 `POST /users/me/avatar`。

### 3.3 `product_lines` 产品线

| 数据库字段 | API | 前端 | 类型 | 约束 | 说明 |
|---|---|---|---|---|---|
| `id` | `id` | `id` | TEXT | PK | `buchi` / `sakamoto` / `tom` / `tama` |
| `name` | `name` | `name` | TEXT | NOT NULL | 系列全名 |
| `tag` | `tag` | `tag` | TEXT | NOT NULL | 醇厚 / 纯选 / 甜心 / 清爽 |
| `en` | `en` | `en` | TEXT | NOT NULL | 英文名 |
| `description` | `desc` | `desc` | TEXT | NOT NULL | 一句话描述 |
| `color` | `color` | `color` | TEXT | `#RRGGBB` | 主题色 |
| `bg` | `bg` | `bg` | TEXT | `#RRGGBB` | 浅色底 |
| `sort_order` | — | 数组顺序 | INTEGER | NOT NULL | 展示顺序 |

### 3.4 `products` 饮品

| 数据库字段 | API | 前端 | 类型 | 约束 | 说明 |
|---|---|---|---|---|---|
| `id` | `id` | `id` | INTEGER | PK | 1 ~ 12 |
| `line_id` | `line_id` | `line` | TEXT | FK → `product_lines.id` | 产品线 |
| `name` | `name` | `name` | TEXT | NOT NULL | 饮品名 |
| `price` | `price` | `price` | DECIMAL/NUMERIC | `>= 0` | 现价（会员价） |
| `orig_price` | `orig_price` | `orig` | DECIMAL/NUMERIC | 可空 | 有值即显示划线价 |
| `paws` | `paws` | `paws` | INTEGER | 1~5 | 猫评分 |
| `is_hot` | `is_hot` | `hot` | BOOL | 0/1 | 招牌 |
| `is_new` | `is_new` | `isNew` | BOOL | 0/1 | 新品 |
| `description` | `desc` | `desc` | TEXT | NOT NULL | 描述 |
| `image_path` | `image` | `img` | TEXT | NOT NULL | 如 `/static/images/drink_1.jpg` |
| `stock` | `stock` | — | INTEGER | `>= 0` | 剩余库存，0 为售罄 |
| `on_sale` | `on_sale` | — | BOOL | 0/1 | 是否上架 |
| `sort_order` | — | 数组顺序 | INTEGER | NOT NULL | 展示顺序 |

- 演示版库存是**全门店共享**的简化模型；生产环境应拆 `store_products(store_id, product_id, stock)`。
- 图片相对路径由 API 层拼接 `settings.base_url`，前端模板无需改动。

### 3.5 `toppings` 小料

| 数据库字段 | API | 前端 | 类型 | 约束 | 说明 |
|---|---|---|---|---|---|
| `id` | `id` | 目前无 id | INTEGER | PK | 下单必须传 id |
| `name` | `name` | `name` | TEXT | NOT NULL | 珍珠 / 椰果 / 布丁 / 芋圆 / 芝士奶盖 |
| `price` | `price` | `price` | DECIMAL/NUMERIC | `>= 0` | 单份加价 |
| `sort_order` | — | 数组顺序 | INTEGER | NOT NULL | 展示顺序 |

### 3.6 `stores` 门店

| 数据库字段 | API | 前端 | 类型 | 约束 | 说明 |
|---|---|---|---|---|---|
| `id` | `id` | `id` | INTEGER | PK | 1 ~ 3 |
| `name` | `name` | `name` | TEXT | NOT NULL | 门店全名 |
| `area` | `area` | `area` | TEXT | NOT NULL | `星悦广场 1F` |
| `address` | `address` | — | TEXT | NOT NULL | 详细地址 |
| `lat` | `lat` | — | DOUBLE | -90~90 | 纬度 |
| `lng` | `lng` | — | DOUBLE | -180~180 | 经度 |
| `distance` | `distance` | `dist`（格式化后） | INTEGER | `>= 0` | **兜底距离**（米）；有定位时按坐标实时算，不读此列 |
| `status` | `status` | 文案 | TEXT | 枚举 | 营业状态 |
| `business_hours` | `business_hours` | — | TEXT | NOT NULL | 如 `10:00-22:00` |
| `making_cups` | `making_cups` | — | INTEGER | `>= 0` | 当前制作杯数，用于估算等待时间 |
| `pack_fee` | `pack_fee` | 打包费 | DECIMAL/NUMERIC | `>= 0` | 自取打包费 |
| `delivery_fee` | `delivery_fee` | 配送费 | DECIMAL/NUMERIC | `>= 0` | 外送配送费 |
| `sort_order` | — | 数组顺序 | INTEGER | NOT NULL | 无定位时的展示顺序 |

### 3.7 `coupon_templates` 券模板

| 数据库字段 | API | 前端 | 类型 | 约束 | 说明 |
|---|---|---|---|---|---|
| `id` | `id` | `id` | INTEGER | PK | 1 ~ 2 |
| `title` | `title` | `title` | TEXT | NOT NULL | 券名 |
| `description` | `desc` | `desc` | TEXT | NOT NULL | 如 `满15减3` |
| `cut` | `cut` | `cut` | DECIMAL/NUMERIC | `> 0` | 减免金额 |
| `min_amount` | `min_amount` | `min` | DECIMAL/NUMERIC | `>= 0` | 使用门槛（按商品小计判断） |
| `valid_days` | `valid_days` | — | INTEGER | `> 0` | 领取后有效天数 |
| `sort_order` | — | 数组顺序 | INTEGER | NOT NULL | 展示顺序 |

- `claimed` 不存表，按当前用户是否已持有该模板实时计算。

### 3.8 `user_coupons` 用户优惠券

| 数据库字段 | API | 前端 | 类型 | 约束 | 说明 |
|---|---|---|---|---|---|
| `id` | `id` | `id` | INTEGER | PK | 从 501 起 |
| `user_id` | 不下发 | — | INTEGER | FK → `users.id`，级联删除 | 持有人 |
| `template_id` | `template_id` | — | INTEGER | FK → `coupon_templates.id` | 来源模板 |
| `title` | `title` | `title` | TEXT | NOT NULL | 领取时快照 |
| `description` | `desc` | `desc` | TEXT | NOT NULL | 领取时快照 |
| `cut` | `cut` | `cut` | DECIMAL/NUMERIC | `> 0` | 领取时快照 |
| `min_amount` | `min_amount` | `min` | DECIMAL/NUMERIC | `>= 0` | 领取时快照 |
| `status` | `status` | — | TEXT | 枚举 | 未使用 / 已使用 / 已过期 |
| `expire_at` | `expire_at` | — | BIGINT | NOT NULL | 过期时间（毫秒） |
| `locked_by` | 不下发 | — | TEXT | 可空，索引 | 被哪个订单锁定（订单号） |
| `created_at` | — | — | BIGINT | NOT NULL | 领取时间 |

- 券状态流转：`unused` --下单锁定--> `locked_by=订单号` --支付--> `used`；取消订单释放回 `unused`；到期由读取时刷新为 `expired`。
- `locked_by` 不设外键：下单时先锁券再落订单号，且订单取消后需保留审计信息。

### 3.9 `addresses` 收货地址

| 数据库字段 | API | 前端 | 类型 | 约束 | 说明 |
|---|---|---|---|---|---|
| `id` | `id` | `id` | INTEGER | PK | 从 1 起 |
| `user_id` | 不下发 | — | INTEGER | FK → `users.id`，级联删除 | 所属用户 |
| `name` | `name` | `name` | TEXT | 1~20 字 | 联系人 |
| `phone` | `phone` | `phone` | TEXT | `^1[3-9]\d{9}$` | 手机号 |
| `detail` | `detail` | `detail` | TEXT | 1~120 字 | 详细地址 |
| `is_default` | `is_default` | `is_default` | BOOL | 0/1 | 默认地址；每用户至多一条，由业务层保证 |

### 3.10 `favorites` 收藏

| 数据库字段 | API | 前端 | 类型 | 约束 | 说明 |
|---|---|---|---|---|---|
| `user_id` | 不下发 | — | INTEGER | PK 之一，FK → `users.id` | 用户 |
| `product_id` | `product_id` | `drink_id` | INTEGER | PK 之一 | 商品 |
| `created_at` | — | — | BIGINT | NOT NULL | 收藏时间 |

- 联合主键 `(user_id, product_id)` 天然去重。
- “我的常点”由历史订单商品频次 + 收藏合并计算，不单独存表。

### 3.11 `orders` 订单主表

| 数据库字段 | API | 前端（本地 Order） | 类型 | 约束 | 说明 |
|---|---|---|---|---|---|
| `out_trade_no` | `out_trade_no` | `out_trade_no` | TEXT | PK | 订单号 |
| `user_id` | 不下发 | — | INTEGER | FK → `users.id` | 下单人 |
| `state` | `state` | `state`（中文） | TEXT | 枚举 | 英文状态 |
| `store_id` | `store_id` | — | INTEGER | FK → `stores.id` | 门店 |
| `store_name` | `store_name` | — | TEXT | NOT NULL | 门店名快照 |
| `mode` | `mode` | `mode`（中文） | TEXT | 枚举 | 取餐方式 |
| `subtotal` | `subtotal` | — | DECIMAL/NUMERIC | `>= 0` | 商品小计（含小料） |
| `pack_fee` | `pack_fee` | — | DECIMAL/NUMERIC | `>= 0` | 打包费或配送费 |
| `coupon_id` | 不下发 | — | INTEGER | FK → `user_coupons.id`，删除置空 | 使用的券 |
| `coupon_cut` | `coupon_cut` | — | DECIMAL/NUMERIC | `>= 0` | 券抵扣 |
| `total` | `total` | `price` | DECIMAL/NUMERIC | `>= 0` | 实付 = max(0, 小计 + 打包费 - 券) |
| `pick_code` | `pick_code` | `pick_code` | TEXT | 可空 | 取餐码，支付后生成 |
| `table_no` | `table_no` | — | TEXT/VARCHAR(8) | 可空 | 堂食桌号（扫码点餐），仅自取单可有 |
| `address_id` | `address.id` | — | INTEGER | FK → `addresses.id`，删除置空 | 下单时地址 ID |
| `address_name` | `address.name` | — | TEXT | 可空 | 地址快照 |
| `address_phone` | `address.phone` | — | TEXT | 可空 | 地址快照 |
| `address_detail` | `address.detail` | — | TEXT | 可空 | 地址快照 |
| `address_is_default` | `address.is_default` | — | BOOL | 可空 | 地址快照 |
| `remark` | `remark` | — | TEXT | 0~100 字 | 备注 |
| `create_time` | `create_time` | `create_time` | BIGINT | NOT NULL | 下单时间 |
| `pay_time` | `pay_time` | — | BIGINT | 可空 | 支付时间 |
| `finish_time` | `finish_time` | — | BIGINT | 可空 | 完成时间 |
| `review_rating` | `review.rating` | — | INTEGER | 1~5，可空 | 评价星级 |
| `review_content` | `review.content` | — | TEXT | 可空 | 评价内容 |
| `review_created_at` | `review.created_at` | — | BIGINT | 可空 | 评价时间 |
| `earning_points` | 不下发 | — | INTEGER | `>= 0` | 本单获得积分，取消时按此退回 |
| `transaction_id` | `transaction_id` | — | TEXT | 可空 | 微信支付流水号 |

- 状态与展示文案：`state_text`、`mode_text` 由 API 按枚举映射生成，不落库。
- 地址快照保证用户删改地址后历史订单仍可展示。
- 评价是 1:1 可选数据，直接放在订单表，不单开 `reviews` 表。

### 3.12 `order_items` 订单明细

| 数据库字段 | API | 前端来源 | 类型 | 约束 | 说明 |
|---|---|---|---|---|---|
| `id` | — | — | INTEGER | PK | 明细行 ID |
| `order_no` | 所属订单 | `out_trade_no` | TEXT | FK → `orders.out_trade_no`，级联删除 | 订单号 |
| `product_id` | `product_id` | `drink_id` | INTEGER | NOT NULL | 商品 ID 快照（不设 FK） |
| `name` | `name` | `name` | TEXT | NOT NULL | 商品名快照 |
| `image_path` | `image` | `img` | TEXT | NOT NULL | 图片快照 |
| `line_id` | `line_id` | `line` | TEXT | NOT NULL | 产品线快照 |
| `ice` | `ice` | `spec` 前半段 | TEXT | 枚举常量 | 冰度 |
| `sugar` | `sugar` | `spec` 后半段 | TEXT | 枚举常量 | 糖度 |
| `count` | `count` | `count` | INTEGER | 1~99 | 数量 |
| `unit_price` | `unit_price` | — | DECIMAL/NUMERIC | `>= 0` | 单价（含小料） |
| `amount` | `amount` | — | DECIMAL/NUMERIC | `>= 0` | 小计 = 单价 × 数量 |
| `sort_order` | — | 数组顺序 | INTEGER | NOT NULL | 展示顺序 |

- `topping_ids` / `topping_names` 不存列，由 `order_item_toppings` 聚合生成。
- `product_id`、`line_id` 故意不设外键：商品下架/删除不影响历史订单。

### 3.13 `order_item_toppings` 明细小料

| 数据库字段 | API | 前端来源 | 类型 | 约束 | 说明 |
|---|---|---|---|---|---|
| `id` | — | — | INTEGER | PK | 行 ID |
| `order_item_id` | — | — | INTEGER | FK → `order_items.id`，级联删除 | 明细行 |
| `topping_id` | `topping_ids[]` | 小料对象 | INTEGER | NOT NULL | 小料 ID 快照（不设 FK） |
| `name` | `topping_names` | `name` | TEXT | NOT NULL | 小料名快照 |
| `price` | 计价依据 | `price` | DECIMAL/NUMERIC | `>= 0` | 小料价快照 |
| `sort_order` | — | 数组顺序 | INTEGER | NOT NULL | 展示顺序 |

- 唯一约束 `(order_item_id, topping_id)`，防止同一行重复加料。

### 3.14 `points_logs` 积分流水

| 数据库字段 | API | 前端 | 类型 | 约束 | 说明 |
|---|---|---|---|---|---|
| `id` | `id` | `id` | INTEGER | PK | 从 1 起 |
| `user_id` | 不下发 | — | INTEGER | FK → `users.id`，级联删除 | 用户 |
| `title` | `title` | `title` | TEXT | NOT NULL | 如 `下单奖励 +14` |
| `points` | `points` | `points` | INTEGER | 可正可负 | 变动值；退回为负数 |
| `type` | `type` | `type` | TEXT | 枚举 | 流水类型 |
| `created_at` | `created_at` | `created_at` | BIGINT | NOT NULL | 发生时间 |

### 3.15 `exchange_items` 积分兑换

| 数据库字段 | API | 前端 | 类型 | 约束 | 说明 |
|---|---|---|---|---|---|
| `id` | `id` | `id` | INTEGER | PK | 1 ~ 2 |
| `title` | `title` | `title` | TEXT | NOT NULL | 如 `¥3 优惠券` |
| `cost` | `cost` | `cost` | INTEGER | `> 0` | 所需积分 |
| `item_type` | `type` | `type` | TEXT | `coupon` | 兑换类型 |
| `template_id` | 不下发 | — | INTEGER | FK → `coupon_templates.id`，可空、RESTRICT | 兑换出的券模板 |
| `sort_order` | — | 数组顺序 | INTEGER | NOT NULL | 展示顺序 |

### 3.16 `idempotency_keys` 下单幂等

| 数据库字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `user_id` | INTEGER | PK 之一，FK → `users.id`，级联删除 | 用户 |
| `idem_key` | TEXT | PK 之一 | 前端 `Idempotency-Key` 请求头 |
| `order_no` | TEXT | FK → `orders.out_trade_no`，级联删除 | 首次创建的订单号 |
| `expires_at` | BIGINT | NOT NULL，索引 | 过期时间（默认 10 分钟） |

- 不使用 Redis 时，用该表实现“同一用户 + 同一 key 重复请求返回首单”。

---

## 4. 派生字段（不落库）

| 字段 | 来源 | 规则 |
|---|---|---|
| `User.coupon_count` | `user_coupons` | `status='unused' AND expire_at > now` 的数量 |
| `User.level` | `users.level_code` + `member_levels` | `${code} ${name}` |
| `MemberProfile.growth` | `users.points` | 与积分相同（演示版成长值 = 积分） |
| `MemberProfile.next_level/progress` | `member_levels` | 按下一等级阈值计算 |
| `Order.state_text` | `orders.state` | 待支付 / 制作中 / 已完成 / 已取消 |
| `Order.mode_text` | `orders.mode` | 自取 / 外送 |
| `OrderItem.topping_ids/topping_names` | `order_item_toppings` | ID 升序，名称用 `+` 连接 |
| `Store.distance` | 请求经纬度 + `stores.lat/lng` | 有定位时实时计算（米）；无定位时用 `stores.distance` |
| `Product.available` | `products.stock/on_sale` | `on_sale=1 AND stock>0` 才可下单 |
| `CouponTemplate.claimed` | `user_coupons` | 当前用户是否已持有该模板 |
| `RankItem.rank` | `products` | 按 `paws` / 销量排序后的序号 |
| `PricePreview.estimated_ready_minutes` | `stores.making_cups` | `8 + making_cups // 5` |

---

## 5. 前端页面 → 数据 → 接口

| 页面 | 当前读取的数据 | 接入后的接口 |
|---|---|---|
| 首页 `pages/index` | `DRINKS`、`LINES`、`COUPONS`、`STORE` | `/menu/lines`、`/menu/products`、`/coupons/templates`、`/stores` |
| 点单页 `pages/menu` | `DRINKS`、`LINES`、静态门店数组 | `/menu/products`、`/menu/options`、`/stores` |
| 详情页 `pages/detail` | `DRINKS`、`LINES`、`TOPPINGS`、`ICE_OPTS`、`SUGAR_OPTS` | `/menu/products/{id}`、`/menu/options`、`/users/me/favorites` |
| 结算页 `pages/checkout` | `session.checkoutDraft`、`TOPPINGS`、静态券 | `/orders/price-preview`、`/coupons/usable`、`/addresses`、`/orders` |
| 订单列表 `pages/order/index` | `milk_orders` | `/orders/counts`、`/orders?state=` |
| 订单详情 `pages/order/order` | `milk_orders` | `/orders/{no}`、`/payments/{no}`、`/orders/{no}/cancel`、`/orders/{no}/review`、`/orders/{no}/repeat` |
| 我的 `pages/user` | `STORE.user`、`milk_orders`、`cat_nickname`、`local_avatar` | `/users/me`、`/member/profile`、`/orders/counts`、`/users/me/coupons` |
| 排行榜 `pages/rank` | `DRINKS` | `/menu/rank?period=week` |
| 扫码入口 `pages/index`、`pages/menu` | 静态桌码 | `/tables/resolve` |
| 店员核销 `pages/staff/verify` | — | `/staff/pickup/lookup`、`/staff/pickup/complete` |

### 5.1 前端本地存储对照

| 存储 | 内容 | 接入后处理 |
|---|---|---|
| `milk_orders` | 本地订单数组 | 首次登录后用 `/orders` 覆盖；未登录时保留为草稿 |
| `cat_nickname` | 用户改过的昵称 | 调 `PATCH /users/me` 成功后清除 |
| `local_avatar` | base64 头像 | 调 `POST /users/me/avatar` 成功后清除 |
| `session.checkoutDraft` | `{ drink, ice, sugar, toppings, count, mode }` | 仅页面间临时状态，不落库 |
| `session.ordersFilter` | 中文状态或 `null` | 仅页面跳转临时状态 |
| `milk_table_context` | `{storeId, storeName, tableNo}` | 扫码堂食上下文，取消堂食或换门店时清除 |
| `milk_staff_pin` | 店员核销口令 | 仅本机保存，演示用 |

### 5.2 结算草稿字段映射

| 草稿字段 | 下单请求字段 | 说明 |
|---|---|---|
| `drink.id` | `items[].product_id` | 商品 ID |
| `ice` | `items[].ice` | 冰度 |
| `sugar` | `items[].sugar` | 糖度 |
| `toppings[].name/price` | `items[].topping_ids[]` | 接入后改为传 ID，服务端计价 |
| `count` | `items[].count` | 数量 |
| `mode`（`自取`/`外送`） | `mode`（`pickup`/`delivery`） | 枚举转换 |
| `tableNo` | `table_no` | 扫码堂食时必填；仅自取单 |
| — | `store_id` | 当前选中门店 |
| — | `coupon_id` | 选中的券 |
| — | `address_id` | 外送必填 |
| — | `remark` | 备注 |

---

## 6. 表关系

| 父表 | 子表 | 关系 | 外键 | 删除行为 |
|---|---|---|---|---|
| `member_levels` | `users` | 1 : N | `users.level_code` | RESTRICT |
| `users` | `user_coupons` | 1 : N | `user_coupons.user_id` | CASCADE |
| `users` | `addresses` | 1 : N | `addresses.user_id` | CASCADE |
| `users` | `favorites` | 1 : N | `favorites.user_id` | CASCADE |
| `users` | `orders` | 1 : N | `orders.user_id` | RESTRICT |
| `users` | `points_logs` | 1 : N | `points_logs.user_id` | CASCADE |
| `users` | `idempotency_keys` | 1 : N | `idempotency_keys.user_id` | CASCADE |
| `product_lines` | `products` | 1 : N | `products.line_id` | RESTRICT |
| `products` | `favorites` | 1 : N | `favorites.product_id` | CASCADE |
| `stores` | `orders` | 1 : N | `orders.store_id` | RESTRICT |
| `coupon_templates` | `user_coupons` | 1 : N | `user_coupons.template_id` | RESTRICT |
| `coupon_templates` | `exchange_items` | 1 : N | `exchange_items.template_id` | RESTRICT |
| `user_coupons` | `orders` | 1 : N | `orders.coupon_id` | SET NULL |
| `addresses` | `orders` | 1 : N | `orders.address_id` | SET NULL |
| `orders` | `order_items` | 1 : N | `order_items.order_no` | CASCADE |
| `order_items` | `order_item_toppings` | 1 : N | `order_item_toppings.order_item_id` | CASCADE |
| `orders` | `idempotency_keys` | 1 : N | `idempotency_keys.order_no` | CASCADE |

```text
member_levels ──< users ──< user_coupons ──< orders ──< order_items ──< order_item_toppings
                    │            └──< orders.coupon_id (SET NULL)
                    ├──< addresses ──< orders.address_id (SET NULL)
                    ├──< favorites >── products >── product_lines
                    ├──< points_logs
                    └──< idempotency_keys >── orders
stores ──< orders
coupon_templates ──< user_coupons
                └──< exchange_items
```

---

## 7. 业务规则

### 7.1 计价（服务端为准）

```text
商品单价 = 饮品 price + Σ 小料 price
商品小计 = Σ(商品单价 × 数量)                    → orders.subtotal
打包费   = pickup ? stores.pack_fee : stores.delivery_fee
券抵扣   = 用户选中且满足 min_amount 的一张券的 cut   → orders.coupon_cut
实付     = max(0, 商品小计 + 打包费 - 券抵扣)        → orders.total
```

- 券门槛按**商品小计**判断，不含打包费。
- 前端计算结果只用于展示，下单必须由服务端重算。
- 下单时写入商品名、图片、单价、小料名与小料价的**快照**。

### 7.2 订单状态机

```text
pending_pay --支付成功--> making --制作完成--> completed
     |                       |
     +--用户取消 / 超时--------+--> cancelled
```

- 支付时扣库存、核销券、加积分（`earning_points = int(total)`）。
- `making` 取消时回滚库存、退回积分、释放券。
- 只有 `completed` 且未评价的订单可评价。

### 7.3 一致性要求

1. **金额**：写库前 `round(x, 2)`；数据库 `DECIMAL(10,2)`；禁止用浮点累加后直接落库。
2. **时间**：全部存毫秒时间戳；`create_time <= pay_time <= finish_time`。
3. **积分**：`users.points = 该用户 points_logs.points 之和`（演示版以 `users.points` 为准，流水用于展示与审计）。
4. **等级**：修改积分后必须同步 `users.level_code`。
5. **券**：同一券同一时间最多被一个订单锁定；支付后必须清空 `locked_by`。
6. **地址**：每个用户最多一条 `is_default = 1`，由业务层在事务内维护。
7. **图片**：数据库只存相对路径，API 层统一拼接域名。

---

## 8. 种子数据

| 表 | 行数 | 内容 |
|---|---|---|
| `member_levels` | 4 | V1 ~ V4 |
| `product_lines` | 4 | 布奇 / 坂本 / 汤姆 / 玉 |
| `products` | 12 | 四条线各 3 款，价格 9 ~ 16 元 |
| `toppings` | 5 | 珍珠、椰果、布丁、芋圆、芝士奶盖 |
| `stores` | 3 | 星悦广场（休息中）、万象城、大学城 |
| `coupon_templates` | 2 | 满15减3、满25减5 |
| `exchange_items` | 2 | 100 积分兑 ¥3 券、200 积分兑 ¥5 券 |
| `users` | 1 | 演示用户 1001 |
| `user_coupons` | 2 | 501 / 502，均未使用且未锁定 |
| `addresses` | 1 | 张女士 · 星悦广场 3 栋 502（默认） |
| `favorites` | 2 | 商品 1、商品 8 |
| `points_logs` | 1 | 历史积分 +320 |
| `orders` / `order_items` / `order_item_toppings` | 0 | 不预置订单 |
| `idempotency_keys` | 0 | 运行时产生 |

演示账号：

| 字段 | 值 |
|---|---|
| `users.id` | 1001 |
| `openid` | `mock-openid-demo` |
| 昵称 | 猫友1234 |
| 等级 | V2 银牌猫评员（320 积分） |
| 余额 | ¥8.50 |
| 注册时间 | 1788220800000（2026-09-01 08:00 UTC+8） |
| 券 | 501 满15减3、502 满25减5，过期时间 1893456000000（2030-01-01 08:00 UTC+8） |

登录方式：`POST /api/v1/auth/wx-login`，请求体 `{"code": "demo"}`。

---

## 9. 数据库文件与使用

### 9.1 文件说明

| 文件 | 用途 |
|---|---|
| `schema_sqlite.sql` | SQLite 建表 + 索引 + 种子数据 |
| `schema_mysql.sql` | MySQL 8.0 建库建表 + 索引 + 种子数据 |
| `build_sqlite.py` | 用 Python 标准库 `sqlite3` 生成 `milktea.db`，无需安装依赖 |
| `milktea.db` | 已生成的 SQLite 数据库文件 |

### 9.2 重建 SQLite

```bash
cd fastapi_demo
python database/build_sqlite.py            # 生成 database/milktea.db
python database/build_sqlite.py --force    # 覆盖已有文件
```

脚本会执行 `PRAGMA foreign_keys=ON` 并校验表数量、种子行数和外键完整性。

### 9.3 导入 MySQL

用 Navicat 打开连接后运行 `schema_mysql.sql`，或使用命令行：

```bash
mysql -u root -p < fastapi_demo/database/schema_mysql.sql
```

脚本会创建数据库 `milktea`（utf8mb4 + InnoDB）并写入种子数据。数据库账号密码请通过本地环境配置，不要写进仓库。

### 9.4 差异说明

| 项 | SQLite | MySQL |
|---|---|---|
| 自增 | `INTEGER PRIMARY KEY AUTOINCREMENT` | `INT AUTO_INCREMENT` |
| 布尔 | `INTEGER` + `CHECK IN (0,1)` | `TINYINT(1)` |
| 金额 | `NUMERIC(10,2)`（NUMERIC 亲和） | `DECIMAL(10,2)` |
| 字符串 | `TEXT` | `VARCHAR(n)` / `TEXT` |
| 外键检查 | 连接级 `PRAGMA foreign_keys=ON` | 默认开启 |
| 种子插入 | `INSERT OR IGNORE` | `INSERT IGNORE` |
| 时区 | 时间戳与库无关，前端本地化 | 同左 |

> SQLite 的 `NUMERIC(10,2)` 只是亲和类型，底层仍可能按浮点存储；正式环境以 MySQL 的 `DECIMAL(10,2)` 为金额准绳，SQLite 仅用于本地演示。

### 9.5 后端运行时接入

`fastapi_demo` 使用 SQLAlchemy 2.0 ORM，模型定义在 `app/models.py`，字段与本文档一一对应；应用启动时**不会自动建表**，需先准备数据库。

| 环境 | 操作 |
|---|---|
| 默认 SQLite | 确保 `fastapi_demo/database/milktea.db` 存在（可用 `build_sqlite.py` 重新生成） |
| MySQL | 先导入 `schema_mysql.sql`，再在 `fastapi_demo/.env` 中设置 `DATABASE_URL` |

```bash
# fastapi_demo/.env（不要提交）
DATABASE_URL=mysql+pymysql://root:你的密码@127.0.0.1:3306/milktea?charset=utf8mb4
```

- 金额在 ORM 层使用 `Decimal`，接口序列化时转 `float`。
- 图片字段存相对路径（如 `/static/images/drink_1.jpg`），接口输出时拼接 `BASE_URL`。
- 订单中的商品、小料、收货地址均为下单时快照；删除地址后 `orders.address_id` 置 NULL，快照字段仍保留用于历史展示。
- 写操作在请求内提交事务；库存扣减与订单支付使用 `SELECT ... FOR UPDATE`（MySQL 生效）。
- AI 点单助手不新增数据表：对话按用户保存在进程内存（2 小时），下单仍写入 `orders` / `order_items` / `order_item_toppings` / `idempotency_keys`，结构调整与普通下单一致。

---

## 10. 变更流程

1. 先改本文档（字段、类型、枚举、规则）。
2. 同步修改 `schema_sqlite.sql` 与 `schema_mysql.sql`，保持列名与约束一致。
3. 重新生成 `milktea.db`，核对表结构和种子行数。
4. 同步更新 `fronted/docs/backend-api.md` 与 FastAPI 的 Pydantic 模型。
5. 前端字段映射变化时，更新第 5 节与 `backend-api.md` 第 9.1 节。
