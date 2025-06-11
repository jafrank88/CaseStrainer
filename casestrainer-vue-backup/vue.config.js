module.exports = {
  // Set base URL for production
  publicPath: process.env.NODE_ENV === 'production' ? '/casestrainer/' : '/',
  
  devServer: {
    port: process.env.VUE_APP_DEV_PORT || 3000,
    host: '0.0.0.0',
    proxy: {
      // For development - proxy /api to backend
      '/api': {
        target: 'http://localhost:5001',  // Changed to match your Flask backend port
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
    port: 3000,  // Changed from 8080 to 3000 to avoid conflicts
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
