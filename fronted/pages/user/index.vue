<template>
	<view class="page">
		<!-- 会员卡 -->
		<view class="member-card">
			<view class="mc-top">
				<view class="avatar-wrap" @tap="changeAvatar">
					<image class="avatar" :src="avatarSrc" mode="aspectFill" @error="onAvatarError" />
					<view class="avatar-cam">
						<view class="cam-body"></view>
						<view class="cam-dot"></view>
					</view>
					<view class="avatar-loading" v-if="uploading">上传中</view>
					<!-- #ifdef MP-WEIXIN -->
					<button
						class="avatar-hit"
						open-type="chooseAvatar"
						@chooseavatar="onChooseAvatar"
					></button>
					<!-- #endif -->
				</view>
				<view class="mc-user">
					<view class="mc-name-row">
						<text class="mc-name">{{ user.nickname || '猫友' }}</text>
						<text class="mc-edit" @tap="openName">编辑</text>
					</view>
					<view class="mc-level">
						<text class="mcl-badge">{{ level.levelCode }}</text>
						<text class="mcl-text">{{ level.levelName }}</text>
					</view>
				</view>
			</view>
			<view class="mc-stats">
				<view class="ms-item" hover-class="hv" @tap="comingSoon">
					<text class="ms-num">{{ user.points }}</text>
					<text class="ms-label">积分</text>
				</view>
				<view class="ms-item" hover-class="hv" @tap="toCoupons">
					<text class="ms-num">{{ user.coupon_count }}</text>
					<text class="ms-label">优惠券</text>
				</view>
				<view class="ms-item" hover-class="hv" @tap="comingSoon">
					<text class="ms-num">{{ user.balance }}</text>
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
				<view class="og-item" hover-class="hv" @tap="toOrders('pending_pay')">
					<view class="og-icon"><text>¥</text><text v-if="counts.pending_pay" class="og-badge">{{ counts.pending_pay }}</text></view>
					<text class="og-text">待支付</text>
				</view>
				<view class="og-item" hover-class="hv" @tap="toOrders('making')">
					<view class="og-icon"><text>制</text><text v-if="counts.making" class="og-badge">{{ counts.making }}</text></view>
					<text class="og-text">制作中</text>
				</view>
				<view class="og-item" hover-class="hv" @tap="toOrders('completed')">
					<view class="og-icon"><text>完</text><text v-if="counts.completed" class="og-badge">{{ counts.completed }}</text></view>
					<text class="og-text">已完成</text>
				</view>
				<view class="og-item" hover-class="hv" @tap="toOrders('cancelled')">
					<view class="og-icon"><text>消</text><text v-if="counts.cancelled" class="og-badge">{{ counts.cancelled }}</text></view>
					<text class="og-text">已取消</text>
				</view>
			</view>
		</view>

		<!-- 功能列表 -->
		<view class="panel">
			<view class="cell" hover-class="cell-hv" @tap="toCoupons">
				<text class="cell-name">优惠券</text>
				<text class="cell-extra">{{ user.coupon_count }} 张</text>
				<text class="cell-arrow">›</text>
			</view>
			<view class="cell" hover-class="cell-hv" @tap="toAddress">
				<text class="cell-name">收货地址</text>
				<text class="cell-arrow">›</text>
			</view>
			<view class="cell" hover-class="cell-hv" @tap="showShareModal">
				<text class="cell-name">分享转发</text>
				<text class="cell-arrow">›</text>
			</view>
			<view class="cell" hover-class="cell-hv" @tap="toStaff">
				<text class="cell-name">店员核销</text>
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
			<view class="cell" hover-class="cell-hv" @tap="logoutAccount">
				<text class="cell-name cell-danger">退出登录</text>
			</view>
		</view>

		<!-- 昵称弹层 -->
		<view class="name-mask" v-if="nameOpen" @tap="nameOpen = false">
			<view class="name-card" @tap.stop>
				<text class="name-title">修改昵称</text>
				<input
					class="name-input"
					v-model="nameInput"
					type="nickname"
					maxlength="20"
					placeholder="输入或选用微信昵称"
					focus
					@blur="syncName"
				/>
				<view class="name-actions">
					<view class="n-cancel" hover-class="hv" @tap="nameOpen = false">取消</view>
					<view class="n-submit" hover-class="hv" @tap="saveName">{{ nameSaving ? '保存中…' : '保存' }}</view>
				</view>
			</view>
		</view>

		<share :shareModal="shareModalOpen"></share>
	</view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { ensureLogin, fetchMe, logout, updateNickname, uploadAvatar } from '@/common/api/auth'
