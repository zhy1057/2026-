/**
 * 用户状态管理（基于 Vue 3 reactive）
 * - token / user 存储在 localStorage
 * - 登录状态同步到 reactive 对象，整个应用响应式更新
 */
import { reactive, computed } from 'vue'
import api from '../api'

const STORAGE_TOKEN_KEY = 'sc_ann_token'
const STORAGE_USER_KEY = 'sc_ann_user'

const state = reactive({
  token: localStorage.getItem(STORAGE_TOKEN_KEY) || '',
  user: JSON.parse(localStorage.getItem(STORAGE_USER_KEY) || 'null')
})

export const isLoggedIn = computed(() => !!state.token)
export const isAdmin = computed(() => state.user?.role === 'admin')
export const currentUser = computed(() => state.user)
export const currentToken = computed(() => state.token)

function persist() {
  if (state.token) {
    localStorage.setItem(STORAGE_TOKEN_KEY, state.token)
  } else {
    localStorage.removeItem(STORAGE_TOKEN_KEY)
  }
  if (state.user) {
    localStorage.setItem(STORAGE_USER_KEY, JSON.stringify(state.user))
  } else {
    localStorage.removeItem(STORAGE_USER_KEY)
  }
}

export async function login(username, password) {
  const res = await api.post('/auth/login', { username, password })
  if (res.code !== 0) {
    throw new Error(res.message || '登录失败')
  }
  state.token = res.data.token
  state.user = {
    username: res.data.username,
    role: res.data.role
  }
  persist()
  return res.data
}

export async function register(username, password) {
  const res = await api.post('/auth/register', { username, password })
  if (res.code !== 0) {
    throw new Error(res.message || '注册失败')
  }
  return res.data
}

export function logout() {
  state.token = ''
  state.user = null
  persist()
}

export async function fetchMe() {
  if (!state.token) return null
  try {
    const res = await api.get('/auth/me')
    if (res.code === 0) {
      state.user = res.data
      persist()
      return res.data
    }
  } catch (e) {
    // token 无效，清除
    logout()
  }
  return null
}

export async function changePassword(oldPwd, newPwd) {
  const res = await api.post('/auth/change_password', {
    old_password: oldPwd,
    new_password: newPwd
  })
  if (res.code !== 0) {
    throw new Error(res.message || '修改失败')
  }
  return true
}

export default state
