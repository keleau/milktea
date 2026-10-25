/**
 * 登录与会话
 * - 微信登录：uni.login 拿 code + 本机固定 mock_id，后端生成稳定的模拟账号
 * - 演示会员：code=demo → 预置会员 1001（有积分/优惠券/历史订单）
 */
import { DEMO_LOGIN_CODE, MOCK_ID_KEY } from '@/common/config'
import { readStorage, writeStorage } from '@/common/utils/storage'
import { ApiError, redirectToLogin, request, upload } from './request'
import { clearSession, getAccessToken, getCachedUser, saveSession, saveUser } from './token'

/** 后端未接 code2session，uni.login 的 code 只用来满足接口参数 */
function getWxCode() {
	return new Promise((resolve) => {
		// #ifdef MP-WEIXIN
		uni.login({
			provider: 'weixin',
			success: (res) => resolve(res.code || 'wx-demo'),
			fail: () => resolve('wx-demo')
		})
		// #endif
		// #ifndef MP-WEIXIN
		resolve('wx-demo')
		// #endif
	})
}

/** 本机固定 ID：同一台设备重复登录仍落到同一个账号，不会每次都新建用户 */
function getMockId() {
	const cached = readStorage(MOCK_ID_KEY, '')
	if (cached) return cached
	const id = `device-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
	writeStorage(MOCK_ID_KEY, id)
	return id
}

/** 登录并写入本地会话；默认走演示会员 */
export async function login(code = DEMO_LOGIN_CODE, mockId = '') {
	const data = await request({
		url: '/auth/wx-login',
		method: 'POST',
		data: mockId ? { code, mock_id: mockId } : { code },
		auth: false
	})
	saveSession(data)
	return data.user
}

/** 微信一键登录（演示环境为模拟身份） */
export async function loginWithWechat() {
	const code = await getWxCode()
	return login(code, getMockId())
}

function authRequiredError(message) {
	const error = new ApiError(1002, message, 401)
	error.silent = true
	return error
}

/** 拉取当前用户并更新缓存 */
export async function fetchMe() {
	const user = await request({ url: '/users/me' })
	saveUser(user)
	return user
}

/**
 * 确保已登录：有本地会话直接用，否则回登录页
 * 页面统一 catch 后用 showError 提示；带 silent 的错误不会弹 toast
 */
export async function ensureLogin() {
	if (!getAccessToken()) {
		redirectToLogin()
		throw authRequiredError('请先登录')
	}
	const cached = getCachedUser()
	if (cached) return cached
	try {
		return await fetchMe()
	} catch (error) {
		if (error.code !== 1002) throw error
		redirectToLogin()
		throw authRequiredError('登录已过期')
	}
}

/** 退出登录：清会话并回登录页；门店选择和结算草稿保留 */
export function logout() {
	clearSession()
	redirectToLogin()
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
