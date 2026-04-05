import { defineConfig } from 'vitest/config';
import vue from '@vitejs/plugin-vue';
import { resolve } from 'path';
import { readFileSync } from 'fs';

const packageJson = JSON.parse(
  readFileSync(new URL('./package.json', import.meta.url), 'utf-8')
);
const appVersion = packageJson.version || '2.1.0';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue()
  ],

  test: {
    environment: 'jsdom',
    include: ['src/**/*.{test,spec}.{js,ts}', 'src/**/__tests__/**/*.{js,ts}'],
  },
  
  // Base public path - use environment variable or default
  base: process.env.BASE_URL || '/casestrainer/',
  
  // Development server configuration
  server: {
    port: 5173,
    strictPort: true,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false,
        ws: true
      }
    }
  },
  
  // Build configuration
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    emptyOutDir: true,
    sourcemap: false,
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: false,  // Temporarily disabled to allow debugging
        drop_debugger: true
      }
    },
    rollupOptions: {
      output: {
        manualChunks: {
          vue: ['vue', 'vue-router', 'pinia'],
          vendor: ['axios', 'bootstrap']
        }
      }
    }
  },
  
  // Resolve aliases
  resolve: {
    alias: {
      '@': resolve(__dirname, './src')
    }
  },
  
  // Environment variables
  define: {
    'process.env': {},
    __APP_VERSION__: JSON.stringify(appVersion)
  }
});
