/**
 * 本地缓存读写封装
 * uni.storage 在数据损坏/超限时会抛异常，统一兜底，避免页面白屏
 */

/**
 * 读取缓存
 * @param {string} key 缓存键
 * @param {*} fallback 读取失败或为空时的默认值
 * @returns {*}
 */
export function readStorage(key, fallback = null) {
	try {
		const value = uni.getStorageSync(key)
		return value === '' || value === null || value === undefined ? fallback : value
	} catch (error) {
		console.warn('[storage] 读取失败:', key, error)
		return fallback
	}
}

/**
 * 写入缓存
 * @param {string} key 缓存键
 * @param {*} value 任意可序列化值
 * @returns {boolean} 是否写入成功
 */
export function writeStorage(key, value) {
	try {
		uni.setStorageSync(key, value)
		return true
	} catch (error) {
		console.warn('[storage] 写入失败:', key, error)
		return false
	}
}

/**
 * 删除缓存
 * @param {string} key 缓存键
 * @returns {boolean} 是否删除成功
 */
export function removeStorage(key) {
	try {
		uni.removeStorageSync(key)
		return true
	} catch (error) {
		console.warn('[storage] 删除失败:', key, error)
		return false
	}
}
