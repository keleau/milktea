# 四猫茶学园微信小程序 UI 设计规范（design.md）

> 纯文本设计规范，所有规格可直接落地到 uniapp（Vue3）代码。

---

## 1. 项目概述

- **项目名称**：四猫茶学园小程序（Four Cats Tea Academy Mini Program）
- **产品类型**：微信小程序 · 奶茶点单
- **核心概念**：全部奶茶饮品按四条"猫评审"产品线归类与评级。猫主题仅通过**命名体系、猫爪图形图标、系列色标签、爪爪评分**传递——**禁止插画吉祥物、禁止全身猫形象、禁止手绘卡通纹理**。
- **布局参照**（益禾堂层级逻辑，严格对应）：
  顶部 Banner → 会员信息条 → 自取/外送双大卡 → 四宫格功能入口 → 推荐产品区 → 底部 Tab 导航
- **设计风格**：干净的商业级移动端 UI，白卡片 + 奶油底色 + 真实质感阴影，亲和但专业。
- **技术载体**：uniapp Vue3（HBuilderX 工程），设计稿基准视口 375px，rpx 换算 1px = 2rpx。

## 2. 品牌识别

- **品牌名**：四猫茶学园 / Four Cats Tea Academy
- **Slogan**：「今天的奶茶，由猫评分」/ Today's Milk Tea, Rated by Cats
- **Logo**：猫爪 + 茶杯的极简几何组合标志（矢量线性风格），仅用于品牌区与分享卡片
- **品牌语气**：温暖、可信、俏皮但专业，面向年轻用户
- **猫元素使用边界（强制）**：
  - 允许：猫爪形状图标/评分、"猫"字命名、系列色标、爪印水印
  - 禁止：卡通猫角色、插画吉祥物、拟人猫、手绘风纹理

## 3. 核心设计原则

1. **内容优先**：饮品摄影图是视觉主角，UI 退后。
2. **层级严格**：页面标题 > 区块标题 > 卡片标题 > 正文 > 辅助文字，字号逐级递减。
3. **留白节奏**：8px 栅格，区块间 24px、组件间 12/16px，不拥挤。
4. **克制配色**：奶油底 + 棕主色 + 橘点缀，一个页面最多出现 3 个功能色。
5. **真实质感**：低透明度大扩散阴影（`0 8rpx 24rpx rgba(61,50,41,0.06)`），不用发光、不用高饱和渐变。
6. **猫元素一致性**：爪印形状全局统一（1 大垫 + 4 趾），线宽一致。

## 4. 设计系统

> **2026-11 视觉升级（当前生效）**：新增全局主题层 [`common/style/premium.css`](common/style/premium.css)，只覆盖配色、字体、表面、圆角、阴影和按钮/标签语法，不改动页面结构、图片位置、脚本与接口。当前核心 token：背景 `#F4EDE3`、卡片 `#FFFCF7`、主色 `#6F4B2E`（按压 `#53351F`）、强调 `#B86A3B`（按钮用 `#9F552D`）、主文字 `#2C211A`、次文字 `#6E5D4E`、分割线 `#E6D9C9`；卡片圆角 24rpx、按钮/输入 12rpx，展示标题与价格使用宋体/Georgia 衬线，按钮改为无渐变的实色胶囊。下文 4.1–4.5 的历史 token 仍作为页面语义参考，实际渲染以 `premium.css` 为准。


### 4.1 色彩（Palette）

| Token | 值 | 用途 |
|---|---|---|
| `--bg-page` | `#FAF6F0` | 页面底色（暖奶油白） |
| `--brand` | `#8B5E3C` | 品牌主色：奶茶暖棕（Tab 选中、主按钮、标题强调） |
| `--brand-press` | `#6F4A2F` | 主色按压态 |
| `--accent` | `#E8833A` | 强调橘：价格、高亮角标、CTA 按钮 |
| `--accent-soft` | `#FDF0E4` | 橘色浅底（券、角标背景） |
| `--matcha` | `#5C9E6E` | 抹茶绿：清爽线辅助色、成功态 |
| `--pink` | `#D9737F` | 软粉：甜心线辅助色 |
| `--card` | `#FFFFFF` | 卡片底 |
| `--text-1` | `#3D3229` | 主文字（深灰棕） |
| `--text-2` | `#8C8177` | 次要文字（中灰） |
| `--text-3` | `#C9C0B7` | 占位/禁用（浅灰） |
| `--line` | `#F0E9E1` | 分割线 |
| `--success` | `#5C9E6E` | 成功 |
| `--warning` | `#E8973A` | 警告/待支付 |
| `--error` | `#D9534F` | 错误/已取消 |

