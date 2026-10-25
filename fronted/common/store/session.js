/**
 * 页面间临时状态（不落盘）
 * 替代散落在 globalData 上的隐式约定，读写入口统一，避免字段名拼错
 */

/** @type {Object|null} 结算草稿：{ storeId, mode, addressId?, items: [{ product, ice, sugar, toppings, count }] } */
let checkoutDraft = null

/** @type {string|null} 订单页待应用的筛选状态，null 表示本次进入不改变筛选 */
let ordersFilter = null

/** @type {number|null} 地址页选中后回传给结算页的地址 ID */
let selectedAddressId = null

/** 写入结算草稿 */
export const setCheckoutDraft = (draft) => {
	checkoutDraft = draft
}

/** 读取结算草稿 */
export const getCheckoutDraft = () => checkoutDraft

/** 清空结算草稿（创建订单成功后调用） */
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
	ordersFilter = null
	return filter
}

/** 地址页点选某条地址后写入 */
export const setSelectedAddressId = (id) => {
	selectedAddressId = id
}

/** 结算页读取并清空选中的地址 ID */
export const takeSelectedAddressId = () => {
	const id = selectedAddressId
	selectedAddressId = null
	return id
}
