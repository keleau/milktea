<template>
	<view class="page">
		<!-- ① 满版海报轮播（近半屏高，海报级大字排版，转场后文字先入、画面后到） -->
		<view class="banner-wrap">
			<swiper
				class="banner-swiper"
				:style="{ height: bannerH }"
				circular
				autoplay
				:interval="4800"
				:duration="640"
				@change="onSlide"
			>
				<swiper-item v-for="(bn, bi) in banners" :key="bi">
					<view class="slide" :class="['t-' + bn.theme, { act: cur === bi }]">
						<image class="slide-bg" :src="bn.bg" mode="aspectFill"></image>
						<view class="slide-scrim"></view>
						<view class="slide-content" :style="{ paddingTop: contentTop }">
							<view class="sl-kicker">{{ bn.kicker }}</view>
							<view class="sl-title">{{ bn.title }}</view>
							<view class="sl-big">
								<text class="big-pre">{{ bn.big[0] }}</text>
								<text class="big-num">{{ bn.big[1] }}</text>
								<text class="big-suf">{{ bn.big[2] }}</text>
							</view>
							<view class="sl-sub">{{ bn.sub }}</view>
							<view class="sl-cta">
								<view class="cta-btn" hover-class="hv" @tap="goBanner(bn)">{{ bn.btn }}</view>
							</view>
						</view>
					</view>
				</swiper-item>
			</swiper>
		</view>

		<!-- ② 白色内容大板：会员行 / 双列 / 四宫格 / 更多惊喜 / 活动条 -->
		<view class="sheet anim d1">
			<view class="member-row">
				<view class="mb-id">
					<view class="mb-badge">{{ level.levelCode }}</view>
					<text class="mb-level">{{ level.levelName }}</text>
				</view>
				<view class="mb-stats">
					<view class="mb-stat"><text class="mb-key">优惠券</text><text class="mb-val">{{ user.coupon_count }}</text><text class="mb-unit">张</text></view>
					<view class="mb-sep"></view>
					<view class="mb-stat"><text class="mb-key">积分</text><text class="mb-val">{{ user.points }}</text></view>
					<view class="mb-sep"></view>
					<view class="mb-stat"><text class="mb-key">余额</text><text class="mb-val">{{ user.balance }}</text><text class="mb-unit">元</text></view>
				</view>
			</view>

			<view class="dual-row">
				<view class="du-col" hover-class="hv" @tap="toMenu">
					<text class="du-en">PICK UP</text>
					<text class="du-title">自取点单</text>
					<text class="du-sub">下单享优惠 ›</text>
				</view>
				<view class="du-divider"></view>
				<view class="du-col" hover-class="hv" @tap="toMenu">
					<text class="du-en">DELIVERY</text>
					<text class="du-title">外送到家</text>
					<text class="du-sub">每周五最高免配 ›</text>
				</view>
			</view>

			<view class="scan-row" hover-class="hv" @tap="toAi">
				<view class="scan-icon">
					<uni-icons type="chat" size="22" color="#8B5E3C"></uni-icons>
				</view>
				<view class="scan-body">
					<text class="scan-title">AI点单</text>
					<text class="scan-sub">说出想喝什么，智能助手帮你查库存、下单</text>
				</view>
				<text class="scan-arrow">›</text>
			</view>

			<view class="scan-row" hover-class="hv" @tap="scanTable">
				<view class="scan-icon">
					<uni-icons type="scan" size="22" color="#8B5E3C"></uni-icons>
				</view>
				<view class="scan-body">
					<text class="scan-title">扫码点餐</text>
					<text class="scan-sub">扫桌面二维码，自动识别门店和桌号</text>
				</view>
				<text class="scan-arrow">›</text>
			</view>

			<view class="grid-row">
				<view class="g-item" hover-class="hv" @tap="comingSoon">
					<uni-icons type="cart" size="22" color="#5A4F43"></uni-icons>
					<text class="g-text">积分商城</text>
				</view>
				<view class="g-item" hover-class="hv" @tap="comingSoon">
					<uni-icons type="gift" size="22" color="#5A4F43"></uni-icons>
					<text class="g-text">进群有礼</text>
				</view>
				<view class="g-item" hover-class="hv" @tap="comingSoon">
					<view class="g-hot">
						<uni-icons type="vip" size="20" color="#FFFFFF"></uni-icons>
						<text class="g-badge">5.8折</text>
					</view>
					<text class="g-text">周二会员日</text>
				</view>
				<view class="g-item" hover-class="hv" @tap="comingSoon">
					<uni-icons type="wallet" size="22" color="#5A4F43"></uni-icons>
					<text class="g-text">储值有礼</text>
				</view>
			</view>

			<view class="act-banner" hover-class="hv" @tap="comingSoon">
				<view class="act-left">
					<text class="act-t1">周二会员日 · 爪价 5.8 折</text>
					<text class="act-t2">每周二全场饮品，会员专享价</text>
				</view>
				<view class="act-btn">立即抢购</view>
			</view>
		</view>

		<!-- ③ 今日猫推荐 -->
		<view class="section anim d2">
			<view class="sec-head">
				<text class="sec-title">今日猫推荐</text>
				<text class="sec-more" hover-class="hv" @tap="toRank">完整榜单 ›</text>
			</view>
			<view
				class="rec-card"
				v-for="item in recommends"
				:key="item.id"
				hover-class="hv"
				@tap="toDetail(item.id)"
			>
				<image class="rec-img" :src="item.img" mode="aspectFill"></image>
				<view class="rec-info">
					<view class="rec-top">
						<text class="rec-name">{{ item.name }}</text>
						<text class="line-tag" :style="{ color: lineOf(item.line).color, background: lineOf(item.line).bg }">
							{{ lineOf(item.line).tag }}
						</text>
					</view>
					<paws :score="item.paws"></paws>
					<text class="rec-desc">{{ item.desc }}</text>
					<view class="rec-bottom">
						<view class="price"><text class="price-sym">¥</text><text class="price-num">{{ item.price }}</text></view>
						<view class="rec-btn" hover-class="hv" @tap.stop="toDetail(item.id)">去点单</view>
					</view>
				</view>
			</view>
		</view>

		<view class="footer-slogan anim d2">
			<text>— 四猫茶学园 · 今天的奶茶，由猫评分 —</text>
		</view>
	</view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getLines, getProducts } from '@/common/api/catalog'