### 4.2 产品线专用色（Series Tags）

| 产品线 | 主色 | 浅底 | 用途 |
|---|---|---|---|
| 布奇·醇厚系列 | `#8B5E3C` | `#F3EAE0` | 系列标签、进度强调 |
| 坂本·纯选系列 | `#5A5A5A` | `#EFEFEF` | 系列标签 |
| 汤姆·甜心角落 | `#D9737F` | `#FAEBED` | 系列标签 |
| 玉·清爽系列 | `#5C9E6E` | `#EAF3EC` | 系列标签 |

### 4.3 字体（Typography）

| 层级 | 字号 | 字重 | 颜色 |
|---|---|---|---|
| 页面标题 | 40rpx | Bold | text-1 |
| 区块标题 | 34rpx | Bold | text-1 |
| 卡片标题 | 30rpx | Medium | text-1 |
| 正文 | 28rpx | Regular | text-1 |
| 辅助文字 | 24rpx | Regular | text-2 |
| 价格 | 36rpx（符号 24rpx） | Medium | accent |
| 按钮文字 | 30rpx | Medium | 白 / brand |

字体族：`PingFang SC` / `sans-serif`，不引入外部字体。

### 4.4 间距与栅格

- 基础栅格：**8px**（16rpx）
- 页面左右边距：**32rpx**
- 卡片圆角：**40rpx**（20px）；小按钮 24rpx；标签 8rpx
- 组件间距档位：**24rpx / 32rpx / 48rpx**
- 区块纵向间距：48rpx
- 卡片内边距：24~32rpx
- 底部 TabBar 高度：**112rpx**（56px）

### 4.5 阴影（Elevation）

| 层级 | 规格 |
|---|---|
| 卡片 | `0 8rpx 24rpx rgba(61,50,41,0.06)` |
| 悬浮按钮/弹层 | `0 12rpx 32rpx rgba(61,50,41,0.12)` |
| 按钮按压 | 透明度 0.85 + 位移 2rpx 向下 |

### 4.6 图标（Icons）

- 功能入口图标统一使用 `uni-icons` 线性字体图标（uni-icons 插件；uni_modules 已加入 .gitignore，克隆后需在 HBuilderX 插件市场自行安装）：积分商城 `cart` / 进群有礼 `gift` / 会员日 `vip` / 储值 `wallet`，size 26（≈52rpx）
- 核心母题：**猫爪形**（评分、品牌位），1 大垫 + 4 趾纯 CSS 几何
- 无卡通描边风格、无填充式可爱图标、无全身动物
- Tab 图标：实底剪影风格，普通态 `#A79B8E`，选中态 `#8B5E3C`，尺寸 81×81px

## 5. 产品线体系（Product Line System）

四条产品线以"猫评审"人设命名，**只用文字命名 + 色标 + 爪图标识别，无角色插画**：

| # | 产品线 | 英文名 | 定位 | 系列色 |
|---|---|---|---|---|
| 1 | 布奇·醇厚系列 | Buchi's Rich Collection | 厚乳浓奶茶 | 暖棕 |
| 2 | 坂本·纯选系列 | Sakamoto's Pure Selection | 原叶茶·低糖 | 深灰 |
| 3 | 汤姆·甜心角落 | Tom's Sweet Corner | 布丁/芋泥/果甜 | 软粉 |
| 4 | 玉·清爽系列 | Tama's Refresh Line | 冷萃/果茶 | 浅绿 |

**爪爪评分体系**：1–5 爪（Paw Score），每张产品卡必带。
- 图形：猫爪剪影 ×5，实心 = 得分，空心 = 未得
- 实心色：`#C9A886`（弱化焦糖，评分不与价格/热项的强调橘抢焦点）；空心色：`#E9DFD3`
- 附文字如「布奇评分 5 爪」

## 6. 页面结构与规格（Full Page Specs）

