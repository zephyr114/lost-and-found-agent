import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'

export const TOKEN_KEY = 'laf_token'
export const REFRESH_KEY = 'laf_refresh'
export const USER_KEY = 'laf_user'

// 统一 Axios 实例：
// - 开发环境 baseURL 为空，请求经 Vite 代理转发到后端
// - 部署环境通过 VITE_API_BASE_URL 指定后端地址
const baseURL = import.meta.env.VITE_API_BASE_URL || ''
const http = axios.create({ baseURL, timeout: 10000 })

// 请求拦截：自动附加 JWT
http.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let refreshing: Promise<string | null> | null = null

async function refreshAccessToken(): Promise<string | null> {
  const refresh = localStorage.getItem(REFRESH_KEY)
  if (!refresh) return null
  try {
    const { data } = await axios.post(`${baseURL}/api/auth/refresh`, { refresh_token: refresh })
    localStorage.setItem(TOKEN_KEY, data.access_token)
    localStorage.setItem(REFRESH_KEY, data.refresh_token)
    localStorage.setItem(USER_KEY, JSON.stringify(data.user))
    return data.access_token as string
  } catch {
    return null
  }
}

function clearSession() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_KEY)
  localStorage.removeItem(USER_KEY)
}

// 响应拦截：401 时先尝试用刷新令牌续期，失败再登出
http.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined
    const url = original?.url || ''
    const isAuthEndpoint = url.includes('/auth/login') || url.includes('/auth/register') || url.includes('/auth/refresh')

    if (error.response?.status === 401 && original && !original._retry && !isAuthEndpoint) {
      original._retry = true
      refreshing ??= refreshAccessToken().finally(() => {
        refreshing = null
      })
      const token = await refreshing
      if (token) {
        original.headers.Authorization = `Bearer ${token}`
        return http(original)
      }
      clearSession()
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)

export default http
