<template>
	<view class="page" v-if="draft">
		<!-- 取餐方式 -->
		<view class="panel">
			<view class="mode-seg">
				<view class="seg-item" :class="{ on: mode === '自取' }" @tap="mode = '自取'">
					<text class="seg-t">自取</text>
					<text class="seg-s">免排队</text>
				</view>
				<view class="seg-item" :class="{ on: mode === '外送' }" @tap="mode = '外送'">
					<text class="seg-t">外送</text>
					<text class="seg-s">周五免配</text>
				</view>
			</view>
			<view class="mode-info">
				<block v-if="mode === '自取'">
					<text class="mi-main">{{ store.name }}</text>
					<text class="mi-sub">出杯约 10 分钟，请留意取餐码</text>
				</block>
				<block v-else>
					<text class="mi-main">星悦广场 · 3 栋 502</text>
					<text class="mi-sub">张女士 138****8888 · 约 40 分钟送达</text>
				</block>
			</view>
		</view>

		<!-- 订单清单 -->
		<view class="panel">
			<text class="p-title">订单清单</text>
			<view class="od-item">
				<image class="od-img" :src="draft.drink.img" mode="aspectFill"></image>
				<view class="od-info">
					<text class="od-name">{{ draft.drink.name }}</text>
					<text class="od-spec">{{ draft.ice }} / {{ draft.sugar }}{{ draft.toppings.length ? ' / ' + draft.toppings.map(t => t.name).join('+') : '' }}</text>
					<text class="od-count">x{{ draft.count }}</text>
				</view>
				<view class="od-price">¥{{ (draft.drink.price + tpFee) * draft.count }}</view>
			</view>
		</view>

		<!-- 优惠券 -->
		<view class="panel">
			<text class="p-title">优惠券</text>
			<view class="coupon-chips">
				<view
					v-for="c in usableCoupons"
					:key="c.id"
					class="coupon-chip"
					:class="{ on: couponId === c.id }"
					@tap="pickCoupon(c)"
				>
					<text class="cc-cut">¥{{ c.cut }}</text>
					<text class="cc-title">{{ c.title }}</text>
					<text class="cc-min">{{ c.desc }}</text>
				</view>
				<text v-if="!usableCoupons.length" class="no-coupon">暂无可用优惠券</text>
			</view>
		</view>

		<!-- 价格汇总 -->
		<view class="panel">
			<view class="sum-line"><text>小计</text><text>¥{{ subTotal }}</text></view>
			<view class="sum-line" v-if="couponCut"><text>优惠券抵扣</text><text class="cut">-¥{{ couponCut }}</text></view>
			<view class="sum-line"><text>{{ mode === '自取' ? '打包费' : '配送费' }}</text><text>¥{{ packFee }}</text></view>
			<view class="sum-line sum-total"><text>合计</text><view class="t"><text class="t-sym">¥</text><text class="t-num">{{ total }}</text></view></view>
		</view>

		<!-- 底部结算栏 -->
		<view class="fix-space"></view>
		<view class="fix-bar">
			<view class="total">
				<text class="t-label">合计</text>
				<text class="t-sym">¥</text>
				<text class="t-num">{{ total }}</text>
			</view>
			<view class="go-btn" :class="{ dis: submitting }" hover-class="go-hv" @tap="submitOrder">
				{{ submitting ? '提交中…' : '提交订单' }}
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { STORE, COUPONS, saveOrder } from '@/common/data'
import { getCheckoutDraft, clearCheckoutDraft } from '@/common/store/session'

const store = STORE

const draft = ref(null)
const mode = ref('自取')
const couponId = ref(0)
const submitting = ref(false)

onLoad(() => {
	draft.value = getCheckoutDraft()
})

onShow(() => {
	// 直接进入（无草稿）时返回点单页
	if (!getCheckoutDraft()) {
		uni.showToast({ title: '请先选择饮品', icon: 'none' })
		setTimeout(() => uni.switchTab({ url: '/pages/menu/index' }), 600)
	}
})

const tpFee = computed(() => (draft.value ? draft.value.toppings.reduce((s, t) => s + t.price, 0) : 0))
const subTotal = computed(() => (draft.value ? (draft.value.drink.price + tpFee.value) * draft.value.count : 0))
const packFee = computed(() => (mode.value === '自取' ? 1 : 4))

const usableCoupons = computed(() =>
	draft.value ? COUPONS.filter(c => subTotal.value >= c.min) : []
)
const couponCut = computed(() => {
	const c = usableCoupons.value.find(x => x.id === couponId.value)
	return c ? c.cut : 0
})
const total = computed(() => Math.max(0, subTotal.value + packFee.value - couponCut.value))

const pickCoupon = (c) => {
	couponId.value = couponId.value === c.id ? 0 : c.id
}

const submitOrder = () => {
	if (submitting.value) return
	submitting.value = true
	const order = saveOrder({
		drink: draft.value.drink,
		ice: draft.value.ice,
		sugar: draft.value.sugar,
		toppings: draft.value.toppings,
		count: draft.value.count,
		mode: mode.value,
		coupon: couponCut.value
	})
	clearCheckoutDraft()
	setTimeout(() => {
		submitting.value = false
		uni.redirectTo({ url: '/pages/order/order?oid=' + order.out_trade_no })
	}, 500)
}
</script>

