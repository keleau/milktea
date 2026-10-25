<template>
	<view class="page" v-if="drink">
		<!-- 顶部大图 -->
		<image class="hero" :src="drink.img" mode="aspectFill"></image>

		<!-- 基础信息卡 -->
		<view class="info-card">
			<view class="row1">
				<text class="d-name">{{ drink.name }}</text>
				<text class="line-tag" :style="{ color: line.color, background: line.bg }">{{ line.tag }}</text>
			</view>
			<view class="row2">
				<paws :score="drink.paws"></paws>
				<text class="paws-num">{{ drink.paws }} 爪认证</text>
				<text class="sold">库存 {{ drink.stock }} 杯</text>
			</view>
			<text class="d-desc">{{ drink.desc }}</text>
		</view>

		<!-- 四猫联合评分 -->
		<view class="panel">
			<text class="p-title">四猫联合评分</text>
			<view class="p-line" v-for="(l, i) in lines" :key="l.id">
				<text class="pl-name" :style="{ color: l.color }">{{ l.name }}</text>
				<view class="pl-paws">
					<paws :score="lineScores[i]" :size="26"></paws>
				</view>
				<text class="pl-score">{{ lineScores[i] }} 爪</text>
			</view>
		</view>

		<!-- 定制面板 -->
		<view class="panel">
			<view class="opt-group">
				<text class="p-title">冰度</text>
				<view class="opt-chips">
					<view
						v-for="o in iceOpts"
						:key="o"
						class="opt-chip"
						:class="{ on: ice === o }"
						@tap="ice = o"
					>
						{{ o }}
					</view>
				</view>
			</view>
			<view class="opt-group">
				<text class="p-title">糖度</text>
				<view class="opt-chips">
					<view
						v-for="o in sugarOpts"
						:key="o"
						class="opt-chip"
						:class="{ on: sugar === o }"
						@tap="sugar = o"
					>
						{{ o }}
					</view>
				</view>
			</view>
			<view class="opt-group">
				<text class="p-title">小料 <text class="p-sub">可多选</text></text>
				<view class="opt-chips">
					<view
						v-for="t in toppings"
						:key="t.id"
						class="opt-chip"
						:class="{ multi: true, on: picked.some(p => p.id === t.id) }"
						@tap="toggleTopping(t)"
					>
						{{ t.name }} +{{ t.price }}
					</view>
				</view>
			</view>
		</view>

		<!-- 底部操作栏 -->
		<view class="fix-space"></view>
		<view class="fix-bar">
			<view class="stepper">
				<view class="st-btn" :class="{ dis: count <= 1 }" @tap="count > 1 && count--">−</view>
				<text class="st-num">{{ count }}</text>
				<view class="st-btn" @tap="count++">+</view>
			</view>
			<view class="total">
				<text class="t-label">合计</text>
				<text class="t-sym">¥</text>
				<text class="t-num">{{ total }}</text>
			</view>
			<view class="go-btn" hover-class="go-hv" @tap="toCheckout">选好了，去结算</view>
		</view>
	</view>
	<view class="loading" v-else>{{ loadingText }}</view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { getLines, getProduct } from '@/common/api/catalog'
import { showError } from '@/common/api/request'
import { toDrink } from '@/common/api/adapters'
import { getStoreId } from '@/common/api/token'
import { setCheckoutDraft } from '@/common/store/session'
import { getTableContext } from '@/common/store/table'

const EMPTY_LINE = { id: '', name: '', tag: '', en: '', desc: '', color: '#8b5e3c', bg: '#f3eae0' }
const lines = ref([])
const iceOpts = ref([])
const sugarOpts = ref([])
const toppings = ref([])

const drink = ref(null)
const ice = ref('正常冰')
const sugar = ref('五分糖')
const picked = ref([])
const count = ref(1)
const mode = ref('pickup')
const loadingText = ref('加载中…')

onLoad(async (params) => {
	mode.value = params.mode === 'delivery' ? 'delivery' : 'pickup'
	try {
		const [lineList, detail] = await Promise.all([
			getLines(),
			getProduct(Number(params.id))
		])
		lines.value = lineList
		drink.value = toDrink(detail)
		iceOpts.value = detail.ice_options || []
		sugarOpts.value = detail.sugar_options || []
		toppings.value = detail.toppings || []
		ice.value = iceOpts.value.includes('正常冰') ? '正常冰' : (iceOpts.value[0] || '正常冰')
		sugar.value = sugarOpts.value.includes('五分糖') ? '五分糖' : (sugarOpts.value[0] || '五分糖')
	} catch (error) {
		loadingText.value = '饮品加载失败'
		showError(error)
		setTimeout(() => uni.navigateBack(), 800)
	}
})

const line = computed(() => lines.value.find(l => l.id === drink.value.line) || EMPTY_LINE)
// 四线评分：自身线 = 自评，其余按固定偏移浮动，保证稳定
const lineScores = computed(() => {
	const base = drink.value.paws
	const offsets = [-1, 0, 1, 0]
	return lines.value.map((l, i) => {
		if (l.id === drink.value.line) return base
		return Math.min(5, Math.max(1, base + offsets[i]))
	})
})

const total = computed(() => {
	const tp = picked.value.reduce((s, t) => s + Number(t.price || 0), 0)
	return Number(((drink.value.price + tp) * count.value).toFixed(2))
})

