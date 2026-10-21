<template>
	<view class="page">
		<!-- ① 顶栏：自取 | 外卖 + 搜索（压缩高度，给列表让空间） -->
		<view class="topbar" :style="{ paddingTop: safeTop }">
			<view class="mode">
				<text class="mode-t" :class="{ on: mode === '自取' }" @tap="mode = '自取'">自取</text>
				<view class="mode-div"></view>
				<text class="mode-t" :class="{ on: mode === '外卖' }" @tap="mode = '外卖'">外卖</text>
			</view>
			<view class="tb-search" hover-class="hv" @tap="onSearch">
				<uni-icons type="search" size="20" color="#3d3229"></uni-icons>
			</view>
		</view>

		<!-- ② 门店行（点击 → 地图选店弹层） -->
		<view class="store-row" hover-class="hv" @tap="storePick = true">
			<view class="st-left">
				<view class="st-name">
					<uni-icons type="star-filled" size="17" color="#E8833A"></uni-icons>
					<text class="st-title">{{ selStore.name }}</text>
					<text class="st-arrow">›</text>
				</view>
				<view class="st-dist">
					<uni-icons type="location" size="13" color="#8C8177"></uni-icons>
					<text class="st-dist-t">{{ selStore.area }} · {{ selStore.dist }}</text>
				</view>
			</view>
			<view class="st-badge">
				<text class="stb-t1">拼单</text>
				<text class="stb-t2">享优惠</text>
			</view>
		</view>

		<!-- ③ 优惠券胶囊条 -->
		<view class="coupon-strip">
			<scroll-view scroll-x class="cs-scroll">
				<view class="cs-inner">
					<view class="cs-pill" v-for="cp in coupons" :key="cp.id" hover-class="hv" @tap="onCoupon">
						<text class="cs-t">{{ cp.title }} {{ cp.desc }}</text>
					</view>
					<view class="cs-pill" hover-class="hv" @tap="onCoupon">
						<text class="cs-t">周二会员日 全场5.8折</text>
					</view>
				</view>
			</scroll-view>
			<view class="cs-more" hover-class="hv" @tap="onCoupon">
				<text class="cs-more-t">点击查看</text>
				<text class="cs-more-a">∨</text>
			</view>
		</view>

		<!-- ④ 新客领券 banner（压缩版） -->
		<view class="promo-banner">
			<view class="pb-deco pb-d1"></view>
			<view class="pb-deco pb-d2"></view>
			<view class="pb-left">
				<text class="pb-tag">新朋友专享</text>
				<view class="pb-title"><text class="pb-big">首单立减 3 元</text><text class="pb-sub2">第二杯半价</text></view>
				<view class="pb-btn" hover-class="hv" @tap="onCoupon">立即领取</view>
			</view>
		</view>

		<!-- ⑤ 页签 -->
		<view class="mtabs">
			<view
				v-for="tb in tabs"
				:key="tb.id"
				class="mt-tab"
				:class="{ on: tabId === tb.id }"
				hover-class="hv"
				@tap="tabId = tb.id"
			>
				<text class="mt-t">{{ tb.name }}</text>
				<view class="mt-bar"></view>
			</view>
		</view>

		<!-- ⑥ 左侧分类 + 右侧商品列表 -->
		<view class="content">
			<scroll-view scroll-y class="sidebar">
				<view
					v-for="sb in sideList"
					:key="sb.id"
					class="sb-item"
					:class="{ on: sideId === sb.id }"
					hover-class="hv"
					@tap="sideId = sb.id"
				>
					<view class="sb-ind"></view>
					<text class="sb-t">{{ sb.name }}</text>
					<text class="sb-badge sb-new" v-if="sb.isNew">NEW</text>
					<text class="sb-badge sb-hot" v-if="sb.isHot">HOT</text>
				</view>
			</scroll-view>

			<scroll-view scroll-y class="plist" :scroll-into-view="'sec-' + sideId" scroll-with-animation>
				<view id="sec-all"></view>
				<view class="no-drink" v-if="!sections.length">这个分区暂时没有饮品，看看别的吧</view>
				<view class="sec" v-for="sec in sections" :key="sec.id" :id="'sec-' + sec.id">
					<view class="sec-head">
						<text class="sec-name" :style="{ color: sec.color }">{{ sec.name }}</text>
						<text class="sec-desc">{{ sec.desc }}</text>
					</view>
					<view class="p-card" v-for="dk in sec.drinks" :key="dk.id" hover-class="hv" @tap="toDetail(dk.id)">
						<image class="p-img" :src="dk.img" mode="aspectFill"></image>
						<view class="p-body">
							<text class="p-name">{{ dk.name }}</text>
							<view class="p-tags">
								<text class="p-tag p-new" v-if="dk.isNew">新品</text>
								<text class="p-tag p-hot" v-if="dk.hot">会员价</text>
								<paws :score="dk.paws" :size="22"></paws>
							</view>
							<text class="p-desc">{{ dk.desc }}</text>
							<view class="p-bottom">
								<view class="p-price">
									<text class="p-sym">¥</text>
									<text class="p-num">{{ dk.price }}</text>
									<text class="p-orig" v-if="dk.orig">¥{{ dk.orig }}</text>
								</view>
								<view class="p-buy" hover-class="hv" @tap.stop="openSpec(dk)">选规格</view>
							</view>
						</view>
					</view>
				</view>
				<view class="list-pad"></view>
			</scroll-view>
		</view>

		<!-- ⑦ 购物车栏（加购后出现） -->
		<view class="cart-wrap" v-if="cartCount">
			<view class="cart-save" v-if="cartSave">已享会员折扣，共减免 ¥{{ cartSave }}</view>
			<view class="cart-bar" :class="{ flat: cartSave }">
				<view class="cb-left" @tap="cartPeek">
					<view class="cb-icon">
						<uni-icons type="cart-filled" size="24" color="#fff7ec"></uni-icons>
						<view class="cb-badge">{{ cartCount }}</view>
					</view>
					<view class="cb-price">
						<text class="cb-pre">预估</text>
						<text class="cb-sym">¥</text>
						<text class="cb-num">{{ cartTotal }}</text>
						<text class="cb-orig" v-if="cartSave">¥{{ cartTotal + cartSave }}</text>
					</view>
				</view>
				<view class="cb-go" hover-class="hv" @tap="checkout">去结算</view>
			</view>
		</view>

		<!-- ⑧ 地图选店弹层 -->
		<view class="mask" v-if="storePick" @tap="storePick = false"></view>
		<view class="store-sheet" v-if="storePick">
			<view class="ss-handle"></view>
			<text class="ss-title">选择门店</text>
			<view class="ss-map">
				<view class="ss-block ss-b1"></view>
				<view class="ss-block ss-b2"></view>
				<view class="ss-block ss-b3"></view>
				<view class="ss-road ss-r1"></view>
				<view class="ss-road ss-r2"></view>
				<view class="ss-pin">
					<view class="ss-pin-dot"></view>
					<view class="ss-bubble">距您 205m</view>
				</view>
			</view>
			<view
				class="ss-item"
				v-for="st in stores"
				:key="st.id"
				hover-class="hv"
				@tap="pickStore(st)"
			>
				<view class="ss-radio" :class="{ on: selStoreId === st.id }"></view>
				<view class="ss-mid">
					<text class="ss-name">{{ st.name }}</text>
					<text class="ss-area">{{ st.area }} · {{ st.dist }} · 营业中</text>
				</view>
				<text class="ss-cur" v-if="selStoreId === st.id">当前</text>
			</view>
			<view class="ss-pad"></view>
		</view>

		<!-- ⑨ 规格选择弹层 -->
		<view class="mask" v-if="specDrink" @tap="closeSpec"></view>
		<view class="spec-sheet" v-if="specDrink">
			<view class="sp-hero" :style="{ background: lineOf(specDrink.line).bg }">
				<image class="sp-img" :src="specDrink.img" mode="aspectFill"></image>
				<view class="sp-close" hover-class="hv" @tap="closeSpec">
					<uni-icons type="closeempty" size="18" color="#fff7ec"></uni-icons>
				</view>
			</view>
			<view class="sp-info">
				<view class="sp-name-row">
					<text class="sp-name">{{ specDrink.name }}</text>
					<text class="sp-ltag" :style="{ color: lineOf(specDrink.line).color, background: '#ffffff' }">{{ lineOf(specDrink.line).tag }}</text>
				</view>
				<text class="sp-desc">{{ specDrink.desc }}</text>
			</view>
			<scroll-view scroll-y class="sp-opts">
				<view class="sp-group">
					<text class="sp-gtitle">可选糖<text class="sp-gsub">（必选1份）</text></text>
					<view class="sp-chips">
						<view
							v-for="sg in sugarOpts"
							:key="sg"
							class="sp-chip"
							:class="{ on: spSugar === sg }"
							hover-class="hv"
							@tap="spSugar = sg"
						>{{ sg }}</view>
					</view>
				</view>
				<view class="sp-group">
					<text class="sp-gtitle">冰度<text class="sp-gsub">（必选1份）</text></text>
					<view class="sp-chips">
						<view
							v-for="ic in iceOpts"
							:key="ic"
							class="sp-chip"
							:class="{ on: spIce === ic }"
							hover-class="hv"
							@tap="spIce = ic"
						>{{ ic }}</view>
					</view>
				</view>
				<view class="sp-group">
					<text class="sp-gtitle">小料<text class="sp-gsub">（可多选）</text></text>
					<view class="sp-chips">
						<view
							v-for="tp in toppings"
							:key="tp.name"
							class="sp-chip"
							:class="{ on: hasTop(tp) }"
							hover-class="hv"
							@tap="toggleTop(tp)"
						>{{ tp.name }} +{{ tp.price }}</view>
					</view>
				</view>
			</scroll-view>
			<view class="sp-foot">
				<view class="sp-price-row">
					<view class="p-price">
						<text class="p-sym">¥</text>
						<text class="p-num">{{ spTotal }}</text>
						<text class="p-orig" v-if="spOrigTotal">¥{{ spOrigTotal }}</text>
					</view>
					<view class="sp-count">
						<view class="sc-btn" hover-class="hv" @tap="spCount > 1 ? spCount-- : ''">－</view>
						<text class="sc-num">{{ spCount }}</text>
						<view class="sc-btn sc-add" hover-class="hv" @tap="spCount++">＋</view>
					</view>
				</view>
				<text class="sp-sum">【{{ spSpecText }}】</text>
				<view class="sp-btns">
					<view class="sp-buy" hover-class="hv" @tap="buyNow">立即购买</view>
					<view class="sp-addcart" hover-class="hv" @tap="addCart">加入购物车</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { DRINKS, LINES, STORE, COUPONS, ICE_OPTS, SUGAR_OPTS, TOPPINGS, saveOrder } from '../../common/js/data.js'

