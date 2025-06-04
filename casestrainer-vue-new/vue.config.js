const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  publicPath: '/casestrainer/',
  transpileDependencies: true,
  devServer: {
    proxy: {
      '^/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        pathRewrite: { '^/api': '' }
      }
    }
  }
})