### 6.1 首页（pages/index/index）
自上而下（V3 版，近半屏海报 + 单张白色内容大板，严格对标益禾堂层级）：
1. **满版海报轮播 Banner**（沉浸式，内容 **700rpx** + 状态栏高度，`image_size=landscape_16_9` 远程场景图 `aspectFill` 铺满，杯子在右、左上留白）：
   - 三页三主题：`light` 新客专享（奶油棕/深棕字/棕按钮）、`dark` 周二会员日（深焦糖/奶白字/橘按钮）、`fresh` 果茶季（浅抹茶/墨绿字/绿按钮）
   - **海报级文字排版（左上叠放）**：主题胶囊 kicker（22rpx）→ 主标题 60rpx/800 → **大数字行**（前缀 40rpx/800 + 数字 104rpx/900 主题强调色 + 后缀 40rpx/800，益禾堂「超值9折」式压题）→ 副题 23rpx 单行 → 胶囊 CTA（72rpx 高）
   - 文字侧同色系渐变纱罩（115deg，实→透明 72%）保证可读性；非激活页各层 opacity 0
   - **切换动效时序（精髓，强制）**：海报随 swiper 滑动落位 **之后** 才依次入场——kicker 0.50s → 标题 0.58s → 大数字 popIn（scale 0.86→1 回弹）0.68s → 副题 0.78s → CTA 0.86s（txtIn 0.36s ease）；场景图 0.95s 压轴 `translateX(64rpx)+scale(1.05→1)` 浮现（bgIn 0.6s ease-out）
   - 4800ms 自动轮播 + circular，640ms 切换，**无指示点/进度条**；文字块从胶囊底部起排（`getMenuButtonBoundingClientRect().bottom + 12px`，兜底 statusBarHeight+54px），避免刘海/状态栏遮挡；场景图未就绪时优雅降级为主题渐变底 + 文字
2. **白色内容大板**（单张圆角卡 32rpx，上浮 -36rpx 压住 Banner，内边距 32rpx，行间 2rpx 发丝线 `#F5EFE7`）：
   - **会员行**（高 84rpx）：左 V2 徽章（42rpx，右下直角）+「银牌猫评员」25rpx；右三组「标签 20rpx text-2 + 值 23rpx Bold + 单位 19rpx text-2 弱化」：优惠券 2 张 · 积分 320 · 余额 8.5 元
   - **双列（页面主入口 · 深度聚焦，用户指定）**（益禾堂式裸文本列，无卡片底）：幽灵英文眉题（27rpx/800，`#E0D6C6`，字距 8rpx）+ 主标题 **58rpx Bold**（全板最大字号）+ 副题 23rpx；列间 2rpx 分隔线，行高 padding 48rpx / 44rpx——放大到绝对主导，周边模块同步缩小，形成焦点层级
   - **四宫格（弱化为辅助入口）**（裸线性 uni-icons，size 22，`#5A4F43`，无圆底）：cart 积分商城 / gift 进群有礼 / vip 周二会员日（accent 橘实底圆 56rpx + 白 icon + 右上白底橘字「5.8折」角标 17rpx）/ wallet 储值有礼
   - **活动条**（奶油渐变 `#FDF0E0→#F6D9B8`，圆角 24rpx，padding 18rpx 24rpx）：左侧两行文案 25rpx/19rpx + 右侧胶囊按钮「立即抢购」50rpx 高（accent 橘渐变 #F09A52→#E8833A）
3. **今日猫推荐**（大板下方奶油底区块，标题 32rpx + 「完整榜单 ›」）：纵向 3 款饮品卡（爪评分 5/4/4 拉开层次）：216rpx 方图（圆角 **16rpx，同心圆角 = 外 40 − 内距 24**）+ 名称 30rpx + 系列标签 + 爪评分（弱化焦糖色）+ 一句话描述 + 价格（accent **40rpx Bold，卡内第一视觉**）+「去点单」（64rpx 高浅底 `#F6EEE3` 棕字，弱于价格，不抢转化焦点）
4. **底部 TabBar**：首页 / 点单 / 订单 / 我的（见第 8 章）

