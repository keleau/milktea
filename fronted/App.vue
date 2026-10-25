<script>
import { ensureLogin } from './common/api/auth'

export default {
	onLaunch() {
		// 演示环境静默登录；后端未启动时各页面会给出网络提示，启动后自动恢复
		ensureLogin().catch(() => {})
	}
}
</script>

<style>
/* 全局公共样式：weui 基础库 + 工具类 + 项目覆盖 */
@import './common/style/app.css'
</style>
