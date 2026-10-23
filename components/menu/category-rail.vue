<template>
	<scroll-view scroll-y class="sidebar">
		<view
			v-for="item in items"
			:key="item.id"
			class="sb-item"
			:class="{ on: active === item.id }"
			hover-class="hv"
			@tap="$emit('pick', item.id)"
		>
			<view class="sb-ind"></view>
			<text class="sb-t">{{ item.name }}</text>
			<text
				class="sb-badge"
				:class="item.isHot ? 'sb-hot' : 'sb-new'"
				v-if="item.isHot || item.isNew"
			>{{ item.isHot ? 'HOT' : 'NEW' }}</text>
		</view>
	</scroll-view>
</template>

<script setup>
defineProps({
	/** 分类项：{ id, name, isNew?, isHot? } */
	items: { type: Array, default: () => [] },
	/** 当前高亮分类 id */
	active: { type: String, default: '' }
})

defineEmits(['pick'])
</script>

<style scoped>
.sidebar {
	width: 176rpx;
	height: 100%;
	background: #f3ede4;
	flex-shrink: 0;
}
.sb-item {
	position: relative;
	padding: 28rpx 10rpx 28rpx 26rpx;
	transition: background 0.18s ease;
}
.sb-t {
	font-size: 25rpx;
	line-height: 1.3;
	color: #8c8177;
}
.sb-item.on {
	background: #faf6f0;
}
.sb-item.on .sb-t {
	font-weight: bold;
	color: #3d3229;
}
.sb-ind {
	position: absolute;
	left: 0;
	top: 50%;
	transform: translateY(-50%);
	width: 6rpx;
	height: 0;
	border-radius: 3rpx;
	background: #e8833a;
	transition: height 0.18s ease;
}
.sb-item.on .sb-ind {
	height: 36rpx;
}
.sb-badge {
	position: absolute;
	top: 4rpx;
	right: 6rpx;
	font-size: 15rpx;
	font-weight: bold;
	line-height: 1;
	padding: 3rpx 7rpx;
	border-radius: 6rpx 6rpx 6rpx 0;
	color: #ffffff;
}
.sb-new {
	background: #e8833a;
}
.sb-hot {
	background: #8b5e3c;
}
</style>
