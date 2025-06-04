module.exports = {
  devServer: {
    proxy: {
      // For development - proxy /api to backend
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        pathRewrite: {
          '^/api': '/casestrainer/api'  // Add casestrainer prefix for development
        },
        logLevel: 'debug',
        secure: false,
        headers: {
          'X-Forwarded-Prefix': '/casestrainer'
        }
      },
      // For production-like URLs in development
      '/casestrainer/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        pathRewrite: {
          '^/casestrainer/api': '/casestrainer/api'  // Keep the full path
        },
        logLevel: 'debug',
        secure: false
      }
    },
    allowedHosts: 'all',
    host: '0.0.0.0',
    port: 8080,
    client: {
      webSocketURL: 'auto://0.0.0.0:0/ws'
    },
    hot: true,
    open: true
  },
  publicPath: '/',
  // For production build with Nginx
  // publicPath: process.env.NODE_ENV === 'production' ? '/casestrainer/' : '/',
  
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
