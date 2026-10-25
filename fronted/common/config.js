/**
 * 前后端联调配置
 * H5 / 微信开发者工具用 127.0.0.1；真机把 API_BASE_URL 改成电脑局域网 IP，
 * 并同步修改后端 .env 的 BASE_URL（后端用它生成图片完整地址）
 */
export const API_BASE_URL = 'http://127.0.0.1:8000'
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

/** 当前选中门店 ID */
export const STORE_KEY = 'milk_store_id'
