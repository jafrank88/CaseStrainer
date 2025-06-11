module.exports = {
  // Set base URL for production
  publicPath: process.env.NODE_ENV === 'production' ? '/casestrainer/' : '/',
  
  devServer: {
    port: 5173,  // Use port 5173 consistently
    host: '0.0.0.0',
    proxy: {
      // For development - proxy /api to backend
      '/api': {
        target: 'http://localhost:5000',  // Use port 5000 consistently
        changeOrigin: true,
        pathRewrite: {
          '^/api': '/api'  // Keep the path as is
        },
        logLevel: 'debug',
        secure: false
      }
    },
    allowedHosts: 'all',
    client: {
      webSocketURL: 'auto://0.0.0.0:0/ws'
    },
    hot: true,
    open: true
  },
  
  // Configure webpack dev server to handle history mode routing
  configureWebpack: {
    devServer: {
      historyApiFallback: true
    }
  },
  
  // Enable source maps for better debugging
  productionSourceMap: true,
  
  // Configure Webpack to handle @/ imports
  chainWebpack: config => {
    config.resolve.alias
      .set('@', require('path').resolve(__dirname, 'src'));
  }
}
