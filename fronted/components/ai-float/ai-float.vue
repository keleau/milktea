<template>
	<view class="ai-float" :style="{ bottom }">
		<view v-if="!hidden" class="af-main">
			<view class="af-sticker-wrap" :class="{ 'af-tap': waving }">
				<!-- 圆形贴纸：待机 GIF / 点击挥手帧 -->
				<view class="af-sticker" hover-class="af-hv" aria-label="打开 AI 点单助手" @tap="onTap">
					<image v-if="!waving" class="af-gif" src="/static/resource/images/ai_maid.gif" mode="scaleToFill"></image>
					<image v-else class="af-gif" src="/static/resource/images/maid_wave.png" mode="aspectFit"></image>
				</view>
				<view class="af-badge">AI</view>

				<!-- 点击光环 -->
				<view v-if="waving" class="af-ring"></view>
				<view v-if="waving" class="af-ring r2"></view>

				<!-- 精致粒子层（overflow visible，可飘到贴纸外） -->
				<view class="af-fx-layer">
					<image
						v-for="(p, i) in particles"
						:key="i"
						class="af-fx"
						:src="p.src"
						:style="{
							left: p.left + 'rpx',
							top: p.top + 'rpx',
							width: p.size + 'rpx',
							height: p.size + 'rpx',
							'--dx': p.dx + 'rpx',
							'--rot': p.rot + 'deg',
							animationDelay: p.delay + 's'
						}"
					></image>
				</view>
			</view>

			<view class="af-hide-hit" hover-class="af-hv" aria-label="隐藏 AI 点单助手" @tap.stop="hide">
				<view class="af-hide">
					<uni-icons type="eye-slash" size="14" color="#8B5E3C"></uni-icons>
				</view>
			</view>
		</view>

		<view v-else class="af-mini-hit" hover-class="af-hv" aria-label="展开 AI 点单助手" @tap.stop="show">
			<view class="af-mini">
				<text class="af-mini-t">AI</text>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { aiFloatHidden, setAiFloatHidden } from '@/common/store/aiFloat'

const props = defineProps({
	/** 点单页有购物车栏时整体上移，避免挡住结算按钮 */
	raised: {
		type: Boolean,
		default: false
	}
})

const hidden = aiFloatHidden
const bottom = computed(() => (props.raised ? '190rpx' : '36rpx'))

const waving = ref(false)
const particles = ref([])

const FX = [
	'heart_orange', 'heart_pink', 'paw_brown', 'paw_deep',
	'sparkle_gold', 'sparkle_cream', 'orb_orange', 'orb_cream'
]
const rand = (min, max) => min + Math.random() * (max - min)

const spawnParticles = () => {
	const list = []
	for (let i = 0; i < 14; i++) {
		const name = FX[Math.floor(Math.random() * FX.length)]
		list.push({
			src: `/static/resource/images/fx/${name}.png`,
			left: rand(30, 130),
			top: rand(50, 120),
			size: rand(26, 46),
			dx: rand(-45, 45),
			rot: rand(-35, 35),
			delay: rand(0, 0.15)
		})
	}
	particles.value = list
}

const onTap = () => {
	if (waving.value) return
	// 先播放挥手动作 + 特效
	waving.value = true
	spawnParticles()
	// 动作看清后再进 AI 对话页
	setTimeout(() => {
		waving.value = false
		particles.value = []
		uni.navigateTo({ url: '/pages/ai/index' })
	}, 550)
}

const hide = () => {
	setAiFloatHidden(true)
}

const show = () => {
	setAiFloatHidden(false)
}
</script>

<style>
.ai-float {
	position: fixed;
	right: 20rpx;
	z-index: 80;
	display: flex;
	flex-direction: column;
	align-items: center;
	transition: bottom 0.2s ease;
}

.af-main {
	display: flex;
	flex-direction: column;
	align-items: center;
}

.af-sticker-wrap {
	position: relative;
	width: 168rpx;
	height: 168rpx;
}

.af-sticker {
	width: 168rpx;
	height: 168rpx;
	background: transparent;
}

/* 点击弹跳 */
.af-tap .af-sticker {
	animation: afBounce 0.55s cubic-bezier(0.22, 0.61, 0.36, 1);
}
@keyframes afBounce {
	0%   { transform: scale(1); }
	35%  { transform: scale(1.12) translateY(-6rpx); }
	65%  { transform: scale(0.97); }
	100% { transform: scale(1); }
}

.af-gif {
	width: 100%;
	height: 100%;
}

.af-badge {
	position: absolute;
	top: -2rpx;
	right: -2rpx;
	padding: 2rpx 12rpx;
	border-radius: 999rpx;
	background: #8b5e3c;
	color: #fff7ec;
	font-size: 18rpx;
	line-height: 1.5;
	box-shadow: 0 2rpx 6rpx rgba(61, 50, 41, 0.2);
	z-index: 3;
}

.af-hv {
	opacity: 0.88;
	transform: scale(0.97);
	transition: transform 0.18s ease, opacity 0.18s ease;
}

/* 点击光环 */
.af-ring {
	position: absolute;
	left: 50%;
	top: 50%;
	width: 120rpx;
	height: 120rpx;
	margin: -60rpx 0 0 -60rpx;
	border-radius: 50%;
	border: 2rpx solid rgba(232, 131, 58, 0.7);
	pointer-events: none;
	animation: afRing 0.9s ease-out forwards;
	z-index: 2;
}
.af-ring.r2 {
	border-color: rgba(255, 225, 190, 0.85);
	animation-delay: 0.12s;
}
@keyframes afRing {
	0%   { opacity: 0; transform: scale(0.4); }
	25%  { opacity: 1; }
	100% { opacity: 0; transform: scale(2.1); }
}

/* 粒子层：与贴纸同尺寸，但 overflow visible */
.af-fx-layer {
	position: absolute;
	left: 0;
	top: 0;
	width: 168rpx;
	height: 168rpx;
	pointer-events: none;
}
.af-fx {
	position: absolute;
	animation: afFloatUp 1.4s cubic-bezier(0.25, 0.5, 0.35, 1) forwards;
}
@keyframes afFloatUp {
	0% {
		opacity: 0;
		transform: translate(0, 0) scale(0.4) rotate(0deg);
	}
	18% {
		opacity: 1;
		transform: translate(calc(var(--dx, 0rpx) * 0.3), -18rpx) scale(1) rotate(8deg);
	}
	100% {
		opacity: 0;
		transform: translate(var(--dx, 0rpx), -130rpx) scale(0.9) rotate(var(--rot, 0deg));
	}
}

.af-hide-hit {
	width: 88rpx;
	height: 88rpx;
	margin-top: -18rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}

.af-hide {
	width: 38rpx;
	height: 38rpx;
	border-radius: 50%;
	background: rgba(255, 255, 255, 0.9);
	display: flex;
	align-items: center;
	justify-content: center;
	box-shadow: 0 2rpx 8rpx rgba(61, 50, 41, 0.12);
}

.af-mini-hit {
	width: 88rpx;
	height: 88rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}

.af-mini {
	width: 58rpx;
	height: 58rpx;
	border-radius: 50%;
	background: #ffffff;
	border: 2rpx solid #f0e3d4;
	display: flex;
	align-items: center;
	justify-content: center;
	box-shadow: 0 6rpx 16rpx rgba(61, 50, 41, 0.16);
}

.af-mini-t {
	font-size: 20rpx;
	font-weight: bold;
	color: #8b5e3c;
	line-height: 1;
}
</style>
