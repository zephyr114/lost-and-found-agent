import axios from 'axios'

// 统一 Axios 实例：
// - 开发环境 baseURL 为空，请求经 Vite 代理转发到后端
// - 部署环境通过 VITE_API_BASE_URL 指定后端地址
const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 10000,
})

// 第二阶段接入 JWT：在此拦截器统一附加 Authorization 头、
// 统一处理 401（跳转登录）与错误提示
http.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error),
)

export default http
