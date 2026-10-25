<template>
	<view class="page">
		<!-- 会员卡 -->
		<view class="member-card">
			<view class="mc-top">
				<view class="avatar-wrap" @tap="changeAvatar">
					<image class="avatar" :src="localAvatar || '/static/resource/images/avatar.jpg'" mode="aspectFill" />
					<view class="avatar-cam">
						<view class="cam-body"></view>
						<view class="cam-dot"></view>
					</view>
				</view>
				<view class="mc-user">
					<text class="mc-name">{{ nickname }}</text>
					<view class="mc-level">
						<text class="mcl-badge">V2</text>
						<text class="mcl-text">银牌猫评员</text>
					</view>
				</view>
			</view>
			<view class="mc-stats">
				<view class="ms-item" hover-class="hv" @tap="comingSoon">
					<text class="ms-num">{{ store.user.points }}</text>
					<text class="ms-label">积分</text>
				</view>
				<view class="ms-item" hover-class="hv" @tap="comingSoon">
					<text class="ms-num">{{ store.user.coupons }}</text>
					<text class="ms-label">优惠券</text>
				</view>
				<view class="ms-item" hover-class="hv" @tap="comingSoon">
					<text class="ms-num">{{ store.user.balance }}</text>
					<text class="ms-label">余额（元）</text>
				</view>
			</view>
		</view>

		<!-- 我的订单 -->
		<view class="panel">
			<view class="panel-head">
				<text class="p-title">我的订单</text>
				<text class="p-more" hover-class="hv" @tap="toOrders('')">全部 ›</text>
			</view>
			<view class="order-grid">
				<view class="og-item" hover-class="hv" @tap="toOrders('待支付')">
					<view class="og-icon"><text>¥</text><text v-if="counts['待支付']" class="og-badge">{{ counts['待支付'] }}</text></view>
					<text class="og-text">待支付</text>
				</view>
				<view class="og-item" hover-class="hv" @tap="toOrders('制作中')">
					<view class="og-icon"><text>制</text><text v-if="counts['制作中']" class="og-badge">{{ counts['制作中'] }}</text></view>
					<text class="og-text">制作中</text>
				</view>
				<view class="og-item" hover-class="hv" @tap="toOrders('已完成')">
					<view class="og-icon"><text>完</text><text v-if="counts['已完成']" class="og-badge">{{ counts['已完成'] }}</text></view>
					<text class="og-text">已完成</text>
				</view>
				<view class="og-item" hover-class="hv" @tap="toOrders('已取消')">
					<view class="og-icon"><text>消</text><text v-if="counts['已取消']" class="og-badge">{{ counts['已取消'] }}</text></view>
					<text class="og-text">已取消</text>
				</view>
			</view>
		</view>

		<!-- 功能列表 -->
		<view class="panel">
			<view class="cell" hover-class="cell-hv" @tap="comingSoon">
				<text class="cell-name">优惠券</text>
				<text class="cell-extra">{{ store.user.coupons }} 张</text>
				<text class="cell-arrow">›</text>
			</view>
			<view class="cell" hover-class="cell-hv" @tap="comingSoon">
				<text class="cell-name">收货地址</text>
				<text class="cell-arrow">›</text>
			</view>
			<view class="cell" hover-class="cell-hv" @tap="showShareModal">
				<text class="cell-name">分享转发</text>
				<text class="cell-arrow">›</text>
			</view>
			<view class="cell" hover-class="cell-hv" @tap="contact">
				<text class="cell-name">联系客服</text>
				<text class="cell-arrow">›</text>
			</view>
			<view class="cell" hover-class="cell-hv" @tap="comingSoon">
				<text class="cell-name">设置</text>
				<text class="cell-arrow">›</text>
			</view>
		</view>

		<share :shareModal="shareModalOpen"></share>
	</view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { STORE, countByState } from '@/common/data'
import { setOrdersFilter } from '@/common/store/session'

const store = STORE

// 昵称：首次生成本地昵称并持久化
const nickname = ref(uni.getStorageSync('cat_nickname') || '')
onShow(() => {
	if (!nickname.value) {
		nickname.value = '猫友' + Math.floor(Math.random() * 9000 + 1000)
		uni.setStorageSync('cat_nickname', nickname.value)
	}
	counts.value = countByState()
})

const counts = ref({ 待支付: 0, 制作中: 0, 已完成: 0, 已取消: 0 })

// 本地头像（base64 存 storage，不依赖后端）
const localAvatar = ref(uni.getStorageSync('local_avatar') || '')
const MAX_SIZE = 2 * 1024 * 1024
const changeAvatar = () => {
	uni.chooseMedia({
		count: 1,
		mediaType: ['image'],
		sourceType: ['album', 'camera'],
		sizeType: ['compressed'],
		success: (res) => {
			const file = res.tempFiles[0]
			if (file.size && file.size > MAX_SIZE) {
				uni.showToast({ title: '图片不能超过 2MB', icon: 'none' })
				return
			}
			uni.getFileSystemManager().readFile({
				filePath: file.tempFilePath,
				encoding: 'base64',
				success: (readRes) => {
					localAvatar.value = 'data:image/jpeg;base64,' + readRes.data
					uni.setStorageSync('local_avatar', localAvatar.value)
					uni.showToast({ title: '头像已更新', icon: 'success' })
				},
				fail: () => {
					uni.showToast({ title: '图片读取失败', icon: 'none' })
				}
			})
		}
	})
}

