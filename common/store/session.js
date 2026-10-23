/**
 * 页面间临时状态（不落盘）
 * 替代散落在 globalData 上的隐式约定，读写入口统一，避免字段名拼错
 */

/** @type {Object|null} 结算草稿：{ drink, ice, sugar, toppings, count } */
let checkoutDraft = null

/** @type {string} 订单页待应用的筛选状态 */
let ordersFilter = ''

/** 写入结算草稿 */
export const setCheckoutDraft = (draft) => {
	checkoutDraft = draft
}

/** 读取结算草稿 */
export const getCheckoutDraft = () => checkoutDraft

/** 清空结算草稿（支付成功后调用） */
export const clearCheckoutDraft = () => {
	checkoutDraft = null
}

/** 设置订单页筛选（“我的”页跳转前写入） */
export const setOrdersFilter = (filter) => {
	ordersFilter = filter
}

/** 读取并清空订单页筛选（订单页 onShow 消费一次） */
export const takeOrdersFilter = () => {
	const filter = ordersFilter
	ordersFilter = ''
	return filter
}
