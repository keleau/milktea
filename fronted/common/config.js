/**
 * 前后端联调配置
 * 当前为本机真机调试地址：手机和电脑需要同一个 Wi-Fi。
 * 换网络后改这里，并同步修改后端 .env 的 BASE_URL。
 * 如果手机连的是电脑热点，可改成 http://192.168.137.1:8000
 */
export const API_BASE_URL = 'http://10.158.252.228:8000'
export const API_PREFIX = '/api/v1'

/** 演示登录：后端把 code=demo 映射到预置会员 1001 */
export const DEMO_LOGIN_CODE = 'demo'
export const REQUEST_TIMEOUT = 15000

/** 登录页路径；未登录或登录失效时跳回这里 */
export const LOGIN_PAGE = '/pages/login/index'

/** 本机固定 ID：微信 code 每次都变，用它让重复登录落到同一个模拟账号 */
export const MOCK_ID_KEY = 'milk_mock_id'

/** 本地会话缓存键 */
export const TOKEN_KEYS = {
	access: 'milk_access_token',
	refresh: 'milk_refresh_token',
	user: 'milk_user'
}

/** 微信基础库不接受 http 图片，本地上传的头像先用临时路径跨页预览 */
export const AVATAR_PREVIEW_KEY = 'milk_avatar_preview'

/** 当前选中门店 ID */
export const STORE_KEY = 'milk_store_id'
