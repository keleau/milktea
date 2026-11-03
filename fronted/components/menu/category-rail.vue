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
	background: #f0e6d9;
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
	color: var(--ink-2, #6e5d4e);
}
.sb-item.on {
	background: var(--paper, #fffcf7);
}
.sb-item.on .sb-t {
	font-weight: 600;
	color: var(--ink, #2c211a);
}
.sb-ind {
	position: absolute;
	left: 0;
	top: 50%;
	transform: translateY(-50%);
	width: 5rpx;
	height: 0;
	border-radius: 3rpx;
	background: var(--accent-deep, #9f552d);
	transition: height 0.18s ease;
}
.sb-item.on .sb-ind {
	height: 34rpx;
}
.sb-badge {
	position: absolute;
	top: 4rpx;
	right: 6rpx;
	font-size: 15rpx;
	font-weight: 600;
	line-height: 1;
	padding: 3rpx 7rpx;
	border-radius: 4rpx 4rpx 4rpx 0;
	color: #fff8ef;
	letter-spacing: 0.04em;
}
.sb-new {
	background: var(--accent-deep, #9f552d);
}
.sb-hot {
	background: var(--brand, #6f4b2e);
}
</style>
