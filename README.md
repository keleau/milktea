# 四猫茶学园 · 奶茶点单小程序

一个可完整跑通的奶茶点单全栈项目：**uni-app（Vue 3）+ FastAPI + SQLite**。覆盖微信登录、扫码堂食、菜单规格/加料、优惠券与会员价、自取/外送结算、模拟支付、订单状态机、取餐二维码与店员核销，并接入 **LangGraph + DeepSeek** 实现 AI 点单助手。

> 这是课程设计 / 面试演示项目，不是生产系统：支付、微信登录降级、店员权限和部分并发设计都按演示边界实现，详见「已知限制」。

---

## 项目规模

- 前端 13 个页面：登录、首页、点单、商品详情、榜单、结算、订单列表、订单详情、我的、券包、地址、AI 助手、店员核销
- 后端 16 张表、4 条产品线、12 款饮品、3 家门店、22 张桌码
- 完整链路：微信登录 → 扫码绑定桌号 → 选规格/加料 → 购物车/结算 → 优惠券/会员价 → 创建订单 → 模拟支付 → 取餐码/二维码 → 店员核销 → AI 点单

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | uni-app + Vue 3 + uni-ui，HBuilderX 工程 |
| 后端 | FastAPI + SQLAlchemy 2 + Pydantic v2 + Uvicorn |
| 数据库 | SQLite（默认）；提供 MySQL 建表脚本与 `DATABASE_URL` 切换配置，未做 MySQL 压测 |
| AI 点单 | LangGraph + LangChain，DeepSeek Chat（OpenAI 兼容接口） |
| 微信能力 | `code2session` 登录、`chooseAvatar` + `type="nickname"` 头像昵称、`uni.scanCode`、`wxacode.getUnlimited` 小程序码、微信 `access_token` 进程内缓存 |
| 测试 | pytest + FastAPI TestClient + 独立临时 SQLite 库 + 并发脚本 |

## 目录结构

```
milktea/
├─ fronted/                         # uni-app 小程序
│  ├─ pages/                        # 13 个页面
│  ├─ components/                   # 商品卡、券票、分类栏、订单商品行、AI 浮窗等
│  ├─ common/
│  │  ├─ api/                       # 请求封装、鉴权、订单、券、地址、AI
│  │  ├─ store/                     # 会话、桌号上下文、AI 浮窗状态
│  │  └─ utils/                     # 扫码、图片、缓存、订单规格/金额格式化
│  ├─ docs/                         # 接口清单与前后端联调说明
│  └─ design.md / premium.css       # 视觉规范与全局样式
├─ fastapi_demo/                    # FastAPI 后端
│  ├─ app/api/v1/                   # auth/users/stores/menu/orders/payments/staff/ai...
│  ├─ app/services/                 # 定价、订单、优惠券、核销、微信、ai_agent
│  ├─ database/                     # SQLite/MySQL schema、种子库、桌码生成
│  ├─ tests/                        # pytest：订单一致性、券/积分、API smoke/E2E
│  ├─ scripts/                      # concurrency_check.py 可复现并发检查
│  ├─ docs/                         # 后端联调说明
│  └─ static/                       # 商品图、桌码、头像
└─ docs/                            # 数据字典
```

## 快速开始

### 1. 后端

```bash
cd fastapi_demo

# 首次安装运行依赖
python -m venv .venv
.venv\Scripts\activate            # Windows；macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# 需要跑测试时安装开发依赖（包含 pytest / httpx）
pip install -r requirements-dev.txt

# 首次生成种子数据库（仓库已带 milktea.db 时可跳过）
python database/build_sqlite.py

python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

- Swagger：<http://127.0.0.1:8000/docs>
- `--host 0.0.0.0` 是手机真机访问的必要条件；只在电脑调试可用 `127.0.0.1`
- 重建数据库会清空订单：`python database/build_sqlite.py --force`

### 2. 前端

1. 用 **HBuilderX** 打开 `fronted/` 目录（这是 HBuilderX 工程，不是 `npm run dev` 工程）
2. 安装微信开发者工具，并在开发者工具中开启「设置 → 安全设置 → 服务端口」
3. HBuilderX → **运行 → 运行到小程序模拟器 → 微信开发者工具**
4. 首次进入选择「演示会员登录」（预置会员 1001，带积分、券和历史订单）

### 3. 配置

复制 `fastapi_demo/.env.example` 为 `fastapi_demo/.env`，按需填写：

| 变量 | 说明 |
|---|---|
| `WECHAT_APPID` / `WECHAT_SECRET` | 微信登录与小程序码生成；不填则走演示/模拟登录 |
| `STAFF_PIN` | 店员核销口令；留空则核销接口返回 503 |
| `DEEPSEEK_API_KEY` | AI 点单助手密钥；留空则 `/ai/chat` 返回 9000/503 |
| `LLM_BASE_URL` / `LLM_MODEL` | 可选，默认 `https://api.deepseek.com/v1` / `deepseek-chat` |
| `BASE_URL` | 后端对外地址，用于拼接图片绝对地址；默认 `http://127.0.0.1:8000` |
| `DATABASE_URL` | 不填默认 SQLite；可切 MySQL |
| `SQL_ECHO` | 设为 `1` 打印 SQL |
| `ORDER_EXPIRY_MINUTES` | 待支付订单自动取消时间，默认 15 分钟 |
| `AI_MIN_INTERVAL_SECONDS` | 同一用户 AI 请求最小间隔，默认 2 秒 |

