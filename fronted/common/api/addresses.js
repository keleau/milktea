/** 收货地址 */
import { request } from './request'

export async function getAddresses() {
	const data = await request({ url: '/addresses' })
	return data.items || []
}

/** @param {{name: string, phone: string, detail: string, is_default?: boolean}} payload */
export function createAddress(payload) {
	return request({ url: '/addresses', method: 'POST', data: payload })
}

export function updateAddress(addressId, payload) {
	return request({ url: `/addresses/${addressId}`, method: 'PATCH', data: payload })
}

export function deleteAddress(addressId) {
	return request({ url: `/addresses/${addressId}`, method: 'DELETE' })
}

export function setDefaultAddress(addressId) {
	return request({ url: `/addresses/${addressId}/default`, method: 'PATCH' })
}