const coupons = COUPONS
const iceOpts = ICE_OPTS
const sugarOpts = SUGAR_OPTS
const toppings = TOPPINGS

// 沉浸式顶栏
const statusBarHeight = uni.getSystemInfoSync().statusBarHeight
const safeTop = statusBarHeight + 4 + 'px'

const mode = ref('自取')
const tabId = ref('classic')
const sideId = ref('all')

const tabs = [
	{ id: 'classic', name: '经典菜单' },
	{ id: 'member', name: '会员专享价' },
	{ id: 'mine', name: '我的常点' }
]

// 门店（点门店行 → 地图选店弹层切换）
const stores = [
	{ id: 1, name: '四猫茶学园·星悦广场店', area: '星悦广场 1F', dist: '距您 205m' },
	{ id: 2, name: '四猫茶学园·万象城店', area: '万象城 L2', dist: '距您 1.2km' },
	{ id: 3, name: '四猫茶学园·大学城店', area: '大学城美食街 B1', dist: '距您 2.4km' }
]
const selStoreId = ref(1)
const selStore = computed(() => stores.find(s => s.id === selStoreId.value))
const storePick = ref(false)
const pickStore = (st) => {
	selStoreId.value = st.id
	storePick.value = false
}

// 页签候选池：经典=全部；会员专享价=hot；我的常点=5爪
const tabDrinks = computed(() => {
	if (tabId.value === 'member') return DRINKS.filter(d => d.hot)
	if (tabId.value === 'mine') return DRINKS.filter(d => d.paws === 5)
	return DRINKS
})

