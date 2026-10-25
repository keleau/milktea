<template>
	<view class="page">
		<view class="head">
			<text class="head-title">本周猫榜</text>
			<text class="head-sub">由布奇、坂本、汤姆、玉四只猫评员每周联合打分</text>
		</view>

		<!-- 榜单列表 -->
		<view class="list">
			<view
				class="rank-item"
				v-for="d in ranked"
				:key="d.id"
				hover-class="hv"
				@tap="toDetail(d.id)"
			>
				<view class="rk-badge" :class="'rk-' + d.rank">{{ d.rank }}</view>
				<image class="rk-img" :src="d.img" mode="aspectFill"></image>
				<view class="rk-info">
					<text class="rk-name">{{ d.name }}</text>
					<view class="rk-meta">
						<text class="line-tag" :style="{ color: lineOf(d.line).color, background: lineOf(d.line).bg }">
							{{ lineOf(d.line).tag }}
						</text>
						<paws :score="d.paws" :size="24"></paws>
					</view>
					<text class="rk-desc">{{ d.desc }}</text>
				</view>
				<view class="rk-price">¥{{ d.price }}</view>
			</view>
		</view>

		<!-- 新品上架 -->
		<view class="new-sec">
			<text class="sec-title">新品上架</text>
			<scroll-view scroll-x class="new-scroll">
				<view class="new-inner">
					<view
						class="new-card"
						v-for="d in newDrinks"
						:key="d.id"
						hover-class="hv"
						@tap="toDetail(d.id)"
					>
						<image class="new-img" :src="d.img" mode="aspectFill"></image>
						<text class="new-name">{{ d.name }}</text>
						<view class="new-bottom">
							<text class="new-price">¥{{ d.price }}</text>
							<paws :score="d.paws" :size="22"></paws>
						</view>
					</view>
				</view>
			</scroll-view>
		</view>
	</view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getLines, getRank } from '@/common/api/catalog'
import { showError } from '@/common/api/request'
import { toDrink } from '@/common/api/adapters'

const lines = ref([])
const ranked = ref([])
const newDrinks = ref([])
const EMPTY_LINE = { id: '', name: '', tag: '', en: '', desc: '', color: '#8b5e3c', bg: '#f3eae0' }
const lineOf = (id) => lines.value.find(l => l.id === id) || EMPTY_LINE

let loaded = false
const load = async () => {
	try {
		const [lineList, data] = await Promise.all([getLines(), getRank('week')])
		lines.value = lineList
		ranked.value = (data.items || []).map(item => ({ ...toDrink(item), rank: item.rank }))
		newDrinks.value = (data.new_items || []).map(toDrink)
		loaded = true
	} catch (error) {
		showError(error)
	}
}

onShow(() => {
	if (!loaded) load()
})

const toDetail = (id) => {
	uni.navigateTo({ url: '/pages/detail/index?id=' + id })
}
</script>

<style>
page {
	background: #faf6f0;
}
.page {
	min-height: 100vh;
	padding: 32rpx;
	box-sizing: border-box;
}
.hv {
	opacity: 0.85;
}
.head-title {
	display: block;
	font-size: 40rpx;
	font-weight: bold;
	color: #3d3229;
}
.head-sub {
	display: block;
	margin-top: 8rpx;
	font-size: 24rpx;
	color: #8c8177;
}

.list {
	margin-top: 32rpx;
}
.rank-item {
	display: flex;
	align-items: center;
	background: #ffffff;
	border-radius: 40rpx;
	padding: 24rpx;
	margin-bottom: 24rpx;
	box-shadow: 0 8rpx 24rpx rgba(61, 50, 41, 0.06);
}
.rk-badge {
	flex-shrink: 0;
	width: 48rpx;
	height: 48rpx;
	line-height: 48rpx;
	text-align: center;
	border-radius: 50%;
	font-size: 26rpx;
	font-weight: bold;
	color: #ffffff;
	background: #c9c0b7;
	margin-right: 20rpx;
}
.rk-1 { background: #e8833a; }
.rk-2 { background: #8b5e3c; }
.rk-3 { background: #a79b8e; }
.rk-img {
	flex-shrink: 0;
	width: 140rpx;
	height: 140rpx;
	border-radius: 24rpx;
	background: #f3eae0;
	margin-right: 20rpx;
}
.rk-info {
	flex: 1;
	min-width: 0;
}
.rk-name {
	font-size: 30rpx;
	font-weight: medium;
	color: #3d3229;
}
.rk-meta {
	display: flex;
	align-items: center;
	gap: 12rpx;
	margin-top: 8rpx;
}
.line-tag {
	font-size: 20rpx;
	padding: 2rpx 12rpx;
	border-radius: 8rpx;
}
.rk-desc {
	display: block;
	margin-top: 8rpx;
	font-size: 22rpx;
	color: #8c8177;
	overflow: hidden;
	white-space: nowrap;
	text-overflow: ellipsis;
}
.rk-price {
	flex-shrink: 0;
	margin-left: 16rpx;
	font-size: 30rpx;
	font-weight: medium;
	color: #e8833a;
}

/* 新品区 */
.new-sec {
	margin-top: 48rpx;
}
.sec-title {
	font-size: 34rpx;
	font-weight: bold;
	color: #3d3229;
}
.new-scroll {
	margin-top: 24rpx;
	white-space: nowrap;
	width: 100%;
}
.new-inner {
	display: inline-flex;
	gap: 24rpx;
}
.new-card {
	display: inline-flex;
	flex-direction: column;
	width: 240rpx;
	background: #ffffff;
	border-radius: 40rpx;
	padding: 20rpx;
	box-sizing: border-box;
	box-shadow: 0 8rpx 24rpx rgba(61, 50, 41, 0.06);
}
.new-img {
	width: 200rpx;
	height: 200rpx;
	border-radius: 24rpx;
	background: #f3eae0;
}
.new-name {
	margin-top: 16rpx;
	font-size: 26rpx;
	color: #3d3229;
	overflow: hidden;
	white-space: nowrap;
	text-overflow: ellipsis;
}
.new-bottom {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-top: 12rpx;
}
.new-price {
	font-size: 28rpx;
	font-weight: medium;
	color: #e8833a;
}
</style>