const toOrders = (filt) => {
	setOrdersFilter(filt)
	uni.switchTab({ url: '/pages/order/index' })
}
const comingSoon = () => {
	uni.showToast({ title: '敬请期待', icon: 'none' })
}
const contact = () => {
	uni.showToast({ title: '客服接入中…', icon: 'none' })
}
const shareModalOpen = ref(false)
const showShareModal = () => {
	shareModalOpen.value = true
}
</script>

<style>
page {
	background: #faf6f0;
}
.page {
	min-height: 100vh;
	padding: 32rpx 32rpx 48rpx;
	box-sizing: border-box;
}
.hv {
	opacity: 0.85;
}

/* 会员卡 */
.member-card {
	background: linear-gradient(150deg, #9a6b46 0%, #8b5e3c 60%, #7a5133 100%);
	border-radius: 40rpx;
	padding: 40rpx 32rpx 32rpx;
	box-shadow: 0 12rpx 32rpx rgba(139, 94, 60, 0.25);
	color: #ffffff;
}
.mc-top {
	display: flex;
	align-items: center;
}
.avatar-wrap {
	position: relative;
	flex-shrink: 0;
	width: 120rpx;
	height: 120rpx;
	margin-right: 24rpx;
}
.avatar {
	width: 120rpx;
	height: 120rpx;
	border-radius: 50%;
	border: 4rpx solid rgba(255, 255, 255, 0.4);
	box-sizing: border-box;
	background: #ffffff;
}
.avatar-cam {
	position: absolute;
	right: 0;
	bottom: 0;
	width: 40rpx;
	height: 40rpx;
	background: #e8833a;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	border: 3rpx solid #ffffff;
	box-sizing: border-box;
}
.cam-body {
	width: 16rpx;
	height: 12rpx;
	background: #ffffff;
	border-radius: 3rpx;
}
.cam-dot {
	position: absolute;
	top: 11rpx;
	left: 50%;
	transform: translateX(-50%);
	width: 6rpx;
	height: 6rpx;
	background: #ffffff;
	border-radius: 50%;
}
.mc-user {
	flex: 1;
}
.mc-name {
	font-size: 36rpx;
	font-weight: bold;
}
.mc-level {
	display: inline-flex;
	align-items: center;
	margin-top: 12rpx;
	background: rgba(255, 255, 255, 0.18);
	border-radius: 20rpx;
	padding: 6rpx 20rpx;
}
.mcl-badge {
	font-size: 22rpx;
	font-weight: bold;
	margin-right: 8rpx;
}
.mcl-text {
	font-size: 22rpx;
	opacity: 0.9;
}
.mc-stats {
	display: flex;
	margin-top: 36rpx;
	background: rgba(255, 255, 255, 0.1);
	border-radius: 24rpx;
	padding: 24rpx 0;
}
.ms-item {
	flex: 1;
	display: flex;
	flex-direction: column;
	align-items: center;
}
.ms-num {
	font-size: 36rpx;
	font-weight: bold;
}
.ms-label {
	margin-top: 6rpx;
	font-size: 22rpx;
	opacity: 0.75;
}

/* 面板 */
.panel {
	margin-top: 24rpx;
	background: #ffffff;
	border-radius: 40rpx;
	padding: 32rpx;
	box-shadow: 0 8rpx 24rpx rgba(61, 50, 41, 0.06);
}
.panel-head {
	display: flex;
	justify-content: space-between;
	align-items: baseline;
}
.p-title {
	font-size: 30rpx;
	font-weight: bold;
	color: #3d3229;
}
.p-more {
	font-size: 24rpx;
	color: #8c8177;
}

/* 订单四宫格 */
.order-grid {
	display: flex;
	margin-top: 32rpx;
}
.og-item {
	flex: 1;
	display: flex;
	flex-direction: column;
	align-items: center;
}
.og-icon {
	position: relative;
	width: 80rpx;
	height: 80rpx;
	line-height: 80rpx;
	text-align: center;
	background: #f3eae0;
	border-radius: 50%;
	font-size: 30rpx;
	font-weight: bold;
	color: #8b5e3c;
}
.og-badge {
	position: absolute;
	top: -6rpx;
	right: -6rpx;
	min-width: 32rpx;
	height: 32rpx;
	line-height: 32rpx;
	padding: 0 6rpx;
	background: #e8833a;
	color: #ffffff;
	font-size: 20rpx;
	font-weight: normal;
	border-radius: 16rpx;
	box-sizing: border-box;
	text-align: center;
}
.og-text {
	margin-top: 12rpx;
	font-size: 24rpx;
	color: #3d3229;
}

/* 功能列表 */
.cell {
	display: flex;
	align-items: center;
	padding: 28rpx 0;
	border-bottom: 2rpx solid #f0e9e1;
}
.cell:last-child {
	border-bottom: none;
	padding-bottom: 8rpx;
}
.cell:first-child {
	padding-top: 8rpx;
}
.cell-hv {
	background: #faf6f0;
}
.cell-name {
	flex: 1;
	font-size: 28rpx;
	color: #3d3229;
}
.cell-extra {
	font-size: 24rpx;
	color: #8c8177;
	margin-right: 12rpx;
}
.cell-arrow {
	font-size: 36rpx;
	color: #c9c0b7;
}
</style>
