import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import basicSsl from '@vitejs/plugin-basic-ssl'
import { resolve, join } from 'path'
import { readFileSync, existsSync } from 'fs'

// Serve onnxruntime-web WASM/MJS files as raw static assets so Vite's module
// pipeline never intercepts dynamic import() calls from ort inside the browser.
function ortStaticPlugin() {
  const ortDist = join(process.cwd(), 'node_modules/onnxruntime-web/dist')
  return {
    name: 'ort-static',
    configureServer(server) {
      server.middlewares.use('/ort', (req, res, next) => {
        const file = join(ortDist, (req.url || '').replace(/\?.*$/, ''))
        if (!existsSync(file)) return next()
        const isWasm = file.endsWith('.wasm')
        res.setHeader('Content-Type', isWasm ? 'application/wasm' : 'application/javascript')
        res.setHeader('Cache-Control', 'public, max-age=86400')
        res.end(readFileSync(file))
      })
    },
  }
}

export default defineConfig({
  plugins: [vue(), basicSsl(), ortStaticPlugin()],
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
    host: true,
    port: 5173,
    https: true,
    proxy: {
      '/predictImage': { target: 'http://cnn-backend:8000', changeOrigin: true },
      '/api':          { target: 'http://cnn-backend:8000', changeOrigin: true },
      '/media':        { target: 'http://cnn-backend:8000', changeOrigin: true },
    },
  },
})
