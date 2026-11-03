/** 订单/购物车共用的规格与金额格式化 */

export function formatItemSpec(item, separator = ' / ') {
	if (!item) return ''
	const toppings = item.topping_names
		? [item.topping_names]
		: (item.toppings || []).map(t => t.name).filter(Boolean)
	return [item.ice, item.sugar, ...toppings].filter(Boolean).join(separator)
}

/** 购物车/草稿行金额：单价（含小料）× 数量 */
export function lineAmount(item) {
	if (!item) return 0
	const base = Number(item.product ? item.product.price : item.unit_price || 0)
	const topping = (item.toppings || []).reduce((sum, t) => sum + Number(t.price || 0), 0)
	return Number(((base + topping) * Number(item.count || 0)).toFixed(2))
}
