import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { fileURLToPath, URL } from 'url';

export default defineConfig({
  plugins: [vue()],
  
  // Base public path - use /casestrainer/ in both development and production
  base: '/casestrainer/',
  
  // Development server configuration
  server: {
    port: 5173,
    strictPort: true,
    host: '0.0.0.0',
    hmr: {
      host: 'localhost',
      protocol: 'ws'
    },
    watch: {
      usePolling: true
    },
    proxy: {
      // Proxy API requests to the backend server
      '/casestrainer/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path,  // Don't rewrite the path, keep /casestrainer prefix
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('proxy error', err);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('Sending Request to the Target:', req.method, req.url);
          });
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
          });
        }
      }
    }
  },
  
  // Resolver configuration
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      'vue': 'vue/dist/vue.esm-bundler.js'
    },
    extensions: ['.js', '.vue', '.json']
  },
  
  // Build configuration
  build: {
    sourcemap: process.env.NODE_ENV !== 'production',
    minify: process.env.NODE_ENV === 'production' ? 'terser' : false,
    chunkSizeWarningLimit: 1600,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia', 'axios']
        }
      }
    }
  },
  
  // Environment variables
  define: {
    'import.meta.env.VITE_API_BASE_URL': JSON.stringify('/casestrainer/api'),  // Set base URL to /casestrainer/api
    'import.meta.env.VITE_APP_ENV': JSON.stringify(process.env.NODE_ENV || 'development'),
    'import.meta.env.VITE_COURTLISTENER_API_KEY': JSON.stringify(process.env.COURTLISTENER_API_KEY || '***REDACTED_COURTLISTENER_KEY***')
  }
});
