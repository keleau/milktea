/** 店员取餐核销 */
import { request } from './request'
import { toOrder } from './adapters'

/** 扫描到的二维码内容或 5 位取餐码 + 店员口令 */
export async function lookupPickup(code, pin) {
	return toOrder(
		await request({
			url: '/staff/pickup/lookup',
			method: 'POST',
			data: { code, pin },
			auth: false
		})
	)
}

export async function completePickup(code, pin) {
	return toOrder(
		await request({
			url: '/staff/pickup/complete',
			method: 'POST',
			data: { code, pin },
			auth: false
		})
	)
}
