import App from './App'
// Date 原型扩展（VP_FORMAT），供时间展示等场景使用，需在应用启动前引入
import './common/js/date.js'

// #ifdef VUE3
import { createSSRApp } from 'vue'
export function createApp() {
	const app = createSSRApp(App)
	return {
		app
	}
}
// #endif
