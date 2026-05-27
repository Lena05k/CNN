import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  optimizeDeps: {
    exclude: ['onnxruntime-web'],
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  build: {
    outDir: '../templates/dist',
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(__dirname, 'index.html'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/predictImage': { target: 'http://cnn-backend:8000', changeOrigin: true },
      '/api':          { target: 'http://cnn-backend:8000', changeOrigin: true },
      '/media':        { target: 'http://cnn-backend:8000', changeOrigin: true },
    },
  },
})
