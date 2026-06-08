<template>
  <div class="register-page">
    <div class="register-card">
      <h2 class="title">用户注册</h2>
      <p class="subtitle">创建一个新账号</p>

      <div v-if="error" class="el-alert error">{{ error }}</div>
      <div v-if="success" class="el-alert success">{{ success }}</div>

      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label>用户名（3-32 位）</label>
          <input
            v-model="username"
            class="el-input"
            type="text"
            placeholder="请输入用户名"
            required
          />
        </div>
        <div class="form-group">
          <label>密码（至少 6 位）</label>
          <input
            v-model="password"
            class="el-input"
            type="password"
            placeholder="请输入密码"
            required
          />
        </div>
        <div class="form-group">
          <label>确认密码</label>
          <input
            v-model="confirmPassword"
            class="el-input"
            type="password"
            placeholder="请再次输入密码"
            required
          />
        </div>
        <button type="submit" class="el-btn primary register-btn" :disabled="loading">
          {{ loading ? '注册中...' : '注 册' }}
        </button>
      </form>

      <div class="footer-link">
        已有账号？
        <router-link to="/login">立即登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { register, login } from '../store/user'

const router = useRouter()

const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const error = ref('')
const success = ref('')

async function handleRegister() {
  error.value = ''
  success.value = ''

  if (username.value.length < 3 || username.value.length > 32) {
    error.value = '用户名长度需为 3-32 位'
    return
  }
  if (password.value.length < 6) {
    error.value = '密码长度至少 6 位'
    return
  }
  if (password.value !== confirmPassword.value) {
    error.value = '两次密码输入不一致'
    return
  }

  loading.value = true
  try {
    await register(username.value.trim(), password.value)
    success.value = '注册成功，正在自动登录...'
    await login(username.value.trim(), password.value)
    setTimeout(() => router.replace('/'), 800)
  } catch (e) {
    error.value = e.message || '注册失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 200px);
}

.register-card {
  background: #fff;
  border-radius: 12px;
  padding: 40px 36px;
  width: 400px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
}

.title {
  font-size: 24px;
  color: #303133;
  margin-bottom: 4px;
  text-align: center;
}

.subtitle {
  color: #909399;
  text-align: center;
  margin-bottom: 32px;
  font-size: 14px;
}

.form-group {
  margin-bottom: 18px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  color: #606266;
  font-size: 14px;
}

.register-btn {
  width: 100%;
  padding: 12px;
  font-size: 15px;
  margin-top: 8px;
  justify-content: center;
}

.footer-link {
  margin-top: 20px;
  text-align: center;
  font-size: 14px;
  color: #606266;
}

.footer-link a {
  color: #409eff;
  text-decoration: none;
  margin-left: 4px;
}
</style>
