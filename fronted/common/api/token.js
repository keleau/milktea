/**
 * 登录态缓存：access_token / refresh_token / 用户对象
 * 只做读写，不发请求，避免和 request.js 循环依赖
 */
import { STORE_KEY, TOKEN_KEYS } from '@/common/config'
import { readStorage, removeStorage, writeStorage } from '@/common/utils/storage'

export const getAccessToken = () => readStorage(TOKEN_KEYS.access, '')
export const getRefreshToken = () => readStorage(TOKEN_KEYS.refresh, '')
export const getCachedUser = () => readStorage(TOKEN_KEYS.user, null)

/** 登录/刷新后写入 token 对 */
export function saveTokens(data) {
	if (!data) return
	if (data.access_token) writeStorage(TOKEN_KEYS.access, data.access_token)
	if (data.refresh_token) writeStorage(TOKEN_KEYS.refresh, data.refresh_token)
}

/** 登录成功后写入 token + 用户 */
export function saveSession(data) {
	saveTokens(data)
	if (data && data.user) saveUser(data.user)
}

/** 更新本地用户缓存（昵称、头像、积分等） */
export function saveUser(user) {
	if (user) writeStorage(TOKEN_KEYS.user, user)
}

/** 清空会话；门店选择与结算草稿保留 */
export function clearSession() {
	removeStorage(TOKEN_KEYS.access)
	removeStorage(TOKEN_KEYS.refresh)
	removeStorage(TOKEN_KEYS.user)
}

export const getStoreId = () => Number(readStorage(STORE_KEY, 1)) || 1
export const saveStoreId = (storeId) => writeStorage(STORE_KEY, Number(storeId) || 1)
