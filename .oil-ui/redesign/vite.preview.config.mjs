import { defineConfig } from 'file:///D:/cxdownload/HBuilderX.3.6.4.20220922/HBuilderX/plugins/uniapp-cli-vite/node_modules/vite/dist/node/index.js'
import uniModule from 'file:///D:/cxdownload/HBuilderX.3.6.4.20220922/HBuilderX/plugins/uniapp-cli-vite/node_modules/@dcloudio/vite-plugin-uni/dist/index.js'
const uni = uniModule.default || uniModule
export default defineConfig({
  plugins: [uni()],
  resolve: {
    alias: {
      vue: 'D:/cxdownload/HBuilderX.3.6.4.20220922/HBuilderX/plugins/uniapp-cli-vite/node_modules/vue'
    }
  }
})
