<template>
	<view class="ps-mask" v-if="visible">
		<view class="ps-card">
			<text class="ps-title">完善个人资料</text>
			<text class="ps-desc">使用微信头像和昵称，点单时更方便</text>

			<view class="ps-avatar-row">
				<button
					class="ps-avatar-btn"
					open-type="chooseAvatar"
					@chooseavatar="onChooseAvatar"
					@tap="onAvatarTap"
				>
					<image class="ps-avatar" :src="avatarSrc" mode="aspectFill" />
					<view class="ps-cam">
						<view class="ps-cam-body"></view>
						<view class="ps-cam-dot"></view>
					</view>
				</button>
				<view class="ps-avatar-copy">
					<text class="ps-avatar-main">点击头像，使用微信头像</text>
					<text class="ps-avatar-sub">仅用于点单展示，可随时修改</text>
				</view>
			</view>

			<view class="ps-field">
				<text class="ps-label">昵称</text>
				<input
					class="ps-input"
					type="nickname"
					:value="nickname"
					maxlength="20"
					placeholder="点击输入，或使用微信昵称"
					placeholder-class="ps-ph"
					@input="onNicknameInput"
					@blur="onNicknameInput"
				/>
			</view>

			<view class="ps-actions">
				<view class="ps-later" hover-class="ps-hv" @tap="onLater">稍后再说</view>
				<view class="ps-save" :class="{ 'ps-busy': saving }" hover-class="ps-hv" @tap="save">
					{{ saving ? '保存中…' : '保存并进入' }}
				</view>
			</view>
		</view>
	</view>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { fetchMe, updateNickname, uploadAvatar } from '@/common/api/auth'
import { getCachedUser } from '@/common/api/token'
import { showError } from '@/common/api/request'
import { resolveImage } from '@/common/api/adapters'
import { AVATAR_PREVIEW_KEY } from '@/common/config'
import { writeStorage } from '@/common/utils/storage'

const MAX_SIZE = 2 * 1024 * 1024
const FALLBACK_AVATAR = '/static/resource/images/avatar.jpg'

const props = defineProps({
	visible: { type: Boolean, default: false },
	avatar: { type: String, default: '' },
	nickname: { type: String, default: '' }
})
const emit = defineEmits(['update:visible', 'saved', 'skip'])

const nickname = ref('')
const pickedAvatar = ref('')
const saving = ref(false)

// 后端 HTTP 头像在小程序里可能加载不出来，回退到包内默认图；刚选的临时路径优先
const avatarSrc = computed(
	() => pickedAvatar.value || resolveImage(props.avatar) || FALLBACK_AVATAR
)

watch(
	() => props.visible,
	(open) => {
		if (!open) return
		nickname.value = props.nickname || ''
		pickedAvatar.value = ''
	}
)

/** 微信原生头像组件回调，detail.avatarUrl 是本地临时路径 */
const onChooseAvatar = (event) => {
	const filePath = event && event.detail && event.detail.avatarUrl
	if (filePath) pickedAvatar.value = filePath
}

/** 非微信端没有 chooseAvatar，退回相册/相机选择 */
const onAvatarTap = () => {
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
			pickedAvatar.value = file.tempFilePath
		}
	})
	// #endif
}

const onNicknameInput = (event) => {
	const value = event && event.detail ? event.detail.value : ''
	if (typeof value === 'string') nickname.value = value
}

const close = () => {
	emit('update:visible', false)
}

const onLater = () => {
	if (saving.value) return
	close()
	emit('skip')
}

const save = async () => {
	if (saving.value) return
	const name = String(nickname.value || '').trim()
	if (!name) {
		uni.showToast({ title: '请输入昵称', icon: 'none' })
		return
	}
	if (name.length > 20) {
		uni.showToast({ title: '昵称不能超过 20 个字', icon: 'none' })
		return
	}
	saving.value = true
	try {
		if (pickedAvatar.value) {
			await uploadAvatar(pickedAvatar.value)
			// 后端返回 http 头像，小程序显示不了，先记住本地临时路径给「我的」页预览
			const cached = getCachedUser()
			if (cached) {
				writeStorage(AVATAR_PREVIEW_KEY, {
					userId: cached.id,
					path: pickedAvatar.value
				})
			}
		}
		let user = null
		if (name !== String(props.nickname || '').trim()) {
			user = await updateNickname(name)
		}
		if (!user) user = await fetchMe()
		close()
		emit('saved', user)
		uni.showToast({ title: '资料已更新', icon: 'success' })
	} catch (error) {
		showError(error)
	} finally {
		saving.value = false
	}
}
</script>

