<template>
	<view class="cp-card" hover-class="hv" @tap="$emit('claim', coupon)">
		<view class="cp-cut">
			<view class="cp-amt">
				<text class="cp-sym">¥</text>
				<text class="cp-num">{{ coupon.cut }}</text>
			</view>
			<text class="cp-min">满{{ coupon.min }}可用</text>
		</view>
		<view class="cp-notch cp-n1"></view>
		<view class="cp-notch cp-n2"></view>
		<view class="cp-mid">
			<text class="cp-title">{{ coupon.title }}</text>
			<text class="cp-desc">{{ coupon.desc }} · 点单自动抵扣</text>
		</view>
		<view class="cp-btn" :class="{ claimed: coupon.claimed }" hover-class="hv" @tap.stop="$emit('claim', coupon)">
			{{ coupon.claimed ? '已领取' : '领取' }}
		</view>
	</view>
</template>

<script setup>
defineProps({
	/** 优惠券模板，见 common/api/adapters.js toCouponTemplate */
	coupon: { type: Object, required: true }
})

defineEmits(['claim'])
</script>

<style scoped>
.cp-card {
	position: relative;
	display: flex;
	align-items: center;
	background: var(--paper, #fffcf7);
	border: 1rpx solid var(--line, #e6d9c9);
	border-radius: 20rpx;
	padding: 20rpx;
	margin: 0 16rpx 16rpx;
	box-shadow: 0 8rpx 20rpx rgba(63, 42, 26, 0.045);
	overflow: hidden;
}
.cp-cut {
	flex-shrink: 0;
	width: 144rpx;
	display: flex;
	flex-direction: column;
	align-items: center;
	border-right: 1rpx dashed var(--line-strong, #d8c7b4);
}
.cp-amt {
	display: flex;
	align-items: baseline;
	color: var(--accent, #b86a3b);
}
.cp-sym {
	font-size: 24rpx;
	font-weight: 500;
}
.cp-num {
	font-family: var(--serif, "Songti SC", "Noto Serif SC", Georgia, serif);
	font-size: 56rpx;
	font-weight: 600;
	line-height: 1;
	letter-spacing: -0.02em;
}
.cp-min {
	margin-top: 6rpx;
	font-size: 22rpx;
	color: var(--ink-2, #6e5d4e);
}
.cp-notch {
	position: absolute;
	left: 133rpx;
	width: 22rpx;
	height: 22rpx;
	border-radius: 50%;
	background: var(--cream-100, #f4ede3);
}
.cp-n1 {
	top: -11rpx;
}
.cp-n2 {
	bottom: -11rpx;
}
.cp-mid {
	flex: 1;
	min-width: 0;
	padding: 0 16rpx;
}
.cp-title {
	display: block;
	font-size: 27rpx;
	font-weight: 600;
	color: var(--ink, #2c211a);
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}
.cp-desc {
	display: block;
	margin-top: 6rpx;
	font-size: 22rpx;
	color: var(--ink-2, #6e5d4e);
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}
.cp-btn {
	flex-shrink: 0;
	height: 56rpx;
	line-height: 56rpx;
	padding: 0 24rpx;
	border-radius: 12rpx;
	background: var(--accent-deep, #9f552d);
	color: #fff8ef;
	font-size: 22rpx;
	font-weight: 600;
}
.cp-btn.claimed {
	background: #ddd2c5;
	color: #fffaf3;
}
</style>
