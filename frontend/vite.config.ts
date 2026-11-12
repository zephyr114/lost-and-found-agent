import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import { defineConfig } from 'vite'

// 后端地址可通过环境变量覆盖（默认 8000；端口被占用时可改成 8001）
const proxyTarget = process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000'

const proxy = {
  '/api': { target: proxyTarget, changeOrigin: true },
  '/health': { target: proxyTarget, changeOrigin: true },
  '/uploads': { target: proxyTarget, changeOrigin: true },
  '/docs': { target: proxyTarget, changeOrigin: true },
  '/redoc': { target: proxyTarget, changeOrigin: true },
  '/openapi.json': { target: proxyTarget, changeOrigin: true },
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    // Element Plus 按需引入：只打包模板中用到的组件与样式
    Components({ resolvers: [ElementPlusResolver()], dts: false }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: true,
    // 端口可通过环境变量覆盖（默认 5173；端口被占用时可改成 5174）
    port: Number(process.env.PORT) || 5173,
    // 允许通过临时隧道域名（trycloudflare / lhr.life 等）访问
    allowedHosts: true,
    // Windows 下文件监视易触发 EBUSY 崩溃，改用轮询模式
    watch: {
      usePolling: true,
      interval: 1000,
    },
    // 开发环境代理到后端，避免跨域
    proxy,
  },
  build: {
    chunkSizeWarningLimit: 1200,
    rollupOptions: {
      output: {
        // 拆包：框架 / UI 库 / 图表 / 其余第三方，降低首屏单包体积
        manualChunks(id: string) {
          if (!id.includes('node_modules')) return
          if (id.includes('echarts') || id.includes('zrender')) return 'echarts'
          if (id.includes('element-plus') || id.includes('@element-plus')) return 'element'
          if (
            id.includes('vue-router') ||
            id.includes('pinia') ||
            /node_modules[\\/]@vue[\\/]/.test(id) ||
            /node_modules[\\/]vue[\\/]/.test(id)
          ) {
            return 'vue'
          }
          return 'vendor'
        },
      },
    },
  },
})
