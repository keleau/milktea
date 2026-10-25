/** 从「小程序码」的 path 里取 scene：pages/menu/index?scene=MILKTEA%3A1%3AA01 */
function sceneFromPath(path) {
	const match = String(path || '').match(/[?&]scene=([^&#]+)/)
	if (!match) return ''
	try {
		return decodeURIComponent(match[1]).trim()
	} catch (error) {
		return match[1].trim()
	}
}

/** 小程序扫码封装：取消时由调用方静默处理 */
export function scanCode() {
	return new Promise((resolve, reject) => {
		uni.scanCode({
			// 不限制 scanType：小程序码与普通二维码都要能扫
			success: (res) => {
				// 扫普通二维码返回 result；扫本店小程序码返回 path（带 scene 参数）
				const value = sceneFromPath(res.path) || String(res.result || '').trim()
				if (value) resolve(value)
				else reject(new Error('empty scan result'))
			},
			fail: (error) => reject(error || new Error('scan failed'))
		})
	})
}

export function isScanCancel(error) {
	return String((error && error.errMsg) || '').includes('cancel')
}
