<template>
	<view class="page" v-if="order">
		<!-- 状态横幅 -->
		<view class="banner" :class="'bn-' + stateClass">
			<text class="bn-title">{{ stateTitle }}</text>
			<text class="bn-sub">{{ stateSub }}</text>
			<!-- 取餐码 -->
			<view class="pick-code" v-if="showPickCode">
				<text class="pc-label">取餐码</text>
				<text class="pc-num">{{ order.pick_code }}</text>
			</view>
			<!-- 待支付提示 -->
			<text class="bn-sub" v-if="order.state === 'pending_pay'">请尽快完成支付，超时订单将自动取消</text>
		</view>

		<!-- 清单 -->
		<view class="panel">
			<text class="p-title">订单清单</text>
			<view class="od-item" v-for="(item, i) in order.items" :key="i">
				<image class="od-img" :src="item.image" mode="aspectFill"></image>
				<view class="od-info">
					<text class="od-name">{{ item.name }}</text>
					<text class="od-spec">{{ itemSpec(item) }}</text>
					<text class="od-count">x{{ item.count }}</text>
				</view>
				<view class="od-price">¥{{ item.amount }}</view>
			</view>
		</view>

		<!-- 订单信息 -->
		<view class="panel">
			<text class="p-title">订单信息</text>
			<view class="sum-line"><text>订单编号</text><text>{{ order.out_trade_no }}</text></view>
			<view class="sum-line"><text>取餐方式</text><text>{{ order.modeText }}</text></view>
			<view class="sum-line"><text>下单时间</text><text>{{ order.createText }}</text></view>
			<view class="sum-line"><text>小计</text><text>¥{{ order.subtotal }}</text></view>
			<view class="sum-line"><text>{{ order.mode === 'pickup' ? '打包费' : '配送费' }}</text><text>¥{{ order.packFee }}</text></view>
			<view class="sum-line" v-if="order.couponCut"><text>优惠券抵扣</text><text class="cut">-¥{{ order.couponCut }}</text></view>
			<view class="sum-line"><text>实付金额</text><text class="strong">¥{{ order.total }}</text></view>
			<view class="sum-line" v-if="order.payText"><text>支付时间</text><text>{{ order.payText }}</text></view>
			<view class="sum-line addr-line" v-if="order.address">
				<text>收货地址</text>
				<text class="addr-text">{{ order.address.name }} {{ order.address.phone }} {{ order.address.detail }}</text>
			</view>
			<view class="sum-line" v-if="order.remark"><text>备注</text><text>{{ order.remark }}</text></view>
			<view class="sum-line" v-if="order.review">
				<text>我的评价</text>
				<text>{{ order.review.rating }} 星 {{ order.review.content }}</text>
			</view>
			<view class="sum-line" hover-class="hv" @tap="contact">
				<text>联系客服</text><text class="arrow">疑问或投诉 ›</text>
			</view>
		</view>

		<!-- 底部操作栏 -->
		<view class="fix-space" v-if="showActions"></view>
		<view class="fix-bar" v-if="showActions">
			<view class="total" v-if="order.state === 'pending_pay'">
				<text class="t-label">待支付</text>
				<text class="t-sym">¥</text>
				<text class="t-num">{{ order.total }}</text>
			</view>
			<view class="act-spacer" v-else></view>
			<view class="ghost-btn" v-if="canCancel" hover-class="hv" @tap="cancelOrder">取消订单</view>
			<view class="go-btn" v-if="order.state === 'pending_pay'" hover-class="go-hv" @tap="payCurrentOrder">
				{{ paying ? '支付中…' : '立即支付' }}
			</view>
			<view class="go-btn" v-if="order.state === 'making'" hover-class="go-hv" @tap="completeCurrentOrder">
				{{ acting ? '处理中…' : '模拟出杯' }}
			</view>
			<view class="go-btn" v-if="order.state === 'completed' && !order.review" hover-class="go-hv" @tap="openReview">去评价</view>
			<view class="ghost-btn" v-if="order.state === 'completed' && order.review" hover-class="hv" @tap="repeatOrder">再来一单</view>
			<view class="go-btn" v-if="order.state === 'cancelled'" hover-class="go-hv" @tap="repeatOrder">再来一单</view>
		</view>

		<!-- 评价弹层 -->
		<view class="rate-mask" v-if="reviewOpen" @tap="reviewOpen = false">
			<view class="rate-card" @tap.stop>
				<text class="rate-title">给这次点单打个分</text>
				<view class="rate-stars">
					<text
						v-for="n in 5"
						:key="n"
						class="rate-star"
						:class="{ on: n <= rating }"
						@tap="rating = n"
					>★</text>
				</view>
				<textarea
					class="rate-input"
					v-model="reviewContent"
					maxlength="200"
					placeholder="说说这杯茶的味道吧（选填）"
				/>
				<view class="rate-actions">
					<view class="rate-cancel" hover-class="hv" @tap="reviewOpen = false">取消</view>
					<view class="rate-submit" hover-class="hv" @tap="submitReview">{{ reviewing ? '提交中…' : '提交评价' }}</view>
				</view>
			</view>
		</view>
	</view>
	<view class="loading" v-else>{{ loadingText }}</view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { getOptions, getProduct } from '@/common/api/catalog'