### 6.2 点单页（pages/menu/index，瑞幸式重构版，navigationStyle custom）
- **顶栏**：自取 | 外送 40rpx 大字切换（选中深棕，未选中灰棕，中间竖分隔线）+ 白圆底搜索按钮
- **门店行**：star-filled 强调橘星标 + 店名 29rpx Bold 截断 + ›；下行「距您 205m · 即将休息」20rpx + 绿色胶囊「当前 N 杯制作中」；右侧「拼单享优惠」圆角小徽（#F3EAE0 底棕字，右下直角 4rpx）
- **优惠券胶囊条 / 新客 banner**：券包区常驻商品列表顶部（`sec-coupon`，优于分类过滤）；新客 banner 奶油橘渐变 + 棕底白字标签 + 大号文案 + 橘渐变「一键领取」；下方 2 张券票卡：左 ¥ 面额 + 虚线撕口 + 券名/说明 + 橘色「领取」
- **页签（4 个）**：经典菜单 / 会员专享价 / 新品上市 / 我的常点，选中 28rpx Bold 深棕 + 40×6rpx brand 下划条
- **主体双栏**（page 100vh flex，仅双栏内滚动；常驻头部只剩 自取|外送切换 + 门店行 + 页签，商品展示框最大化）：左侧 **176rpx** 分类栏（#F3EDE4 底，9 项：券包特惠（默认，NEW）/ 全部饮品 / 醇厚系列 / 纯选系列 / 甜心系列 / 清爽系列 / 人气必喝（HOT）/ 新品上市 / 会员专享；选中白底加粗 + 左侧 6×36rpx accent 指示条；NEW/HOT 角标），右侧 scroll-view **连续分节滚动**：券包区常驻置顶（`sec-coupon`）→ 四条产品线分节 → 经典页签追加「人气必喝 / 新品上市 / 会员专享价」汇总节，一直滑到底都有商品；点左侧分类仅做 `scroll-into-view` 锚点跳转（`sec-<id>`），不重挂载列表，切页签才回顶
- **分节**：线名 28rpx Bold（线色）+ 线描述 20rpx；**商品卡**（白底 22rpx 圆角 + 阴影，点单主战场要大）：**196rpx 方图**（18rpx 圆角）+ 名称 30rpx Bold 单行 + 标签行（新品 accent 浅底 / 会员价 棕浅底 / 小爪评分，可换行）+ 描述单行灰 + 底部「¥ 价格 accent 44rpx Bold + 划线原价」+「**选规格**」accent 橘渐变胶囊 74rpx 高（点卡片其余区域进详情）
- **交互闭环（点单页内完成下单链路）**：
  - 点门店行 → **地图选店弹层**（底部上滑：CSS 风格化地图 + 3 家门店单选，选中即换显示的门店/距离）
  - 商品卡「选规格」→ **规格弹层**（82vh 底部上滑：线色渐变 hero 图 + 名称/线标/描述 + 可选糖·冰度单选 chips + 小料多选 chips（+¥）+ 数量步进器 + 底部「¥总价 划线原价」+ 规格摘要【冰·糖·小料】+「立即购买」描边 /「加入购物车」accent 渐变）
  - 加入购物车 → **底部购物车栏**（深棕 999rpx 圆条 + 底部渐隐垫层，商品卡从其后淡出：cart-filled 图标 + accent 数量角标 + 「预估 ¥x」+ 划线原价 + 展开箭头 + 内嵌 capsule「去结算」；有会员折扣时上方居中奶油黄小标签「已享会员折扣，共减免 ¥x」）；**点条左侧即展开已选明细**（白卡浮于购物车条上方，逐项显示 图 / 名称 / 冰·糖·小料 / 小计 / ×数量 + 「删除」，逐项删空自动收起，轻遮罩点外部收起）；去结算 = 逐项 saveOrder（mode 跟随自取/外送）→ switchTab 订单列表
  - 分类栏 NEW/HOT 角标数据驱动（线内含 isNew / hot 款时显示）；热门款卡价带划线原价 `orig`
- 顶栏门店/券条/banner 为静态头部，点击均为 comingSoon 占位

### 6.3 饮品详情页（pages/detail/index）
- 顶部大图（750×750rpx，白底产品摄影）
- 白卡信息区：名称 40rpx Bold + 系列标签 + 爪评分 + 描述 28rpx
- **四线评分面板**：四个产品线视角的爪评分（布奇/坂本/汤姆/玉 各一行：线名 + 5 爪）
- 定制面板（白卡分组）：
  - 冰度：正常冰/少冰/去冰/热饮（chips 单选）
  - 糖度：全糖/七分/五分/三分/不加（chips 单选）
  - 小料：珍珠+1/椰果+1/布丁+2/芋圆+2/奶盖+3（chips 多选，选中 accent 浅底）
- 底部操作栏（固定，白底上阴影）：数量步进器（− 数字 +）+ 合计价格 + 主按钮「选好了，去结算」（brand 底白字，640×88rpx，圆角 44rpx）

