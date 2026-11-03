<template>
	<view class="page" v-if="draft">
		<!-- 取餐方式 -->
		<view class="panel">
			<view class="mode-seg" v-if="!tableNo">
				<view class="seg-item" :class="{ on: mode === 'pickup' }" @tap="switchMode('pickup')">
					<text class="seg-t">自取</text>
					<text class="seg-s">免排队</text>
				</view>
				<view class="seg-item" :class="{ on: mode === 'delivery' }" @tap="switchMode('delivery')">
					<text class="seg-t">外送</text>
					<text class="seg-s">送到家</text>
				</view>
			</view>
			<view class="mode-info table-info" v-if="tableNo">
				<view class="ti-row">
					<text class="ti-tag">堂食</text>
					<text class="ti-no">{{ tableNo }} 桌</text>
				</view>
				<text class="mi-sub">{{ store ? store.name : '门店加载中…' }} · 做好后请到吧台取餐</text>
			</view>
			<view class="mode-info" v-else-if="mode === 'pickup'">
				<text class="mi-main">{{ store ? store.name : '门店加载中…' }}</text>
				<text class="mi-sub">出杯约 {{ preview.estimated_ready_minutes || 10 }} 分钟，请留意取餐码</text>
			</view>
			<view class="mode-info addr-box" v-else @tap="toAddress">
				<text class="mi-main">{{ selectedAddress ? selectedAddress.detail : '请选择收货地址' }}</text>
				<text class="mi-sub">{{ selectedAddress ? selectedAddress.name + ' ' + selectedAddress.phone : '点击新增或选择地址' }}</text>
			</view>
		</view>

		<!-- 订单清单 -->
		<view class="panel">
			<text class="p-title">订单清单</text>
			<OrderItemCard
				v-for="(it, i) in draft.items"
				:key="i"
				:image="it.product.img"
				:name="it.product.name"
				:spec="formatItemSpec(it)"
				:count="it.count"
				:amount="lineAmount(it)"
			/>
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
			<view class="sum-line"><text>小计</text><text>¥{{ preview.subtotal }}</text></view>
			<view class="sum-line" v-if="preview.coupon_cut"><text>优惠券抵扣</text><text class="cut">-¥{{ preview.coupon_cut }}</text></view>
			<view class="sum-line"><text>{{ mode === 'pickup' ? '打包费' : '配送费' }}</text><text>¥{{ preview.pack_fee }}</text></view>
			<view class="sum-line sum-total"><text>合计</text><view class="t"><text class="t-sym">¥</text><text class="t-num">{{ preview.total }}</text></view></view>
		</view>

		<!-- 底部结算栏 -->
		<view class="fix-space"></view>
		<view class="fix-bar">
			<view class="total">
				<text class="t-label">合计</text>
				<text class="t-sym">¥</text>
				<text class="t-num">{{ preview.total }}</text>
			</view>
			<view class="go-btn" :class="{ dis: submitting || previewLoading }" hover-class="go-hv" @tap="submitOrder">
				{{ submitting ? '提交中…' : '提交订单' }}
			</view>
		</view>

		<WechatPaySheet
			:visible="paySheetOpen"
			:amount="pendingOrder ? pendingOrder.total : 0"
			:paying="payPaying"
			:paid="payPaid"
			@close="closePaySheet"
			@confirm="confirmPay"
		/>
	</view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import OrderItemCard from '@/components/order/order-item-card.vue'
import WechatPaySheet from '@/components/pay/wechat-pay-sheet.vue'
import { getStore } from '@/common/api/catalog'
import { getAddresses } from '@/common/api/addresses'
import { createOrder, payOrder, pricePreview } from '@/common/api/orders'
import { ensureLogin } from '@/common/api/auth'
import { showError } from '@/common/api/request'
import { toCoupon, toOrderItems } from '@/common/api/adapters'
import { formatItemSpec, lineAmount } from '@/common/utils/order'
import { clearCheckoutDraft, getCheckoutDraft, takeSelectedAddressId } from '@/common/store/session'

const draft = ref(null)
const store = ref(null)
const mode = ref('pickup')
const addresses = ref([])
const selectedAddressId = ref(0)
const couponId = ref(0)
const usableCoupons = ref([])
const submitting = ref(false)
const previewLoading = ref(false)
const initialized = ref(false)
const paySheetOpen = ref(false)
const payPaying = ref(false)
const payPaid = ref(false)
const pendingOrder = ref(null)
const preview = ref({
	subtotal: 0,
	pack_fee: 0,
	coupon_cut: 0,
	total: 0,
	estimated_ready_minutes: 0
})

const idempotencyKey = `CAT-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`

const tableNo = computed(() => (draft.value && draft.value.tableNo) || '')

const selectedAddress = computed(() => {
	if (!addresses.value.length) return null
	return addresses.value.find(a => a.id === selectedAddressId.value)
		|| addresses.value.find(a => a.is_default)
		|| addresses.value[0]
})

