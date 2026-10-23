/**
 * 图片地址工厂
 * 本地图缺失时回退到远程生成图（风格锁定见 design.md 11.1）
 */

const PHOTO_STYLE =
	'Premium commercial beverage photography, warm cream seamless studio backdrop, soft diffused daylight from upper left, ' +
	'gentle contact shadow, low-saturation caramel brown cream and burnt orange palette, 85mm lens, shallow depth of field, ' +
	'minimal props, photorealistic, appetizing, ultra clean composition, no text, no letters, no logo, no people, no cartoon, no neon, '

/**
 * 单杯饮品图（1:1）
 * @param {string} prompt 主体描述
 * @returns {string}
 */
export const genImg = (prompt) =>
	'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=' +
	encodeURIComponent(
		PHOTO_STYLE +
			prompt +
			', tall transparent takeaway cup with flat lid, centered composition, consistent brand photography style, high resolution'
	) +
	'&image_size=square_hd'

/**
 * 活动海报图（16:9，主体靠右、左侧留文案空位）
 * @param {string} prompt 场景描述
 * @returns {string}
 */
export const genBanner = (prompt) =>
	'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=' +
	encodeURIComponent(
		'Premium commercial milk tea campaign photography, warm cream and caramel palette with burnt orange accents, ' +
			'soft diffused studio light, realistic, high resolution, no text, no letters, no logo, no people, no cartoon, ' +
			prompt +
			', cups and props clustered on the right side, clean empty copy space on the left, consistent brand campaign style'
	) +
	'&image_size=landscape_16_9'
