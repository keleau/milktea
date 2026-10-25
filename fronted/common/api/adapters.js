/**
 * 后端字段 → 页面视图字段
 * 页面仍用原来的 drink.img / coupon.min / state_text 等名字，避免大改模板
 */

export const ORDER_STATE_TEXT = {
	pending_pay: '待支付',
	making: '制作中',
	completed: '已完成',
	cancelled: '已取消'
}

export const STORE_STATUS_TEXT = {
	open: '营业中',
	resting: '即将休息',
	closed: '已打烊'
}

export const money = (value) => Number(value || 0)

/** 金额保留两位，去掉浮点误差 */
export const fixed = (value) => Number(Number(value || 0).toFixed(2))

/** 小程序包内已有的图片：后端静态图与它们同名，可直接用本地文件 */
const LOCAL_IMAGE_FILES = new Set([
	'avatar.jpg',
	...Array.from({ length: 12 }, (_, index) => `drink_${index + 1}.jpg`)
])

/**
 * 微信小程序 <image> 不再接受 http:// 地址。
 * 后端静态图与本地资源同名时改用本地文件；其余 HTTP 图片在微信端返回占位值。
 */
export function resolveImage(url, fallback = '') {
	const value = String(url || '')
	if (!value) return fallback
	// HTTPS 图片小程序可以直接加载，保留后端真实地址
	if (value.startsWith('https://')) return value
	// #ifdef MP-WEIXIN
	const name = value.split(/[?#]/)[0].split('/').pop()
	if (LOCAL_IMAGE_FILES.has(name)) return `/static/resource/images/${name}`
	if (value.startsWith('http://')) return fallback
	// #endif
	return value
}

/** 距离：米 → 205m / 1.2km */
export function formatDistance(meters) {
	const value = Number(meters) || 0
	return value >= 1000 ? `${(value / 1000).toFixed(1)}km` : `${value}m`
}

/** 毫秒时间戳 → YYYY-MM-DD HH:mm */
export function formatTime(ms) {
	if (!ms) return ''
	const date = new Date(ms)
	const pad = (n) => String(n).padStart(2, '0')
	return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

/** 商品：ProductOut → 视图 drink */
export function toDrink(product) {
	if (!product) return null
	return {
		id: product.id,
		line: product.line_id,
		name: product.name,
		price: money(product.price),
		orig: product.orig_price === null || product.orig_price === undefined ? null : money(product.orig_price),
		paws: product.paws || 0,
		hot: !!product.is_hot,
		isNew: !!product.is_new,
		desc: product.desc || '',
		img: resolveImage(product.image),
		stock: product.stock || 0,
		onSale: product.on_sale !== false
	}
}

/** 产品线：后端字段与视图一致，补齐默认值 */
export function toLine(line) {
	return { ...line }
}

/** 门店：补视图用的距离文案与状态文案 */
export function toStore(store) {
	if (!store) return null
	return {
		...store,
		dist: formatDistance(store.distance),
		statusText: STORE_STATUS_TEXT[store.status] || store.status,
		makingCups: store.making_cups || 0,
		packFee: money(store.pack_fee),
		deliveryFee: money(store.delivery_fee)
	}
}

/** 优惠券 → 视图（coupon-ticket 用 cut/min/title/desc） */
export function toCoupon(coupon) {
	if (!coupon) return null
	return {
		...coupon,
		cut: money(coupon.cut),
		min: money(coupon.min_amount),
		expireText: formatTime(coupon.expire_at)
	}
}

/** 券模板 → 视图 */
export function toCouponTemplate(template) {
	if (!template) return null
	return {
		...template,
		cut: money(template.cut),
		min: money(template.min_amount),
		claimed: !!template.claimed
	}
}

/** 用户等级 "V2 银牌猫评员" → 徽章 + 文案 */
export function levelParts(levelText) {
	const text = levelText || ''
	const index = text.indexOf(' ')
	if (index < 0) return { levelCode: text, levelName: '' }
	return {
		levelCode: text.slice(0, index),
		levelName: text.slice(index + 1)
	}
}

/** 订单列表卡片摘要 */
export function toOrderSummary(order) {
	const first = order.items && order.items[0]
	const count = (order.items || []).reduce((sum, item) => sum + item.count, 0)
	return {
		...order,
		shortNo: (order.out_trade_no || '').slice(-8),
		img: first ? resolveImage(first.image) : '',
		name: first ? first.name : '',
		spec: first ? [first.ice, first.sugar, first.topping_names].filter(Boolean).join(' / ') : '',
		count,
		stateText: order.state_text || ORDER_STATE_TEXT[order.state] || order.state,
		modeText: order.mode_text,
		price: money(order.total),
		createText: formatTime(order.create_time)
	}
}

/** 订单详情补充格式化字段 */
export function toOrder(order) {
	return {
		...toOrderSummary(order),
		items: (order.items || []).map((item) => ({ ...item, image: resolveImage(item.image) })),
		createText: formatTime(order.create_time),
		payText: formatTime(order.pay_time),
		finishText: formatTime(order.finish_time),
		subtotalText: money(order.subtotal),
		packFee: money(order.pack_fee),
		couponCut: money(order.coupon_cut),
		total: money(order.total)
	}
}

/** 购物车/草稿 → 下单 items（只传 ID 和规格，价格由后端算） */
export function toOrderItems(items) {
	return (items || []).map((item) => ({
		product_id: item.product ? item.product.id : item.product_id,
		ice: item.ice,
		sugar: item.sugar,
		topping_ids: (item.toppings || []).map((topping) => topping.id),
		count: item.count
	}))
}
