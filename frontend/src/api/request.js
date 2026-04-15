import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import router from '@/router'

// 创建axios实例
const service = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'https://shanshan-87--smart-orchard-smartorchardapi-api.modal.run',
  timeout: 30000, // 超时时间30秒，适配大图片上传
  headers: {
    'Content-Type': 'application/json;charset=utf-8'
  }
})

// 请求拦截器
service.interceptors.request.use(
  (config) => {
    // 携带token
    const token = localStorage.getItem('apple-disease-token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response) => {
    // blob 类型（文件下载）直接返回原始响应数据
    if (response.config.responseType === 'blob') {
      return response.data
    }
    const res = response.data
    // 业务逻辑成功
    if (res.code === 200) {
      return res
    }
    // 业务逻辑失败
    ElMessage.error(res.message || '请求失败')
    return Promise.reject(new Error(res.message || '请求失败'))
  },
  (error) => {
    // 401未授权，跳转登录
    if (error.response?.status === 401) {
      ElMessageBox.confirm('登录状态已过期，请重新登录', '提示', {
        confirmButtonText: '去登录',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        localStorage.removeItem('apple-disease-token')
        router.push('/login')
      })
    } else if (error.response?.status === 403) {
      // 403静默处理（管理员专属接口普通用户调用时无需提示）
      console.warn('权限不足:', error.config?.url)
    } else {
      ElMessage.error(error.message || '网络请求异常')
    }
    return Promise.reject(error)
  }
)

// 核心接口封装
export const api = {
  // 登录接口
  login: (data) => service.post('/auth/login', data),
  // 注册接口
  register: (data) => service.post('/auth/register', data),
  // 获取当前用户信息
  getUserInfo: () => service.get('/auth/userinfo'),
  // 更新当前用户信息
  updateUserInfo: (data) => service.put('/auth/userinfo', data),
  // 单张图片病害检测
  singleDetect: (data) => service.post('/detect/single', data, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  // 批量图片病害检测
  batchDetect: (data) => service.post('/detect/batch', data, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  // 获取检测历史列表
  getHistoryList: (params) => service.get('/history/list', { params }),
  // 删除检测记录
  deleteHistory: (id) => service.delete(`/history/${id}`),
  // 获取历史记录详情（含完整病害列表）
  getHistoryDetail: (id) => service.get(`/history/${id}`),
  // 导出检测记录
  exportHistory: (params) => service.get('/history/export', { params, responseType: 'blob' }),
  // 获取果园地块数据
  getOrchardList: () => service.get('/orchard/list'),
  // 新增果园地块
  addOrchard: (data) => service.post('/orchard/add', data),
  // 删除果园地块
  deleteOrchard: (id) => service.delete(`/orchard/${id}`),
  // 获取病害空间分布数据
  getDiseaseSpatialData: (params) => service.get('/disease/spatial', { params }),
  // 获取统计分析数据
  getStatisticsData: (params) => service.get('/statistics/data', { params }),
  // 获取图表统计数据
  getChartStatistics: (params) => service.get('/statistics/chart', { params }),
  // 下载检测报告（HTML格式，直接传检测结果数据，不依赖数据库id）
  downloadReport: (data) => service.post('/report/generate', data, { responseType: 'blob' }),
  // 用户管理接口
  getUserList: () => service.get('/users/list'),
  createUser: (data) => service.post('/users/create', data),
  updateUser: (id, data) => service.put(`/users/${id}`, data),
  deleteUser: (id) => service.delete(`/users/${id}`),
  // 数据库维护接口（整理ID）
  maintainDatabase: () => service.post('/admin/maintain')
}

export default service