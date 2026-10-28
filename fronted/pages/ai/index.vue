<template>
	<view class="ai-page">
		<scroll-view
			class="msg-scroll"
			scroll-y
			:scroll-top="scrollTop"
			scroll-with-animation
			:show-scrollbar="false"
		>
			<view class="msg-list">
				<view v-for="m in messages" :key="m.id">
					<view v-if="m.role === 'system'" class="system-line">{{ m.content }}</view>

					<view v-else-if="m.role === 'user'" class="msg-row user">
						<view v-if="m.status === 'failed'" class="retry" @tap="retry(m)">!</view>
						<view class="bubble user-bubble">
							<text class="bubble-text">{{ m.content }}</text>
						</view>
					</view>

					<view v-else-if="m.role === 'loading'" class="msg-row ai">
						<view class="bubble ai-bubble loading-bubble">
							<view class="dot dot1"></view>
							<view class="dot dot2"></view>
							<view class="dot dot3"></view>
						</view>
					</view>

					<view v-else class="msg-row ai">
						<view class="ai-stack">
							<view class="bubble ai-bubble">
								<text class="bubble-text">{{ m.content }}</text>
							</view>
							<view
								v-if="m.order && m.order.items && m.order.items.length"
								class="order-card"
								hover-class="oc-hv"
								@tap="toOrder(m.order)"
							>
								<view class="oc-head">
									<text class="oc-tag">下单成功</text>
									<text class="oc-state">{{ m.order.state_text }}</text>
								</view>
								<text class="oc-name">{{ m.order.items[0].name }}</text>
								<text class="oc-spec">{{ specText(m.order.items[0]) }}</text>
								<view class="oc-foot">
									<text class="oc-no">单号 {{ shortNo(m.order.out_trade_no) }}</text>
									<text class="oc-total">¥{{ m.order.total }}</text>
								</view>
								<view class="oc-action">查看订单 ›</view>
							</view>
						</view>
					</view>
				</view>
			</view>
		</scroll-view>

		<view class="composer">
			<input
				class="composer-input"
				v-model="input"
				:disabled="sending"
				maxlength="500"
				confirm-type="send"
				placeholder="想喝什么？例如：少冰五分糖一杯黑糖波波厚奶茶"
				placeholder-class="input-ph"
				:adjust-position="true"
				:cursor-spacing="20"
				@confirm="send"
			/>
			<view class="send-btn" :class="{ 'send-off': !canSend }" hover-class="send-hv" @tap="send">发送</view>
		</view>
	</view>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { ensureLogin } from '@/common/api/auth'
import { chatWithAi, getAiHistory } from '@/common/api/ai'
import { getStoreId } from '@/common/api/token'
import { getTableContext } from '@/common/store/table'

const messages = ref([])
const input = ref('')
const sending = ref(false)
const scrollTop = ref(0)
let seq = 0

const canSend = computed(() => !sending.value && input.value.trim().length > 0)

const scrollToBottom = () => {
	nextTick(() => {
		scrollTop.value += 100000
		setTimeout(() => {
			scrollTop.value += 100000
		}, 80)
	})
}

const addMessage = (role, content, order = null) => {
	const id = ++seq
	messages.value.push({ id, role, content, order, status: 'sent' })
	scrollToBottom()
	return id
}

const removeMessage = (id) => {
	messages.value = messages.value.filter((message) => message.id !== id)
}

const setMessageStatus = (id, status) => {
	const message = messages.value.find((item) => item.id === id)
	if (message) message.status = status
}

const addWelcome = () => {
	addMessage('assistant', '你好呀～想点什么奶茶，可以直接告诉我哦😊')
}

onLoad(async () => {
	try {
		await ensureLogin()
		const data = await getAiHistory()
		messages.value = (data.messages || []).map((item) => ({
			id: ++seq,
			role: item.role,
			content: item.content,
			order: item.order || null,
			status: 'sent'
		}))
		if (!messages.value.length) addWelcome()
		scrollToBottom()
	} catch (error) {
		if (error.silent) return
		addMessage('system', error.code === -1 ? '网络不佳，请检查网络' : '会话加载失败，可以直接开始对话')
	}
})

const sendText = async (text, userMessageId) => {
	if (sending.value) return
	sending.value = true
	setMessageStatus(userMessageId, 'sent')
	const loaderId = addMessage('loading', '')
	try {
		const table = getTableContext()
		const data = await chatWithAi(text, table ? table.storeId : getStoreId(), table ? table.tableNo : null)
		removeMessage(loaderId)
		addMessage('assistant', data.answer || '我在呢～可以告诉我想喝什么。', data.order || null)
	} catch (error) {
		removeMessage(loaderId)
		if (error.silent) return
		setMessageStatus(userMessageId, 'failed')
		addMessage(
			'system',
			error.code === -1 ? '网络不佳，请检查网络，点感叹号可重试' : error.message || '系统繁忙，请稍后再试'
		)
	} finally {
		sending.value = false
		scrollToBottom()
	}
}

const send = () => {
	const text = input.value.trim()
	if (!text || sending.value) return
	if (text.length > 500) {
		uni.showToast({ title: '内容过长，请精简描述', icon: 'none' })
		return
	}
	input.value = ''
	const userMessageId = addMessage('user', text)
	sendText(text, userMessageId)
}

const retry = (message) => {
	if (sending.value) return
	sendText(message.content, message.id)
}

