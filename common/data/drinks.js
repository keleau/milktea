/**
 * 饮品与产品线静态数据
 * 饮品图优先用本地 560×560 资源，未拍摄的 9~12 号走远程生成图
 */
import { genImg } from '@/common/utils/image'

/**
 * @typedef {Object} DrinkLine
 * @property {string} id 产品线标识
 * @property {string} name 名称
 * @property {string} tag 短标签
 * @property {string} en 英文名
 * @property {string} desc 一句话描述
 * @property {string} color 主题色
 * @property {string} bg 浅色底
 */

/**
 * @typedef {Object} Drink
 * @property {number} id 饮品 ID
 * @property {string} line 所属产品线
 * @property {string} name 名称
 * @property {number} price 现价
 * @property {number} [orig] 原价（有值即参与会员价）
 * @property {number} paws 猫评分（1~5）
 * @property {boolean} hot 是否招牌
 * @property {boolean} isNew 是否新品
 * @property {string} desc 描述
 * @property {string} img 图片地址
 */

/** @type {DrinkLine[]} 四条产品线 */
export const LINES = [
	{ id: 'buchi', name: '布奇·醇厚系列', tag: '醇厚', en: "Buchi's Rich Collection", desc: '厚乳打底，浓郁治愈', color: '#8B5E3C', bg: '#F3EAE0' },
	{ id: 'sakamoto', name: '坂本·纯选系列', tag: '纯选', en: "Sakamoto's Pure Selection", desc: '原叶直萃，低糖轻负担', color: '#5A5A5A', bg: '#EFEFEF' },
	{ id: 'tom', name: '汤姆·甜心角落', tag: '甜心', en: "Tom's Sweet Corner", desc: '布丁芋泥，甜蜜暴击', color: '#D9737F', bg: '#FAEBED' },
	{ id: 'tama', name: '玉·清爽系列', tag: '清爽', en: "Tama's Refresh Line", desc: '冷萃鲜果，一口回魂', color: '#5C9E6E', bg: '#EAF3EC' }
]

/** 本地饮品图路径 */
const localImg = (id) => `/static/resource/images/drink_${id}.jpg`

/** @type {Drink[]} 十二款饮品（四线各 3 款） */
export const DRINKS = [
	// 布奇·醇厚
	{ id: 1, line: 'buchi', name: '黑糖波波厚奶茶', price: 14, orig: 17, paws: 5, hot: true, isNew: false, desc: '手熬黑糖挂壁，波波Q弹，厚乳香浓', img: localImg(1) },
	{ id: 2, line: 'buchi', name: '经典原味厚乳奶茶', price: 12, orig: 15, paws: 4, hot: true, isNew: false, desc: '锡兰红茶配厚牛乳，经典不翻车', img: localImg(2) },
	{ id: 3, line: 'buchi', name: '提拉米苏厚乳茶', price: 16, paws: 4, hot: false, isNew: true, desc: '可可粉轻撒，奶油顶配厚乳茶底', img: localImg(3) },
	// 坂本·纯选
	{ id: 4, line: 'sakamoto', name: '茉莉初雪轻乳茶', price: 12, paws: 4, hot: false, isNew: false, desc: '茉莉雪芽打底，轻薄乳盖', img: localImg(4) },
	{ id: 5, line: 'sakamoto', name: '四季春原叶纯茶', price: 9, paws: 4, hot: false, isNew: false, desc: '原叶冷萃，零奶零糖也回甘', img: localImg(5) },
	{ id: 6, line: 'sakamoto', name: '轻乳乌龙茶', price: 11, paws: 3, hot: false, isNew: true, desc: '三分甜轻负担，乌龙回香', img: localImg(6) },
	// 汤姆·甜心角落
	{ id: 7, line: 'tom', name: '布丁可可萌宠杯', price: 15, orig: 18, paws: 4, hot: true, isNew: false, desc: '整颗焦糖布丁沉底，可可香浓', img: localImg(7) },
	{ id: 8, line: 'tom', name: '芋泥啵啵鲜奶茶', price: 15, paws: 5, hot: false, isNew: false, desc: '手捣芋泥厚挂壁，芋圆软糯', img: localImg(8) },
	{ id: 9, line: 'tom', name: '草莓芝士奶盖', price: 16, paws: 4, hot: false, isNew: true, desc: '鲜草莓果肉，咸香芝士奶盖', img: genImg('one cup of strawberry milk tea with pink strawberry puree and white cheese foam top') },
	// 玉·清爽
	{ id: 10, line: 'tama', name: '满杯百香果茶', price: 12, paws: 5, hot: false, isNew: false, desc: '整颗百香果，冰爽维C满格', img: genImg('one cup of passion fruit tea with visible seeds and orange yellow color, full of ice') },
	{ id: 11, line: 'tama', name: '手打香水柠檬茶', price: 11, paws: 5, hot: false, isNew: false, desc: '现捶香水柠檬，酸爽解腻', img: genImg('one cup of smashed lemon green tea with fresh lemon slices, bright green yellow color') },
	{ id: 12, line: 'tama', name: '冷萃乌龙青提茶', price: 14, paws: 4, hot: false, isNew: true, desc: '冷萃乌龙配青提，低糖果香', img: genImg('one cup of cold brew oolong tea with green grapes, light jade color with fruit pieces') }
]

/** 冰度选项 */
export const ICE_OPTS = ['正常冰', '少冰', '去冰', '热饮']

/** 糖度选项 */
export const SUGAR_OPTS = ['全糖', '七分糖', '五分糖', '三分糖', '不加糖']

/** 小料选项 */
export const TOPPINGS = [
	{ name: '珍珠', price: 1 },
	{ name: '椰果', price: 1 },
	{ name: '布丁', price: 2 },
	{ name: '芋圆', price: 2 },
	{ name: '芝士奶盖', price: 3 }
]