// 分类栏：带 NEW / HOT 角标（数据驱动：线内含新品/人气款）
const sideList = computed(() => [{ id: 'all', name: '全部' }].concat(LINES.map(l => ({
	id: l.id,
	name: l.tag,
	isNew: tabDrinks.value.some(d => d.line === l.id && d.isNew),
	isHot: tabDrinks.value.some(d => d.line === l.id && d.hot)
}))))

// 按产品线分节，空节隐藏
const sections = computed(() =>
	LINES.map(l => ({ ...l, drinks: tabDrinks.value.filter(d => d.line === l.id) })).filter(s => s.drinks.length)
)

const lineOf = (id) => LINES.find(l => l.id === id)

// ===== 规格弹层 =====
const specDrink = ref(null)
const spIce = ref('正常冰')
const spSugar = ref('七分糖')
const spTops = ref([])
const spCount = ref(1)

const openSpec = (dk) => {
	specDrink.value = dk
	spIce.value = '正常冰'
	spSugar.value = '七分糖'
	spTops.value = []
	spCount.value = 1
}
const closeSpec = () => { specDrink.value = null }
const hasTop = (tp) => spTops.value.some(t => t.name === tp.name)
const toggleTop = (tp) => {
	const i = spTops.value.findIndex(t => t.name === tp.name)
	if (i > -1) spTops.value.splice(i, 1)
	else spTops.value.push(tp)
}
const spTopTotal = computed(() => spTops.value.reduce((s, t) => s + t.price, 0))
const spTotal = computed(() => (specDrink.value ? (specDrink.value.price + spTopTotal.value) * spCount.value : 0))
const spOrigTotal = computed(() => (specDrink.value && specDrink.value.orig ? specDrink.value.orig * spCount.value : 0))
const spSpecText = computed(() => [spIce.value, spSugar.value].concat(spTops.value.map(t => t.name)).join('·'))