const shortNo = (outTradeNo) => (outTradeNo || '').slice(-8)

const specText = (item) => {
	if (!item) return ''
	const parts = [item.ice, item.sugar]
	if (item.topping_names) parts.push(item.topping_names)
	parts.push(`×${item.count}`)
	return parts.filter(Boolean).join(' · ')
}

const toOrder = (order) => {
	if (!order || !order.out_trade_no) return
	uni.navigateTo({ url: `/pages/order/order?oid=${order.out_trade_no}` })
}
</script>

<style>
.ai-page {
	position: fixed;
	top: 0;
	right: 0;
	bottom: 0;
	left: 0;
	display: flex;
	flex-direction: column;
	background: #faf6f0;
}

.msg-scroll {
	flex: 1;
	height: 0;
}

.msg-list {
	padding: 28rpx 24rpx 32rpx;
}

.msg-row {
	display: flex;
	align-items: flex-start;
	margin-bottom: 26rpx;
}

.msg-row.user {
	justify-content: flex-end;
}

.bubble {
	max-width: 75%;
	padding: 20rpx 24rpx;
	border-radius: 16rpx;
	font-size: 28rpx;
	line-height: 1.55;
	box-sizing: border-box;
}

.bubble-text {
	font-size: 28rpx;
	line-height: 1.55;
	white-space: pre-wrap;
	word-break: break-word;
}

.user-bubble {
	max-width: 70%;
	background: #8b5e3c;
	color: #ffffff;
	border-top-right-radius: 4rpx;
}

.user-bubble .bubble-text {
	color: #ffffff;
}

.ai-stack {
	max-width: 78%;
	display: flex;
	flex-direction: column;
}

.ai-bubble {
	background: #ffffff;
	color: #333333;
	box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
	border-top-left-radius: 4rpx;
}

.ai-stack .ai-bubble {
	max-width: 100%;
}

.retry {
	flex-shrink: 0;
	width: 36rpx;
	height: 36rpx;
	margin: 18rpx 12rpx 0 0;
	border-radius: 50%;
	background: #d9534f;
	color: #ffffff;
	font-size: 24rpx;
	line-height: 36rpx;
	text-align: center;
}

.system-line {
	margin: 8rpx auto 26rpx;
	max-width: 82%;
	text-align: center;
	font-size: 22rpx;
	line-height: 1.5;
	color: #a79b8e;
}

.loading-bubble {
	display: flex;
	align-items: center;
	padding: 26rpx 30rpx;
}

.dot {
	width: 12rpx;
	height: 12rpx;
	margin-right: 10rpx;
	border-radius: 50%;
	background: #8b5e3c;
	animation: dotBounce 1.1s infinite ease-in-out;
}

.dot:last-child {
	margin-right: 0;
}

.dot2 {
	animation-delay: 0.15s;
}

.dot3 {
	animation-delay: 0.3s;
}

@keyframes dotBounce {
	0%,
	60%,
	100% {
		transform: translateY(0);
		opacity: 0.4;
	}
	30% {
		transform: translateY(-8rpx);
		opacity: 1;
	}
}

.order-card {
	margin-top: 16rpx;
	padding: 24rpx;
	background: #ffffff;
	border-radius: 20rpx;
	box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
	box-sizing: border-box;
}

.oc-hv {
	opacity: 0.9;
}

.oc-head {
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.oc-tag {
	padding: 4rpx 14rpx;
	border-radius: 999rpx;
	background: #fdf1e4;
	color: #8b5e3c;
	font-size: 20rpx;
}

.oc-state {
	font-size: 22rpx;
	color: #b08d57;
}

.oc-name {
	display: block;
	margin-top: 16rpx;
	font-size: 30rpx;
	font-weight: bold;
	color: #3d3229;
}

.oc-spec {
	display: block;
	margin-top: 6rpx;
	font-size: 24rpx;
	color: #8c8177;
}

.oc-foot {
	display: flex;
	align-items: baseline;
	justify-content: space-between;
	margin-top: 18rpx;
	padding-top: 16rpx;
	border-top: 2rpx dashed #f0e9e1;
}

.oc-no {
	font-size: 22rpx;
	color: #a79b8e;
}

.oc-total {
	font-size: 30rpx;
	font-weight: bold;
	color: #8b5e3c;
}

.oc-action {
	margin-top: 12rpx;
	text-align: right;
	font-size: 24rpx;
	color: #8b5e3c;
}

.composer {
	flex-shrink: 0;
	display: flex;
	align-items: center;
	padding: 16rpx 24rpx calc(16rpx + env(safe-area-inset-bottom));
	background: #ffffff;
	border-top: 2rpx solid #f0e9e1;
}

.composer-input {
	flex: 1;
	min-width: 0;
	height: 84rpx;
	padding: 0 28rpx;
	border-radius: 42rpx;
	background: #faf6f0;
	font-size: 28rpx;
	color: #333333;
}

.input-ph {
	color: #b7ab9e;
}

.send-btn {
	flex-shrink: 0;
	margin-left: 16rpx;
	height: 84rpx;
	padding: 0 34rpx;
	border-radius: 42rpx;
	background: #8b5e3c;
	color: #ffffff;
	font-size: 28rpx;
	line-height: 84rpx;
}

.send-off {
	background: #e2d8cc;
	color: #ffffff;
}

.send-hv {
	opacity: 0.85;
}
</style>
