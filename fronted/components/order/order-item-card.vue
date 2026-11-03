<template>
	<view class="od-item" :class="{ bordered }">
		<image class="od-img" :src="image" mode="aspectFill"></image>
		<view class="od-info">
			<text class="od-name">{{ name }}</text>
			<text class="od-spec">{{ spec }}</text>
			<text class="od-count">x{{ count }}</text>
		</view>
		<view class="od-price" :class="{ accent }">¥{{ amount }}</view>
	</view>
</template>

<script setup>
defineProps({
	image: { type: String, default: '' },
	name: { type: String, default: '' },
	spec: { type: String, default: '' },
	count: { type: Number, default: 0 },
	amount: { type: [Number, String], default: 0 },
	bordered: { type: Boolean, default: false },
	accent: { type: Boolean, default: false }
})
</script>

<style scoped>
.od-item {
	display: flex;
	align-items: center;
	margin-top: 24rpx;
}

.od-item.bordered {
	padding-bottom: 24rpx;
	border-bottom: 2rpx solid #f0e9e1;
}

.od-item.bordered:last-child {
	padding-bottom: 0;
	border-bottom: none;
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
	font-weight: 500;
	color: #3d3229;
}

.od-spec {
	font-size: 22rpx;
	color: #8c8177;
	margin-top: 6rpx;
	overflow: hidden;
	white-space: nowrap;
	text-overflow: ellipsis;
}

.od-count {
	font-size: 22rpx;
	color: #c9c0b7;
	margin-top: 6rpx;
}

.od-price {
	font-size: 28rpx;
	font-weight: 500;
	color: #3d3229;
}

.od-price.accent {
	color: #e8833a;
}
</style>
