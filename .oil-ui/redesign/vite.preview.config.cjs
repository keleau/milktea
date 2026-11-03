const { defineConfig } = require('D:/cxdownload/HBuilderX.3.6.4.20220922/HBuilderX/plugins/uniapp-cli-vite/node_modules/vite')
const uni = require('D:/cxdownload/HBuilderX.3.6.4.20220922/HBuilderX/plugins/uniapp-cli-vite/node_modules/@dcloudio/vite-plugin-uni').default
module.exports = defineConfig({
  plugins: [uni()],
  resolve: {
    alias: {
      vue: 'D:/cxdownload/HBuilderX.3.6.4.20220922/HBuilderX/plugins/uniapp-cli-vite/node_modules/vue'
    }
  }
})
