<template>
  <div class="admin-page">
    <h2 class="page-title">系统管理</h2>

    <div class="el-card">
      <div class="card-header">
        <span class="el-card-title">用户管理</span>
        <button class="el-btn primary" @click="showCreateDialog = true">+ 创建用户</button>
      </div>

      <div v-if="error" class="el-alert error">{{ error }}</div>

      <table class="el-table">
        <thead>
          <tr>
            <th>用户名</th>
            <th>角色</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.username">
            <td>{{ u.username }}</td>
            <td>
              <span class="role-badge" :class="{ admin: u.role === 'admin' }">
                {{ u.role === 'admin' ? '管理员' : '用户' }}
              </span>
            </td>
            <td>{{ formatTime(u.created_at) }}</td>
            <td>
              <button
                class="el-btn danger"
                :disabled="u.username === currentUsername"
                @click="handleDelete(u.username)"
              >
                删除
              </button>
            </td>
          </tr>
          <tr v-if="users.length === 0">
            <td colspan="4" style="text-align: center; color: #909399;">暂无数据</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 创建用户对话框 -->
    <div v-if="showCreateDialog" class="modal-overlay" @click.self="showCreateDialog = false">
      <div class="modal">
        <h3>创建用户</h3>
        <div v-if="dialogError" class="el-alert error">{{ dialogError }}</div>
        <div class="form-group">
          <label>用户名</label>
          <input v-model="newUser.username" class="el-input" />
        </div>
        <div class="form-group">
          <label>密码</label>
          <input v-model="newUser.password" type="password" class="el-input" />
        </div>
        <div class="form-group">
          <label>角色</label>
          <select v-model="newUser.role" class="el-select">
            <option value="user">普通用户</option>
            <option value="admin">管理员</option>
          </select>
        </div>
        <div class="modal-footer">
          <button class="el-btn" @click="showCreateDialog = false">取消</button>
          <button class="el-btn primary" :disabled="creating" @click="handleCreate">
            {{ creating ? '创建中...' : '确定' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { authApi } from '../api'
import { currentUser } from '../store/user'

const users = ref([])
const error = ref('')
const showCreateDialog = ref(false)
const dialogError = ref('')
const creating = ref(false)
const newUser = ref({ username: '', password: '', role: 'user' })

const currentUsername = computed(() => currentUser.value?.username)

async function loadUsers() {
  error.value = ''
  try {
    const res = await authApi.listUsers()
    users.value = res.data || []
  } catch (e) {
    error.value = e.message || '加载用户列表失败'
  }
}

async function handleDelete(username) {
  if (!confirm(`确认删除用户 ${username}？`)) return
  try {
    await authApi.deleteUser(username)
    await loadUsers()
  } catch (e) {
    alert(e.message || '删除失败')
  }
}

async function handleCreate() {
  dialogError.value = ''
  if (!newUser.value.username || !newUser.value.password) {
    dialogError.value = '用户名和密码不能为空'
    return
  }
  creating.value = true
  try {
    await authApi.createUser(newUser.value.username, newUser.value.password, newUser.value.role)
    showCreateDialog.value = false
    newUser.value = { username: '', password: '', role: 'user' }
    await loadUsers()
  } catch (e) {
    dialogError.value = e.message || '创建失败'
  } finally {
    creating.value = false
  }
}

function formatTime(ts) {
  if (!ts) return '-'
  return new Date(ts * 1000).toLocaleString('zh-CN')
}

onMounted(loadUsers)
</script>

<style scoped>
.page-title {
  font-size: 22px;
  color: #303133;
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.role-badge {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 10px;
  background: #e1f3d8;
  color: #67c23a;
}

.role-badge.admin {
  background: #fef0f0;
  color: #f56c6c;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  width: 400px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
}

.modal h3 {
  margin-bottom: 16px;
  color: #303133;
}

.form-group {
  margin-bottom: 14px;
}

.form-group label {
  display: block;
  margin-bottom: 4px;
  font-size: 13px;
  color: #606266;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 20px;
}
</style>
