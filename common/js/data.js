/**
 * 四猫茶学园 · 本地数据层
 * 无后端依赖：产品线/饮品/定制选项为静态数据，饮品图为远程生成图（不占包体），
 * 订单读写走 uni.storage（key: milk_orders）。
 */

// 远程饮品图生成（Image Guidelines 唯一允许的图片源，URL 固定可被 CDN 缓存）
const genImg = (prompt) =>
	'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=' +
	encodeURIComponent('Commercial milk tea product photography, ' + prompt + ', single takeaway plastic cup, warm cream seamless background, soft studio lighting, centered composition, appetizing, realistic, high resolution') +
	'&image_size=square'

// 远程 Banner 场景图生成（16:9 横幅，满版海报轮播用）
const genBanner = (prompt) =>
	'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=' +
	encodeURIComponent('Commercial milk tea advertisement scene photography, ' + prompt + ', no text, no letters, soft studio lighting, realistic, high resolution') +
	'&image_size=landscape_16_9'

export { genBanner }

// ===== 四条产品线（猫评审人设，仅文字+色标，无角色插画） =====
export const LINES = [
	{ id: 'buchi', name: '布奇·醇厚系列', tag: '醇厚', en: "Buchi's Rich Collection", desc: '厚乳打底，浓郁治愈', color: '#8B5E3C', bg: '#F3EAE0' },
	{ id: 'sakamoto', name: '坂本·纯选系列', tag: '纯选', en: "Sakamoto's Pure Selection", desc: '原叶直萃，低糖轻负担', color: '#5A5A5A', bg: '#EFEFEF' },
	{ id: 'tom', name: '汤姆·甜心角落', tag: '甜心', en: "Tom's Sweet Corner", desc: '布丁芋泥，甜蜜暴击', color: '#D9737F', bg: '#FAEBED' },
	{ id: 'tama', name: '玉·清爽系列', tag: '清爽', en: "Tama's Refresh Line", desc: '冷萃鲜果，一口回魂', color: '#5C9E6E', bg: '#EAF3EC' }
]

// ===== 饮品（四线各 3 款） =====
export const DRINKS = [
	// 布奇·醇厚
	{ id: 1, line: 'buchi', name: '黑糖波波厚奶茶', price: 14, paws: 5, hot: true, isNew: false, desc: '手熬黑糖挂壁，波波Q弹，厚乳香浓', img: genImg('one cup of brown sugar boba milk tea with dark syrup streaks and tapioca pearls at the bottom') },
	{ id: 2, line: 'buchi', name: '经典原味厚乳奶茶', price: 12, paws: 5, hot: true, isNew: false, desc: '锡兰红茶配厚牛乳，经典不翻车', img: genImg('one cup of classic hong kong style milk tea, silky tan brown color') },
	{ id: 3, line: 'buchi', name: '提拉米苏厚乳茶', price: 16, paws: 4, hot: false, isNew: true, desc: '可可粉轻撒，奶油顶配厚乳茶底', img: genImg('one cup of tiramisu layered milk tea topped with cocoa powder and cream foam') },
	// 坂本·纯选
	{ id: 4, line: 'sakamoto', name: '茉莉初雪轻乳茶', price: 12, paws: 4, hot: false, isNew: false, desc: '茉莉雪芽打底，轻薄乳盖', img: genImg('one cup of jasmine green milk tea with light milk foam, pale golden tea color') },
	{ id: 5, line: 'sakamoto', name: '四季春原叶纯茶', price: 9, paws: 4, hot: false, isNew: false, desc: '原叶冷萃，零奶零糖也回甘', img: genImg('one cup of amber oolong tea, clear brewed tea with ice cubes') },
	{ id: 6, line: 'sakamoto', name: '轻乳乌龙茶', price: 11, paws: 3, hot: false, isNew: true, desc: '三分甜轻负担，乌龙回香', img: genImg('one cup of oolong milk tea, light beige color with gentle tea and milk layers') },
	// 汤姆·甜心角落
	{ id: 7, line: 'tom', name: '布丁可可萌宠杯', price: 15, paws: 5, hot: false, isNew: false, desc: '整颗焦糖布丁沉底，可可香浓', img: genImg('one cup of chocolate milk with caramel pudding at the bottom, creamy brown layers') },
	{ id: 8, line: 'tom', name: '芋泥啵啵鲜奶茶', price: 15, paws: 5, hot: false, isNew: false, desc: '手捣芋泥厚挂壁，芋圆软糯', img: genImg('one cup of purple taro milk tea with taro paste smears and chewy taro balls') },
	{ id: 9, line: 'tom', name: '草莓芝士奶盖', price: 16, paws: 4, hot: false, isNew: true, desc: '鲜草莓果肉，咸香芝士奶盖', img: genImg('one cup of strawberry milk tea with pink strawberry puree and white cheese foam top') },
	// 玉·清爽
	{ id: 10, line: 'tama', name: '满杯百香果茶', price: 12, paws: 5, hot: false, isNew: false, desc: '整颗百香果，冰爽维C满格', img: genImg('one cup of passion fruit tea with visible seeds and orange yellow color, full of ice') },
	{ id: 11, line: 'tama', name: '手打香水柠檬茶', price: 11, paws: 5, hot: false, isNew: false, desc: '现捶香水柠檬，酸爽解腻', img: genImg('one cup of smashed lemon green tea with fresh lemon slices, bright green yellow color') },
	{ id: 12, line: 'tama', name: '冷萃乌龙青提茶', price: 14, paws: 4, hot: false, isNew: true, desc: '冷萃乌龙配青提，低糖果香', img: genImg('one cup of cold brew oolong tea with green grapes, light jade color with fruit pieces') }
]

