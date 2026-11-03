<template>
	<view class="page">
		<view class="panel">
			<text class="p-title">店员取餐核销</text>
			<text class="p-sub">扫描顾客的取餐二维码，或手动输入 5 位取餐码</text>

			<view class="pin-row">
				<input
					class="pin-input"
					v-model="pin"
					password
					maxlength="12"
					placeholder="店员口令（后端 STAFF_PIN）"
					@input="pinSaved = false"
				/>
				<view class="pin-save" hover-class="hv" @tap="savePin">{{ pinSaved ? '已保存' : '保存' }}</view>
			</view>
			<text class="pin-tip">口令只保存在本机，演示版权限校验</text>

			<view class="scan-btn" hover-class="go-hv" @tap="scanPickup">
				{{ loading && scanned ? '查询中…' : '扫描取餐码' }}
			</view>

			<view class="code-row">
				<input class="code-input" v-model="code" maxlength="64" placeholder="或输入 5 位取餐码" />
				<view class="code-btn" hover-class="hv" @tap="lookup()">{{ loading && !scanned ? '查询中…' : '查询' }}</view>
			</view>
		</view>

		<view class="panel" v-if="order">
			<view class="res-head">
				<text class="res-code">{{ order.pick_code }}</text>
				<text class="res-state" :class="{ done: order.state === 'completed' }">{{ order.stateText }}</text>
			</view>
			<view class="sum-line"><text>订单编号</text><text>{{ order.out_trade_no }}</text></view>
			<view class="sum-line"><text>取餐方式</text><text>{{ order.modeText }}</text></view>
			<view class="sum-line" v-if="order.table_no"><text>堂食桌号</text><text>{{ order.table_no }} 桌</text></view>
			<view class="res-items">
				<view class="res-item" v-for="(it, i) in order.items" :key="i">
					<text class="ri-name">{{ it.name }} ×{{ it.count }}</text>
					<text class="ri-spec">{{ formatItemSpec(it) }}</text>
				</view>
			</view>
			<view class="done-btn" v-if="order.state === 'making'" hover-class="go-hv" @tap="confirmPickup">
				{{ completing ? '核销中…' : '确认取餐' }}
			</view>
			<text class="done-tip" v-else-if="order.state === 'completed'">已核销，请把饮品交给顾客</text>
		</view>
	</view>
</template>

<script setup>
import { ref } from 'vue'
import { lookupPickup, completePickup } from '@/common/api/staff'
import { showError } from '@/common/api/request'
import { formatItemSpec } from '@/common/utils/order'
import { scanCode, isScanCancel } from '@/common/utils/scan'
import { readStorage, writeStorage } from '@/common/utils/storage'

const PIN_KEY = 'milk_staff_pin'

const pin = ref(readStorage(PIN_KEY, ''))
const pinSaved = ref(!!pin.value)
const code = ref('')
const query = ref('')
const order = ref(null)
const loading = ref(false)
const scanned = ref(false)
const completing = ref(false)

const savePin = () => {
	const value = pin.value.trim()
	if (!value) {
		uni.showToast({ title: '请输入店员口令', icon: 'none' })
		return
	}
	pin.value = value
	writeStorage(PIN_KEY, value)
	pinSaved.value = true
	uni.showToast({ title: '口令已保存', icon: 'none' })
}

const ensurePin = () => {
	if (!pin.value.trim()) {
		uni.showToast({ title: '请先填写店员口令', icon: 'none' })
		return false
	}
	return true
}

const lookup = async (raw) => {
	if (loading.value) return
	const target = (raw || code.value).trim()
	if (!ensurePin()) return
	if (!target) {
		uni.showToast({ title: '请输入取餐码', icon: 'none' })
		return
	}
	scanned.value = !!raw
	loading.value = true
	try {
		order.value = await lookupPickup(target, pin.value.trim())
		query.value = target
	} catch (error) {
		order.value = null
		showError(error)
	} finally {
		loading.value = false
	}
}