const pickDefaultAddress = () => {
	if (addresses.value.some(a => a.id === selectedAddressId.value)) return
	const target = addresses.value.find(a => a.is_default) || addresses.value[0]
	selectedAddressId.value = target ? target.id : 0
}

const loadAddresses = async () => {
	try {
		addresses.value = await getAddresses()
		pickDefaultAddress()
	} catch (error) {
		showError(error)
	}
}

onLoad(async () => {
	draft.value = getCheckoutDraft()
	if (!draft.value) return
	mode.value = draft.value.tableNo || draft.value.mode !== 'delivery' ? 'pickup' : 'delivery'
	selectedAddressId.value = draft.value.addressId || 0

	try {
		await ensureLogin()
	} catch (error) {
		showError(error)
		return
	}

	try {
		store.value = await getStore(draft.value.storeId)
	} catch (error) {
		showError(error)
	}

	await loadAddresses()
	initialized.value = true
	refreshPreview()
})

onShow(() => {
	if (!draft.value) {
		uni.showToast({ title: '请先选择饮品', icon: 'none' })
		setTimeout(() => uni.switchTab({ url: '/pages/menu/index' }), 600)
		return
	}
	if (!initialized.value) return

	const picked = takeSelectedAddressId()
	if (picked) selectedAddressId.value = picked
	loadAddresses()
})

const buildPayload = () => ({
	store_id: draft.value.storeId,
	mode: mode.value,
	coupon_id: couponId.value || null,
	items: toOrderItems(draft.value.items)
})

let previewSeq = 0
const refreshPreview = async () => {
	if (!draft.value) return
	const seq = ++previewSeq
	previewLoading.value = true
	try {
		const data = await pricePreview(buildPayload())
		if (seq !== previewSeq) return
		preview.value = data
		usableCoupons.value = (data.usable_coupons || []).map(toCoupon)
	} catch (error) {
		if (seq !== previewSeq) return
		// 券被占用/过期/门槛变化：清空重算，不让用户卡在错误态
		if (couponId.value && [3001, 3002, 3004].includes(error.code)) {
			couponId.value = 0
			uni.showToast({ title: error.message, icon: 'none' })
			refreshPreview()
			return
		}
		showError(error)
	} finally {
		if (seq === previewSeq) previewLoading.value = false
	}
}

const switchMode = (next) => {
	if (mode.value === next) return
	if (tableNo.value) {
		uni.showToast({ title: '堂食订单仅支持自取', icon: 'none' })
		return
	}
	mode.value = next
	refreshPreview()
}

const pickCoupon = (coupon) => {
	couponId.value = couponId.value === coupon.id ? 0 : coupon.id
	refreshPreview()
}

const toAddress = () => {
	uni.navigateTo({ url: '/pages/address/index?select=1' })
}

const submitOrder = async () => {
	if (submitting.value || previewLoading.value || !draft.value) return
	if (mode.value === 'delivery' && !selectedAddress.value) {
		uni.showToast({ title: '请先选择收货地址', icon: 'none' })
		toAddress()
		return
	}

	submitting.value = true
	try {
		await ensureLogin()
		const order = await createOrder({
			store_id: draft.value.storeId,
			mode: mode.value,
			address_id: mode.value === 'delivery' ? selectedAddress.value.id : null,
			coupon_id: couponId.value || null,
			table_no: tableNo.value || null,
			remark: '',
			items: toOrderItems(draft.value.items)
		}, idempotencyKey)
		clearCheckoutDraft()
		pendingOrder.value = order
		payPaying.value = false
		payPaid.value = false
		paySheetOpen.value = true
		submitting.value = false
	} catch (error) {
		showError(error)
		submitting.value = false
	}
}

const goOrderDetail = () => {
	if (!pendingOrder.value) return
	uni.redirectTo({ url: '/pages/order/order?oid=' + pendingOrder.value.out_trade_no })
}

const closePaySheet = () => {
	if (payPaying.value) return
	paySheetOpen.value = false
	goOrderDetail()
	setTimeout(() => uni.showToast({ title: '订单已创建，请在详情页支付', icon: 'none' }), 300)
}

const confirmPay = async () => {
	if (payPaying.value || !pendingOrder.value) return
	payPaying.value = true
	try {
		await payOrder(pendingOrder.value.out_trade_no)
		payPaying.value = false
		payPaid.value = true
		setTimeout(() => {
			paySheetOpen.value = false
			goOrderDetail()
		}, 600)
	} catch (error) {
		payPaying.value = false
		showError(error)
		// 订单已支付/已取消时不再让用户停在收银台，直接去详情页看最新状态
		if (error.code === 4002 || error.code === 4003) {
			paySheetOpen.value = false
			goOrderDetail()
		}
	}
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
.ti-row {
	display: flex;
	align-items: center;
}
.ti-tag {
	padding: 4rpx 14rpx;
	border-radius: 10rpx;
	background: #e8833a;
	font-size: 22rpx;
	color: #ffffff;
}
.ti-no {
	margin-left: 16rpx;
	font-size: 34rpx;
	font-weight: bold;
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