// ===== 购物车 =====
const cart = ref([])
const cartCount = computed(() => cart.value.reduce((s, it) => s + it.count, 0))
const cartTotal = computed(() => cart.value.reduce((s, it) => s + (it.drink.price + it.topTotal) * it.count, 0))
const cartSave = computed(() => cart.value.reduce((s, it) => s + (it.drink.orig ? (it.drink.orig - it.drink.price) * it.count : 0), 0))

const addCart = () => {
	cart.value.push({
		drink: specDrink.value,
		ice: spIce.value,
		sugar: spSugar.value,
		tops: spTops.value.map(t => t.name),
		topTotal: spTopTotal.value,
		count: spCount.value
	})
	closeSpec()
	uni.showToast({ title: '已加入购物车', icon: 'none' })
}
const buyNow = () => {
	saveOrder({ drink: specDrink.value, ice: spIce.value, sugar: spSugar.value, toppings: spTops.value, count: spCount.value, mode: mode.value })
	closeSpec()
	uni.switchTab({ url: '/pages/order/index' })
}
const checkout = () => {
	if (!cart.value.length) return
	cart.value.forEach(it => saveOrder({
		drink: it.drink, ice: it.ice, sugar: it.sugar,
		toppings: TOPPINGS.filter(t => it.tops.includes(t.name)),
		count: it.count, mode: mode.value
	}))
	cart.value = []
	uni.switchTab({ url: '/pages/order/index' })
}
const cartPeek = () => {
	uni.showToast({ title: '购物车明细即将上线', icon: 'none' })
}

const toDetail = (id) => {
	uni.navigateTo({ url: '/pages/detail/index?id=' + id })
}
const onSearch = () => {
	uni.showToast({ title: '搜索即将上线', icon: 'none' })
}
const onCoupon = () => {
	uni.showToast({ title: '领券中心即将上线', icon: 'none' })
}
</script>

<style lang="scss" scoped>
.page {
	height: 100vh;
	display: flex;
	flex-direction: column;
	overflow: hidden;
	background: #faf6f0;
}
.hv {
	opacity: 0.85;
}

/* ① 顶栏（紧凑） */
.topbar {
	display: flex;
	align-items: center;
	padding: 4px 24rpx 4rpx;
}
.mode {
	display: flex;
	align-items: center;
}
.mode-t {
	font-size: 34rpx;
	font-weight: bold;
	color: #b7ab9e;
	transition: color 0.18s ease;
}
.mode-t.on {
	color: #3d3229;
}
.mode-div {
	width: 2rpx;
	height: 26rpx;
	background: #ddd2c5;
	margin: 0 20rpx;
}
.tb-search {
	margin-left: 22rpx;
	width: 54rpx;
	height: 54rpx;
	border-radius: 50%;
	background: #ffffff;
	display: flex;
	align-items: center;
	justify-content: center;
	box-shadow: 0 4rpx 12rpx rgba(61, 50, 41, 0.06);
}

/* ② 门店行（紧凑） */
.store-row {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 4rpx 24rpx 6rpx;
}
.st-name {
	display: flex;
	align-items: center;
}
.st-title {
	margin: 0 6rpx 0 8rpx;
	font-size: 29rpx;
	font-weight: bold;
	color: #3d3229;
	max-width: 430rpx;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}
.st-arrow {
	font-size: 28rpx;
	color: #8c8177;
}
.st-dist {
	display: flex;
	align-items: center;
	margin-top: 2rpx;
}
.st-dist-t {
	margin-left: 4rpx;
	font-size: 20rpx;
	color: #8c8177;
}
.st-badge {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	width: 74rpx;
	height: 74rpx;
	border-radius: 18rpx 18rpx 18rpx 4rpx;
	background: #f3eae0;
}
.stb-t1 {
	font-size: 20rpx;
	font-weight: bold;
	color: #8b5e3c;
}
.stb-t2 {
	font-size: 16rpx;
	color: #8b5e3c;
	margin-top: 2rpx;
}