<style>
.ps-mask {
	position: fixed;
	left: 0;
	right: 0;
	top: 0;
	bottom: 0;
	z-index: 99;
	display: flex;
	align-items: center;
	justify-content: center;
	background: rgba(40, 32, 26, 0.5);
}
.ps-card {
	width: 620rpx;
	padding: 44rpx 40rpx 36rpx;
	box-sizing: border-box;
	background: #ffffff;
	border-radius: 40rpx;
	box-shadow: 0 24rpx 64rpx rgba(40, 32, 26, 0.2);
}
.ps-title {
	display: block;
	text-align: center;
	font-size: 36rpx;
	font-weight: bold;
	color: #3d3229;
}
.ps-desc {
	display: block;
	margin-top: 12rpx;
	text-align: center;
	font-size: 24rpx;
	color: #a79b8e;
}

.ps-avatar-row {
	display: flex;
	align-items: center;
	margin-top: 40rpx;
}
.ps-avatar-btn {
	position: relative;
	flex-shrink: 0;
	width: 132rpx;
	height: 132rpx;
	padding: 0;
	margin: 0;
	background: transparent;
	border: none;
	border-radius: 50%;
	line-height: 1;
	overflow: visible;
}
.ps-avatar-btn::after {
	border: none;
}
.ps-avatar {
	width: 132rpx;
	height: 132rpx;
	border-radius: 50%;
	border: 4rpx solid #f0e4d6;
	box-sizing: border-box;
	background: #faf6f0;
}
.ps-cam {
	position: absolute;
	right: 0;
	bottom: 0;
	width: 44rpx;
	height: 44rpx;
	background: #e8833a;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	border: 3rpx solid #ffffff;
	box-sizing: border-box;
}
.ps-cam-body {
	width: 18rpx;
	height: 14rpx;
	background: #ffffff;
	border-radius: 3rpx;
}
.ps-cam-dot {
	position: absolute;
	top: 12rpx;
	left: 50%;
	transform: translateX(-50%);
	width: 6rpx;
	height: 6rpx;
	background: #ffffff;
	border-radius: 50%;
}
.ps-avatar-copy {
	flex: 1;
	margin-left: 24rpx;
	display: flex;
	flex-direction: column;
}
.ps-avatar-main {
	font-size: 26rpx;
	color: #3d3229;
}
.ps-avatar-sub {
	margin-top: 8rpx;
	font-size: 22rpx;
	color: #a79b8e;
}

.ps-field {
	margin-top: 36rpx;
}
.ps-label {
	display: block;
	margin-bottom: 14rpx;
	font-size: 24rpx;
	color: #8c8177;
}
.ps-input {
	width: 100%;
	height: 88rpx;
	padding: 0 24rpx;
	box-sizing: border-box;
	background: #faf6f0;
	border-radius: 20rpx;
	font-size: 28rpx;
	color: #3d3229;
}
.ps-ph {
	color: #b6a897;
}

.ps-actions {
	display: flex;
	margin-top: 40rpx;
}
.ps-later,
.ps-save {
	flex: 1;
	height: 84rpx;
	line-height: 84rpx;
	text-align: center;
	border-radius: 42rpx;
	font-size: 28rpx;
}
.ps-later {
	margin-right: 20rpx;
	background: #f3ece3;
	color: #6f6258;
}
.ps-save {
	background: linear-gradient(135deg, #9a6b46 0%, #8b5e3c 60%, #7a5133 100%);
	color: #ffffff;
	box-shadow: 0 10rpx 24rpx rgba(139, 94, 60, 0.24);
}
.ps-busy {
	opacity: 0.7;
}
.ps-hv {
	opacity: 0.86;
}
</style>
