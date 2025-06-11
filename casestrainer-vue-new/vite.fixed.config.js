import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { fileURLToPath, URL } from 'url';

export default defineConfig({
  plugins: [vue()],
  
  // Base public path
  base: process.env.NODE_ENV === 'production' ? '/casestrainer/' : '/',
  
  // Development server configuration
  server: {
    port: 5173,
    strictPort: true,
    host: true, // Use 'true' to expose on all network interfaces
    open: true,  // Automatically open browser
    hmr: {
      host: 'localhost',
      port: 5173,
      protocol: 'ws'
    },
    watch: {
      usePolling: true // Needed for Windows
    },
    proxy: process.env.BACKEND_URL ? {
      '/casestrainer/api': {
        target: process.env.BACKEND_URL,
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/casestrainer\/api/, '')
      }
    } : undefined
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
  }
});
