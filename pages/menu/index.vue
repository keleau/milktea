<template>
	<view class="page">
		<!-- 搜索框 -->
		<view class="search-bar">
			<view class="search-icon">
				<view class="si-ring"></view>
				<view class="si-line"></view>
			</view>
			<input class="search-input" placeholder="搜索想要的奶茶" placeholder-class="ph" v-model="keyword" />
		</view>

		<!-- 快捷筛选 chips -->
		<view class="chips">
			<view
				v-for="c in chips"
				:key="c.id"
				class="chip"
				:class="{ on: chipId === c.id }"
				hover-class="hv"
				@tap="chipId = c.id"
			>
				{{ c.name }}
			</view>
		</view>

		<!-- 本周猫榜入口 -->
		<view class="rank-bar" hover-class="hv" @tap="toRank">
			<view class="rank-left">
				<text class="rank-title">本周猫榜</text>
				<text class="rank-sub">四猫评员联合打分：{{ top3Text }}</text>
			</view>
			<text class="rank-arrow">›</text>
		</view>

		<!-- 产品线分类 Tab -->
		<scroll-view scroll-x class="line-tabs">
			<view class="lt-inner">
				<view class="lt-item" :class="{ on: lineId === '' }" @tap="lineId = ''">全部</view>
				<view
					v-for="l in lines"
					:key="l.id"
					class="lt-item"
					:class="{ on: lineId === l.id }"
					:style="lineId === l.id ? 'color:' + l.color : ''"
					@tap="lineId = l.id"
				>
					{{ l.name }}
				</view>
			</view>
		</scroll-view>

		<!-- 饮品两列网格 -->
		<view class="grid" v-if="filtered.length">
			<view class="g-card" v-for="d in filtered" :key="d.id" hover-class="hv" @tap="toDetail(d.id)">
				<image class="g-img" :src="d.img" mode="aspectFill"></image>
				<view class="g-body">
					<text class="g-name">{{ d.name }}</text>
					<view class="g-meta">
						<paws :score="d.paws" :size="24"></paws>
						<text class="line-tag" :style="{ color: lineOf(d.line).color, background: lineOf(d.line).bg }">
							{{ lineOf(d.line).tag }}
						</text>
					</view>
					<view class="g-bottom">
						<view class="price">
							<text class="price-sym">¥</text>
							<text class="price-num">{{ d.price }}</text>
						</view>
						<view class="g-add" hover-class="hv" @tap.stop="toDetail(d.id)">+</view>
					</view>
				</view>
			</view>
		</view>

		<!-- 空态：CSS 爪印 -->
		<view class="empty" v-else>
			<view class="empty-paw">
				<view class="ep-pad"></view>
				<view class="ep-toe ep-t1"></view>
				<view class="ep-toe ep-t2"></view>
				<view class="ep-toe ep-t3"></view>
				<view class="ep-toe ep-t4"></view>
			</view>
			<text class="empty-text">喵～没有找到相关饮品</text>
		</view>
	</view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { DRINKS, LINES } from '../../common/js/data.js'

const lines = LINES
const keyword = ref('')
const chipId = ref(0)
const lineId = ref('')
const chips = [
	{ id: 0, name: '全部' },
	{ id: 1, name: '猫榜精选' },
	{ id: 2, name: '新品上架' }
]

const lineOf = (id) => LINES.find(l => l.id === id)
const top3Text = computed(() =>
	[...DRINKS].sort((a, b) => b.paws - a.paws).slice(0, 3).map(d => d.name).join(' / ')
)

const filtered = computed(() => {
	return DRINKS.filter(d => {
		if (lineId.value && d.line !== lineId.value) return false
		if (chipId.value === 1 && !d.hot) return false
		if (chipId.value === 2 && !d.isNew) return false
		if (keyword.value && d.name.indexOf(keyword.value.trim()) === -1) return false
		return true
	})
})

const toDetail = (id) => {
	uni.navigateTo({ url: '/pages/detail/index?id=' + id })
}
const toRank = () => {
	uni.navigateTo({ url: '/pages/rank/index' })
}
</script>

<style>
page {
	background: #faf6f0;
}
.page {
	min-height: 100vh;
	padding: 24rpx 32rpx 48rpx;
	box-sizing: border-box;
}
.hv {
	opacity: 0.85;
}

/* 搜索框 */
.search-bar {
	display: flex;
	align-items: center;
	height: 72rpx;
	background: #ffffff;
	border-radius: 36rpx;
	padding: 0 32rpx;
	box-shadow: 0 8rpx 24rpx rgba(61, 50, 41, 0.06);
}
.search-icon {
	position: relative;
	width: 32rpx;
	height: 32rpx;
	margin-right: 16rpx;
}
.si-ring {
	width: 22rpx;
	height: 22rpx;
	border: 4rpx solid #c9c0b7;
	border-radius: 50%;
	box-sizing: border-box;
}
.si-line {
	position: absolute;
	right: 2rpx;
	bottom: 2rpx;
	width: 4rpx;
	height: 12rpx;
	background: #c9c0b7;
	border-radius: 2rpx;
	transform: rotate(-45deg);
}
.search-input {
	flex: 1;
	font-size: 28rpx;
	color: #3d3229;
}
.ph {
	color: #c9c0b7;
}

