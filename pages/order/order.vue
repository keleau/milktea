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
			<!-- 待支付倒计时提示 -->
			<text class="bn-sub" v-if="order.state === '待支付'">请尽快完成支付，超时订单将自动取消</text>
		</view>

		<!-- 清单 -->
		<view class="panel">
			<text class="p-title">订单清单</text>
			<view class="od-item">
				<image class="od-img" :src="order.img" mode="aspectFill"></image>
				<view class="od-info">
					<text class="od-name">{{ order.name }}</text>
					<text class="od-spec">{{ order.spec }}</text>
					<text class="od-count">x{{ order.count }} · {{ order.mode }}</text>
				</view>
				<view class="od-price">¥{{ order.price }}</view>
			</view>
		</view>

		<!-- 订单信息 -->
		<view class="panel">
			<text class="p-title">订单信息</text>
			<view class="sum-line"><text>订单编号</text><text>{{ order.out_trade_no }}</text></view>
			<view class="sum-line"><text>取餐方式</text><text>{{ order.mode }}</text></view>
			<view class="sum-line"><text>下单时间</text><text>{{ createTime }}</text></view>
			<view class="sum-line"><text>应付金额</text><text class="strong">¥{{ order.price }}</text></view>
			<view class="sum-line" hover-class="hv" @tap="contact">
				<text>联系客服</text><text class="arrow">疑问或投诉 ›</text>
			</view>
		</view>

		<!-- 待支付操作栏 -->
		<view class="fix-space" v-if="order.state === '待支付'"></view>
		<view class="fix-bar" v-if="order.state === '待支付'">
			<view class="total">
				<text class="t-label">待支付</text>
				<text class="t-sym">¥</text>
				<text class="t-num">{{ order.price }}</text>
			</view>
			<view class="go-btn" hover-class="go-hv" @tap="payOrder">立即支付</view>
		</view>
	</view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { getOrder, updateOrderState } from '@/common/data'

const order = ref(null)
let orderNo = ''

onLoad((params) => {
	orderNo = params.oid
})
onShow(() => {
	order.value = getOrder(orderNo)
})

const stateClass = computed(() => ({
	待支付: 'warn',
	制作中: 'make',
	已完成: 'done',
	已取消: 'cancel'
}[order.value?.state] || 'cancel'))

const stateTitle = computed(() => ({
	待支付: '订单待支付',
	制作中: '猫咪制作中～',
	已完成: '已完成取餐',
	已取消: '订单已取消'
}[order.value?.state] || ''))

const stateSub = computed(() => ({
	待支付: '四只猫已在等待你的确认',
	制作中: '正在为你摇茶，请留意取餐码',
	已完成: '感谢惠顾，欢迎给猫评员打分',
	已取消: '期待下次为你服务'
}[order.value?.state] || ''))

const showPickCode = computed(() => order.value?.state === '制作中' || order.value?.state === '已完成')

// 模拟支付：更新为制作中
const payOrder = () => {
	updateOrderState(orderNo, '制作中')
	order.value = getOrder(orderNo)
	uni.showToast({ title: '支付成功', icon: 'success' })
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
</style>
