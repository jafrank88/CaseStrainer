import { defineConfig, loadEnv } from 'vite';
import vue from '@vitejs/plugin-vue';
import { fileURLToPath, URL } from 'url';
import { version } from './package.json';

// Optional: Add other common imports that might have been missing
// import { resolve } from 'path';
// import legacy from '@vitejs/plugin-legacy';
// import { visualizer } from 'rollup-plugin-visualizer';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load environment variables based on the current mode
  const env = loadEnv(mode, process.cwd(), '');
  
  return {
    plugins: [
      vue(),
      // Add HTML cache busting plugin
      {
        name: 'html-cache-bust',
        generateBundle(options, bundle) {
          // Add timestamp to HTML file
          const htmlFile = bundle['index.html'];
          if (htmlFile) {
            htmlFile.code = htmlFile.code.replace(
              /<script type="module" crossorigin src="([^"]+)"><\/script>/g,
              `<script type="module" crossorigin src="$1?v=${Date.now()}"></script>`
            );
          }
        }
      }
      // Optional: Legacy browser support
      // legacy({
      //   targets: ['defaults', 'not IE 11']
      // }),
      // Optional: Bundle analyzer
      // visualizer({
      //   filename: 'dist/stats.html',
      //   open: true,
      //   gzipSize: true
      // })
    ],
    
    // Base public path when served in production
    base: '/casestrainer/',
    
    // Development server configuration
    server: {
      port: 5173, // Standard Vite dev port
      strictPort: true,
      host: '0.0.0.0', // Bind to all interfaces for Docker
      allowedHosts: [
        'localhost',
        '127.0.0.1',
        '0.0.0.0',
        'wolf.law.uw.edu'
      ],
      proxy: {
        // Proxy API requests to the backend server during development
        '/casestrainer/api': {
          target: 'http://backend:5000',
          changeOrigin: true,
          secure: false,
          ws: true,
          configure: (proxy, _options) => {
            proxy.on('error', (err, _req, _res) => {
              console.log('proxy error', err);
            });
            proxy.on('proxyReq', (proxyReq, req, _res) => {
              console.log('Sending Request to the Target:', req.method, req.url);
            });
          }
        },
      },
    },
    
    // Preview server configuration (for production builds)
    preview: {
      port: parseInt(process.env.PROD_FRONTEND_PORT) || 5000,
      host: '127.0.0.1',
      strictPort: true,
      proxy: {
        '/api': {
          target: `http://localhost:${process.env.PROD_BACKEND_PORT || 5002}`,
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
      sourcemap: env.VITE_APP_ENV !== 'production',
      minify: env.VITE_APP_ENV === 'production' ? 'terser' : false,
      chunkSizeWarningLimit: 1600,
      // Add cache busting with timestamp
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['vue', 'vue-router'],
            // Add other manual chunks as needed
          },
          // Add timestamp to file names for cache busting
          entryFileNames: `assets/[name]-[hash]-${Date.now()}-${Math.random().toString(36).substring(7)}.js`,
          chunkFileNames: `assets/[name]-[hash]-${Date.now()}-${Math.random().toString(36).substring(7)}.js`,
          assetFileNames: `assets/[name]-[hash]-${Date.now()}-${Math.random().toString(36).substring(7)}.[ext]`
        }
      }
    },
    
    // Add cache busting for HTML
    // Note: This is handled by the rollupOptions above
    
    // Resolve aliases
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
        // Optional: Additional aliases
        // '@components': fileURLToPath(new URL('./src/components', import.meta.url)),
        // '@views': fileURLToPath(new URL('./src/views', import.meta.url)),
        // '@utils': fileURLToPath(new URL('./src/utils', import.meta.url)),
      },
    },
    
    // CSS configuration
    css: {
      preprocessorOptions: {
        scss: {
          additionalData: `@import "@/styles/variables.scss";`
        }
      },
      // CSS modules configuration
      modules: {
        localsConvention: 'camelCase'
      }
    },
    
    // Optimization dependencies
    optimizeDeps: {
      include: ['vue', 'vue-router'],
      // exclude: ['some-dep']
    },
    
    // Environment variables to expose to the client
    define: {
      'import.meta.env.VITE_APP_NAME': JSON.stringify(env.VITE_APP_NAME || 'CaseStrainer'),
      'import.meta.env.VITE_APP_ENV': JSON.stringify(env.VITE_APP_ENV || 'development'),
      'import.meta.env.VITE_API_BASE_URL': JSON.stringify(
        env.VITE_APP_ENV === 'production' 
          ? '/casestrainer/api' 
          : 'http://localhost:5000/casestrainer/api'
      ),
      'import.meta.env.DEV_FRONTEND_PORT': JSON.stringify(process.env.DEV_FRONTEND_PORT || '5000'),
      'import.meta.env.DEV_BACKEND_PORT': JSON.stringify(process.env.DEV_BACKEND_PORT || '5001'),
      '__APP_VERSION__': JSON.stringify(version),
      // Optional: Global constants
      // __VUE_OPTIONS_API__: true,
      // __VUE_PROD_DEVTOOLS__: false,
    },
    
    // ESBuild configuration
    esbuild: {
      drop: env.VITE_APP_ENV === 'production' ? ['console', 'debugger'] : []
    },
    
    // Worker configuration
    worker: {
      format: 'es'
    }
  };
});