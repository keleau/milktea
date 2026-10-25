<template>
	<view class="login-page" :style="{ paddingTop: statusBarHeight + 'px' }">
		<view class="glow glow-a"></view>
		<view class="glow glow-b"></view>

		<view class="brand">
			<image class="logo" src="/static/resource/images/avatar.jpg" mode="aspectFill" />
			<view class="brand-name">四猫茶学园</view>
			<view class="brand-en">FOUR CATS TEA ACADEMY</view>
			<view class="brand-desc">一杯好茶，四只猫陪你慢慢喝</view>
		</view>

		<view class="actions">
			<view
				class="btn btn-primary"
				:class="{ busy: loading }"
				hover-class="btn-hv"
				@tap="onWxLogin"
			>
				<text v-if="loading === 'wx'">登录中…</text>
				<text v-else>微信一键登录</text>
			</view>
			<view
				class="btn btn-demo"
				:class="{ busy: loading }"
				hover-class="btn-hv"
				@tap="onDemoLogin"
			>
				<text v-if="loading === 'demo'">登录中…</text>
				<text v-else>演示会员登录</text>
			</view>

			<view class="tips">
				<text class="tip-line">微信登录为演示模拟，不会获取你的微信资料。</text>
				<text class="tip-line">演示会员已预置积分、优惠券和历史订单。</text>
			</view>
		</view>

		<view class="footer">登录即表示使用本演示项目</view>
	</view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { login, loginWithWechat } from '@/common/api/auth'
import { getAccessToken } from '@/common/api/token'
import { showError } from '@/common/api/request'
import { DEMO_LOGIN_CODE } from '@/common/config'

const statusBarHeight = uni.getWindowInfo().statusBarHeight || 20
const loading = ref('')

onLoad(() => {
	// 已登录直接进首页，避免每次启动都停在登录页
	if (getAccessToken()) {
		uni.switchTab({ url: '/pages/index/index' })
	}
})

const submit = async (type, task) => {
	if (loading.value) return
	loading.value = type
	try {
		await task()
		uni.showToast({ title: '登录成功', icon: 'success', duration: 800 })
		setTimeout(() => {
			uni.switchTab({ url: '/pages/index/index' })
		}, 400)
	} catch (error) {
		loading.value = ''
		showError(error)
	}
}

const onWxLogin = () => submit('wx', loginWithWechat)
const onDemoLogin = () => submit('demo', () => login(DEMO_LOGIN_CODE))
</script>

<style>
page {
	background: #faf6f0;
}
.login-page {
	position: relative;
	min-height: 100vh;
	padding: 0 56rpx 48rpx;
	box-sizing: border-box;
	display: flex;
	flex-direction: column;
	overflow: hidden;
	background: linear-gradient(180deg, #fdf9f3 0%, #f6ecdf 100%);
}

/* 背景暖色光斑 */
.glow {
	position: absolute;
	border-radius: 50%;
	filter: blur(2rpx);
	opacity: 0.55;
}
.glow-a {
	top: -180rpx;
	right: -160rpx;
	width: 520rpx;
	height: 520rpx;
	background: radial-gradient(circle, rgba(232, 131, 58, 0.28) 0%, rgba(250, 246, 240, 0) 70%);
}
.glow-b {
	bottom: 80rpx;
	left: -200rpx;
	width: 560rpx;
	height: 560rpx;
	background: radial-gradient(circle, rgba(139, 94, 60, 0.2) 0%, rgba(250, 246, 240, 0) 70%);
}

.brand {
	position: relative;
	margin-top: 150rpx;
	display: flex;
	flex-direction: column;
	align-items: center;
}
.logo {
	width: 168rpx;
	height: 168rpx;
	border-radius: 50%;
	border: 6rpx solid #ffffff;
	box-shadow: 0 16rpx 40rpx rgba(139, 94, 60, 0.22);
	background: #ffffff;
}
.brand-name {
	margin-top: 36rpx;
	font-size: 52rpx;
	font-weight: bold;
	letter-spacing: 4rpx;
	color: #3d3229;
}
.brand-en {
	margin-top: 14rpx;
	font-size: 20rpx;
	letter-spacing: 6rpx;
	color: #b6a897;
}
.brand-desc {
	margin-top: 28rpx;
	font-size: 26rpx;
	color: #8c8177;
}

.actions {
	position: relative;
	margin-top: 120rpx;
}
.btn {
	height: 96rpx;
	line-height: 96rpx;
	text-align: center;
	border-radius: 48rpx;
	font-size: 30rpx;
	letter-spacing: 2rpx;
}
.btn-hv {
	opacity: 0.88;
}
.busy {
	opacity: 0.75;
}
.btn-primary {
	background: linear-gradient(135deg, #9a6b46 0%, #8b5e3c 60%, #7a5133 100%);
	color: #ffffff;
	box-shadow: 0 14rpx 32rpx rgba(139, 94, 60, 0.3);
}
.btn-demo {
	margin-top: 28rpx;
	background: #ffffff;
	color: #8b5e3c;
	border: 2rpx solid #e6d8c8;
	box-shadow: 0 8rpx 24rpx rgba(139, 94, 60, 0.08);
}

.tips {
	margin-top: 56rpx;
	display: flex;
	flex-direction: column;
	align-items: center;
}
.tip-line {
	font-size: 22rpx;
	line-height: 36rpx;
	color: #a79b8e;
}

.footer {
	position: relative;
	margin-top: auto;
	padding-top: 80rpx;
	text-align: center;
	font-size: 22rpx;
	color: #c2b6a8;
}
</style>
