import { ref } from 'vue'
import { readStorage, writeStorage } from '@/common/utils/storage'

const KEY = 'milk_ai_float_hidden'

/** 首页/点单页共享：隐藏后两页同步，收成小 AI 气泡 */
export const aiFloatHidden = ref(readStorage(KEY, '') === '1')

export function setAiFloatHidden(hidden) {
	aiFloatHidden.value = !!hidden
	writeStorage(KEY, hidden ? '1' : '')
}