import { getOrderCounts } from '@/common/api/orders'
import { showError } from '@/common/api/request'
import { levelParts, resolveImage } from '@/common/api/adapters'
import { getCachedUser } from '@/common/api/token'
import { AVATAR_PREVIEW_KEY } from '@/common/config'
import { readStorage, removeStorage, writeStorage } from '@/common/utils/storage'
import { setOrdersFilter } from '@/common/store/session'

const user = ref(getCachedUser() || {
	nickname: '猫友',
	avatar: '',
	level: 'V1 新手猫友',
	points: 0,
	balance: 0,
	coupon_count: 0
})
const counts = ref({ pending_pay: 0, making: 0, completed: 0, cancelled: 0 })
const uploading = ref(false)

/** 登录页/本页选过头像时，用本地临时路径跨页预览（微信不接受 http 图片） */
const readAvatarPreview = () => {
	const preview = readStorage(AVATAR_PREVIEW_KEY, null)
	return preview && preview.userId === user.value.id ? preview.path : ''
}
const uploadedAvatar = ref(readAvatarPreview())

const level = computed(() => levelParts(user.value.level))
const avatarSrc = computed(
	() => uploadedAvatar.value || resolveImage(user.value.avatar) || '/static/resource/images/avatar.jpg'
)

const onAvatarError = () => {
	uploadedAvatar.value = ''
	removeStorage(AVATAR_PREVIEW_KEY)
}

onShow(() => {
	loadProfile()
})

const loadProfile = async () => {
	try {
		await ensureLogin()
		const [me, orderCounts] = await Promise.all([fetchMe(), getOrderCounts()])
		user.value = me
		counts.value = orderCounts
		const storedPreview = readAvatarPreview()
		if (storedPreview) uploadedAvatar.value = storedPreview
	} catch (error) {
		showError(error)
	}
}

const MAX_SIZE = 2 * 1024 * 1024

const uploadAvatarFile = async (filePath) => {
	uploading.value = true
	try {
		const avatar = await uploadAvatar(filePath)
		user.value = { ...user.value, avatar }
		// 微信小程序不能显示后端 HTTP 头像，先记住本地临时路径用于预览
		uploadedAvatar.value = filePath
		writeStorage(AVATAR_PREVIEW_KEY, { userId: user.value.id, path: filePath })
		uni.showToast({ title: '头像已更新', icon: 'success' })
	} catch (error) {
		showError(error)
	} finally {
		uploading.value = false
	}
}

/** 微信原生头像组件（open-type="chooseAvatar"）回调 */
const onChooseAvatar = (event) => {
	if (uploading.value) return
	const filePath = event && event.detail && event.detail.avatarUrl
	if (filePath) uploadAvatarFile(filePath)
}

/** 非微信端退回相册/相机选择 */
const changeAvatar = () => {
	if (uploading.value) return
	// #ifdef MP-WEIXIN
	return
	// #endif
	// #ifndef MP-WEIXIN
	uni.chooseMedia({
		count: 1,
		mediaType: ['image'],
		sourceType: ['album', 'camera'],
		sizeType: ['compressed'],
		success: (res) => {
			const file = res.tempFiles && res.tempFiles[0]
			if (!file) return
			if (file.size && file.size > MAX_SIZE) {
				uni.showToast({ title: '图片不能超过 2MB', icon: 'none' })
				return
			}
			uploadAvatarFile(file.tempFilePath)
		}
	})
	// #endif
}