import { resolveTable } from '@/common/api/tables'
import { ensureLogin, fetchMe } from '@/common/api/auth'
import { showError } from '@/common/api/request'
import { levelParts, toDrink } from '@/common/api/adapters'
import { getCachedUser } from '@/common/api/token'
import { saveTableContext } from '@/common/store/table'
import { scanCode, isScanCancel } from '@/common/utils/scan'

// 状态栏高度：海报轮播沉浸到状态栏之下
const statusBarHeight = uni.getWindowInfo().statusBarHeight
const bannerH = 700 + statusBarHeight * 2 + 'rpx'
// 胶囊定位：海报文字从微信胶囊底部起排，避免被刘海/状态栏遮挡
const menuBtn = uni.getMenuButtonBoundingClientRect ? uni.getMenuButtonBoundingClientRect() : null
const contentTop = (menuBtn ? menuBtn.bottom + 12 : statusBarHeight + 54) + 'px'

const user = ref(getCachedUser() || { nickname: '猫友', level: '', points: 0, balance: 0, coupon_count: 0 })
const level = computed(() => levelParts(user.value.level))
const lines = ref([])
const recommendations = ref([])
const recommends = computed(() => recommendations.value)
const EMPTY_LINE = { id: '', name: '', tag: '', en: '', desc: '', color: '#8b5e3c', bg: '#f3eae0' }
const lineOf = (id) => lines.value.find(l => l.id === id) || EMPTY_LINE

const loadUser = async () => {
	try {
		user.value = await ensureLogin()
		user.value = await fetchMe()
	} catch (error) {
		// 用户信息失败不影响菜单展示
	}
}
const loadCatalog = async () => {
	try {
		const [lineList, page] = await Promise.all([
			getLines(),
			getProducts({ tab: 'classic', page_size: 100 })
		])
		lines.value = lineList
		const drinks = (page.items || []).map(toDrink)
		const hot = drinks.filter(d => d.hot)
		recommendations.value = (hot.length ? hot : drinks).slice(0, 3)
	} catch (error) {
		console.warn('[home] 推荐加载失败', error)
	}
}

onShow(() => {
	loadUser()
	loadCatalog()
})

// 当前轮播页索引：驱动「海报滑入 → 文字依次入场 → 场景图压轴」的动效时序
const cur = ref(0)
const onSlide = (e) => {
	cur.value = e.detail.current
}

