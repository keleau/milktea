/**
 * 门店 / 会员 / 优惠券静态数据
 */

/** 门店与会员信息 */
export const STORE = {
	name: '四猫茶学园·星悦广场店',
	slogan: '今天的奶茶，由猫评分',
	user: { level: 'V2 银牌猫评员', coupons: 2, balance: 8.5, points: 320 }
}

/** 可领优惠券（演示数据） */
export const COUPONS = [
	{ id: 1, cut: 3, min: 15, title: '新猫见面礼', desc: '满15减3' },
	{ id: 2, cut: 5, min: 25, title: '周二会员日', desc: '满25减5' }
]