前端接口地址在 [`fronted/common/config.js`](fronted/common/config.js)：电脑调试保持 `http://127.0.0.1:8000`，真机改成电脑局域网 IP。

## 测试与并发证据

测试默认使用**独立临时 SQLite 库**，不会读写 `database/milktea.db`，可以放心重复运行。

### pytest

```bash
cd fastapi_demo
.venv\Scripts\python.exe -m pytest -q
```

当前覆盖 16 个用例：

- 创建订单预占库存；同一幂等键重复提交返回同一订单
- 两线程抢最后 1 件库存：仅 1 单成功，另 1 单返回 `2002`
- 两线程同时取消同一订单：库存只回补一次
- 支付重复回调：库存/积分不重复处理
- 制作中取消：回补库存、释放优惠券、退回积分
- 超时取消：释放库存与优惠券
- 优惠券锁定/核销/释放；同一张券不能被两个订单占用
- 桌号/外送地址校验在扣库存之前完成
- 外送订单保存地址快照；堂食订单绑定桌号
- 积分扣减不会出现负数，积分流水记录实际变动
- API smoke：演示登录、商品列表
- API E2E：下单 → 模拟支付 → 取餐码 → 店员核销

### 并发脚本（简历/答辩可直接展示）

```bash
cd fastapi_demo
.venv\Scripts\python.exe scripts/concurrency_check.py
```

脚本会把种子库复制到临时目录，然后执行两项检查：

```text
[1/2] 最后 1 件库存并发：成功 1 单，库存不足 1 单，库存 0，新增订单 1 笔
[2/2] 同一订单并发取消：取消成功 2 次，库存 0 -> 1，订单状态 cancelled
RESULT: PASS
```

这就是简历里「最后 1 件库存仅 1 单成功、重复取消仅回补一次」的可复现证据。

## 演示流程

1. 启动后端，HBuilderX 运行到微信开发者工具，完成登录（可顺手选用微信头像和昵称）
2. 点单页点「扫码」，扫 `fastapi_demo/static/qrcodes/print.html` 中的桌码（或用编译模式模拟扫码）
3. 桌号自动绑定 → 选规格加料 → 加入购物车
4. 结算页确认桌号/优惠 → 提交订单 → 模拟支付
5. 订单页出示取餐码与取餐二维码
6. 我的 → 店员核销 → 输入 `STAFF_PIN` → 扫码或手输取餐码 → 确认取餐
7. 首页/点单页右下角点猫娘 → AI 点单 → 说「少冰五分糖一杯黑糖波波厚奶茶」→ 查库存并生成订单卡片 → 去订单详情支付

### 模拟微信扫码进入

微信开发者工具 → 编译模式 → 添加编译模式：

- 启动页面：`pages/menu/index`
- 启动参数：`scene=MILKTEA%3A1%3AA01`

即可验证「扫码直达点单页并自动绑定桌号」的冷启动逻辑，无需真实扫码。

## 桌码生成

桌位配置集中在 [`fastapi_demo/app/tables.py`](fastapi_demo/app/tables.py)，scene 格式为 `MILKTEA:<门店id>:<桌号>`。

**普通二维码（应用内扫码，无需 AppID）**

```bash
cd fastapi_demo
.venv\Scripts\python database/build_table_qrcodes.py --mode plain --out static/qrcodes_plain --clean
```

**微信小程序码（原生「扫一扫」直达）**

```bash
cd fastapi_demo
.venv\Scripts\python database/build_table_qrcodes.py --mode wechat --env trial --clean
```

- 需要 `.env` 配置 `WECHAT_APPID` / `WECHAT_SECRET`
- `--env trial|develop` 生成的码只有体验成员/开发者能扫开；对外开放需 `--env release` 且小程序已发布
- 两种模式都会输出 `print.html`（打印页）和 `manifest.csv`（清单）

## 真机调试（本地后端）