/* chips */
.chips {
	display: flex;
	gap: 16rpx;
	margin-top: 24rpx;
}
.chip {
	height: 64rpx;
	line-height: 64rpx;
	padding: 0 28rpx;
	background: #ffffff;
	border-radius: 16rpx;
	font-size: 26rpx;
	color: #8c8177;
}
.chip.on {
	background: #8b5e3c;
	color: #ffffff;
	font-weight: medium;
}

/* 本周猫榜横条 */
.rank-bar {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-top: 24rpx;
	padding: 24rpx 32rpx;
	background: #fdf0e4;
	border-radius: 40rpx;
}
.rank-left {
	flex: 1;
	min-width: 0;
	display: flex;
	flex-direction: column;
}
.rank-title {
	font-size: 28rpx;
	font-weight: bold;
	color: #e8833a;
}
.rank-sub {
	margin-top: 4rpx;
	font-size: 22rpx;
	color: #8c8177;
	overflow: hidden;
	white-space: nowrap;
	text-overflow: ellipsis;
}
.rank-arrow {
	font-size: 40rpx;
	color: #e8833a;
	margin-left: 16rpx;
}

/* 产品线 Tab */
.line-tabs {
	margin-top: 24rpx;
	white-space: nowrap;
	width: 100%;
}
.lt-inner {
	display: inline-flex;
	gap: 40rpx;
	padding: 8rpx 8rpx 16rpx;
}
.lt-item {
	font-size: 28rpx;
	color: #8c8177;
	position: relative;
	padding-bottom: 8rpx;
}
.lt-item.on {
	color: #3d3229;
	font-weight: bold;
}
.lt-item.on::after {
	content: '';
	position: absolute;
	left: 50%;
	transform: translateX(-50%);
	bottom: 0;
	width: 32rpx;
	height: 6rpx;
	border-radius: 3rpx;
	background: #8b5e3c;
}

/* 两列网格 */
.grid {
	display: flex;
	flex-wrap: wrap;
	gap: 24rpx;
	margin-top: 8rpx;
}
.g-card {
	width: calc(50% - 12rpx);
	background: #ffffff;
	border-radius: 40rpx;
	overflow: hidden;
	box-shadow: 0 8rpx 24rpx rgba(61, 50, 41, 0.06);
	box-sizing: border-box;
}
.g-img {
	display: block;
	width: 100%;
	height: 300rpx;
	background: #f3eae0;
}
.g-body {
	padding: 20rpx 24rpx 24rpx;
}
.g-name {
	font-size: 28rpx;
	font-weight: medium;
	color: #3d3229;
}
.g-meta {
	display: flex;
	align-items: center;
	gap: 12rpx;
	margin-top: 12rpx;
}
.line-tag {
	font-size: 20rpx;
	padding: 2rpx 12rpx;
	border-radius: 8rpx;
}
.g-bottom {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-top: 16rpx;
}
.price {
	color: #e8833a;
}
.price-sym {
	font-size: 22rpx;
}
.price-num {
	font-size: 34rpx;
	font-weight: medium;
}
.g-add {
	width: 56rpx;
	height: 56rpx;
	line-height: 52rpx;
	text-align: center;
	background: #8b5e3c;
	color: #ffffff;
	font-size: 36rpx;
	border-radius: 50%;
}

/* 空态 */
.empty {
	display: flex;
	flex-direction: column;
	align-items: center;
	padding: 96rpx 0;
}
.empty-paw {
	position: relative;
	width: 140rpx;
	height: 140rpx;
	opacity: 0.4;
}
.ep-pad {
	position: absolute;
	left: 34rpx;
	bottom: 0;
	width: 72rpx;
	height: 58rpx;
	background: #c9c0b7;
	border-radius: 50% 50% 45% 45%;
}
.ep-toe {
	position: absolute;
	width: 30rpx;
	height: 38rpx;
	background: #c9c0b7;
	border-radius: 50%;
}
.ep-t1 { left: 0; top: 34rpx; transform: rotate(-24deg); }
.ep-t2 { left: 38rpx; top: 18rpx; }
.ep-t3 { right: 38rpx; top: 18rpx; }
.ep-t4 { right: 0; top: 34rpx; transform: rotate(24deg); }
.empty-text {
	margin-top: 24rpx;
	font-size: 28rpx;
	color: #8c8177;
}
</style>
