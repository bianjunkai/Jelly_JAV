import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 请求拦截器
api.interceptors.request.use(config => {
  return config
})

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// 影片 API
export const moviesApi = {
  list: (params) => api.get('/movies', { params }),
  get: (code) => api.get(`/movies/${code}`),
  refresh: (code) => api.post(`/movies/${code}/refresh`),
  delete: (code) => api.delete(`/movies/${code}`)
}

// 演员 API
export const actorsApi = {
  list: (params) => api.get('/actors', { params }),
  get: (name) => api.get(`/actors/${name}`),
  follow: (id) => api.put(`/actors/${id}/follow`)
}

// 榜单 API
export const chartsApi = {
  list: () => api.get('/charts'),
  get: (name, params) => api.get(`/charts/${name}`, { params }),
  gaps: (name) => api.get(`/charts/${name}/gaps`),
  refresh: (name) => api.post(`/charts/${name}/refresh`)
}

// 报告 API
export const reportsApi = {
  latest: () => api.get('/reports/latest'),
  list: () => api.get('/reports'),
  generate: (type) => api.post('/reports/generate', { type }),
  markRead: (id) => api.put(`/reports/${id}/read`)
}

// 待看清单 API
export const todosApi = {
  list: (params) => api.get('/todos', { params }),
  add: (data) => api.post('/todos', data),
  updateStatus: (id, status) => api.put(`/todos/${id}/status`, { status }),
  delete: (id) => api.delete(`/todos/${id}`),
  batchAdd: (items) => api.post('/todos/batch', { items })
}

// 任务 API
export const tasksApi = {
  status: () => api.get('/tasks'),
  sync: () => api.post('/tasks/sync'),
  updateScores: () => api.post('/tasks/scores')
}

// 统计 API
export const statsApi = {
  get: () => api.get('/stats')
}

// 配置 API
export const configApi = {
  get: () => api.get('/config'),
  update: (data) => api.put('/config', data),
  getCharts: () => api.get('/config/charts')
}

// 榜单管理 API
export const chartManageApi = {
  create: (data) => api.post('/charts', data)
}

export default api