const scanPickup = async () => {
	if (loading.value || !ensurePin()) return
	let content = ''
	try {
		content = await scanCode()
	} catch (error) {
		if (!isScanCancel(error)) uni.showToast({ title: '扫码失败，请重试', icon: 'none' })
		return
	}
	code.value = content
	lookup(content)
}

const confirmPickup = async () => {
	if (completing.value || !order.value) return
	completing.value = true
	try {
		order.value = await completePickup(query.value || order.value.pick_code, pin.value.trim())
		code.value = ''
		uni.showToast({ title: '核销成功', icon: 'success' })
	} catch (error) {
		showError(error)
	} finally {
		completing.value = false
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
	font-size: 32rpx;
	font-weight: bold;
	color: #3d3229;
}
.p-sub {
	display: block;
	margin-top: 8rpx;
	font-size: 24rpx;
	color: #8c8177;
}
.pin-row {
	display: flex;
	align-items: center;
	margin-top: 28rpx;
}
.pin-input {
	flex: 1;
	height: 80rpx;
	padding: 0 24rpx;
	border-radius: 20rpx;
	background: #f7f2eb;
	font-size: 26rpx;
	color: #3d3229;
	box-sizing: border-box;
}
.pin-save {
	flex-shrink: 0;
	margin-left: 16rpx;
	height: 80rpx;
	line-height: 80rpx;
	padding: 0 30rpx;
	border-radius: 20rpx;
	background: #fdf1e4;
	font-size: 26rpx;
	color: #8b5e3c;
}
.pin-tip {
	display: block;
	margin-top: 10rpx;
	font-size: 20rpx;
	color: #b7ab9e;
}
.scan-btn {
	margin-top: 28rpx;
	height: 96rpx;
	line-height: 96rpx;
	text-align: center;
	border-radius: 48rpx;
	background: #8b5e3c;
	font-size: 32rpx;
	font-weight: bold;
	color: #ffffff;
}
.go-hv {
	background: #6f4a2f;
}
.code-row {
	display: flex;
	align-items: center;
	margin-top: 20rpx;
}
.code-input {
	flex: 1;
	height: 80rpx;
	padding: 0 24rpx;
	border-radius: 20rpx;
	background: #f7f2eb;
	font-size: 26rpx;
	color: #3d3229;
	box-sizing: border-box;
}
.code-btn {
	flex-shrink: 0;
	margin-left: 16rpx;
	height: 80rpx;
	line-height: 80rpx;
	padding: 0 36rpx;
	border-radius: 20rpx;
	background: #e8833a;
	font-size: 26rpx;
	color: #ffffff;
}
.res-head {
	display: flex;
	align-items: baseline;
	justify-content: space-between;
	padding-bottom: 20rpx;
	border-bottom: 2rpx solid #f0e9e1;
}
.res-code {
	font-size: 56rpx;
	font-weight: bold;
	color: #3d3229;
	letter-spacing: 6rpx;
}
.res-state {
	font-size: 22rpx;
	color: #e8833a;
}
.res-state.done {
	color: #5c9e6e;
}
.sum-line {
	display: flex;
	justify-content: space-between;
	margin-top: 16rpx;
	font-size: 24rpx;
	color: #8c8177;
}
.res-items {
	margin-top: 20rpx;
	padding-top: 20rpx;
	border-top: 2rpx solid #f0e9e1;
}
.res-item {
	display: flex;
	flex-direction: column;
	margin-bottom: 12rpx;
}
.ri-name {
	font-size: 26rpx;
	color: #3d3229;
}
.ri-spec {
	margin-top: 4rpx;
	font-size: 22rpx;
	color: #8c8177;
}
.done-btn {
	margin-top: 28rpx;
	height: 92rpx;
	line-height: 92rpx;
	text-align: center;
	border-radius: 46rpx;
	background: #5c9e6e;
	font-size: 30rpx;
	font-weight: bold;
	color: #ffffff;
}
.done-tip {
	display: block;
	margin-top: 24rpx;
	text-align: center;
	font-size: 24rpx;
	color: #5c9e6e;
}
</style>