import {
	cancelOrder as cancelOrderApi,
	completeOrder as completeOrderApi,
	getOrder,
	payOrder,
	repeatOrder as repeatOrderApi,
	reviewOrder
} from '@/common/api/orders'
import { ensureLogin } from '@/common/api/auth'
import { showError } from '@/common/api/request'
import { toDrink } from '@/common/api/adapters'
import { setCheckoutDraft } from '@/common/store/session'

const order = ref(null)
const loadingText = ref('加载中…')
const paying = ref(false)
const acting = ref(false)
const reviewing = ref(false)
const reviewOpen = ref(false)
const rating = ref(5)
const reviewContent = ref('')
let orderNo = ''

onLoad((params) => {
	orderNo = params.oid || ''
})
onShow(() => {
	if (orderNo) loadOrder()
})

const loadOrder = async () => {
	try {
		await ensureLogin()
		order.value = await getOrder(orderNo)
	} catch (error) {
		loadingText.value = '订单加载失败'
		showError(error)
	}
}

const stateClass = computed(() => ({
	pending_pay: 'warn',
	making: 'make',
	completed: 'done',
	cancelled: 'cancel'
}[order.value?.state] || 'cancel'))

const stateTitle = computed(() => ({
	pending_pay: '订单待支付',
	making: '猫咪制作中～',
	completed: '已完成取餐',
	cancelled: '订单已取消'
}[order.value?.state] || ''))

const stateSub = computed(() => ({
	pending_pay: '四只猫已在等待你的确认',
	making: '正在为你摇茶，请留意取餐码',
	completed: '感谢惠顾，欢迎给猫评员打分',
	cancelled: '期待下次为你服务'
}[order.value?.state] || ''))

const showPickCode = computed(() => order.value?.state === 'making' || order.value?.state === 'completed')
const canCancel = computed(() => order.value?.state === 'pending_pay' || order.value?.state === 'making')
const showActions = computed(() => ['pending_pay', 'making', 'completed', 'cancelled'].includes(order.value?.state))

const itemSpec = (item) => [item.ice, item.sugar, item.topping_names]
	.filter(Boolean)
	.join(' / ')

const payCurrentOrder = async () => {
	if (paying.value) return
	paying.value = true
	try {
		await payOrder(orderNo)
		await loadOrder()
		uni.showToast({ title: '支付成功', icon: 'success' })
	} catch (error) {
		showError(error)
	} finally {
		paying.value = false
	}
}

const cancelOrder = () => {
	uni.showModal({
		title: '取消订单',
		content: order.value?.state === 'making'
			? '制作中取消会退回库存、积分和优惠券，确定取消？'
			: '确定取消这笔订单？优惠券会自动释放。',
		success: async (res) => {
			if (!res.confirm || acting.value) return
			acting.value = true
			try {
				order.value = await cancelOrderApi(orderNo)
				uni.showToast({ title: '订单已取消', icon: 'none' })
			} catch (error) {
				showError(error)
			} finally {
				acting.value = false
			}
		}
	})
}

const completeCurrentOrder = async () => {
	if (acting.value) return
	acting.value = true
	try {
		order.value = await completeOrderApi(orderNo)
		uni.showToast({ title: '已出杯，请取餐', icon: 'none' })
	} catch (error) {
		showError(error)
	} finally {
		acting.value = false
	}
}

const openReview = () => {
	rating.value = 5
	reviewContent.value = ''
	reviewOpen.value = true
}

const submitReview = async () => {
	if (reviewing.value) return
	reviewing.value = true
	try {
		await reviewOrder(orderNo, rating.value, reviewContent.value.trim())
		reviewOpen.value = false
		await loadOrder()
		uni.showToast({ title: '评价成功', icon: 'none' })
	} catch (error) {
		showError(error)
	} finally {
		reviewing.value = false
	}
}

const repeatOrder = async () => {
	if (acting.value) return
	acting.value = true
	try {
		const draft = await repeatOrderApi(orderNo)
		const [options, ...details] = await Promise.all([
			getOptions(),
			...draft.items.map(item => getProduct(item.product_id))
		])
		setCheckoutDraft({
			storeId: draft.store_id,
			mode: draft.mode,
			addressId: draft.address_id || 0,
			items: draft.items.map((item, index) => ({
				product: toDrink(details[index]),
				ice: item.ice,
				sugar: item.sugar,
				toppings: item.topping_ids
					.map(id => (options.toppings || []).find(t => t.id === id))
					.filter(Boolean),
				count: item.count
			}))
		})
		uni.navigateTo({ url: '/pages/checkout/index' })
	} catch (error) {
		showError(error)
	} finally {
		acting.value = false
	}
}

