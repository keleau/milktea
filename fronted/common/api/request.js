/**
 * uni.request 封装
 * - 统一拼 API_BASE_URL + /api/v1
 * - 自动带 Bearer，拆 { code, message, data }，页面直接拿 data
 * - 401/1002 自动刷新 token 并重放一次；并发 401 共用一个刷新 Promise
 */
import { API_BASE_URL, API_PREFIX, LOGIN_PAGE, REQUEST_TIMEOUT } from '@/common/config'
import { clearSession, getAccessToken, getRefreshToken, saveTokens } from './token'

export class ApiError extends Error {
	constructor(code, message, statusCode = 0) {
		super(message)
		this.name = 'ApiError'
		this.code = code
		this.statusCode = statusCode
	}
}

let redirecting = false

/** 未登录/登录失效统一回登录页；已在登录页或正在跳转时不重复触发 */
export function redirectToLogin() {
	if (redirecting) return
	const pages = getCurrentPages()
	const route = pages.length ? pages[pages.length - 1].route : ''
	if (route === 'pages/login/index') return
	redirecting = true
	uni.reLaunch({
		url: LOGIN_PAGE,
		complete: () => {
			setTimeout(() => {
				redirecting = false
			}, 800)
		}
	})
}

/** 拼接 query，空值不传（后端 state 等 Literal 参数不能收空字符串） */
function encodeQuery(query) {
	if (!query) return ''
	const parts = []
	Object.keys(query).forEach((key) => {
		const value = query[key]
		if (value === undefined || value === null || value === '') return
		parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
	})
	return parts.join('&')
}

export function buildUrl(path, query) {
	const base = API_BASE_URL.replace(/\/+$/, '')
	const suffix = path.startsWith('/') ? path : `/${path}`
	const qs = encodeQuery(query)
	return `${base}${API_PREFIX}${suffix}${qs ? `?${qs}` : ''}`
}

/** 原始请求，只负责拿到 HTTP 响应，不处理业务码 */
function send({ url, method = 'GET', query, data, header = {}, auth = true, timeout = REQUEST_TIMEOUT }) {
	return new Promise((resolve, reject) => {
		const token = auth ? getAccessToken() : ''
		const finalHeader = { 'Content-Type': 'application/json', ...header }
		if (token) finalHeader.Authorization = `Bearer ${token}`
		uni.request({
			url: buildUrl(url, query),
			method,
			data,
			header: finalHeader,
			timeout,
			success: resolve,
			fail: () => reject(new ApiError(-1, '网络请求失败，请检查后端是否启动', 0))
		})
	})
}

/** 解包统一响应，非 0 业务码抛 ApiError */
function unwrap(res) {
	const body = res.data
	if (res.statusCode >= 200 && res.statusCode < 300 && body && body.code === 0) {
		return body.data
	}
	const code = body && typeof body.code === 'number'
		? body.code
		: res.statusCode === 401 ? 1002 : -1
	const message = body && body.message
		? body.message
		: `请求失败（HTTP ${res.statusCode}）`
	throw new ApiError(code, message, res.statusCode)
}

let refreshPromise = null

/** 刷新 token；失败返回 false，不抛异常 */
function refreshTokens() {
	if (refreshPromise) return refreshPromise
	const refreshToken = getRefreshToken()
	if (!refreshToken) return Promise.resolve(false)

	refreshPromise = new Promise((resolve) => {
		uni.request({
			url: buildUrl('/auth/refresh'),
			method: 'POST',
			data: { refresh_token: refreshToken },
			header: { 'Content-Type': 'application/json' },
			timeout: REQUEST_TIMEOUT,
			success: (res) => {
				const body = res.data
				if (
					res.statusCode >= 200 && res.statusCode < 300 &&
					body && body.code === 0 && body.data && body.data.access_token
				) {
					saveTokens(body.data)
					resolve(true)
				} else {
					resolve(false)
				}
			},
			fail: () => resolve(false)
		})
	}).finally(() => {
		refreshPromise = null
	})
	return refreshPromise
}

/**
 * 业务请求
 * @param {{url: string, method?: string, query?: Object, data?: Object, header?: Object, auth?: boolean, retried?: boolean, timeout?: number}} options
 * @returns {Promise<*>} 后端 data
 */
export async function request(options) {
	let res = await send(options)

	const needAuth = res.statusCode === 401 || (res.data && res.data.code === 1002)
	if (!needAuth) return unwrap(res)

	if (options.auth !== false && !options.retried && (await refreshTokens())) {
		return request({ ...options, retried: true })
	}

	const error = new ApiError(
		(res.data && res.data.code) || 1002,
		(res.data && res.data.message) || '登录状态已过期，请重新登录',
		res.statusCode || 401
	)
	if (options.auth !== false) {
		clearSession()
		redirectToLogin()
		// 已统一跳转登录页，页面不必再弹错误提示
		error.silent = true
	}
	throw error
}

/** 上传文件（头像），逻辑与 request 一致，只是换用 uni.uploadFile */
export function upload(path, filePath, name = 'file') {
	const attempt = (retried) => new Promise((resolve, reject) => {
		const token = getAccessToken()
		uni.uploadFile({
			url: buildUrl(path),
			filePath,
			name,
			header: token ? { Authorization: `Bearer ${token}` } : {},
			success: async (res) => {
				let body = null
				try {
					body = typeof res.data === 'string' ? JSON.parse(res.data) : res.data
				} catch (error) {
					body = null
				}
				if (res.statusCode >= 200 && res.statusCode < 300 && body && body.code === 0) {
					resolve(body.data)
					return
				}
				const needAuth = res.statusCode === 401 || (body && body.code === 1002)
				if (needAuth && !retried && (await refreshTokens())) {
					attempt(true).then(resolve, reject)
					return
				}
				const error = new ApiError(
					body && typeof body.code === 'number' ? body.code : -1,
					(body && body.message) || `上传失败（HTTP ${res.statusCode}）`,
					res.statusCode
				)
				if (needAuth) {
					clearSession()
					redirectToLogin()
					error.silent = true
				}
				reject(error)
			},
			fail: () => reject(new ApiError(-1, '网络请求失败，请检查后端是否启动', 0))
		})
	})
	return attempt(false)
}

/** 页面统一错误提示 */
export function showError(error) {
	if (error && error.silent) return
	if (error && error.code === 1002) {
		uni.showToast({ title: '登录已过期，请重新登录', icon: 'none' })
		return
	}
	uni.showToast({
		title: (error && error.message) || '请求失败',
		icon: 'none',
		duration: 2200
	})
}
