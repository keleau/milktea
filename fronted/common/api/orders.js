/** 订单与支付 */
import { request } from './request'
import { toOrder, toOrderSummary } from './adapters'

export function pricePreview(payload) {
	return request({ url: '/orders/price-preview', method: 'POST', data: payload })
}

/** @param {Object} payload store_id/mode/address_id/coupon_id/remark/items */
export function createOrder(payload, idempotencyKey) {
	return request({
		url: '/orders',
		method: 'POST',
		data: payload,
		header: idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {}
	})
}

/** 不传 state 才是全部；page_size 最大 100 */
export async function getOrders({ state, page = 1, pageSize = 50 } = {}) {
	const data = await request({
		url: '/orders',
		query: { state, page, page_size: pageSize }
	})
	return {
		...data,
		items: (data.items || []).map(toOrderSummary)
	}
}

export function getOrderCounts() {
	return request({ url: '/orders/counts' })
}

export async function getOrder(outTradeNo) {
	return toOrder(await request({ url: `/orders/${outTradeNo}` }))
}

export async function cancelOrder(outTradeNo) {
	return toOrder(await request({ url: `/orders/${outTradeNo}/cancel`, method: 'POST' }))
}

export async function completeOrder(outTradeNo) {
	return toOrder(await request({ url: `/orders/${outTradeNo}/complete`, method: 'POST' }))
}

/** 取餐二维码（后端返回 data:image/png;base64） */
export function getPickupQr(outTradeNo) {
	return request({ url: `/orders/${outTradeNo}/pickup-qr` })
}

export function reviewOrder(outTradeNo, rating, content = '') {
	return request({
		url: `/orders/${outTradeNo}/review`,
		method: 'POST',
		data: { rating, content }
	})
}

export function repeatOrder(outTradeNo) {
	return request({ url: `/orders/${outTradeNo}/repeat`, method: 'POST' })
}

export function prepay(outTradeNo) {
	return request({
		url: '/payments/wechat/prepay',
		method: 'POST',
		data: { out_trade_no: outTradeNo }
	})
}

/** 演示支付回调：真实微信支付时改为 uni.requestPayment(prepayParams) */
export function payDemo(outTradeNo) {
	return request({
		url: '/payments/wechat/notify',
		method: 'POST',
		data: { out_trade_no: outTradeNo, result_code: 'SUCCESS' }
	})
}

/** 统一下单 + 模拟回调，两步合成一次页面操作 */
export async function payOrder(outTradeNo) {
	await prepay(outTradeNo)
	return payDemo(outTradeNo)
}

export function getPayment(outTradeNo) {
	return request({ url: `/payments/${outTradeNo}` })
}
