/** 菜单、规格、门店 */
import { request } from './request'
import { toLine, toStore } from './adapters'

export async function getLines() {
	const data = await request({ url: '/menu/lines' })
	return (data.items || []).map(toLine)
}

/** @param {{line_id?: string, tab?: string, keyword?: string, store_id?: number, page?: number, page_size?: number}} params */
export function getProducts(params = {}) {
	return request({ url: '/menu/products', query: params })
}

export function getProduct(productId) {
	return request({ url: `/menu/products/${productId}` })
}

export function getOptions() {
	return request({ url: '/menu/options' })
}

export function getRank(period = 'week') {
	return request({ url: '/menu/rank', query: { period } })
}

/** @param {{latitude?: number, longitude?: number}} [location] */
export async function getStores(location) {
	const query = location && location.latitude != null
		? { lat: location.latitude, lng: location.longitude }
		: {}
	const data = await request({ url: '/stores', query })
	return (data.items || []).map(toStore)
}

export async function getStore(storeId) {
	return toStore(await request({ url: `/stores/${storeId}` }))
}
