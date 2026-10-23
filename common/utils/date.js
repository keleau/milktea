/**
 * 时间格式化工具（替代原先挂在 Date.prototype 上的 VP_FORMAT，避免污染原生原型）
 */

const pad = (n) => String(n).padStart(2, '0')

/**
 * 格式化时间
 * @param {number|string|Date} value 时间戳 / 时间字符串 / Date
 * @param {string} template 支持 YYYY MM dd hh mm ss
 * @returns {string}
 */
export function formatTime(value, template = 'YYYY-MM-DD hh:mm') {
	const date = value instanceof Date ? value : new Date(value)
	if (Number.isNaN(date.getTime())) return ''

	const map = {
		YYYY: date.getFullYear(),
		MM: pad(date.getMonth() + 1),
		dd: pad(date.getDate()),
		hh: pad(date.getHours()),
		mm: pad(date.getMinutes()),
		ss: pad(date.getSeconds())
	}

	return template.replace(/YYYY|MM|dd|hh|mm|ss/g, (key) => map[key])
}