const nameOpen = ref(false)
const nameInput = ref('')
const nameSaving = ref(false)
const openName = () => {
	nameInput.value = user.value.nickname || ''
	nameOpen.value = true
}
/** type="nickname" 选用微信昵称后，blur 的 value 兜底同步一次 */
const syncName = (event) => {
	const value = event && event.detail ? event.detail.value : ''
	if (typeof value === 'string') nameInput.value = value
}
const saveName = async () => {
	if (nameSaving.value) return
	const nickname = nameInput.value.trim()
	if (!nickname) {
		uni.showToast({ title: '昵称不能为空', icon: 'none' })
		return
	}
	nameSaving.value = true
	try {
		user.value = await updateNickname(nickname)
		nameOpen.value = false
		uni.showToast({ title: '昵称已更新', icon: 'none' })
	} catch (error) {
		showError(error)
	} finally {
		nameSaving.value = false
	}
}

const toOrders = (filt) => {
	setOrdersFilter(filt)
	uni.switchTab({ url: '/pages/order/index' })
}
const toCoupons = () => {
	uni.navigateTo({ url: '/pages/coupon/index' })
}
const toAddress = () => {
	uni.navigateTo({ url: '/pages/address/index' })
}
const toStaff = () => {
	uni.navigateTo({ url: '/pages/staff/verify' })
}
const comingSoon = () => {
	uni.showToast({ title: '敬请期待', icon: 'none' })
}
const contact = () => {
	uni.showToast({ title: '客服接入中…', icon: 'none' })
}
const logoutAccount = () => {
	uni.showModal({
		title: '退出登录',
		content: '退出后需要重新登录才能查看会员信息',
		confirmText: '退出',
		confirmColor: '#8B5E3C',
		success: (res) => {
			if (res.confirm) logout()
		}
	})
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
/* 透明按钮盖在头像上，专门接收微信 open-type="chooseAvatar" 的点击 */
.avatar-hit {
	position: absolute;
	left: 0;
	top: 0;
	z-index: 3;
	width: 120rpx;
	height: 120rpx;
	padding: 0;
	margin: 0;
	background: transparent;
	border: none;
	border-radius: 50%;
	line-height: 1;
	opacity: 0;
}
.avatar-hit::after {
	border: none;
}
.avatar {
	width: 120rpx;
	height: 120rpx;
	border-radius: 50%;
	border: 4rpx solid rgba(255, 255, 255, 0.4);
	box-sizing: border-box;
	background: #ffffff;
}
.avatar-loading {
	position: absolute;
	left: 0;
	top: 0;
	width: 120rpx;
	height: 120rpx;
	border-radius: 50%;
	background: rgba(40, 32, 26, 0.5);
	color: #ffffff;
	font-size: 20rpx;
	display: flex;
	align-items: center;
	justify-content: center;
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
.mc-name-row {
	display: flex;
	align-items: center;
}
.mc-edit {
	margin-left: 16rpx;
	padding: 2rpx 14rpx;
	border: 2rpx solid rgba(255, 255, 255, 0.45);
	border-radius: 999rpx;
	font-size: 20rpx;
	opacity: 0.85;
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
.cell-danger {
	color: #b4543f;
}
.cell-arrow {
	font-size: 36rpx;
	color: #c9c0b7;
}

/* 昵称弹层 */
.name-mask {
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
.name-card {
	width: 600rpx;
	background: #ffffff;
	border-radius: 36rpx;
	padding: 36rpx;
	box-sizing: border-box;
}
.name-title {
	display: block;
	text-align: center;
	font-size: 32rpx;
	font-weight: bold;
	color: #3d3229;
}
.name-input {
	width: 100%;
	height: 88rpx;
	margin-top: 28rpx;
	padding: 0 24rpx;
	box-sizing: border-box;
	background: #faf6f0;
	border-radius: 20rpx;
	font-size: 28rpx;
	color: #3d3229;
}
.name-actions {
	display: flex;
	margin-top: 28rpx;
}
.n-cancel,
.n-submit {
	flex: 1;
	height: 80rpx;
	line-height: 80rpx;
	text-align: center;
	border-radius: 40rpx;
	font-size: 28rpx;
}
.n-cancel {
	margin-right: 20rpx;
	background: #f3ece3;
	color: #6f6258;
}
.n-submit {
	background: #8b5e3c;
	color: #ffffff;
}
</style>
