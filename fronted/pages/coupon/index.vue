<template>
	<view class="page">
		<!-- 我的券 -->
		<view class="tabs">
			<view
				v-for="tab in tabs"
				:key="tab.key"
				class="tab"
				:class="{ on: status === tab.key }"
				@tap="switchTab(tab.key)"
			>
				<text>{{ tab.name }}</text>
			</view>
		</view>

		<BrandLoading v-if="loading" :size="240" />

		<view class="coupon-list" v-if="myCoupons.length">
			<view class="my-card" v-for="cp in myCoupons" :key="cp.id" :class="{ dim: cp.status !== 'unused' }">
				<view class="mc-cut">
					<view class="mc-amt"><text class="mc-sym">¥</text><text class="mc-num">{{ cp.cut }}</text></view>
					<text class="mc-min">满{{ cp.min }}可用</text>
				</view>
				<view class="mc-mid">
					<text class="mc-title">{{ cp.title }}</text>
					<text class="mc-desc">{{ cp.desc }}</text>
					<text class="mc-expire">有效期至 {{ cp.expireText }}</text>
				</view>
				<text class="mc-status">{{ statusText(cp.status) }}</text>
			</view>
		</view>
		<view class="empty" v-else-if="!loading">暂无{{ tabName }}优惠券</view>

		<!-- 可领券包 -->
		<view class="cp-head">
			<text class="cp-h-t">可领券包</text>
			<text class="cp-h-s">{{ unclaimedCount }} 张待领取</text>
		</view>
		<coupon-ticket
			v-for="cp in templates"
			:key="cp.id"
			:coupon="cp"
			@claim="claim"
		/>
		<view class="empty small" v-if="!templates.length && !loading">暂无可领取的券</view>
	</view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import CouponTicket from '@/components/menu/coupon-ticket.vue'
import BrandLoading from '@/components/loading/brand-loading.vue'
import { claimCoupon, getMyCoupons, getTemplates } from '@/common/api/coupons'
import { ensureLogin } from '@/common/api/auth'
import { showError } from '@/common/api/request'

const tabs = [
	{ key: 'unused', name: '未使用' },
	{ key: 'used', name: '已使用' },
	{ key: 'expired', name: '已过期' }
]
const status = ref('unused')
const myCoupons = ref([])
const templates = ref([])
const loading = ref(true)
const claiming = ref(false)

const tabName = computed(() => (tabs.find(t => t.key === status.value) || tabs[0]).name)
const unclaimedCount = computed(() => templates.value.filter(t => !t.claimed).length)

const statusText = (value) => ({
	unused: '未使用',
	used: '已使用',
	expired: '已过期'
}[value] || value)

onShow(() => {
	loadAll()
})

const loadAll = async () => {
	loading.value = true
	try {
		await ensureLogin()
		const [mine, list] = await Promise.all([
			getMyCoupons(status.value),
			getTemplates()
		])
		myCoupons.value = mine
		templates.value = list
	} catch (error) {
		showError(error)
	} finally {
		loading.value = false
	}
}

const switchTab = (key) => {
	if (status.value === key) return
	status.value = key
	loadMine()
}

const loadMine = async () => {
	try {
		myCoupons.value = await getMyCoupons(status.value)
	} catch (error) {
		showError(error)
	}
}

const claim = async (coupon) => {
	if (claiming.value || coupon.claimed) return
	claiming.value = true
	try {
		await claimCoupon(coupon.id)
		coupon.claimed = true
		uni.showToast({ title: '领取成功', icon: 'success' })
		await loadAll()
	} catch (error) {
		if (error.code === 3003) {
			coupon.claimed = true
			uni.showToast({ title: '该券已领取', icon: 'none' })
			return
		}
		showError(error)
	} finally {
		claiming.value = false
	}
}
</script>

<style>
page {
	background: #faf6f0;
}
.page {
	min-height: 100vh;
	padding: 24rpx 0 48rpx;
	box-sizing: border-box;
}
.tabs {
	display: flex;
	margin: 0 32rpx 24rpx;
	background: #ffffff;
	border-radius: 999rpx;
	padding: 8rpx;
	box-shadow: 0 8rpx 24rpx rgba(61, 50, 41, 0.06);
}
.tab {
	flex: 1;
	height: 68rpx;
	line-height: 68rpx;
	text-align: center;
	font-size: 26rpx;
	color: #8c8177;
	border-radius: 999rpx;
}
.tab.on {
	background: #8b5e3c;
	color: #ffffff;
	font-weight: 500;
}
.coupon-list {
	padding: 0 32rpx;
}
.my-card {
	display: flex;
	align-items: center;
	background: #ffffff;
	border-radius: 28rpx;
	padding: 24rpx;
	margin-bottom: 20rpx;
	box-shadow: 0 8rpx 24rpx rgba(61, 50, 41, 0.06);
}
.my-card.dim {
	opacity: 0.55;
}
.mc-cut {
	flex-shrink: 0;
	width: 140rpx;
	display: flex;
	flex-direction: column;
	align-items: center;
	border-right: 2rpx dashed #eadfcd;
}
.mc-amt {
	display: flex;
	align-items: baseline;
	color: #e8833a;
}
.mc-sym {
	font-size: 22rpx;
	font-weight: bold;
}
.mc-num {
	font-size: 52rpx;
	font-weight: 900;
	line-height: 1;
}
.mc-min {
	margin-top: 6rpx;
	font-size: 18rpx;
	color: #b7ab9e;
}
.mc-mid {
	flex: 1;
	min-width: 0;
	padding: 0 20rpx;
	display: flex;
	flex-direction: column;
}
.mc-title {
	font-size: 28rpx;
	font-weight: bold;
	color: #3d3229;
}
.mc-desc {
	margin-top: 6rpx;
	font-size: 22rpx;
	color: #8c8177;
}
.mc-expire {
	margin-top: 10rpx;
	font-size: 20rpx;
	color: #b7ab9e;
}
.mc-status {
	flex-shrink: 0;
	font-size: 22rpx;
	color: #a79b8e;
}
.empty {
	padding: 120rpx 0;
	text-align: center;
	font-size: 26rpx;
	color: #a79b8e;
}
.empty.small {
	padding: 40rpx 0;
}
.cp-head {
	display: flex;
	align-items: baseline;
	justify-content: space-between;
	padding: 32rpx 48rpx 16rpx;
}
.cp-h-t {
	font-size: 30rpx;
	font-weight: bold;
	color: #3d3229;
}
.cp-h-s {
	font-size: 22rpx;
	color: #a79b8e;
}
</style>