// 海报轮播：三页三色，杯子在右、左上留白放文字（prompt 与预热 URL 严格一致）
const banners = [
	{
		theme: 'light',
		kicker: '新客专享',
		title: '猫爪认证好茶',
		big: ['新客', '9', '折 喝爆款'],
		sub: '双杯 85 折 · 三杯 8 折',
		btn: '点击领取',
		bg: '/static/resource/images/banner_summer.jpg',
		link: 'menu'
	},
	{
		theme: 'dark',
		kicker: '每周二 · 会员日',
		title: '猫爪会员日',
		big: ['爪价低至', '5.8', '折'],
		sub: '银牌 5.8 · 金牌 5 · 黑金 4.5 折',
		btn: '立即查看',
		bg: '/static/resource/images/banner_boba.jpg',
		link: 'soon'
	},
	{
		theme: 'light',
		kicker: '坂本 · 纯选',
		title: '猫爪厚乳茶',
		big: ['奶香', '2', '倍加厚'],
		sub: '手打奶泡 · 猫爪拉花限定',
		btn: '去点单',
		bg: '/static/resource/images/banner_milk.jpg',
		link: 'menu'
	}
]

const goBanner = (b) => {
	if (b.link === 'soon') comingSoon()
	else toMenu()
}
const toMenu = () => {
	uni.switchTab({ url: '/pages/menu/index' })
}
const toAi = () => {
	uni.navigateTo({ url: '/pages/ai/index' })
}
const scanTable = async () => {
	let scene = ''
	try {
		scene = await scanCode()
	} catch (error) {
		if (!isScanCancel(error)) uni.showToast({ title: '扫码失败，请重试', icon: 'none' })
		return
	}
	uni.showLoading({ title: '识别桌号…' })
	try {
		const table = await resolveTable(scene)
		uni.hideLoading()
		saveTableContext(table)
		uni.showToast({ title: `${table.tableNo} 桌 · ${table.storeName}`, icon: 'none' })
		setTimeout(() => uni.switchTab({ url: '/pages/menu/index' }), 500)
	} catch (error) {
		uni.hideLoading()
		showError(error)
	}
}
const toDetail = (id) => {
	uni.navigateTo({ url: '/pages/detail/index?id=' + id })
}
const toRank = () => {
	uni.navigateTo({ url: '/pages/rank/index' })
}
const comingSoon = () => {
	uni.showToast({ title: '敬请期待', icon: 'none' })
}
</script>

<style>
page {
	background: #faf6f0;
}
.page {
	min-height: 100vh;
	padding-bottom: 48rpx;
}
.hv {
	opacity: 0.85;
	transform: scale(0.97);
}