### 6.4 排行榜页（pages/rank/index）
- 标题「本周猫榜」+ 副题「由四只猫评员每周联合打分」
- 列表按爪评分降序：排名序号（前三名 accent/棕/灰）+ 产品图 + 名称 + 系列标签 + 爪评分 + 价格
- 底部「新品上架」区：横向滑动新品卡

### 6.5 我的页（pages/user/index）
- 顶部会员卡（brand 渐变底，白字）：头像 + 昵称 + 会员等级 + 「积分 N · 优惠券 N 张 · 余额 N 元」三列
- 订单入口卡：待支付/制作中/已完成/已取消 四宫格（带角标数）
- 功能列表（白卡 weui-cell 风格）：收货地址 / 优惠券 / 客服中心 / 设置
- 退出登录（次要按钮）

### 6.6 结算页（pages/checkout/index）
- 取餐方式选择：自取（门店名+时间）/ 外送（地址）
- 订单清单卡：饮品图缩略 + 名称 + 定制规格（冰/糖/小料）+ 数量 + 小计
- 优惠券选择行（箭头进入）
- 价格汇总：小计 / 打包费 / 优惠券抵扣 / 合计（accent）
- 底部固定结算栏：合计 + 「提交订单」主按钮

### 6.7 订单列表页（pages/order/index）
- 顶部状态 Tab：全部 / 待支付 / 制作中 / 已完成 / 已取消
- 订单卡：状态标签（右上）+ 饮品图 + 名称 + 规格 + 数量 + 金额 + 「去支付/再来一单」按钮
- 空态：爪印图形 + 「还没有订单，去点一杯吧」

### 6.8 订单详情页（pages/order/order）
- 状态横幅（brand 底白字：制作中/待支付/已完成…）
- 取餐码大号展示（已完成/制作中）
- 订单清单、定制规格、价格汇总、订单编号
- 待支付态：底部「立即支付」主按钮

## 7. 组件库规格（Component Library）

| 组件 | 规格 |
|---|---|
| 主按钮 Primary | 640×88rpx，圆角 44rpx，brand 底白字 30rpx Medium；按压 `--brand-press`；禁用 40% 透明 |
| 次按钮 Secondary | 640×88rpx，白底 brand 描边 2rpx，brand 字；按压底 `#F3EAE0` |
| 小按钮 Mini | 高 64rpx，圆角 32rpx，横向 padding 32rpx |
| 产品卡 ProductCard | 白底 40rpx 圆角，图 280rpx 方角 24rpx，内边距 24rpx，卡片阴影 level-1 |
| 爪评分 PawsRating | 单爪 32rpx，间距 8rpx；实心 `#C9A886` / 空心 `#E9DFD3` |
| 系列标签 SeriesTag | 高 40rpx，padding 0 16rpx，8rpx 圆角，24rpx 字，线色字+浅底 |
| 信息卡 InfoCard | 白底 40rpx 圆角 32rpx 内边距，标题 30rpx + 右侧箭头 |
| 选择器 Chip | 高 64rpx，padding 0 28rpx，16rpx 圆角；默认浅灰底 text-2 字；选中 brand 底白字；多选选中 accent 浅底 accent 字 |
| 步进器 Stepper | 56rpx 圆按钮，brand 描边，中间数字 28rpx |
| 输入框 Input | 高 80rpx，浅灰底 16rpx 圆角，24rpx 占位 text-3 |
| 空状态 Empty | 爪印图形 160rpx + 文案 28rpx text-2 |
| 徽标 Badge | 32rpx 圆，accent 底白字 20rpx，右上角偏移 |

## 8. 交互与导航规则

### 8.1 底部导航（TabBar）
- 四个标准 Tab：首页 / 点单 / 订单 / 我的；中央凸起品牌按钮为规范预留（后续自定义 tabBar 实现），首版以标准 tabBar 交付
- 选中态：图标+文字变 brand（`#6F4B2E`）；未选中 `#9A8A7A`
- 切换：`uni.switchTab`，无转场动画

### 8.2 页面跳转
- 首页「去点单/自取/外送」→ switchTab 点单页
- 产品卡/网格 → navigateTo 详情页（传 id）
- 详情「去结算」→ navigateTo 结算页（传定制参数）
- 结算「提交订单」→ 写入本地订单（storage）→ redirectTo 订单详情
- 榜单入口 → navigateTo 排行榜页

### 8.3 按钮三态
| 状态 | 表现 |
|---|---|
| 默认 | 正常色 |
| 按压 | 深一号色（brand-press）+ 下移 2rpx |
| 禁用 | 40% 透明度，去点击 |

