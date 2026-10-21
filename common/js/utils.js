/**
 * 全局请求封装（保持原有的回调式用法）
 * 业务约定：接口返回 code === 10000 视为成功，走 option.success；否则走 option.fail
 */
class Utils {
	constructor() {
		// 后端接口基础地址
		this.baseUrl = 'http://159.75.169.224:7300/pz'
	}

	// 微信登录：用 code 换 token 并存入本地缓存
	getUserInfo() {
		uni.login({
			success: (res) => {
				this.request({
					url: '/auth/wxLogin',
					data: {
						code: res.code
					},
					success: (res) => {
						// 登录成功后把 token 存到本地（兼容后端不同字段名）
						const d = res.data || {}
						const token = d.token || d.user_token || (d.userInfo && d.userInfo.token)
						if (token) {
							uni.setStorageSync('token', token)
						}
					}
				})
			}
		})
	}

	// 统一请求：option = { url, data, header, method, showLoading, success, fail }
	request(option = {
		showLoading: false
	}) {
		// 判断 url 是否存在
		if (!option.url) {
			return false
		}
		// 判断是否需要显示 loading
		if (option.showLoading) {
			this.showLoading()
		}
		uni.request({
			url: this.baseUrl + option.url,
			data: option.data ? option.data : {},
			header: option.header ? option.header : {},
			method: option.method ? option.method : 'GET',
			success: (res) => {
				uni.hideLoading()
				if (res.data.code !== 10000) {
					// 业务失败
					if (option.fail && typeof option.fail == 'function') {
						option.fail(res)
					}
				} else {
					// 业务成功
					if (option.success && typeof option.success == 'function') {
						option.success(res.data)
					}
				}
			},
			fail: (res) => {
				// 网络层失败：仅停止 loading，提示交由调用方处理
				uni.hideLoading()
			}
		})
	}

	// 显示加载框（通过 storage 标记防止重复弹出）
	showLoading() {
		const isShowLoading = uni.getStorageSync('isShowLoading')
		if (isShowLoading) {
			uni.hideLoading()
			uni.setStorageSync('isShowLoading', false)
		}
		uni.showLoading({
			title: '加载中',
			complete: () => {
				uni.setStorageSync('isShowLoading', true)
			},
			fail: () => {
				uni.setStorageSync('isShowLoading', false)
			}
		})
		uni.setStorageSync('isShowLoading', true)
	}
}

export default new Utils()
