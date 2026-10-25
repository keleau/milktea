/** 小程序扫码封装：取消时由调用方静默处理 */
export function scanCode() {
	return new Promise((resolve, reject) => {
		uni.scanCode({
			scanType: ['qrCode'],
			success: (res) => {
				const value = String(res.result || '').trim()
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
