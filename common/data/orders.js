/**
 * 订单数据层：本地 storage 持久化（无后端）
 */
import { readStorage, writeStorage } from '@/common/utils/storage'
import { DRINKS } from './drinks'

/** 订单缓存键 */
const ORDER_KEY = 'milk_orders'

/**
 * @typedef {Object} Order
 * @property {string} out_trade_no 订单号
 * @property {string} state 状态：待支付 / 制作中 / 已完成 / 已取消
 * @property {number} drink_id 饮品 ID
 * @property {string} name 饮品名
 * @property {string} img 饮品图
 * @property {string} line 产品线
 * @property {string} spec 规格摘要（冰度 / 糖度 / 小料）
 * @property {number} count 数量
 * @property {string} mode 取餐方式
 * @property {string} pick_code 取餐码
 * @property {number} price 实付金额
 * @property {number} create_time 下单时间戳
 */

/**
 * 读取订单列表
 * 老订单存的图片地址可能已失效，这里按 drink_id 回填当前饮品图
 * @returns {Order[]}
 */
export function getOrders() {
	const list = readStorage(ORDER_KEY, [])
	if (!Array.isArray(list)) return []

	return list.map((order) => {
		const drink = DRINKS.find((item) => item.id === order.drink_id)
		return drink ? { ...order, img: drink.img } : order
	})
}

/**
 * 按订单号查单
 * @param {string} orderNo
 * @returns {Order|null}
 */
export function getOrder(orderNo) {
	return getOrders().find((order) => order.out_trade_no === orderNo) || null
}

/**
 * 生成订单号
 * @returns {string}
 */
export function makeOrderNo() {
	return `CAT${Date.now()}${Math.floor(Math.random() * 90 + 10)}`
}

/**
 * 保存新订单
 * @param {{drink: import('./drinks').Drink, ice: string, sugar: string, toppings: Array<{name: string, price: number}>, count: number, mode?: string, coupon?: number, packFee?: number}} payload
 * @returns {Order} 已保存的订单
 */
export function saveOrder({ drink, ice, sugar, toppings = [], count, mode = '自取', coupon = 0, packFee }) {
	const toppingPrice = toppings.reduce((sum, item) => sum + item.price, 0)
	const fee = packFee != null ? packFee : mode === '自取' ? 1 : 4
	const total = Math.max(0, (drink.price + toppingPrice) * count + fee - coupon)

	/** @type {Order} */
	const order = {
		out_trade_no: makeOrderNo(),
		state: '待支付',
		drink_id: drink.id,
		name: drink.name,
		img: drink.img,
		line: drink.line,
		spec: ice + ' / ' + sugar + (toppings.length ? ' / ' + toppings.map((item) => item.name).join('+') : ''),
		count,
		mode,
		pick_code: `${Math.floor(Math.random() * 90 + 10)}${String(Date.now() % 1000).padStart(3, '0')}`,
		price: total,
		create_time: Date.now()
	}

	const list = getOrders()
	list.unshift(order)
	writeStorage(ORDER_KEY, list)
	return order
}

/**
 * 更新订单状态
 * @param {string} orderNo
 * @param {Order['state']} state
 */
export function updateOrderState(orderNo, state) {
	const list = getOrders().map((order) => (order.out_trade_no === orderNo ? { ...order, state } : order))
	writeStorage(ORDER_KEY, list)
}

/**
 * 各状态订单数（“我的”页角标）
 * @returns {Record<'待支付'|'制作中'|'已完成'|'已取消', number>}
 */
export function countByState() {
	const counter = { 待支付: 0, 制作中: 0, 已完成: 0, 已取消: 0 }
	getOrders().forEach((order) => {
		if (counter[order.state] !== undefined) counter[order.state] += 1
	})
	return counter
}
