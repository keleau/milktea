/** AI 点单助手 */
import { request } from './request'

/** 大模型推理 + 工具调用耗时高于普通接口，单独放宽超时 */
const AI_TIMEOUT = 60000

export function chatWithAi(message, storeId, tableNo = null) {
	return request({
		url: '/ai/chat',
		method: 'POST',
		data: { message, store_id: storeId || null, table_no: tableNo || null },
		timeout: AI_TIMEOUT
	})
}

export function getAiHistory() {
	return request({ url: '/ai/history' })
}

export function clearAiSession() {
	return request({ url: '/ai/session', method: 'DELETE' })
}
