module.exports = {
  devServer: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    },
    allowedHosts: 'all',
    host: '0.0.0.0'
  },
  publicPath: process.env.NODE_ENV === 'production'
    ? '/casestrainer/'
    : '/'
}