const contact = () => {
	uni.showToast({ title: '客服接入中…', icon: 'none' })
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
}

/* 状态横幅 */
.banner {
	padding: 48rpx 32rpx 56rpx;
	background: #8b5e3c;
	position: relative;
	overflow: hidden;
}
.bn-warn { background: #e8833a; }
.bn-make { background: #8b5e3c; }
.bn-done { background: #5c9e6e; }
.bn-cancel { background: #a79b8e; }
.bn-title {
	display: block;
	font-size: 40rpx;
	font-weight: bold;
	color: #ffffff;
}
.bn-sub {
	display: block;
	margin-top: 12rpx;
	font-size: 24rpx;
	color: rgba(255, 255, 255, 0.8);
}
.pick-code {
	margin-top: 32rpx;
	display: inline-flex;
	flex-direction: column;
	background: rgba(255, 255, 255, 0.16);
	border-radius: 24rpx;
	padding: 20rpx 48rpx;
}
.pc-label {
	font-size: 22rpx;
	color: rgba(255, 255, 255, 0.8);
}
.pc-num {
	font-size: 56rpx;
	font-weight: bold;
	color: #ffffff;
	letter-spacing: 8rpx;
}

/* 面板 */
.panel {
	margin: 24rpx 32rpx 0;
	background: #ffffff;
	border-radius: 40rpx;
	padding: 32rpx;
	box-shadow: 0 8rpx 24rpx rgba(61, 50, 41, 0.06);
}
.p-title {
	font-size: 30rpx;
	font-weight: bold;
	color: #3d3229;
}
.od-item {
	display: flex;
	align-items: center;
	margin-top: 24rpx;
	padding-bottom: 24rpx;
	border-bottom: 2rpx solid #f0e9e1;
}
.od-item:last-child {
	padding-bottom: 0;
	border-bottom: none;
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
}
.od-count {
	font-size: 22rpx;
	color: #c9c0b7;
	margin-top: 6rpx;
}
.od-price {
	font-size: 28rpx;
	font-weight: medium;
	color: #e8833a;
}

.sum-line {
	display: flex;
	justify-content: space-between;
	font-size: 26rpx;
	color: #8c8177;
	margin-top: 20rpx;
}
.sum-line .strong {
	color: #3d3229;
	font-weight: medium;
}
.sum-line .arrow {
	color: #c9c0b7;
}
.sum-line .cut {
	color: #e8833a;
}
.addr-line {
	align-items: flex-start;
}
.addr-text {
	max-width: 440rpx;
	margin-left: 24rpx;
	text-align: right;
	color: #3d3229;
}

/* 加载 */
.loading {
	padding: 240rpx 0;
	text-align: center;
	font-size: 26rpx;
	color: #a79b8e;
}

/* 底部操作栏 */
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
.go-hv {
	background: #6f4a2f;
}
.act-spacer {
	flex: 1;
}
.ghost-btn {
	height: 84rpx;
	line-height: 84rpx;
	padding: 0 36rpx;
	margin-right: 16rpx;
	border: 2rpx solid #d8ccc0;
	border-radius: 42rpx;
	font-size: 28rpx;
	color: #6f6258;
}

/* 评价弹层 */
.rate-mask {
	position: fixed;
	left: 0;
	right: 0;
	top: 0;
	bottom: 0;
	background: rgba(40, 32, 26, 0.45);
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 20;
}
.rate-card {
	width: 600rpx;
	background: #ffffff;
	border-radius: 40rpx;
	padding: 40rpx 36rpx 32rpx;
}
.rate-title {
	display: block;
	text-align: center;
	font-size: 32rpx;
	font-weight: bold;
	color: #3d3229;
}
.rate-stars {
	display: flex;
	justify-content: center;
	margin: 28rpx 0;
}
.rate-star {
	font-size: 56rpx;
	color: #e8ded3;
	margin: 0 10rpx;
}
.rate-star.on {
	color: #f2b233;
}
.rate-input {
	width: 100%;
	box-sizing: border-box;
	height: 160rpx;
	padding: 20rpx;
	background: #faf6f0;
	border-radius: 20rpx;
	font-size: 26rpx;
	color: #3d3229;
}
.rate-actions {
	display: flex;
	margin-top: 32rpx;
}
.rate-cancel,
.rate-submit {
	flex: 1;
	height: 80rpx;
	line-height: 80rpx;
	text-align: center;
	border-radius: 40rpx;
	font-size: 28rpx;
}
.rate-cancel {
	margin-right: 20rpx;
	background: #f3ece3;
	color: #6f6258;
}
.rate-submit {
	background: #8b5e3c;
	color: #ffffff;
}
</style>