/* ③ 优惠券胶囊条（紧凑） */
.coupon-strip {
	display: flex;
	align-items: center;
	padding: 2rpx 24rpx 6rpx;
}
.cs-scroll {
	flex: 1;
	white-space: nowrap;
}
.cs-inner {
	display: inline-flex;
	gap: 10rpx;
}
.cs-pill {
	flex-shrink: 0;
	padding: 6rpx 16rpx;
	background: #ffffff;
	border: 2rpx solid #eadfcd;
	border-radius: 999rpx;
	font-size: 20rpx;
	color: #6f4a2f;
}
.cs-more {
	flex-shrink: 0;
	display: flex;
	align-items: center;
	margin-left: 10rpx;
}
.cs-more-t {
	font-size: 20rpx;
	color: #8c8177;
}
.cs-more-a {
	font-size: 17rpx;
	color: #8c8177;
	margin-left: 2rpx;
}

/* ④ 新客 banner（紧凑） */
.promo-banner {
	position: relative;
	margin: 2rpx 24rpx 8rpx;
	padding: 18rpx 26rpx;
	border-radius: 22rpx;
	background: linear-gradient(120deg, #fdeedc 0%, #f9dcb8 58%, #f6cf9e 100%);
	overflow: hidden;
}
.pb-deco {
	position: absolute;
	border-radius: 50%;
}
.pb-d1 {
	right: -40rpx;
	top: -50rpx;
	width: 170rpx;
	height: 170rpx;
	background: rgba(255, 255, 255, 0.45);
}
.pb-d2 {
	right: 80rpx;
	bottom: -60rpx;
	width: 120rpx;
	height: 120rpx;
	background: rgba(232, 131, 58, 0.14);
}
.pb-left {
	position: relative;
}
.pb-tag {
	display: inline-block;
	padding: 2rpx 12rpx;
	border-radius: 8rpx;
	background: #8b5e3c;
	color: #fff7ec;
	font-size: 18rpx;
}
.pb-title {
	display: flex;
	align-items: baseline;
	margin-top: 8rpx;
}
.pb-big {
	font-size: 34rpx;
	font-weight: 900;
	color: #5a3a1e;
	letter-spacing: 1rpx;
}
.pb-sub2 {
	margin-left: 14rpx;
	font-size: 24rpx;
	font-weight: bold;
	color: #8b5e3c;
}
.pb-btn {
	display: inline-block;
	margin-top: 10rpx;
	padding: 6rpx 24rpx;
	border-radius: 999rpx;
	background: linear-gradient(135deg, #f09a52 0%, #e8833a 100%);
	box-shadow: 0 4rpx 12rpx rgba(232, 131, 58, 0.35);
	color: #ffffff;
	font-size: 22rpx;
	font-weight: 500;
}

/* ⑤ 页签（紧凑） */
.mtabs {
	display: flex;
	padding: 0 24rpx;
	border-bottom: 2rpx solid #f0e7da;
	background: #faf6f0;
}
.mt-tab {
	margin-right: 44rpx;
	padding: 8rpx 0 0;
	display: flex;
	flex-direction: column;
	align-items: center;
}
.mt-t {
	font-size: 26rpx;
	color: #8c8177;
	padding-bottom: 10rpx;
}
.mt-tab.on .mt-t {
	font-size: 28rpx;
	font-weight: bold;
	color: #3d3229;
}
.mt-bar {
	width: 40rpx;
	height: 6rpx;
	border-radius: 3rpx;
	background: transparent;
}
.mt-tab.on .mt-bar {
	background: #8b5e3c;
}

/* ⑥ 分类 + 列表（占据剩余全部高度） */
.content {
	flex: 1;
	min-height: 0;
	display: flex;
}
.sidebar {
	width: 150rpx;
	height: 100%;
	background: #f3ede4;
	flex-shrink: 0;
}
.sb-item {
	position: relative;
	padding: 26rpx 8rpx 26rpx 24rpx;
	transition: background 0.18s ease;
}
.sb-t {
	font-size: 25rpx;
	color: #8c8177;
}
.sb-item.on {
	background: #faf6f0;
}
.sb-item.on .sb-t {
	font-weight: bold;
	color: #3d3229;
}
.sb-ind {
	position: absolute;
	left: 0;
	top: 50%;
	transform: translateY(-50%);
	width: 6rpx;
	height: 0;
	border-radius: 3rpx;
	background: #e8833a;
	transition: height 0.18s ease;
}
.sb-item.on .sb-ind {
	height: 36rpx;
}
.sb-badge {
	position: absolute;
	top: 8rpx;
	right: 12rpx;
	font-size: 16rpx;
	font-weight: bold;
	line-height: 1;
	padding: 3rpx 8rpx;
	border-radius: 6rpx 6rpx 6rpx 0;
	color: #ffffff;
}
.sb-new {
	background: #e8833a;
}
.sb-hot {
	background: #8b5e3c;
	top: auto;
	bottom: 8rpx;
}

.plist {
	flex: 1;
	height: 100%;
	padding: 0 20rpx;
	box-sizing: border-box;
}
.no-drink {
	padding: 60rpx 0;
	text-align: center;
	font-size: 24rpx;
	color: #b7ab9e;
}
.sec-head {
	display: flex;
	align-items: baseline;
	padding: 22rpx 4rpx 14rpx;
}
.sec-name {
	font-size: 26rpx;
	font-weight: bold;
}
.sec-desc {
	margin-left: 12rpx;
	font-size: 19rpx;
	color: #b7ab9e;
}
.p-card {
	display: flex;
	background: #ffffff;
	border-radius: 24rpx;
	padding: 18rpx;
	margin-bottom: 18rpx;
	box-shadow: 0 8rpx 24rpx rgba(61, 50, 41, 0.06);
}
.p-img {
	flex-shrink: 0;
	width: 150rpx;
	height: 150rpx;
	border-radius: 16rpx;
	background: #f3eae0;
}
.p-body {
	flex: 1;
	min-width: 0;
	margin-left: 18rpx;
	display: flex;
	flex-direction: column;
}
.p-name {
	font-size: 28rpx;
	font-weight: bold;
	color: #3d3229;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}
.p-tags {
	display: flex;
	align-items: center;
	margin-top: 6rpx;
}
.p-tag {
	flex-shrink: 0;
	margin-right: 10rpx;
	padding: 2rpx 12rpx;
	border-radius: 6rpx;
	font-size: 18rpx;
}
.p-new {
	color: #e8833a;
	background: #fdeedd;
}
.p-hot {
	color: #8b5e3c;
	background: #f3eae0;
}
.p-desc {
	margin-top: 6rpx;
	font-size: 21rpx;
	color: #8c8177;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}
.p-bottom {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-top: auto;
}
.p-price {
	display: flex;
	align-items: baseline;
	color: #e8833a;
}
.p-sym {
	font-size: 22rpx;
	font-weight: bold;
}
.p-num {
	font-size: 36rpx;
	font-weight: bold;
}
.p-orig {
	margin-left: 10rpx;
	font-size: 20rpx;
	color: #b7ab9e;
	text-decoration: line-through;
}
.p-buy {
	flex-shrink: 0;
	height: 56rpx;
	line-height: 56rpx;
	padding: 0 26rpx;
	border-radius: 999rpx;
	background: linear-gradient(135deg, #f09a52 0%, #e8833a 100%);
	box-shadow: 0 6rpx 14rpx rgba(232, 131, 58, 0.3);
	color: #ffffff;
	font-size: 24rpx;
	font-weight: 500;
}

/* ⑦ 购物车栏 */
.cart-wrap {
	position: fixed;
	left: 24rpx;
	right: 24rpx;
	bottom: 24rpx;
	z-index: 60;
}
.cart-save {
	background: #fdf3dd;
	color: #8b5e3c;
	font-size: 21rpx;
	text-align: center;
	padding: 10rpx 0;
	border-radius: 16rpx 16rpx 0 0;
}
.cart-bar {
	display: flex;
	align-items: center;
	height: 96rpx;
	border-radius: 999rpx;
	background: #3d3229;
	box-shadow: 0 12rpx 32rpx rgba(61, 50, 41, 0.35);
	overflow: hidden;
}
.cart-bar.flat {
	border-radius: 0 0 999rpx 999rpx;
}
.cb-left {
	flex: 1;
	display: flex;
	align-items: center;
	padding-left: 28rpx;
}
.cb-icon {
	position: relative;
	width: 72rpx;
	height: 72rpx;
	border-radius: 50%;
	background: #574a3f;
	display: flex;
	align-items: center;
	justify-content: center;
}
.cb-badge {
	position: absolute;
	top: -6rpx;
	right: -6rpx;
	min-width: 30rpx;
	height: 30rpx;
	line-height: 30rpx;
	padding: 0 6rpx;
	border-radius: 15rpx;
	background: #e8833a;
	color: #ffffff;
	font-size: 18rpx;
	font-weight: bold;
	text-align: center;
}
.cb-price {
	display: flex;
	align-items: baseline;
	margin-left: 20rpx;
	color: #fff7ec;
}
.cb-pre {
	font-size: 20rpx;
	color: #b7ab9e;
	margin-right: 6rpx;
}
.cb-sym {
	font-size: 22rpx;
	font-weight: bold;
}
.cb-num {
	font-size: 38rpx;
	font-weight: bold;
}
.cb-orig {
	margin-left: 10rpx;
	font-size: 20rpx;
	color: #8c8177;
	text-decoration: line-through;
}
.cb-go {
	flex-shrink: 0;
	height: 96rpx;
	line-height: 96rpx;
	padding: 0 44rpx;
	background: linear-gradient(135deg, #f09a52 0%, #e8833a 100%);
	color: #ffffff;
	font-size: 28rpx;
	font-weight: bold;
}

/* 弹层通用 */
.mask {
	position: fixed;
	left: 0;
	top: 0;
	right: 0;
	bottom: 0;
	background: rgba(30, 24, 18, 0.55);
	z-index: 90;
	animation: fadeIn 0.22s ease both;
}
@keyframes fadeIn {
	from { opacity: 0; }
	to { opacity: 1; }
}
@keyframes slideUp {
	from { transform: translateY(60rpx); opacity: 0; }
	to { transform: translateY(0); opacity: 1; }
}

/* ⑧ 地图选店弹层 */
.store-sheet {
	position: fixed;
	left: 0;
	right: 0;
	bottom: 0;
	z-index: 100;
	background: #ffffff;
	border-radius: 32rpx 32rpx 0 0;
	padding: 16rpx 32rpx 0;
	animation: slideUp 0.28s cubic-bezier(0.32, 0.72, 0.4, 1) both;
}
.ss-handle {
	width: 72rpx;
	height: 8rpx;
	border-radius: 4rpx;
	background: #e6dccc;
	margin: 0 auto 18rpx;
}
.ss-title {
	display: block;
	text-align: center;
	font-size: 30rpx;
	font-weight: bold;
	color: #3d3229;
}
.ss-map {
	position: relative;
	height: 260rpx;
	border-radius: 20rpx;
	background: #f1ebe1;
	overflow: hidden;
	margin: 20rpx 0 8rpx;
}
.ss-block {
	position: absolute;
	border-radius: 12rpx;
	background: #e6dcc8;
}
.ss-b1 {
	left: -30rpx;
	top: -40rpx;
	width: 220rpx;
	height: 180rpx;
}
.ss-b2 {
	right: -40rpx;
	top: 30rpx;
	width: 260rpx;
	height: 200rpx;
	background: #e2f0e4;
}
.ss-b3 {
	left: 60rpx;
	bottom: -60rpx;
	width: 300rpx;
	height: 160rpx;
}
.ss-road {
	position: absolute;
	background: #ffffff;
	border-radius: 8rpx;
}
.ss-r1 {
	left: -20rpx;
	right: -20rpx;
	top: 40%;
	height: 26rpx;
	transform: rotate(-4deg);
}
.ss-r2 {
	top: -20rpx;
	bottom: -20rpx;
	left: 58%;
	width: 26rpx;
	transform: rotate(6deg);
}
.ss-pin {
	position: absolute;
	left: 46%;
	top: 24%;
}
.ss-pin-dot {
	width: 36rpx;
	height: 36rpx;
	border-radius: 50% 50% 50% 0;
	background: #e8833a;
	transform: rotate(-45deg);
	box-shadow: 0 6rpx 16rpx rgba(232, 131, 58, 0.5);
	border: 4rpx solid #ffffff;
}
.ss-bubble {
	position: absolute;
	left: 30rpx;
	top: -34rpx;
	padding: 6rpx 16rpx;
	border-radius: 999rpx;
	background: #3d3229;
	color: #fff7ec;
	font-size: 20rpx;
	white-space: nowrap;
}
.ss-item {
	display: flex;
	align-items: center;
	padding: 24rpx 4rpx;
	border-bottom: 2rpx solid #f5efe7;
}
.ss-radio {
	flex-shrink: 0;
	width: 32rpx;
	height: 32rpx;
	border-radius: 50%;
	border: 4rpx solid #ddd2c5;
	box-sizing: border-box;
	transition: all 0.18s ease;
}
.ss-radio.on {
	border: 10rpx solid #e8833a;
}
.ss-mid {
	flex: 1;
	min-width: 0;
	margin-left: 20rpx;
}
.ss-name {
	display: block;
	font-size: 27rpx;
	font-weight: bold;
	color: #3d3229;
}
.ss-area {
	display: block;
	margin-top: 4rpx;
	font-size: 20rpx;
	color: #8c8177;
}
.ss-cur {
	flex-shrink: 0;
	font-size: 20rpx;
	color: #e8833a;
	font-weight: bold;
}
.ss-pad {
	height: calc(24rpx + env(safe-area-inset-bottom));
}

/* ⑨ 规格弹层 */
.spec-sheet {
	position: fixed;
	left: 0;
	right: 0;
	bottom: 0;
	z-index: 100;
	display: flex;
	flex-direction: column;
	max-height: 82vh;
	background: #ffffff;
	border-radius: 32rpx 32rpx 0 0;
	overflow: hidden;
	animation: slideUp 0.28s cubic-bezier(0.32, 0.72, 0.4, 1) both;
}
.sp-hero {
	position: relative;
	height: 320rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	flex-shrink: 0;
}
.sp-img {
	width: 250rpx;
	height: 250rpx;
	border-radius: 24rpx;
	box-shadow: 0 16rpx 40rpx rgba(61, 50, 41, 0.18);
}
.sp-close {
	position: absolute;
	right: 28rpx;
	top: 24rpx;
	width: 56rpx;
	height: 56rpx;
	border-radius: 50%;
	background: rgba(61, 50, 41, 0.4);
	display: flex;
	align-items: center;
	justify-content: center;
}
.sp-info {
	padding: 20rpx 32rpx 6rpx;
	flex-shrink: 0;
}
.sp-name-row {
	display: flex;
	align-items: center;
}
.sp-name {
	font-size: 34rpx;
	font-weight: bold;
	color: #3d3229;
}
.sp-ltag {
	margin-left: 14rpx;
	padding: 2rpx 14rpx;
	border-radius: 8rpx;
	font-size: 19rpx;
}
.sp-desc {
	display: block;
	margin-top: 8rpx;
	font-size: 22rpx;
	color: #8c8177;
}
.sp-opts {
	flex: 1;
	min-height: 0;
	padding: 0 32rpx;
	box-sizing: border-box;
}
.sp-group {
	padding: 18rpx 0 4rpx;
}
.sp-gtitle {
	display: block;
	font-size: 25rpx;
	font-weight: bold;
	color: #3d3229;
}
.sp-gsub {
	font-size: 20rpx;
	font-weight: normal;
	color: #b7ab9e;
}
.sp-chips {
	display: flex;
	flex-wrap: wrap;
	gap: 16rpx;
	margin-top: 14rpx;
}
.sp-chip {
	padding: 10rpx 28rpx;
	border-radius: 12rpx;
	background: #f5efe7;
	color: #5a4f43;
	font-size: 23rpx;
	border: 2rpx solid transparent;
	transition: all 0.16s ease;
}
.sp-chip.on {
	background: #fdeedd;
	border-color: #e8833a;
	color: #e8833a;
	font-weight: bold;
}
.sp-foot {
	flex-shrink: 0;
	padding: 16rpx 32rpx calc(20rpx + env(safe-area-inset-bottom));
	border-top: 2rpx solid #f5efe7;
}
.sp-price-row {
	display: flex;
	align-items: center;
	justify-content: space-between;
}
.sp-count {
	display: flex;
	align-items: center;
}
.sc-btn {
	width: 52rpx;
	height: 52rpx;
	line-height: 48rpx;
	text-align: center;
	border-radius: 50%;
	background: #f5efe7;
	color: #5a4f43;
	font-size: 30rpx;
}
.sc-add {
	background: #e8833a;
	color: #ffffff;
}
.sc-num {
	min-width: 64rpx;
	text-align: center;
	font-size: 28rpx;
	font-weight: bold;
	color: #3d3229;
}
.sp-sum {
	display: block;
	margin-top: 10rpx;
	font-size: 20rpx;
	color: #8c8177;
}
.sp-btns {
	display: flex;
	gap: 20rpx;
	margin-top: 18rpx;
}
.sp-buy {
	flex: 1;
	height: 84rpx;
	line-height: 84rpx;
	text-align: center;
	border-radius: 999rpx;
	border: 2rpx solid #8b5e3c;
	color: #8b5e3c;
	font-size: 27rpx;
	font-weight: bold;
	box-sizing: border-box;
}
.sp-addcart {
	flex: 1.6;
	height: 84rpx;
	line-height: 84rpx;
	text-align: center;
	border-radius: 999rpx;
	background: linear-gradient(135deg, #f09a52 0%, #e8833a 100%);
	box-shadow: 0 8rpx 20rpx rgba(232, 131, 58, 0.35);
	color: #ffffff;
	font-size: 27rpx;
	font-weight: bold;
}
.list-pad {
	height: 170rpx;
}
</style>
