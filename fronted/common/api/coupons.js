/** 优惠券：券模板、领券、我的券、结算可用券 */
import { request } from './request'
import { toCoupon, toCouponTemplate } from './adapters'

export async function getTemplates() {
	const data = await request({ url: '/coupons/templates' })
	return (data.items || []).map(toCouponTemplate)
}

export function claimCoupon(templateId) {
	return request({ url: `/coupons/${templateId}/claim`, method: 'POST' })
}

export async function getMyCoupons(status = 'all') {
	const data = await request({ url: '/users/me/coupons', query: { status } })
	return (data.items || []).map(toCoupon)
}

export async function getUsableCoupons(amount, storeId) {
	const data = await request({
		url: '/coupons/usable',
		query: { amount, store_id: storeId }
	})
	return (data.items || []).map(toCoupon)
}
