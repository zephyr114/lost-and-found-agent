import axios from 'axios'

export const TOKEN_KEY = 'laf_token'
export const USER_KEY = 'laf_user'

// 统一 Axios 实例：
// - 开发环境 baseURL 为空，请求经 Vite 代理转发到后端
// - 部署环境通过 VITE_API_BASE_URL 指定后端地址
const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 10000,
})

// 请求拦截：自动附加 JWT
http.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截：401 统一清除登录态并跳转登录页
http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)

export default http
