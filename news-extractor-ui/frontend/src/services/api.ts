// API 服务
import axios from 'axios'
import type { ExtractRequest, ExtractResponse, Platform } from '@/types'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    const message = error.response?.data?.detail?.error?.message || error.message || '请求失败'
    return Promise.reject(new Error(message))
  }
)

// 提取新闻
export const extractNews = (data: ExtractRequest): Promise<ExtractResponse> => {
  return api.post('/extract', data)
}

// 获取支持的平台列表
export const getPlatforms = (): Promise<{ status: string; platforms: Platform[] }> => {
  return api.get('/platforms')
}

// 健康检查
export const healthCheck = (): Promise<{ status: string; timestamp: string }> => {
  return api.get('/health')
}

export default api