### 8.4 反馈状态
- **加载**：页面级骨架（灰块 16rpx 圆角呼吸动画）；按钮内文字变「提交中…」
- **空态**：爪印 + 文案（订单空、搜索无结果）
- **错误**：toast `icon:'none'`，文案 ≤ 12 字
- **成功**：toast icon success
- **下拉刷新**：列表页开启，圆点配色 brand

### 8.5 动效规范（Motion）
- **页面入场**：各区块 `fadeUp 0.55s cubic-bezier(0.22,0.61,0.36,1)`，级联延迟 0.08s/0.16s
- **海报轮播切换（精髓时序，强制）**：海报随 swiper 落位后文字组才入场——kicker 0.50s → 标题 0.58s → 大数字 popIn 0.68s（scale 0.86→1 回弹）→ 副题 0.78s → CTA 0.86s（txtIn 0.36s ease）；场景图最后 0.95s `translateX(64rpx)+scale(1.05→1)` 浮现（bgIn 0.6s ease-out）。「先文字、后画面」顺序不可倒置
- **悬浮 AI 入口**：首页/点单页右下角 168rpx 圆形猫娘 GIF，`afFloat` 3.4s ±10rpx 上下浮动；下方 38rpx 眼睛按钮收起，收起后只留 58rpx「AI」小气泡；有购物车时上移 154rpx，弹层打开时隐藏
- **按压反馈**：可点元素 `hover-class` 缩放 0.97 + 透明度 0.85，过渡 0.18s ease；入场动画与按压态分层（动画放包装层，按压放本体）
- **时长上限**：单段动效 ≤ 650ms，缓动一律 ease-out 系

## 9. 可访问性（Accessibility）

1. 正文与背景对比度 ≥ 4.5:1（text-1/card ≈ 10.9:1，text-2/card ≈ 3.9:1 仅用于辅助信息）
2. 可点击元素最小 88×88rpx，间距 ≥ 16rpx
3. 不用纯色传达状态：状态均带文字（如「待支付」）
4. 图片均有语义化 alt（image 组件加 `aria-label`）
5. 动效尊重系统「减弱动态效果」，时长 200–300ms，缓动 ease-out

## 10. 文件命名与导出规范

