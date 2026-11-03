<template>
	<view class="p-card" :class="{ 'is-sold-out': drink.stock <= 0 }" hover-class="hv" @tap="$emit('detail', drink.id)">
		<image class="p-img" :src="drink.img" mode="aspectFill"></image>
		<view class="p-body">
			<text class="p-name">{{ drink.name }}</text>
			<view class="p-tags">
				<text class="p-tag p-sold" v-if="drink.stock <= 0">售罄</text>
				<text class="p-tag p-new" v-if="drink.isNew && drink.stock > 0">新品</text>
				<text class="p-tag p-hot" v-if="drink.orig && drink.stock > 0">会员价</text>
				<paws :score="drink.paws" :size="20"></paws>
			</view>
			<text class="p-desc">{{ drink.desc }}</text>
			<view class="p-bottom">
				<view class="p-price">
					<text class="p-sym">¥</text>
					<text class="p-num">{{ drink.price }}</text>
					<text class="p-orig" v-if="drink.orig">¥{{ drink.orig }}</text>
				</view>
				<view class="p-buy" :class="{ dis: drink.stock <= 0 }" hover-class="hv" @tap.stop="openSpec">
					{{ drink.stock > 0 ? '选规格' : '售罄' }}
				</view>
			</view>
		</view>
	</view>
</template>

<script setup>
import paws from '@/components/paws/paws.vue'

const props = defineProps({
	/** 饮品视图数据，见 common/api/adapters.js toDrink */
	drink: { type: Object, required: true }
})

const emit = defineEmits(['detail', 'spec'])

const openSpec = () => {
	if (props.drink.stock > 0) emit('spec', props.drink)
}
</script>

<style scoped>
.p-card {
	display: flex;
	background: var(--paper, #fffcf7);
	border: 1rpx solid var(--line, #e6d9c9);
	border-radius: 24rpx;
	padding: 22rpx;
	margin: 0 16rpx 18rpx;
	box-shadow: 0 10rpx 28rpx rgba(63, 42, 26, 0.05);
}
.p-card.is-sold-out .p-img,
.p-card.is-sold-out .p-name,
.p-card.is-sold-out .p-price {
	opacity: 0.5;
}
.p-img {
	flex-shrink: 0;
	width: 196rpx;
	height: 196rpx;
	border-radius: 14rpx;
	background: var(--paper-soft, #faf3e8);
}
.p-body {
	flex: 1;
	min-width: 0;
	margin-left: 18rpx;
	display: flex;
	flex-direction: column;
}
.p-name {
	font-family: var(--serif, "Songti SC", "Noto Serif SC", serif);
	font-size: 33rpx;
	font-weight: 600;
	color: var(--ink, #2c211a);
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}
.p-tags {
	display: flex;
	align-items: center;
	flex-wrap: wrap;
	row-gap: 6rpx;
	margin-top: 8rpx;
}
.p-tag {
	flex-shrink: 0;
	margin-right: 10rpx;
	padding: 3rpx 12rpx;
	border-radius: 4rpx;
	font-size: 22rpx;
	letter-spacing: 0.04em;
}
.p-new {
	color: var(--accent-deep, #9f552d);
	background: var(--accent-soft, #f3e2d2);
}
.p-hot {
	color: var(--brand, #6f4b2e);
	background: var(--paper-soft, #faf3e8);
	border: 1rpx solid var(--line, #e6d9c9);
}
.p-sold {
	color: var(--ink-2, #6e5d4e);
	background: var(--cream-200, #ece1d3);
}
.p-desc {
	margin-top: 8rpx;
	font-size: 24rpx;
	color: var(--ink-2, #6e5d4e);
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}
.p-bottom {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-top: auto;
}
.p-price {
	display: flex;
	align-items: baseline;
	color: var(--accent-deep, #9f552d);
}
.p-sym {
	font-size: 24rpx;
	font-weight: 500;
}
.p-num {
	font-family: var(--serif, "Songti SC", "Noto Serif SC", Georgia, serif);
	font-size: 38rpx;
	font-weight: 600;
	letter-spacing: -0.02em;
}
.p-orig {
	margin-left: 10rpx;
	font-size: 21rpx;
	color: var(--ink-3, #9a8a7a);
	text-decoration: line-through;
}
.p-buy {
	flex-shrink: 0;
	height: 64rpx;
	line-height: 64rpx;
	padding: 0 22rpx;
	border-radius: 12rpx;
	border: 1rpx solid var(--line-strong, #d8c7b4);
	background: transparent;
	color: var(--brand, #6f4b2e);
	font-size: 24rpx;
	font-weight: 600;
	letter-spacing: 0.02em;
}
.p-buy.dis {
	border-color: var(--line, #e6d9c9);
	color: var(--ink-3, #9a8a7a);
}
</style>