/* 入场动效 */
@keyframes fadeUp {
	from {
		opacity: 0;
		transform: translateY(28rpx);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
}
.anim {
	animation: fadeUp 0.55s cubic-bezier(0.22, 0.61, 0.36, 1) both;
}
.d1 { animation-delay: 0.08s; }
.d2 { animation-delay: 0.16s; }

/* ===== ① 满版海报轮播 ===== */
.banner-wrap {
	position: relative;
}
.banner-swiper {
	height: 700rpx;
}
.slide {
	position: relative;
	height: 100%;
	overflow: hidden;
}
.slide.t-light { background: linear-gradient(160deg, #f8ecd6 0%, #f0dcba 100%); }
.slide.t-dark { background: linear-gradient(160deg, #6f4b2c 0%, #4c311c 100%); }
.slide.t-fresh { background: linear-gradient(160deg, #eef4e4 0%, #d7e8ce 100%); }

.slide-bg {
	position: absolute;
	left: 0;
	top: 0;
	width: 100%;
	height: 100%;
	opacity: 0;
}
.slide-scrim {
	position: absolute;
	left: 0;
	top: 0;
	right: 0;
	bottom: 0;
}
.t-light .slide-scrim {
	background: linear-gradient(115deg, rgba(250, 240, 222, 0.9) 10%, rgba(250, 240, 222, 0.45) 45%, rgba(250, 240, 222, 0) 72%);
}
.t-dark .slide-scrim {
	background: linear-gradient(115deg, rgba(56, 36, 20, 0.88) 10%, rgba(56, 36, 20, 0.4) 45%, rgba(56, 36, 20, 0) 72%);
}
.t-fresh .slide-scrim {
	background: linear-gradient(115deg, rgba(242, 248, 234, 0.9) 10%, rgba(242, 248, 234, 0.45) 45%, rgba(242, 248, 234, 0) 72%);
}

.slide-content {
	position: relative;
	z-index: 1;
	height: 100%;
	padding-left: 44rpx;
	padding-right: 320rpx;
	box-sizing: border-box;
}

/* 转场动效：海报滑稳后，kicker→标题→大数字→副题→按钮 依次入场，场景图最后浮现 */
.sl-kicker,
.sl-title,
.sl-big,
.sl-sub,
.sl-cta {
	opacity: 0;
}
.slide.act .sl-kicker { animation: txtIn 0.36s ease 0.5s both; }
.slide.act .sl-title { animation: txtIn 0.36s ease 0.58s both; }
.slide.act .sl-big { animation: popIn 0.42s cubic-bezier(0.34, 1.4, 0.64, 1) 0.68s both; }
.slide.act .sl-sub { animation: txtIn 0.36s ease 0.78s both; }
.slide.act .sl-cta { animation: txtIn 0.36s ease 0.86s both; }
.slide.act .slide-bg { animation: bgIn 0.6s ease-out 0.95s both; }
@keyframes txtIn {
	from {
		opacity: 0;
		transform: translateY(22rpx);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
}
@keyframes popIn {
	from {
		opacity: 0;
		transform: scale(0.86) translateY(16rpx);
	}
	to {
		opacity: 1;
		transform: scale(1) translateY(0);
	}
}
@keyframes bgIn {
	from {
		opacity: 0;
		transform: translateX(64rpx) scale(1.05);
	}
	to {
		opacity: 1;
		transform: translateX(0) scale(1);
	}
}

.sl-kicker {
	display: inline-block;
	font-size: 22rpx;
	font-weight: 500;
	letter-spacing: 4rpx;
	padding: 8rpx 22rpx;
	border-radius: 999rpx;
}
.t-light .sl-kicker { background: rgba(255, 255, 255, 0.8); color: #8b5e3c; }
.t-dark .sl-kicker { background: rgba(255, 255, 255, 0.16); color: #ffe9d2; }
.t-fresh .sl-kicker { background: rgba(255, 255, 255, 0.75); color: #4f8a60; }

.sl-title {
	margin-top: 18rpx;
	font-size: 60rpx;
	font-weight: 800;
	letter-spacing: 3rpx;
	line-height: 1.2;
	white-space: nowrap;
}
.t-light .sl-title { color: #3d3229; }
.t-dark .sl-title { color: #fff7ec; }
.t-fresh .sl-title { color: #2f4634; }

/* 海报大数字行：前缀小字 + 超大数字 + 后缀小字 */
.sl-big {
	margin-top: 6rpx;
	display: flex;
	align-items: baseline;
}
.big-pre {
	font-size: 40rpx;
	font-weight: 800;
	letter-spacing: 2rpx;
	margin-right: 8rpx;
}
.big-num {
	font-size: 104rpx;
	font-weight: 900;
	line-height: 1.05;
	letter-spacing: 0;
}
.big-suf {
	font-size: 40rpx;
	font-weight: 800;
	letter-spacing: 2rpx;
	margin-left: 8rpx;
}
.t-light .sl-big { color: #3d3229; }
.t-light .big-num { color: #c96f2a; }
.t-dark .sl-big { color: #fff7ec; }
.t-dark .big-num { color: #ffb054; }
.t-fresh .sl-big { color: #2f4634; }
.t-fresh .big-num { color: #4f8a60; }

.sl-sub {
	margin-top: 14rpx;
	font-size: 23rpx;
	letter-spacing: 1rpx;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}
.t-light .sl-sub { color: #7a6c5d; }
.t-dark .sl-sub { color: rgba(255, 240, 220, 0.82); }
.t-fresh .sl-sub { color: #5d7362; }

.sl-cta {
	margin-top: 30rpx;
}
.cta-btn {
	display: inline-block;
	height: 72rpx;
	line-height: 72rpx;
	padding: 0 44rpx;
	border-radius: 999rpx;
	font-size: 29rpx;
	font-weight: 500;
	color: #ffffff;
	transition: transform 0.18s ease, opacity 0.18s ease;
}
.t-light .cta-btn { background: #8b5e3c; box-shadow: 0 10rpx 24rpx rgba(139, 94, 60, 0.35); }
.t-dark .cta-btn { background: #e8833a; box-shadow: 0 10rpx 24rpx rgba(232, 131, 58, 0.4); }
.t-fresh .cta-btn { background: #5c9e6e; box-shadow: 0 10rpx 24rpx rgba(92, 158, 110, 0.35); }

/* ===== ② 白色内容大板 ===== */
.sheet {
	margin: -36rpx 24rpx 0;
	position: relative;
	z-index: 2;
	background: #ffffff;
	border-radius: 32rpx;
	padding: 8rpx 32rpx 32rpx;
	box-shadow: 0 8rpx 24rpx rgba(61, 50, 41, 0.06);
}
.member-row {
	display: flex;
	align-items: center;
	justify-content: space-between;
	height: 84rpx;
	border-bottom: 2rpx solid #f5efe7;
}
.mb-id {
	display: flex;
	align-items: center;
}
.mb-badge {
	width: 42rpx;
	height: 42rpx;
	line-height: 42rpx;
	text-align: center;
	background: #8b5e3c;
	color: #ffffff;
	font-size: 19rpx;
	font-weight: bold;
	border-radius: 11rpx 11rpx 11rpx 4rpx;
	margin-right: 10rpx;
}
.mb-level {
	font-size: 25rpx;
	font-weight: 500;
	color: #3d3229;
}
.mb-stats {
	display: flex;
	align-items: center;
}
.mb-stat {
	display: flex;
	align-items: center;
}
.mb-key {
	font-size: 20rpx;
	color: #8c8177;
	margin-right: 6rpx;
}
.mb-val {
	font-size: 23rpx;
	font-weight: bold;
	color: #3d3229;
}
.mb-unit {
	font-size: 19rpx;
	color: #8c8177;
	margin-left: 2rpx;
}
.mb-sep {
	width: 2rpx;
	height: 24rpx;
	background: #f0e9e1;
	margin: 0 16rpx;
}

/* 双列（益禾堂式：裸文本列 + 幽灵英文眉题）——页面主入口，放大做深度聚焦 */
.dual-row {
	display: flex;
	align-items: stretch;
	padding: 48rpx 0 44rpx;
	border-bottom: 2rpx solid #f5efe7;
}
.du-col {
	flex: 1;
	display: flex;
	flex-direction: column;
	align-items: center;
	transition: transform 0.18s ease, opacity 0.18s ease;
}
.du-en {
	font-size: 27rpx;
	color: #e0d6c6;
	font-weight: bold;
	letter-spacing: 8rpx;
}
.du-title {
	margin-top: 10rpx;
	font-size: 58rpx;
	font-weight: bold;
	color: #3d3229;
	letter-spacing: 3rpx;
}
.du-sub {
	margin-top: 12rpx;
	font-size: 23rpx;
	color: #8c8177;
}
.du-divider {
	width: 2rpx;
	background: #f5efe7;
	margin: 10rpx 0;
}

/* 扫码点餐：桌号上下文入口 */
.scan-row {
	display: flex;
	align-items: center;
	margin: 24rpx 0 4rpx;
	padding: 22rpx 24rpx;
	border-radius: 28rpx;
	background: #fdf1e4;
}
.scan-icon {
	flex-shrink: 0;
	width: 68rpx;
	height: 68rpx;
	border-radius: 50%;
	background: #ffffff;
	display: flex;
	align-items: center;
	justify-content: center;
}
.scan-body {
	flex: 1;
	min-width: 0;
	margin-left: 18rpx;
	display: flex;
	flex-direction: column;
}
.scan-title {
	font-size: 30rpx;
	font-weight: bold;
	color: #3d3229;
}
.scan-sub {
	margin-top: 4rpx;
	font-size: 22rpx;
	color: #8c8177;
}
.scan-arrow {
	flex-shrink: 0;
	font-size: 32rpx;
	color: #b7ab9e;
}

/* 四宫格（裸线性图标，热项彩色圆）——弱化为辅助入口 */
.grid-row {
	display: flex;
	padding: 24rpx 0 20rpx;
}
.g-item {
	flex: 1;
	display: flex;
	flex-direction: column;
	align-items: center;
	transition: transform 0.18s ease, opacity 0.18s ease;
}
.g-item > view,
.g-item > .uni-icons {
	height: 56rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}
.g-hot {
	position: relative;
	width: 56rpx;
	height: 56rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	background: #e8833a;
	border-radius: 50%;
	box-shadow: 0 4rpx 12rpx rgba(232, 131, 58, 0.28);
}
.g-badge {
	position: absolute;
	top: -10rpx;
	right: -22rpx;
	font-size: 17rpx;
	line-height: 1;
	padding: 5rpx 9rpx;
	background: #ffffff;
	color: #e8833a;
	border-radius: 999rpx;
	border: 2rpx solid #fdeedd;
}
.g-text {
	margin-top: 10rpx;
	font-size: 21rpx;
	color: #6f6357;
}

/* 活动条 */
.act-banner {
	display: flex;
	align-items: center;
	justify-content: space-between;
	background: linear-gradient(96deg, #fdf0e0 0%, #f9e3c8 60%, #f6d9b8 100%);
	border-radius: 24rpx;
	padding: 18rpx 24rpx;
}
.act-left {
	display: flex;
	flex-direction: column;
}
.act-t1 {
	font-size: 25rpx;
	font-weight: bold;
	color: #6f4a2f;
}
.act-t2 {
	margin-top: 4rpx;
	font-size: 19rpx;
	color: #a3856b;
}
.act-btn {
	flex-shrink: 0;
	height: 50rpx;
	line-height: 50rpx;
	padding: 0 22rpx;
	background: linear-gradient(135deg, #f09a52 0%, #e8833a 100%);
	box-shadow: 0 5rpx 12rpx rgba(232, 131, 58, 0.3);
	color: #ffffff;
	font-size: 21rpx;
	font-weight: 500;
	border-radius: 999rpx;
	transition: transform 0.18s ease, opacity 0.18s ease;
}

/* ===== ③ 今日猫推荐 ===== */
.section {
	margin: 32rpx 32rpx 0;
}
.sec-head {
	display: flex;
	align-items: baseline;
	justify-content: space-between;
	margin-bottom: 24rpx;
}
.sec-title {
	font-size: 32rpx;
	font-weight: bold;
	color: #3d3229;
}
.sec-more {
	font-size: 24rpx;
	color: #8c8177;
	transition: transform 0.18s ease, opacity 0.18s ease;
}
.rec-card {
	display: flex;
	background: #ffffff;
	border-radius: 40rpx;
	padding: 24rpx;
	margin-bottom: 24rpx;
	box-shadow: 0 8rpx 24rpx rgba(61, 50, 41, 0.06);
	transition: transform 0.18s ease, opacity 0.18s ease;
}
.rec-img {
	flex-shrink: 0;
	width: 216rpx;
	height: 216rpx;
	border-radius: 16rpx;
	background: #f3eae0;
}
.rec-info {
	flex: 1;
	min-width: 0;
	margin-left: 24rpx;
	display: flex;
	flex-direction: column;
}
.rec-top {
	display: flex;
	align-items: center;
	gap: 12rpx;
}
.rec-name {
	font-size: 30rpx;
	font-weight: 500;
	color: #3d3229;
	overflow: hidden;
	white-space: nowrap;
	text-overflow: ellipsis;
}
.line-tag {
	flex-shrink: 0;
	font-size: 20rpx;
	padding: 4rpx 14rpx;
	border-radius: 8rpx;
}
.rec-desc {
	font-size: 24rpx;
	color: #8c8177;
	margin-top: 10rpx;
	overflow: hidden;
	white-space: nowrap;
	text-overflow: ellipsis;
}
.rec-bottom {
	margin-top: auto;
	display: flex;
	align-items: center;
	justify-content: space-between;
}
.price {
	color: #e8833a;
}
.price-sym {
	font-size: 24rpx;
}
.price-num {
	font-size: 40rpx;
	font-weight: bold;
}
.rec-btn {
	height: 64rpx;
	line-height: 64rpx;
	padding: 0 32rpx;
	background: #f6eee3;
	color: #6f4a2f;
	font-size: 26rpx;
	font-weight: 500;
	border-radius: 32rpx;
	transition: transform 0.18s ease, opacity 0.18s ease;
}

.footer-slogan {
	margin-top: 32rpx;
	text-align: center;
	font-size: 22rpx;
	color: #c9c0b7;
}
</style>
