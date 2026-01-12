import axios, { type AxiosInstance, type AxiosRequestConfig, type InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import type { ApiResponse } from '@/types'
import { useUserStore } from '@/stores/user'
import router from '@/router'

// 创建 axios 实例
const request: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    const { code, message } = response.data as ApiResponse

    if (code === 200) {
      return response.data
    }

    // 业务错误
    ElMessage.error(message || '请求失败')
    return Promise.reject(new Error(message))
  },
  (error) => {
    const { response } = error

    if (response) {
      const { status, data } = response

      // 401 未授权，跳转登录
      if (status === 401) {
        const userStore = useUserStore()
        userStore.logout()
        router.push('/login')
        ElMessage.error(data?.message || '登录已过期，请重新登录')
        return Promise.reject(error)
      }

      // 其他错误
      const message = data?.message || getErrorMessage(status)
      ElMessage.error(message)
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }

    return Promise.reject(error)
  }
)

// HTTP 状态码对应的错误信息
function getErrorMessage(status: number): string {
  const messages: Record<number, string> = {
    400: '请求参数错误',
    401: '未授权，请登录',
    403: '拒绝访问',
    404: '请求的资源不存在',
    500: '服务器内部错误',
    502: '网关错误',
    503: '服务不可用',
    504: '网关超时',
  }
  return messages[status] || `请求失败 (${status})`
}

// 封装请求方法
export async function get<T>(url: string, params?: Record<string, unknown>, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
  return request.get(url, { params, ...config }) as Promise<ApiResponse<T>>
}

export async function post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
  return request.post(url, data, config) as Promise<ApiResponse<T>>
}

export async function put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
  return request.put(url, data, config) as Promise<ApiResponse<T>>
}

export async function del<T>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
  return request.delete(url, config) as Promise<ApiResponse<T>>
}

// 文件上传
export async function upload<T>(url: string, file: File, subdir = ''): Promise<ApiResponse<T>> {
  const formData = new FormData()
  formData.append('file', file)

  return request.post(`${url}?subdir=${subdir}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  }) as Promise<ApiResponse<T>>
}
