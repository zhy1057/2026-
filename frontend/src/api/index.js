import axios from 'axios'

const STORAGE_TOKEN_KEY = 'sc_ann_token'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器：自动添加 token
api.interceptors.request.use(config => {
  const token = localStorage.getItem(STORAGE_TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    const status = error.response?.status
    const data = error.response?.data || {}

    // 401: 未登录或 token 失效，清除并跳转登录
    if (status === 401) {
      localStorage.removeItem(STORAGE_TOKEN_KEY)
      localStorage.removeItem('sc_ann_user')
      // 避免在 login 页面重复跳转
      if (!location.pathname.startsWith('/login')) {
        const redirect = encodeURIComponent(location.pathname + location.search)
        location.href = `/login?redirect=${redirect}`
      }
    }

    // 统一错误信息
    const message = data.message || error.message || '请求失败'
    console.error(`[API ${status || 'ERR'}] ${message}`)

    // 仍然返回标准化的错误对象
    return Promise.reject({
      code: data.code ?? -1,
      status,
      message,
      raw: error
    })
  }
)

// ============ 模块化 API ============

export const authApi = {
  login: (username, password) => api.post('/auth/login', { username, password }),
  register: (username, password) => api.post('/auth/register', { username, password }),
  me: () => api.get('/auth/me'),
  logout: () => api.post('/auth/logout'),
  changePassword: (oldPwd, newPwd) =>
    api.post('/auth/change_password', { old_password: oldPwd, new_password: newPwd }),
  verify: (token) => api.post('/auth/verify', { token }),
  // admin
  listUsers: () => api.get('/auth/users'),
  createUser: (username, password, role) =>
    api.post('/auth/users/create', { username, password, role }),
  deleteUser: (username) => api.delete(`/auth/users/${username}`)
}

export const dataApi = {
  list: () => api.get('/data/datasets'),
  detail: (id) => api.get(`/data/datasets/${id}`),
  upload: (formData, extraConfig = {}) =>
    api.post('/data/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 0,
      ...extraConfig
    }),
  delete: (id) => api.delete(`/data/delete/${id}`),
  cellTypes: (id) => api.get(`/data/cell_types/${id}`),
  cell: (id, cellIdx) => api.get(`/data/cell/${id}/${cellIdx}`)
}

export const searchApi = {
  query: (params) => api.post('/search/query', params),
  recall: (params) => api.post('/search/recall', params),
  // 索引管理
  indexList: () => api.get('/search/index/list'),
  indexStatus: (id) => api.get(`/search/index/status/${id}`),
  indexBuild: (id, params) => api.post(`/search/index/build/${id}`, params || {}),
  indexDelete: (id) => api.delete(`/search/index/${id}`),
  indexUpdateEf: (id, ef) => api.post(`/search/index/ef/${id}`, { ef })
}

export const visualApi = {
  embedding: (id, params) => api.get(`/visual/embedding/${id}`, { params }),
  cellsCoords: (id, cellIndices, type = 'umap') =>
    api.post(`/visual/cells/${id}`, { cell_indices: cellIndices, type })
}

export default api