const toggleTopping = (t) => {
	const i = picked.value.findIndex(p => p.id === t.id)
	if (i > -1) picked.value.splice(i, 1)
	else picked.value.push(t)
}

const toCheckout = () => {
	const table = getTableContext()
	const useTable = table && table.tableNo
	setCheckoutDraft({
		storeId: useTable ? table.storeId : getStoreId(),
		mode: useTable ? 'pickup' : mode.value,
		tableNo: useTable ? table.tableNo : null,
		items: [{
			product: drink.value,
			ice: ice.value,
			sugar: sugar.value,
			toppings: picked.value.slice(),
			count: count.value
		}]
	})
	uni.navigateTo({ url: '/pages/checkout/index' })
}
</script>

<style>
page {
	background: #faf6f0;
}
.page {
	min-height: 100vh;
	padding-bottom: 200rpx;
}
.loading {
	padding-top: 300rpx;
	text-align: center;
	font-size: 28rpx;
	color: #8c8177;
}

.hero {
	display: block;
	width: 100%;
	height: 750rpx;
	background: #f3eae0;
}

.info-card {
	margin: -40rpx 32rpx 0;
	position: relative;
	background: #ffffff;
	border-radius: 40rpx;
	padding: 32rpx;
	box-shadow: 0 8rpx 24rpx rgba(61, 50, 41, 0.06);
}
.row1 {
	display: flex;
	align-items: center;
	gap: 16rpx;
}
.d-name {
	font-size: 40rpx;
	font-weight: bold;
	color: #3d3229;
	flex: 1;
	min-width: 0;
}
.line-tag {
	flex-shrink: 0;
	font-size: 22rpx;
	padding: 4rpx 16rpx;
	border-radius: 8rpx;
}
.row2 {
	display: flex;
	align-items: center;
	gap: 16rpx;
	margin-top: 20rpx;
}
.paws-num {
	font-size: 24rpx;
	color: #e8833a;
}
.sold {
	font-size: 22rpx;
	color: #c9c0b7;
	margin-left: auto;
}
.d-desc {
	display: block;
	margin-top: 16rpx;
	font-size: 26rpx;
	color: #8c8177;
	line-height: 1.6;
}

.panel {
	margin: 24rpx 32rpx 0;
	background: #ffffff;
	border-radius: 40rpx;
	padding: 32rpx;
	box-shadow: 0 8rpx 24rpx rgba(61, 50, 41, 0.06);
}
.p-title {
	font-size: 30rpx;
	font-weight: bold;
	color: #3d3229;
}
.p-sub {
	font-size: 22rpx;
	font-weight: normal;
	color: #c9c0b7;
}
.p-line {
	display: flex;
	align-items: center;
	margin-top: 24rpx;
}
.pl-name {
	width: 220rpx;
	font-size: 26rpx;
	font-weight: medium;
}
.pl-paws {
	flex: 1;
}
.pl-score {
	font-size: 24rpx;
	color: #8c8177;
}

.opt-group {
	margin-top: 32rpx;
}
.opt-group:first-child {
	margin-top: 0;
}
.opt-chips {
	display: flex;
	flex-wrap: wrap;
	gap: 16rpx;
	margin-top: 20rpx;
}
.opt-chip {
	height: 64rpx;
	line-height: 64rpx;
	padding: 0 28rpx;
	background: #f7f2eb;
	border-radius: 16rpx;
	font-size: 26rpx;
	color: #8c8177;
}
.opt-chip.on {
	background: #8b5e3c;
	color: #ffffff;
}
.opt-chip.multi.on {
	background: #fdf0e4;
	color: #e8833a;
	font-weight: medium;
}

/* 底部操作栏 */
.fix-space {
	height: 40rpx;
}
.fix-bar {
	position: fixed;
	left: 0;
	right: 0;
	bottom: 0;
	display: flex;
	align-items: center;
	padding: 20rpx 32rpx calc(20rpx + env(safe-area-inset-bottom));
	background: #ffffff;
	box-shadow: 0 -8rpx 24rpx rgba(61, 50, 41, 0.08);
	z-index: 9;
}
.stepper {
	display: flex;
	align-items: center;
}
.st-btn {
	width: 56rpx;
	height: 56rpx;
	line-height: 52rpx;
	text-align: center;
	border: 2rpx solid #8b5e3c;
	color: #8b5e3c;
	font-size: 32rpx;
	border-radius: 50%;
	box-sizing: border-box;
}
.st-btn.dis {
	opacity: 0.3;
}
.st-num {
	min-width: 64rpx;
	text-align: center;
	font-size: 30rpx;
	font-weight: medium;
	color: #3d3229;
}
.total {
	flex: 1;
	margin-left: 16rpx;
	display: flex;
	align-items: baseline;
}
.t-label {
	font-size: 24rpx;
	color: #8c8177;
	margin-right: 8rpx;
}
.t-sym {
	font-size: 24rpx;
	color: #e8833a;
}
.t-num {
	font-size: 44rpx;
	font-weight: bold;
	color: #e8833a;
}
.go-btn {
	height: 88rpx;
	line-height: 88rpx;
	padding: 0 48rpx;
	background: #8b5e3c;
	color: #ffffff;
	font-size: 30rpx;
	border-radius: 44rpx;
}
.go-hv {
	background: #6f4a2f;
}
</style>
