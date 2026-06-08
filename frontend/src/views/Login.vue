<template>
  <div class="login-page">
    <div class="login-card">
      <h2 class="title">欢迎登录</h2>
      <p class="subtitle">单细胞 ANN 检索系统</p>

      <div v-if="error" class="el-alert error">{{ error }}</div>

      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label>用户名</label>
          <input
            v-model="username"
            class="el-input"
            type="text"
            placeholder="请输入用户名"
            autocomplete="username"
            required
          />
        </div>
        <div class="form-group">
          <label>密码</label>
          <input
            v-model="password"
            class="el-input"
            type="password"
            placeholder="请输入密码"
            autocomplete="current-password"
            required
          />
        </div>
        <button type="submit" class="el-btn primary login-btn" :disabled="loading">
          {{ loading ? '登录中...' : '登 录' }}
        </button>
      </form>

      <div class="footer-link">
        还没有账号？
        <router-link to="/register">立即注册</router-link>
      </div>

      <div class="hint">
        <strong>测试账号：</strong>admin / admin123
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { login } from '../store/user'

const router = useRouter()
const route = useRoute()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  if (!username.value || !password.value) {
    error.value = '请输入用户名和密码'
    return
  }
  loading.value = true
  error.value = ''
  try {
    await login(username.value.trim(), password.value)
    const redirect = route.query.redirect || '/'
    router.replace(redirect)
  } catch (e) {
    error.value = e.message || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 200px);
}

.login-card {
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

.login-btn {
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

.hint {
  margin-top: 24px;
  padding: 10px 12px;
  background: #f4f4f5;
  border-radius: 4px;
  font-size: 12px;
  color: #909399;
  text-align: center;
}
</style>
