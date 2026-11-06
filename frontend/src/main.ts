import { createPinia } from 'pinia'
import { createApp } from 'vue'
import { ElLoading } from 'element-plus'
import 'element-plus/theme-chalk/dark/css-vars.css'
// 按需引入模式下，非模板用法（ElMessage / ElMessageBox / v-loading）需显式引入样式
import 'element-plus/es/components/message/style/css'
import 'element-plus/es/components/message-box/style/css'
import 'element-plus/es/components/loading/style/css'

import App from './App.vue'
import router from './router'
import './styles/theme.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
// 注册 v-loading 指令（组件已由 unplugin-vue-components 按需引入）
app.use(ElLoading)

app.mount('#app')

// PWA：生产环境注册 Service Worker（开发环境不注册，避免缓存干扰热更新）
if (import.meta.env.PROD && 'serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {
      /* 注册失败不影响正常使用 */
    })
  })
}
