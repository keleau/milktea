<template>
	<view class="paws" :style="'font-size:' + size + 'rpx'">
		<view v-for="i in 5" :key="i" class="paw" :class="{ on: i <= score }"></view>
	</view>
</template>

<script setup>
defineProps({
	// 1-5 爪评分
	score: { type: Number, default: 5 },
	// 单爪尺寸（rpx）
	size: { type: Number, default: 32 }
})
</script>

<style>
/* 单爪 = 肉垫 + 中趾 + 左右趾（box-shadow 复制），纯 CSS 几何，无插画 */
.paws {
	display: inline-flex;
	align-items: flex-end;
	gap: 0.35em;
}
.paw {
	position: relative;
	display: inline-block;
	width: 0.62em;
	height: 0.5em;
	background: currentColor;
	color: #e8ddcf;
	border-radius: 50% 50% 45% 45%;
}
.paw::before {
	content: '';
	position: absolute;
	top: -0.42em;
	left: 50%;
	transform: translateX(-50%);
	width: 0.3em;
	height: 0.38em;
	background: inherit;
	border-radius: 50%;
}
.paw::after {
	content: '';
	position: absolute;
	top: -0.34em;
	left: -0.18em;
	width: 0.3em;
	height: 0.38em;
	background: inherit;
	border-radius: 50%;
	box-shadow: 0.68em 0.06em 0 0 currentColor;
}
.paw.on {
	/* 评分用弱化焦糖色，不与价格/热项的强调橘抢焦点 */
	color: #b79a6b;
}
</style>
