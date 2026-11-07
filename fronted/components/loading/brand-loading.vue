<template>
	<view class="brand-loading" :style="{ width: size + 'rpx', height: size + 'rpx' }">
		<image class="brand-loading__img" src="/static/resource/images/loading.gif" mode="aspectFit"></image>
	</view>
</template>

<script setup>
defineProps({
	size: { type: Number, default: 260 }
})
</script>

<style scoped>
.brand-loading {
	margin: 0 auto;
	display: flex;
	align-items: center;
	justify-content: center;
}

.brand-loading__img {
	width: 100%;
	height: 100%;
}
</style>
