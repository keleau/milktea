# 四猫茶学园 · 奶茶点单小程序

一个可完整跑通的奶茶点单演示项目：**uni-app（Vue 3）+ FastAPI + SQLite**。

覆盖微信登录、扫码点单、菜单规格/加料、优惠券与会员价、自取/外送结算、订单状态机、取餐二维码与店员核销的完整链路。

> 支付与微信登录在未配置真实资质时使用模拟实现，适合学习、课程设计与面试演示。

---

## 功能

- **登录**：微信一键登录（`code2session`）+ 演示会员登录；登录后可用微信原生组件（`chooseAvatar` / `type="nickname"`）补头像昵称，未配置 AppSecret 也能跑
- **点单**：产品线/分类、冷热糖度、加料、门店切换、推荐与新客券
- **扫码点单**：应用内扫普通二维码；也支持微信「扫一扫」小程序码直达点单页并自动绑定桌号
- **结算**：自取/外送、优惠券、会员折扣、堂食桌号
- **订单**：下单幂等、模拟支付、订单状态机、取餐码与取餐二维码
- **核销**：店员口令校验，扫码或手输取餐码完成核销
- **AI 点单**：LangGraph ReAct 智能助手，自然语言查库存、推荐、下单、查订单进度；下单复用原有订单服务
- **会员**：等级、积分、优惠券、常用地址与常点

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | uni-app + Vue 3 + uni-ui，HBuilderX 工程 |
| 后端 | FastAPI + SQLAlchemy 2 + Pydantic v2 + Uvicorn |
| 数据库 | SQLite（默认）/ MySQL（通过 `DATABASE_URL` 切换） |
| AI 点单 | LangGraph + LangChain，DeepSeek Chat（OpenAI 兼容接口） |
| 微信能力 | `code2session` 登录、`chooseAvatar` + `type="nickname"` 头像昵称组件、`wxacode.getUnlimited` 小程序码、access_token 进程内缓存 |

## 目录结构

```
milktea/
├─ fronted/                      # uni-app 小程序
│  ├─ pages/                     # 页面（首页/点单/详情/结算/订单/我的/AI/核销）
│  ├─ common/                    # API 封装、请求、状态、工具
│  ├─ components/                # 业务组件
│  └─ docs/                      # 接口清单与前后端联调说明
├─ fastapi_demo/                 # FastAPI 后端
│  ├─ app/api/v1/                # 路由：auth/users/stores/menu/orders/ai/...
│  ├─ app/services/              # 业务：定价、订单、优惠券、核销、微信、ai_agent
│  ├─ database/                  # 建库脚本、桌码生成脚本、SQLite 文件
│  └─ static/                    # 商品图、桌码、头像
└─ docs/                         # 数据字典
```

## 快速开始

### 1. 后端

```bash
cd fastapi_demo
python -m venv .venv            # 仓库已带 .venv 时可跳过
.venv\Scripts\activate          # Windows；macOS/Linux 用 source .venv/bin/activate
pip install -r requirements.txt
python database/build_sqlite.py # 首次运行生成种子数据库
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

启动后打开 <http://127.0.0.1:8000/docs> 查看 Swagger。

> `--host 0.0.0.0` 是手机真机访问的必要条件；只在电脑上调试可用 `127.0.0.1`。
> 数据库已提交了种子数据，正常情况下不需要重建；重建会清空订单，使用 `python database/build_sqlite.py --force`。

### 2. 前端

1. 用 **HBuilderX** 打开 `fronted/` 目录（不要用 `npm run dev`，这是 HBuilderX 工程）
2. 确认已安装微信开发者工具，并在开发者工具中开启「设置 → 安全设置 → 服务端口」
3. HBuilderX → **运行 → 运行到小程序模拟器 → 微信开发者工具**
4. 首次进入选择「演示会员登录」（对应预置会员 1001，带积分/券/历史订单）

### 3. 配置

复制 `fastapi_demo/.env.example` 为 `fastapi_demo/.env`，按需填写：

| 变量 | 说明 |
|---|---|
| `WECHAT_APPID` / `WECHAT_SECRET` | 微信登录与小程序码生成；不填则使用模拟登录 |
| `STAFF_PIN` | 店员核销口令；留空则核销接口不可用 |
| `DEEPSEEK_API_KEY` | AI 点单助手密钥；留空则 `/ai/chat` 返回 9000/503 |
| `LLM_BASE_URL` / `LLM_MODEL` | 可选，默认 `https://api.deepseek.com/v1` / `deepseek-chat` |
| `BASE_URL` | 后端对外地址，用于拼接图片绝对地址；默认 `http://127.0.0.1:8000` |
| `DATABASE_URL` | 不填默认 SQLite；可切 MySQL |
| `SQL_ECHO` | 设为 `1` 打印 SQL |

前端接口地址在 [`fronted/common/config.js`](fronted/common/config.js)：电脑调试保持 `http://127.0.0.1:8000`，真机改成电脑局域网 IP。

## 演示流程

1. 启动后端，HBuilderX 运行到微信开发者工具，完成登录（可顺手选用微信头像和昵称）
2. 点单页点「扫码」，扫 `fastapi_demo/static/qrcodes/print.html` 中的桌码（或使用编译模式模拟扫码，见下）
3. 桌号自动绑定 → 选规格加料 → 加入购物车
4. 结算页确认桌号/优惠 → 提交订单 → 模拟支付
5. 订单页出示取餐码与取餐二维码
6. 我的 → 店员核销 → 输入 `STAFF_PIN` → 扫码或手输取餐码 → 确认取餐
7. 首页 → AI点单 → 说「少冰五分糖一杯黑糖波波厚奶茶」→ 查库存并生成订单卡片 → 查看订单并支付

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

## 已知限制

- 支付为模拟流程，未接入真实微信支付（需要企业/个体户与商户号）
- 未配置微信 AppID 时，微信登录使用设备 `mock_id` 生成稳定模拟账号
- 头像上传后返回 `http://` 静态地址，微信基础库对 HTTP 图片有限制；当前用本地临时路径跨页预览（`milk_avatar_preview`），应用重启后可能失效，部署到 HTTPS 后恢复正常
- 小程序码的 `trial`/`develop` 版本仅开发者与体验成员可打开
- AI 会话保存在后端进程内存（2 小时），重启或超时后清空；AI 下单只支持单款自取，不会自动支付
- access_token 缓存为进程内实现，多进程部署需替换为 Redis 等共享缓存
- SQLite 适合演示与单机开发；生产环境建议 MySQL，并补齐迁移、并发与库存一致性设计

## Roadmap

- [ ] pytest 覆盖桌码解析、下单、支付、核销等核心链路，接入 GitHub Actions
- [ ] Dockerfile + docker-compose + Nginx 部署，提供可在线体验的 H5 版本
- [ ] 真实微信支付与对账（需商户资质）
- [ ] 同桌并发下单、库存扣减与订单幂等压测

## 说明

本项目仅用于学习、课程设计与面试演示。微信 AppSecret、店员口令等敏感配置只放在本地 `.env`，不要提交到仓库。