// ===== 定制选项 =====
export const ICE_OPTS = ['正常冰', '少冰', '去冰', '热饮']
export const SUGAR_OPTS = ['全糖', '七分糖', '五分糖', '三分糖', '不加糖']
export const TOPPINGS = [
	{ name: '珍珠', price: 1 },
	{ name: '椰果', price: 1 },
	{ name: '布丁', price: 2 },
	{ name: '芋圆', price: 2 },
	{ name: '芝士奶盖', price: 3 }
]

// ===== 门店/会员信息 =====
export const STORE = {
	name: '四猫茶学园·星悦广场店',
	slogan: '今天的奶茶，由猫评分',
	user: { level: 'V2 银牌猫评员', coupons: 2, balance: 8.5, points: 320 }
}

// ===== 订单（本地 storage 持久化） =====
const ORDER_KEY = 'milk_orders'

export function getOrders() {
	return uni.getStorageSync(ORDER_KEY) || []
}

export function getOrder(no) {
	return getOrders().find(o => o.out_trade_no === no) || null
}

export function makeOrderNo() {
	return 'CAT' + Date.now() + Math.floor(Math.random() * 90 + 10)
}

// 保存新订单，成功返回订单号
export function saveOrder({ drink, ice, sugar, toppings, count, mode, coupon }) {
	const tp = (toppings || []).reduce((s, t) => s + t.price, 0)
	const couponCut = coupon || 0
	const total = Math.max(0, (drink.price + tp) * count - couponCut)
	const order = {
		out_trade_no: makeOrderNo(),
		state: '待支付',
		drink_id: drink.id,
		name: drink.name,
		img: drink.img,
		line: drink.line,
		spec: ice + ' / ' + sugar + (toppings && toppings.length ? ' / ' + toppings.map(t => t.name).join('+') : ''),
		count,
		mode: mode || '自取',
		pick_code: Math.floor(Math.random() * 90 + 10).toString() + (Date.now() % 1000).toString().padStart(3, '0'),
		price: total,
		create_time: Date.now()
	}
	const list = getOrders()
	list.unshift(order)
	uni.setStorageSync(ORDER_KEY, list)
	return order
}

export function updateOrderState(no, state) {
	const list = getOrders().map(o => (o.out_trade_no === no ? { ...o, state } : o))
	uni.setStorageSync(ORDER_KEY, list)
}

// 各状态计数（“我的”页角标）
export function countByState() {
	const c = { 待支付: 0, 制作中: 0, 已完成: 0, 已取消: 0 }
	getOrders().forEach(o => { if (c[o.state] !== undefined) c[o.state]++ })
	return c
}

// 优惠券（演示数据）
export const COUPONS = [
	{ id: 1, cut: 3, min: 15, title: '新猫见面礼', desc: '满15减3' },
	{ id: 2, cut: 5, min: 25, title: '周二会员日', desc: '满25减5' }
]
