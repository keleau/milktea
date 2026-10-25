/** 桌号上下文：扫码点餐后跨页面保留 */
import { readStorage, removeStorage, writeStorage } from '@/common/utils/storage'

const KEY = 'milk_table_context'

export function getTableContext() {
	const ctx = readStorage(KEY, null)
	return ctx && ctx.tableNo ? ctx : null
}

export function saveTableContext(ctx) {
	writeStorage(KEY, ctx)
}

export function clearTableContext() {
	removeStorage(KEY)
}
