<template>
	<view class="page">
		<!-- 状态 Tab -->
		<view class="tabs">
			<view class="tab-inner">
				<view
					v-for="t in tabs"
					:key="t.id"
					class="tab-item"
					:class="{ on: filt === t.id }"
					@tap="onFilterChange(t.id)"
				>
					{{ t.name }}
				</view>
			</view>
		</view>

		<BrandLoading v-if="loading" :size="240" />

		<!-- 订单列表 -->
		<view class="list" v-else-if="list.length">
			<view class="od-card" v-for="o in list" :key="o.out_trade_no" hover-class="hv" @tap="toOrder(o.out_trade_no)">
				<view class="od-head">
					<text class="od-no">单号 {{ o.shortNo }}</text>
					<text class="od-state" :class="'st-' + stateClass(o.state)">{{ o.stateText }}</text>
				</view>
				<view class="od-body">
					<image class="od-img" :src="o.img" mode="aspectFill"></image>
					<view class="od-info">
						<text class="od-name">{{ o.name }}</text>
						<text class="od-spec">{{ o.spec }}</text>
						<text class="od-count">x{{ o.count }} · {{ o.modeText }}</text>
					</view>
					<view class="od-right">
						<view class="od-price">¥{{ o.price }}</view>
						<view class="od-pay" v-if="o.state === 'pending_pay'" hover-class="hv" @tap.stop="toOrder(o.out_trade_no)">去支付</view>
					</view>
				</view>
			</view>
		</view>

		<!-- 空态 -->
		<view class="empty" v-else>
			<view class="empty-paw">
				<view class="ep-pad"></view>
				<view class="ep-toe ep-t1"></view>
				<view class="ep-toe ep-t2"></view>
				<view class="ep-toe ep-t3"></view>
				<view class="ep-toe ep-t4"></view>
			</view>
			<text class="empty-text">{{ filt ? '暂无「' + filtName + '」订单' : '还没有订单，去点一杯吧' }}</text>
			<view class="empty-btn" hover-class="hv" @tap="toMenu">去点单</view>
		</view>
	</view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getOrders as fetchOrders } from '@/common/api/orders'
import { ensureLogin } from '@/common/api/auth'
import { showError } from '@/common/api/request'
import BrandLoading from '@/components/loading/brand-loading.vue'
import { takeOrdersFilter } from '@/common/store/session'

const tabs = [
	{ id: '', name: '全部' },
	{ id: 'pending_pay', name: '待支付' },
	{ id: 'making', name: '制作中' },
	{ id: 'completed', name: '已完成' },
	{ id: 'cancelled', name: '已取消' }
]

const filt = ref('')
const list = ref([])
const loading = ref(false)
const filtName = computed(() => (tabs.find(t => t.id === filt.value) || tabs[0]).name)

let loadSeq = 0
const loadList = async () => {
	const seq = ++loadSeq
	loading.value = true
	try {
		await ensureLogin()
		const data = await fetchOrders({ state: filt.value || undefined, pageSize: 50 })
		if (seq !== loadSeq) return
		list.value = data.items || []
	} catch (error) {
		if (seq !== loadSeq) return
		list.value = []
		showError(error)
	} finally {
		if (seq === loadSeq) loading.value = false
	}
}

onShow(() => {
	// 与“我的”页订单入口联动；从详情页返回时保留当前筛选
	const nextFilter = takeOrdersFilter()
	if (nextFilter !== null) filt.value = nextFilter
	loadList()
})

const onFilterChange = (id) => {
	if (filt.value === id) return
	filt.value = id
	loadList()
}

const stateClass = (state) => ({
	pending_pay: 'warn',
	making: 'make',
	completed: 'done',
	cancelled: 'cancel'
}[state] || 'cancel')

const toOrder = (no) => {
	uni.navigateTo({ url: '/pages/order/order?oid=' + no })
}
const toMenu = () => {
	uni.switchTab({ url: '/pages/menu/index' })
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

.tabs {
	background: #faf6f0;
	padding: 24rpx 32rpx 8rpx;
}
.tab-inner {
	display: flex;
	gap: 32rpx;
}
.tab-item {
	font-size: 28rpx;
	color: #8c8177;
	position: relative;
	padding-bottom: 12rpx;
}
.tab-item.on {
	color: #3d3229;
	font-weight: bold;
}
.tab-item.on::after {
	content: '';
	position: absolute;
	left: 50%;
	transform: translateX(-50%);
	bottom: 0;
	width: 32rpx;
	height: 6rpx;
	border-radius: 3rpx;
	background: #8b5e3c;
}

.list {
	padding: 24rpx 32rpx 0;
}
.od-card {
	background: #ffffff;
	border-radius: 40rpx;
	padding: 24rpx 32rpx;
	margin-bottom: 24rpx;
	box-shadow: 0 8rpx 24rpx rgba(61, 50, 41, 0.06);
}
.od-head {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding-bottom: 16rpx;
	border-bottom: 2rpx solid #f0e9e1;
}
.od-no {
	font-size: 22rpx;
	color: #c9c0b7;
}
.od-state {
	font-size: 24rpx;
	font-weight: medium;
}
.st-warn { color: #e8973a; }
.st-make { color: #8b5e3c; }
.st-done { color: #5c9e6e; }
.st-cancel { color: #c9c0b7; }

.od-body {
	display: flex;
	align-items: center;
	padding-top: 20rpx;
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
.od-right {
	display: flex;
	flex-direction: column;
	align-items: flex-end;
}
.od-price {
	font-size: 30rpx;
	font-weight: medium;
	color: #e8833a;
}
.od-pay {
	margin-top: 12rpx;
	height: 56rpx;
	line-height: 56rpx;
	padding: 0 28rpx;
	background: #e8833a;
	color: #ffffff;
	font-size: 24rpx;
	border-radius: 28rpx;
}

/* 空态 */
.empty {
	display: flex;
	flex-direction: column;
	align-items: center;
	padding: 128rpx 0;
}
.empty-paw {
	position: relative;
	width: 140rpx;
	height: 140rpx;
	opacity: 0.4;
}
.ep-pad {
	position: absolute;
	left: 34rpx;
	bottom: 0;
	width: 72rpx;
	height: 58rpx;
	background: #c9c0b7;
	border-radius: 50% 50% 45% 45%;
}
.ep-toe {
	position: absolute;
	width: 30rpx;
	height: 38rpx;
	background: #c9c0b7;
	border-radius: 50%;
}
.ep-t1 { left: 0; top: 34rpx; transform: rotate(-24deg); }
.ep-t2 { left: 38rpx; top: 18rpx; }
.ep-t3 { right: 38rpx; top: 18rpx; }
.ep-t4 { right: 0; top: 34rpx; transform: rotate(24deg); }
.empty-text {
	margin-top: 24rpx;
	font-size: 28rpx;
	color: #8c8177;
}
.empty-btn {
	margin-top: 32rpx;
	height: 72rpx;
	line-height: 72rpx;
	padding: 0 48rpx;
	background: #8b5e3c;
	color: #ffffff;
	font-size: 28rpx;
	border-radius: 36rpx;
}
</style>
