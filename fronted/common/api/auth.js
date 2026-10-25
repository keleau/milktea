/**
 * 登录与会话
 * 演示环境固定用 code=demo 静默登录；接真实微信时把 login() 里换成 uni.login() 的 code
 */
import { DEMO_LOGIN_CODE } from '@/common/config'
import { request, upload } from './request'
import { getAccessToken, getCachedUser, saveSession, saveUser } from './token'

let loginPromise = null

/** 微信登录（演示：code=demo → 预置会员 1001） */
export async function login(code = DEMO_LOGIN_CODE) {
	const data = await request({
		url: '/auth/wx-login',
		method: 'POST',
		data: { code },
		auth: false
	})
	saveSession(data)
	return data.user
}

/** 拉取当前用户并更新缓存 */
export async function fetchMe() {
	const user = await request({ url: '/users/me' })
	saveUser(user)
	return user
}

/** 确保已登录：有本地会话直接用，否则静默登录；并发调用共用一个登录请求 */
export async function ensureLogin() {
	if (getAccessToken()) {
		const cached = getCachedUser()
		if (cached) return cached
		try {
			return await fetchMe()
		} catch (error) {
			if (error.code !== 1002) throw error
		}
	}

	if (!loginPromise) {
		loginPromise = login().finally(() => {
			loginPromise = null
		})
	}
	return loginPromise
}

/** 修改昵称 */
export async function updateNickname(nickname) {
	const user = await request({
		url: '/users/me',
		method: 'PATCH',
		data: { nickname }
	})
	saveUser(user)
	return user
}

/** 上传头像，返回后端完整 URL */
export async function uploadAvatar(filePath) {
	const data = await upload('/users/me/avatar', filePath, 'file')
	const cached = getCachedUser()
	if (cached) saveUser({ ...cached, avatar: data.avatar })
	return data.avatar
}