<style>
page {
	background: #faf6f0;
}
.page {
	min-height: 100vh;
	padding: 24rpx 32rpx 48rpx;
	box-sizing: border-box;
}
.hv {
	opacity: 0.85;
}

.panel {
	background: #ffffff;
	border-radius: 40rpx;
	padding: 32rpx;
	margin-bottom: 24rpx;
	box-shadow: 0 8rpx 24rpx rgba(61, 50, 41, 0.06);
}
.p-title {
	font-size: 30rpx;
	font-weight: bold;
	color: #3d3229;
}

/* 取餐方式 */
.mode-seg {
	display: flex;
	background: #f7f2eb;
	border-radius: 24rpx;
	padding: 8rpx;
}
.seg-item {
	flex: 1;
	text-align: center;
	padding: 16rpx 0;
	border-radius: 18rpx;
	display: flex;
	flex-direction: column;
}
.seg-item.on {
	background: #8b5e3c;
}
.seg-t {
	font-size: 30rpx;
	font-weight: medium;
	color: #3d3229;
}
.seg-item.on .seg-t {
	color: #ffffff;
}
.seg-s {
	font-size: 20rpx;
	color: #c9c0b7;
	margin-top: 2rpx;
}
.seg-item.on .seg-s {
	color: rgba(255, 255, 255, 0.7);
}
.mode-info {
	margin-top: 24rpx;
	display: flex;
	flex-direction: column;
}
.mi-main {
	font-size: 30rpx;
	font-weight: medium;
	color: #3d3229;
}
.mi-sub {
	margin-top: 8rpx;
	font-size: 24rpx;
	color: #8c8177;
}

/* 清单 */
.od-item {
	display: flex;
	align-items: center;
	margin-top: 24rpx;
}
.od-img {
	flex-shrink: 0;
	width: 120rpx;
	height: 120rpx;
	border-radius: 24rpx;
	background: #f3eae0;
}
.od-info {
	flex: 1;
	min-width: 0;
	margin: 0 20rpx;
	display: flex;
	flex-direction: column;
}
.od-name {
	font-size: 28rpx;
	font-weight: medium;
	color: #3d3229;
}
.od-spec {
	font-size: 22rpx;
	color: #8c8177;
	margin-top: 6rpx;
	overflow: hidden;
	white-space: nowrap;
	text-overflow: ellipsis;
}
.od-count {
	font-size: 22rpx;
	color: #c9c0b7;
	margin-top: 6rpx;
}
.od-price {
	font-size: 28rpx;
	font-weight: medium;
	color: #3d3229;
}

/* 优惠券 */
.coupon-chips {
	display: flex;
	flex-wrap: wrap;
	gap: 16rpx;
	margin-top: 24rpx;
}
.coupon-chip {
	flex: 1;
	min-width: 40%;
	background: #fdf0e4;
	border: 2rpx solid transparent;
	border-radius: 24rpx;
	padding: 20rpx 24rpx;
	display: flex;
	flex-direction: column;
	box-sizing: border-box;
}
.coupon-chip.on {
	border-color: #e8833a;
	background: #ffffff;
}
.cc-cut {
	font-size: 34rpx;
	font-weight: bold;
	color: #e8833a;
}
.cc-title {
	font-size: 24rpx;
	color: #3d3229;
	margin-top: 4rpx;
}
.cc-min {
	font-size: 20rpx;
	color: #8c8177;
	margin-top: 2rpx;
}
.no-coupon {
	font-size: 24rpx;
	color: #c9c0b7;
}

/* 汇总 */
.sum-line {
	display: flex;
	justify-content: space-between;
	font-size: 26rpx;
	color: #8c8177;
	margin-top: 16rpx;
}
.sum-line:first-child {
	margin-top: 0;
}
.sum-line .cut {
	color: #e8833a;
}
.sum-total {
	margin-top: 24rpx;
	padding-top: 24rpx;
	border-top: 2rpx solid #f0e9e1;
	color: #3d3229;
	font-weight: medium;
}
.sum-total .t {
	display: flex;
	align-items: baseline;
}
.t-sym {
	font-size: 24rpx;
	color: #e8833a;
}
.t-num {
	font-size: 40rpx;
	font-weight: bold;
	color: #e8833a;
}

/* 底部结算栏 */
.fix-space {
	height: 40rpx;
}
.fix-bar {
	position: fixed;
	left: 0;
	right: 0;
	bottom: 0;
	display: flex;
	align-items: center;
	padding: 20rpx 32rpx calc(20rpx + env(safe-area-inset-bottom));
	background: #ffffff;
	box-shadow: 0 -8rpx 24rpx rgba(61, 50, 41, 0.08);
	z-index: 9;
}
.total {
	flex: 1;
	display: flex;
	align-items: baseline;
}
.t-label {
	font-size: 24rpx;
	color: #8c8177;
	margin-right: 8rpx;
}
.t-sym {
	font-size: 24rpx;
	color: #e8833a;
}
.t-num {
	font-size: 44rpx;
	font-weight: bold;
	color: #e8833a;
}
.go-btn {
	height: 88rpx;
	line-height: 88rpx;
	padding: 0 48rpx;
	background: #8b5e3c;
	color: #ffffff;
	font-size: 30rpx;
	border-radius: 44rpx;
}
.go-btn.dis {
	opacity: 0.5;
}
.go-hv {
	background: #6f4a2f;
}
</style>
