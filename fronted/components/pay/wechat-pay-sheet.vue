<template>
	<view v-if="visible" class="wx-mask" @tap="onMask">
		<view class="wx-sheet" @tap.stop>
			<view class="wx-head">
				<view class="wx-title-wrap">
					<view class="wx-logo">
						<uni-icons type="weixin" size="16" color="#ffffff"></uni-icons>
					</view>
					<text class="wx-title">微信支付</text>
				</view>
				<view class="wx-close" hover-class="wx-close-hv" @tap="onClose">
					<uni-icons type="closeempty" size="22" color="#9a9a9a"></uni-icons>
				</view>
			</view>

			<text class="wx-merchant">{{ merchant }}</text>
			<view class="wx-amount">
				<text class="wx-sym">¥</text>
				<text class="wx-num">{{ amountText }}</text>
			</view>

			<text class="wx-section-label">支付方式</text>
			<view class="wx-method">
				<view class="wx-method-left">
					<view class="wx-method-icon">
						<uni-icons type="weixin" size="18" color="#07C160"></uni-icons>
					</view>
					<text class="wx-method-name">零钱</text>
				</view>
				<uni-icons type="checkmarkempty" size="18" color="#07C160"></uni-icons>
			</view>

			<view v-if="paid" class="wx-paid">
				<view class="wx-paid-icon">
					<uni-icons type="checkmarkempty" size="20" color="#ffffff"></uni-icons>
				</view>
				<text class="wx-paid-text">支付成功</text>
			</view>
			<view
				v-else
				class="wx-pay-btn"
				:class="{ dis: paying }"
				hover-class="wx-pay-hv"
				@tap="onConfirm"
			>
				{{ paying ? '支付中…' : '支付' }}
			</view>

			<text class="wx-foot">演示环境 · 不会真实扣款</text>
		</view>
	</view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
	visible: { type: Boolean, default: false },
	amount: { type: [Number, String], default: 0 },
	merchant: { type: String, default: '四猫茶学园' },
	paying: { type: Boolean, default: false },
	paid: { type: Boolean, default: false }
})

const emit = defineEmits(['close', 'confirm'])

const amountText = computed(() => Number(props.amount || 0).toFixed(2))

const canClose = () => !props.paying && !props.paid
const onMask = () => {
	if (canClose()) emit('close')
}
const onClose = () => {
	if (canClose()) emit('close')
}
const onConfirm = () => {
	if (!props.paying && !props.paid) emit('confirm')
}
</script>

<style scoped>
.wx-mask {
	position: fixed;
	left: 0;
	right: 0;
	top: 0;
	bottom: 0;
	z-index: 999;
	display: flex;
	flex-direction: column;
	justify-content: flex-end;
	background: rgba(0, 0, 0, 0.45);
	animation: wxFade 0.2s ease-out;
}

.wx-sheet {
	background: #ffffff;
	border-radius: 28rpx 28rpx 0 0;
	padding: 32rpx 32rpx calc(24rpx + env(safe-area-inset-bottom));
	animation: wxUp 0.28s cubic-bezier(0.22, 0.61, 0.36, 1);
}

.wx-head {
	position: relative;
	height: 48rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}

.wx-title-wrap {
	display: flex;
	align-items: center;
}

.wx-logo {
	width: 32rpx;
	height: 32rpx;
	margin-right: 10rpx;
	border-radius: 8rpx;
	background: #07c160;
	display: flex;
	align-items: center;
	justify-content: center;
}

.wx-title {
	font-size: 30rpx;
	font-weight: 600;
	color: #191919;
}

.wx-close {
	position: absolute;
	right: -4rpx;
	top: -6rpx;
	padding: 8rpx;
}

.wx-close-hv {
	opacity: 0.5;
}

.wx-merchant {
	display: block;
	margin-top: 24rpx;
	text-align: center;
	font-size: 24rpx;
	color: #999999;
}

.wx-amount {
	margin-top: 12rpx;
	display: flex;
	align-items: baseline;
	justify-content: center;
	color: #191919;
}

.wx-sym {
	font-size: 30rpx;
	font-weight: 500;
}

.wx-num {
	margin-left: 4rpx;
	font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", "PingFang SC", sans-serif;
	font-size: 68rpx;
	font-weight: 600;
	letter-spacing: -1rpx;
}

.wx-section-label {
	display: block;
	margin-top: 44rpx;
	font-size: 24rpx;
	color: #999999;
}

.wx-method {
	margin-top: 14rpx;
	padding: 24rpx;
	border-radius: 16rpx;
	background: #f7f7f7;
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.wx-method-left {
	display: flex;
	align-items: center;
}

.wx-method-icon {
	width: 40rpx;
	height: 40rpx;
	margin-right: 16rpx;
	border-radius: 20rpx;
	background: #e8f8ee;
	display: flex;
	align-items: center;
	justify-content: center;
}

.wx-method-name {
	font-size: 28rpx;
	color: #191919;
}

.wx-pay-btn {
	margin-top: 36rpx;
	height: 96rpx;
	line-height: 96rpx;
	text-align: center;
	border-radius: 12rpx;
	background: #07c160;
	color: #ffffff;
	font-size: 32rpx;
	font-weight: 500;
}

.wx-pay-btn.dis {
	opacity: 0.6;
}

.wx-pay-hv {
	background: #06ad56;
}

.wx-paid {
	margin-top: 36rpx;
	height: 96rpx;
	border-radius: 12rpx;
	background: #f2fbf5;
	display: flex;
	align-items: center;
	justify-content: center;
}

.wx-paid-icon {
	width: 36rpx;
	height: 36rpx;
	margin-right: 12rpx;
	border-radius: 18rpx;
	background: #07c160;
	display: flex;
	align-items: center;
	justify-content: center;
}

.wx-paid-text {
	font-size: 30rpx;
	font-weight: 600;
	color: #07c160;
}

.wx-foot {
	display: block;
	margin-top: 20rpx;
	text-align: center;
	font-size: 20rpx;
	color: #b2b2b2;
}

@keyframes wxFade {
	from { opacity: 0; }
	to { opacity: 1; }
}

@keyframes wxUp {
	from { transform: translateY(100%); }
	to { transform: translateY(0); }
}
</style>