- 页面：`pages/<语义名>/index.vue`（如 `pages/menu/index.vue`、`pages/detail/index.vue`）
- 组件：`components/<名>/<名>.vue`，easycom 自动注册（如 `components/paws/paws.vue`）；**仅保留有页面引用的组件**（paws/share/ai-float），未引用的 navbar/formater/counter 已清理
- 数据与工具：`common/data/`（`drinks.js` 产品线与饮品、`shop.js` 门店/优惠券、`orders.js` 订单读写，`index.js` 统一出口）；`common/utils/`（`image.js` 图片工厂、`storage.js` 安全缓存）；`common/store/session.js` 页面间临时态（结算草稿、订单筛选）
- 样式 Token：`uni.scss` 中 `$vp-*` 变量，页面样式内联于 SFC `<style>`
- 静态资源：`static/resource/images/`，小写 + 下划线；**仅保留被引用资源**（tab 图标 8 张、avatar.jpg、share 弹层、banner_summer.jpg / banner_boba.jpg / banner_milk.jpg、drink_1~12.jpg、ai_maid.gif、maid_wave.png、fx/*.png），模板遗留图已清理
- 饮品图：1~12 号全部使用本地 `drink_<id>.jpg`（560×560，已去水印、压缩 19~27KB）。Banner：本地 3 张 `banner_summer / banner_boba / banner_milk`（750×788，与轮播容器同比例——保证猫、奶茶杯、背景三者都完整露出，不被 aspectFill 裁掉），轮播固定 3 页（新客专享 → 会员日 → 猫爪厚乳茶，浅/深/浅交替）；静态图统一 ≤100KB。AI 悬浮猫娘 `ai_maid.gif`（240×240，135KB）与点击挥手帧 `maid_wave.png`（240×240，113KB）均已压缩，不要再放大或拉长；`static` 当前约 842KB
- 本地订单：`uni.storage` key `milk_orders`（数组，`out_trade_no` 唯一）
- 分支命名：`feature/cat-theme`；提交信息：`feat: 四猫茶学园首页改版` 格式

## 11. 图像生成提示词库（Image Prompt Library）

> 全部走 `https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=...&image_size=...`，远程 URL 不进包体。
> 提示词分两条轨：**摄影轨**（饮品、海报）与**极简矢量插图轨**（空态、纹理、品牌图形）。两轨共用同一色盘，禁止混用。

### 11.1 风格锁定（Style Lock）

**摄影轨 · 统一前置**（已内置于 `data.js` 的 `PHOTO_STYLE`，勿逐张改写）：

```text
Premium commercial beverage photography, warm cream seamless studio backdrop, soft diffused daylight from upper left,
gentle contact shadow, low-saturation caramel brown cream and burnt orange palette, 85mm lens, shallow depth of field,
minimal props, photorealistic, appetizing, ultra clean composition, no text, no letters, no logo, no people, no cartoon, no neon
```

**摄影轨 · 统一尾部**：`tall transparent takeaway cup with flat lid, centered composition, consistent brand photography style, high resolution`

**海报轨 · 统一前置**：

```text
Premium commercial milk tea campaign photography, warm cream and caramel palette with burnt orange accents,
soft diffused studio light, realistic, high resolution, no text, no letters, no logo, no people, no cartoon
```

**海报轨 · 统一尾部**：`cups and props clustered on the right side, clean empty copy space on the left, consistent brand campaign style`

**插图轨 · 统一前置**：

```text
Minimal flat vector illustration, warm cream background (#FAF6F0), thin 2px monoline strokes in warm brown (#8B5E3C)
with burnt orange (#E8833A) accent shapes, geometric, generous negative space, subtle paper grain,
centered composition, no text, no letters, no logo, no mascot, no cartoon cat character, no 3D, no gradient mesh, no neon
```

**全局禁用**：文字/字母/水印/价格标签、卡通猫角色、拟人猫、手绘纹理、霓虹荧光色、冷白光、紫调、3D 渲染、强反光、杂乱道具。猫元素只允许**爪印图形**（品牌边界见第 2 章）。

### 11.2 尺寸与参数矩阵（"大小"规范）

| 用途 | 页面显示 | 比例 | `image_size` | 建议 |
|---|---|---|---|---|
| 饮品图（详情头图 / 卡片共用同一 URL） | 详情头图 750×750rpx；卡图 120–216rpx | 1:1 | `square_hd` | 一张图复用全部场景，高处取清晰度；单图 < 400KB |
| 首页满版海报 | 750rpx × ≈700rpx（近半屏） | 16:9 | `landscape_16_9` | `aspectFill` 裁切，主体必须靠右，左侧留白放文字 |
| 订单/优惠券空态插图 | 320rpx 方形容器 | 1:1 | `square` | 线稿+负空间，缩小后仍可辨 |
| 排行榜头图 | 750×360rpx | 4:3 | `landscape_4_3` | 横向插画，不抢榜卡信息 |
| 会员卡底色纹理 | 750×400rpx | 4:3 | `landscape_4_3` | 低对比同色系，不能有视觉焦点 |
| 分享卡封面 | 5:4 分享卡 | 4:3 | `landscape_4_3` | 品牌几何图形居中，安全区内构图 |
| 产品线封面（4 张，可选） | 750×280rpx | 1:1 | `square` | 各用系列主色做点缀，其余保持奶油底 |

### 11.3 饮品图（12 张 · `square_hd`）

在统一前置 + 尾部之间替换下列主体描述（英文，SDXL 写法：主体 → 细节 → 材质）：

| # | 饮品 | 主体描述（拼进 `genImg`） |
|---|---|---|
| 1 | 黑糖波波厚奶茶 | `one cup of brown sugar boba milk tea, glossy dark syrup streaks on the inner wall, dense tapioca pearls at the bottom, thick milk layer and foam cap, wooden coaster` |
| 2 | 经典原味厚乳奶茶 | `one cup of classic hong kong style milk tea, silky uniform tan brown color, clean cup wall, tiny condensation droplets, minimal styling` |
| 3 | 提拉米苏厚乳茶 | `one cup of tiramisu milk tea, cocoa dusted cream foam cap, layered coffee and milk body, a small tiramisu cube garnish on the side` |
| 4 | 茉莉初雪轻乳茶 | `one cup of jasmine green milk tea, pale golden tea body, thin white milk foam layer, three jasmine petals on the lid` |
| 5 | 四季春原叶纯茶 | `one cup of clear amber oolong tea with ice cubes, no milk, translucent tea body, fresh tea leaves beside the cup` |
| 6 | 轻乳乌龙茶 | `one cup of light oolong milk tea, soft beige two-tone layers, gentle milk swirl, minimal foam` |
| 7 | 布丁可可萌宠杯 | `one cup of chocolate milk, whole caramel pudding at the bottom, creamy cocoa layers, cocoa powder dusting on the foam` |
| 8 | 芋泥啵啵鲜奶茶 | `one cup of taro milk tea, purple taro paste smeared on the inner wall, chewy taro balls, white milk layer on top` |
| 9 | 草莓芝士奶盖 | `one cup of strawberry milk tea, pink strawberry puree at the bottom, thick white cheese foam cap, one fresh strawberry beside the cup` |
| 10 | 满杯百香果茶 | `one cup of passion fruit tea, bright orange yellow body, visible passion fruit seeds, crushed ice, half a passion fruit beside the cup` |
| 11 | 手打香水柠檬茶 | `one cup of smashed lemon green tea, bright green yellow body, crushed lemon slices and mint leaves, ice cubes` |
| 12 | 冷萃乌龙青提茶 | `one cup of cold brew oolong tea with green grapes, light jade green body, halved green grapes and ice cubes` |

### 11.4 首页海报（3 张 · `landscape_16_9`）

只替换海报轨主体段，构图（右主体/左留白）由统一尾部保证：

| 主题 | 主体描述 |
|---|---|
| 新客专享（light） | `warm creamy caramel milk tea swirl scene, silky milk waves in beige tones, two cups on a wooden table, cozy dessert shop counter, soft morning light` |
| 会员日（dark） | `dark roasted brown sugar bubble milk tea with glossy syrup drizzle, deep caramel tones, moody warm rim light, luxurious dark background` |
| 果茶季（fresh） | `fresh fruit tea with passion fruit seeds, lemon slices and mint, bright airy pastel green background, summer refreshing vibe` |

### 11.5 插图（极简矢量 · 无猫角色 · 前置用 11.1 的插图轨统一前置）

| 用途 | `image_size` | 主体描述 |
|---|---|---|
| 订单空态 | `square` | `a single line-art takeaway cup with three rising steam curls shaped like paw prints, two small orange dots as boba at the base, a soft cream circle behind the cup, lots of empty space around` |
| 优惠券空态 | `square` | `a line-art paper coupon with a paw-shaped notch on the right edge, a dashed tear line, one burnt orange star seal at the corner` |
| 排行榜头图 | `landscape_4_3` | `three geometric podiums in warm brown line art, a paw-print emblem on the tallest center podium, soft orange tea waves as a band along the bottom, wide empty space above` |
| 会员卡纹理 | `landscape_4_3` | `seamless subtle pattern of tiny paw prints and tea cup outlines, tone-on-tone warm cream and light caramel, very low contrast, generous spacing, no focal point` |
| 分享卡封面 | `landscape_4_3` | `geometric brand mark of a paw print merged with a milk tea cup silhouette, thin brown monoline, one burnt orange arc behind, cream background, centered` |
| 产品线封面 · 醇厚 | `square` | `abstract thick milk wave, flowing warm brown rounded shapes, one rich caramel swirl` |
| 产品线封面 · 纯选 | `square` | `abstract minimal tea leaf, clean single line, soft grey brown tone, one pale gold accent dot` |
| 产品线封面 · 甜心 | `square` | `abstract pudding dome with a caramel drizzle line, soft pink accent shape, rounded geometry` |
| 产品线封面 · 清爽 | `square` | `abstract citrus slice, thin radial lines, fresh green accent, one mint leaf outline` |

### 11.6 生成与体积注意

1. 所有提示词必须 `encodeURIComponent`；文中代码块的换行仅为排版，实际拼接为**单行**，中文不出现在 prompt 里（命名仅作为文件/注释）。
2. 接口**不支持 negative prompt**，"no text / no logo / no cartoon" 必须写进正向提示词（已内置）。
3. URL 固定 → 结果被 CDN 缓存：**改提示词 = 换图**，上线后不要反复微调措辞。
4. 单图控制在 400KB 以内；小卡片与详情页共用同一 URL，靠尺寸参数一次生成、多处复用。
5. 生成服务排队时返回固定占位图（约 176KB），页面须保留底色/渐变兜底，不得出现空白破图。
6. 禁止把生成图下载进 `static/`——会直接增大主包，且无法享受 CDN。

