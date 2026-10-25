<template>
	<view class="cp-card" hover-class="hv" @tap="$emit('claim')">
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
		<view class="cp-btn" hover-class="hv" @tap.stop="$emit('claim')">领取</view>
	</view>
</template>

<script setup>
defineProps({
	/** 优惠券数据，见 common/data/shop.js */
	coupon: { type: Object, required: true }
})

defineEmits(['claim'])
</script>

<style scoped>
.cp-card {
	position: relative;
	display: flex;
	align-items: center;
	background: #ffffff;
	border-radius: 22rpx;
	padding: 20rpx;
	margin: 0 16rpx 16rpx;
	box-shadow: 0 8rpx 24rpx rgba(61, 50, 41, 0.06);
	overflow: hidden;
}
.cp-cut {
	flex-shrink: 0;
	width: 144rpx;
	display: flex;
	flex-direction: column;
	align-items: center;
	border-right: 2rpx dashed #eadfcd;
}
.cp-amt {
	display: flex;
	align-items: baseline;
	color: #e8833a;
}
.cp-sym {
	font-size: 24rpx;
	font-weight: bold;
}
.cp-num {
	font-size: 56rpx;
	font-weight: 900;
	line-height: 1;
}
.cp-min {
	margin-top: 6rpx;
	font-size: 18rpx;
	color: #b7ab9e;
}
.cp-notch {
	position: absolute;
	left: 133rpx;
	width: 22rpx;
	height: 22rpx;
	border-radius: 50%;
	background: #faf6f0;
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
	font-weight: bold;
	color: #3d3229;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}
.cp-desc {
	display: block;
	margin-top: 6rpx;
	font-size: 19rpx;
	color: #8c8177;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}
.cp-btn {
	flex-shrink: 0;
	height: 56rpx;
	line-height: 56rpx;
	padding: 0 24rpx;
	border-radius: 999rpx;
	background: linear-gradient(135deg, #f09a52 0%, #e8833a 100%);
	box-shadow: 0 4rpx 12rpx rgba(232, 131, 58, 0.3);
	color: #ffffff;
	font-size: 22rpx;
	font-weight: 500;
}
</style>
