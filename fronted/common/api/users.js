/** 用户：常点、收藏 */
import { request } from './request'

export async function getFavorites() {
	const data = await request({ url: '/users/me/favorites' })
	return data.items || []
}

export function addFavorite(productId) {
	return request({ url: `/users/me/favorites/${productId}`, method: 'POST' })
}

export function removeFavorite(productId) {
	return request({ url: `/users/me/favorites/${productId}`, method: 'DELETE' })
}
