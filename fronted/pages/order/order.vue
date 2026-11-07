<template>
	<view class="page" v-if="order">
		<!-- 状态横幅 -->
		<view class="banner" :class="'bn-' + stateClass">
			<text class="bn-title">{{ stateTitle }}</text>
			<text class="bn-sub">{{ stateSub }}</text>
			<!-- 取餐码 -->
			<view class="pick-ticket" v-if="showPickCode">
				<view class="pt-main">
					<text class="pt-kicker">PICK-UP NO.</text>
					<text class="pt-num">{{ order.pick_code }}</text>
					<text class="pt-label">取餐码</text>
				</view>
				<view class="pt-stub">
					<text class="pt-stub-title">{{ order.state === 'completed' ? '已取餐' : '到吧台' }}</text>
					<text class="pt-stub-title">{{ order.state === 'completed' ? '感谢惠顾' : '出示此码' }}</text>
					<text class="pt-stub-en">{{ order.state === 'completed' ? 'THANK YOU' : 'SHOW TICKET' }}</text>
				</view>
			</view>
			<!-- 待支付提示 -->
			<text class="bn-sub" v-if="order.state === 'pending_pay'">请尽快完成支付，超时订单将自动取消</text>
		</view>

		<!-- 取餐二维码：制作中才需要到吧台出示 -->
		<view class="panel qr-panel" v-if="order.mode === 'pickup' && order.state === 'making' && pickupQr">
			<text class="p-title">取餐二维码</text>
			<image class="qr-img" :src="pickupQr" mode="aspectFit"></image>
			<text class="qr-tip">到吧台出示，店员扫码核销</text>
		</view>

		<!-- 清单 -->
		<view class="panel">
			<text class="p-title">订单清单</text>
			<OrderItemCard
				v-for="(item, i) in order.items"
				:key="i"
				:image="item.image"
				:name="item.name"
				:spec="formatItemSpec(item)"
				:count="item.count"
				:amount="item.amount"
				bordered
				accent
			/>
		</view>

		<!-- 订单信息 -->
		<view class="panel">
			<text class="p-title">订单信息</text>
			<view class="sum-line"><text>订单编号</text><text>{{ order.out_trade_no }}</text></view>
			<view class="sum-line"><text>取餐方式</text><text>{{ order.modeText }}</text></view>
			<view class="sum-line" v-if="order.table_no"><text>堂食桌号</text><text class="strong">{{ order.table_no }} 桌</text></view>
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
			<view class="go-btn" v-if="order.state === 'pending_pay'" hover-class="go-hv" @tap="openPaySheet">
				立即支付
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

		<WechatPaySheet
			:visible="paySheetOpen"
			:amount="order.total"
			:paying="payPaying"
			:paid="payPaid"
			@close="closePaySheet"
			@confirm="confirmPay"
		/>
	</view>
	<view class="loading" v-else>
		<BrandLoading v-if="loadingText === '加载中…'" :size="280" />
		<text v-else>{{ loadingText }}</text>
	</view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import OrderItemCard from '@/components/order/order-item-card.vue'
import WechatPaySheet from '@/components/pay/wechat-pay-sheet.vue'
import BrandLoading from '@/components/loading/brand-loading.vue'
import { getOptions, getProduct } from '@/common/api/catalog'
import {
	cancelOrder as cancelOrderApi,
	completeOrder as completeOrderApi,
	getOrder,
	getPickupQr,
	payOrder,
	repeatOrder as repeatOrderApi,
	reviewOrder
} from '@/common/api/orders'
import { ensureLogin } from '@/common/api/auth'
import { showError } from '@/common/api/request'
import { toDrink } from '@/common/api/adapters'
import { formatItemSpec } from '@/common/utils/order'
import { setCheckoutDraft } from '@/common/store/session'

const order = ref(null)
const pickupQr = ref('')
const loadingText = ref('加载中…')
const paySheetOpen = ref(false)
const payPaying = ref(false)
const payPaid = ref(false)
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

const loadPickupQr = async () => {
	if (pickupQr.value) return
	try {
		const data = await getPickupQr(orderNo)
		pickupQr.value = data.image
	} catch (error) {
		console.warn('[order] 取餐二维码加载失败', error)
	}
}

const loadOrder = async () => {
	try {
		await ensureLogin()
		order.value = await getOrder(orderNo)
		if (order.value.mode === 'pickup' && order.value.state === 'making') {
			loadPickupQr()
		}
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

const openPaySheet = () => {
	if (payPaying.value) return
	payPaying.value = false
	payPaid.value = false
	paySheetOpen.value = true
}

const closePaySheet = () => {
	if (payPaying.value) return
	paySheetOpen.value = false
}

const confirmPay = async () => {
	if (payPaying.value) return
	payPaying.value = true
	try {
		await payOrder(orderNo)
		payPaying.value = false
		payPaid.value = true
		setTimeout(async () => {
			paySheetOpen.value = false
			await loadOrder()
			uni.showToast({ title: '支付成功', icon: 'success' })
		}, 600)
	} catch (error) {
		payPaying.value = false
		showError(error)
		// 已在其他端支付 / 已取消时，当前页状态是旧的，重新拉一次订单
		if (error.code === 4002 || error.code === 4003) {
			paySheetOpen.value = false
			await loadOrder()
		}
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
.pick-ticket {
	margin-top: 28rpx;
	display: flex;
	align-items: stretch;
	width: 100%;
	box-sizing: border-box;
	background: #fffcf7;
	border-radius: 22rpx;
	box-shadow: 0 14rpx 30rpx rgba(45, 27, 16, 0.18);
	overflow: hidden;
}
.pt-main {
	flex: 1;
	min-width: 0;
	padding: 22rpx 28rpx 20rpx;
	display: flex;
	flex-direction: column;
}
.pt-kicker {
	font-size: 18rpx;
	font-weight: 600;
	letter-spacing: 3rpx;
	color: #a17f62;
}
.pt-num {
	margin-top: 4rpx;
	font-family: var(--serif);
	font-size: 76rpx;
	font-weight: 700;
	line-height: 1.05;
	font-variant-numeric: tabular-nums;
	letter-spacing: 6rpx;
	color: #3b2417;
}
.pt-label {
	margin-top: 2rpx;
	font-size: 20rpx;
	color: #8e7661;
}
.pt-stub {
	flex-shrink: 0;
	width: 176rpx;
	padding: 22rpx 16rpx;
	box-sizing: border-box;
	border-left: 2rpx dashed #d8c4ae;
	background: #fbf4ea;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
}
.pt-stub-title {
	font-size: 22rpx;
	line-height: 1.5;
	color: #6f4b2e;
}
.pt-stub-en {
	margin-top: 8rpx;
	font-size: 13rpx;
	letter-spacing: 1rpx;
	color: #b7a08a;
	white-space: nowrap;
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
.qr-panel {
	display: flex;
	flex-direction: column;
	align-items: center;
}
.qr-img {
	width: 300rpx;
	height: 300rpx;
	margin-top: 20rpx;
}
.qr-tip {
	margin-top: 8rpx;
	font-size: 22rpx;
	color: #8c8177;
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
