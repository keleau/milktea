<template>
	<view class="p-card" hover-class="hv" @tap="$emit('detail', drink.id)">
		<image class="p-img" :src="drink.img" mode="aspectFill"></image>
		<view class="p-body">
			<text class="p-name">{{ drink.name }}</text>
			<view class="p-tags">
				<text class="p-tag p-new" v-if="drink.isNew">新品</text>
				<text class="p-tag p-hot" v-if="drink.orig">会员价</text>
				<paws :score="drink.paws" :size="20"></paws>
			</view>
			<text class="p-desc">{{ drink.desc }}</text>
			<view class="p-bottom">
				<view class="p-price">
					<text class="p-sym">¥</text>
					<text class="p-num">{{ drink.price }}</text>
					<text class="p-orig" v-if="drink.orig">¥{{ drink.orig }}</text>
				</view>
				<view class="p-buy" hover-class="hv" @tap.stop="$emit('spec', drink)">选规格</view>
			</view>
		</view>
	</view>
</template>

<script setup>
import paws from '@/components/paws/paws.vue'

defineProps({
	/** 饮品视图数据，见 common/api/adapters.js toDrink */
	drink: { type: Object, required: true }
})

defineEmits(['detail', 'spec'])
</script>

<style scoped>
.p-card {
	display: flex;
	background: #ffffff;
	border-radius: 22rpx;
	padding: 22rpx;
	margin: 0 16rpx 18rpx;
	box-shadow: 0 8rpx 24rpx rgba(61, 50, 41, 0.06);
}
.p-img {
	flex-shrink: 0;
	width: 196rpx;
	height: 196rpx;
	border-radius: 18rpx;
	background: #f3eae0;
}
.p-body {
	flex: 1;
	min-width: 0;
	margin-left: 18rpx;
	display: flex;
	flex-direction: column;
}
.p-name {
	font-size: 30rpx;
	font-weight: bold;
	color: #3d3229;
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
	padding: 3rpx 14rpx;
	border-radius: 6rpx;
	font-size: 19rpx;
}
.p-new {
	color: #e8833a;
	background: #fdeedd;
}
.p-hot {
	color: #8b5e3c;
	background: #f3eae0;
}
.p-desc {
	margin-top: 8rpx;
	font-size: 22rpx;
	color: #8c8177;
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
	color: #e8833a;
}
.p-sym {
	font-size: 24rpx;
	font-weight: bold;
}
.p-num {
	font-size: 44rpx;
	font-weight: bold;
}
.p-orig {
	margin-left: 10rpx;
	font-size: 21rpx;
	color: #b7ab9e;
	text-decoration: line-through;
}
.p-buy {
	flex-shrink: 0;
	height: 74rpx;
	line-height: 74rpx;
	padding: 0 28rpx;
	border-radius: 999rpx;
	background: linear-gradient(135deg, #f09a52 0%, #e8833a 100%);
	box-shadow: 0 6rpx 14rpx rgba(232, 131, 58, 0.3);
	color: #ffffff;
	font-size: 26rpx;
	font-weight: 500;
}
</style>
