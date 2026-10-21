<script>
import utils from './common/js/utils.js'

export default {
	onLaunch() {
		// 四猫茶学园无后端依赖：数据见 common/js/data.js，订单走本地 storage
	},
	// 全局数据：各页面通过 getApp().globalData 访问
	globalData: {
		utils: utils,
		name: '四猫茶学园',
		orders_filt: ''
	}
}
</script>

<style>
/* 全局公共样式：weui 基础库 + 工具类 + 项目覆盖 */
@import './common/style/app.css'
</style>
