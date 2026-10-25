/** 会员：等级进度、积分明细、积分兑换 */
import { request } from './request'

export function getProfile() {
	return request({ url: '/member/profile' })
}

export function getPointsLogs(page = 1, pageSize = 20) {
	return request({
		url: '/member/points/logs',
		query: { page, page_size: pageSize }
	})
}

export async function getExchangeItems() {
	const data = await request({ url: '/member/points/items' })
	return data.items || []
}

export function exchange(itemId) {
	return request({
		url: '/member/points/exchange',
		method: 'POST',
		data: { item_id: itemId }
	})
}
