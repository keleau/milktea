/**
 * 用户资料辅助判断
 * 后端新注册用户的默认昵称是「猫友1234」，用它区分是否完成过资料填写
 */

const DEFAULT_NICKNAME = /^猫友\d{4}$/

/** 是否仍是系统默认昵称（未填写过资料） */
export function isDefaultNickname(nickname) {
	const name = String(nickname || '').trim()
	return !name || name === '猫友' || DEFAULT_NICKNAME.test(name)
}