1. `ipconfig` 查电脑在当前网络中的 IPv4 地址
2. 修改 [`fronted/common/config.js`](fronted/common/config.js) 的 `API_BASE_URL` 为 `http://<电脑IP>:8000`
3. 需要图片绝对地址时，在 `.env` 设置 `BASE_URL=http://<电脑IP>:8000`，然后重启后端
4. 后端用 `--host 0.0.0.0` 启动，并放行防火墙 8000 端口
5. 手机浏览器先访问 `http://<电脑IP>:8000/docs`，确认网络可达
6. 微信开发者工具 → 真机调试 → 手机微信扫码，打开调试模式

注意事项：

- 热点/网络重连后电脑 IP 可能变化，演示前重新确认
- 提交代码前把 `API_BASE_URL` 改回 `http://127.0.0.1:8000`
- 体验版/正式版强制要求公网 HTTPS 且已备案的服务器域名，「不校验合法域名」只对开发者工具生效

## 接口与文档

- Swagger：`http://127.0.0.1:8000/docs`
- 接口清单：[fronted/docs/backend-api.md](fronted/docs/backend-api.md)
- 前后端联调：[fronted/docs/frontend-backend-integration.md](fronted/docs/frontend-backend-integration.md)
- 数据字典：[docs/data-dictionary.md](docs/data-dictionary.md)

## 设计说明（面试可讲）

- **库存**：创建订单时用条件 UPDATE 预占库存（`stock >= count`），支付不再重复扣；取消/超时释放。并发下只有库存足够的请求能成功。
- **状态机**：支付、取消、核销、超时取消都用条件 UPDATE 抢占状态，重复回调/重复点击不会重复执行。
- **优惠券**：锁定、支付核销、取消释放集中在 `app/services/coupons.py`；条件 UPDATE 保证同一张券不会被两个订单占用。
- **幂等**：前端传 `Idempotency-Key`，后端用 `(user_id, key)` 唯一键；并发冲突时返回已创建订单，避免重复下单。
- **超时取消**：后台线程每 60 秒扫描待支付超时订单，先抢占状态，再释放库存/券。
- **AI 点单**：单 Agent + 3 个工具（库存查询、下单、订单查询）的有界 ReAct 循环；工具内做参数/库存/打烊/重复下单校验，AI 下单复用普通订单服务，不绕过库存和状态机；prompt 不是安全边界，服务端校验才是。
- **AI 会话**：按用户保存在进程内存（2 小时 TTL），重启/多进程会丢；生产需要 Redis/DB + 共享幂等表。

## 已知限制

- 支付为模拟流程：`prepay` 返回模拟参数，`notify` 不验签、直接置为成功；真实微信支付 APIv3 的验签/解密/退款未接入，不能用于生产。
- 未配置微信 AppID 时，微信登录使用设备 `mock_id` 生成稳定模拟账号；`code=demo` 固定登录演示会员 1001，多台设备同时演示会共享订单/积分/券。
- 店员核销使用 `.env` 中的共享口令 `STAFF_PIN`，不是店员账号 + 角色权限；演示版没有 PIN 限流。
- 头像上传后返回 `http://` 静态地址，微信基础库对 HTTP 图片有限制；当前用本地临时路径跨页预览（`milk_avatar_preview`），应用重启后可能失效，部署到 HTTPS 后恢复正常。
- 小程序码的 `trial` / `develop` 版本仅开发者与体验成员可打开。
- AI 会话保存在后端进程内存；AI 下单只支持单款自取，不会自动支付；多轮会话在重启后清空。
- 微信 `access_token` 缓存为进程内实现，多进程部署需替换为 Redis 等共享缓存。
- 登录 token 为 HMAC 签名，access / refresh 有固定有效期，未做服务端撤销/黑名单；演示够用，生产需补 jti/黑名单。
- 库存是全门店共享的简化模型，不是每店独立库存；生产应拆 `store_products(store_id, product_id, stock)`。
- 取餐码为 5 位随机码，极端情况下可能重复；扫码核销不受影响，手输重复码会提示改用扫码。
- SQLite 适合演示与单机开发，不适合多进程高并发写；生产建议 MySQL，并补充分布式锁/压测/监控。
- 管理后台、真实微信支付、每店库存、MySQL 迁移和线上部署未实现；这是演示项目，不要按生产系统宣传。

## Roadmap

- [x] pytest 覆盖库存、幂等、取消、超时、券、积分、API smoke/E2E
- [x] 可复现的并发检查脚本
- [ ] GitHub Actions 自动跑测试
- [ ] MySQL 实库回归与简单压测
- [ ] Dockerfile + Nginx + 在线 H5 演示（可选）
- [ ] 真实微信支付与对账（需商户资质）
- [ ] 同桌并发下单、库存扣减与订单幂等压测

## 说明

本项目仅用于学习、课程设计与面试演示。微信 AppSecret、店员口令、DeepSeek Key 等敏感配置只放在本地 `.env`，不要提交到仓库。
