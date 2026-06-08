<template>
  <div id="app">
    <nav class="navbar">
      <div class="nav-left">
        <div class="nav-brand">🧬 单细胞 ANN 检索系统</div>
        <div class="nav-links">
          <router-link
            v-for="r in menuRoutes"
            :key="r.path"
            :to="r.path"
          >
            <span class="icon">{{ r.meta.icon }}</span>{{ r.meta.title }}
          </router-link>
        </div>
      </div>
      <div class="nav-right">
        <template v-if="isLoggedIn">
          <span class="user-info">
            <span class="role-badge" :class="{ admin: isAdmin }">
              {{ isAdmin ? '管理员' : '用户' }}
            </span>
            {{ user?.username }}
          </span>
          <button class="btn-link" @click="handleLogout">登出</button>
        </template>
        <template v-else>
          <router-link to="/login" class="btn-link">登录</router-link>
          <router-link to="/register" class="btn-primary">注册</router-link>
        </template>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
    <footer class="footer">
      软件工程大作业 · 单细胞 ANN 检索系统 · Vue 3 + Flask + HNSWLIB
    </footer>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { isLoggedIn, isAdmin, currentUser, logout, fetchMe } from './store/user'

const router = useRouter()
const route = useRoute()

const user = currentUser

const menuRoutes = computed(() => {
  return router.options.routes.filter(r => {
    if (r.meta?.hideInMenu) return false
    // 管理员路由仅 admin 可见
    if (r.meta?.requireAdmin && !isAdmin.value) return false
    return true
  })
})

function handleLogout() {
  logout()
  router.push('/login')
}

onMounted(() => {
  // 启动时验证一次 token
  if (isLoggedIn.value) {
    fetchMe()
  }
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC',
    'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  background-color: #f5f7fa;
  color: #333;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  height: 60px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 32px;
}

.nav-brand {
  font-size: 18px;
  font-weight: 600;
  color: #409eff;
  white-space: nowrap;
}

.nav-links {
  display: flex;
  gap: 4px;
}

.nav-links a {
  text-decoration: none;
  color: #606266;
  padding: 8px 14px;
  border-radius: 4px;
  transition: all 0.2s;
  font-size: 14px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.nav-links a .icon {
  font-size: 16px;
}

.nav-links a:hover {
  color: #409eff;
  background-color: #ecf5ff;
}

.nav-links a.router-link-active {
  color: #409eff;
  background-color: #ecf5ff;
  font-weight: 500;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-info {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #303133;
}

.role-badge {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;
  background: #e1f3d8;
  color: #67c23a;
}

.role-badge.admin {
  background: #fef0f0;
  color: #f56c6c;
}

.btn-link {
  background: none;
  border: none;
  color: #409eff;
  cursor: pointer;
  font-size: 14px;
  padding: 8px 14px;
  border-radius: 4px;
  text-decoration: none;
}

.btn-link:hover {
  background: #ecf5ff;
}

.btn-primary {
  background: #409eff;
  color: #fff;
  padding: 8px 16px;
  border-radius: 4px;
  text-decoration: none;
  font-size: 14px;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover {
  background: #66b1ff;
}

.main-content {
  flex: 1;
  max-width: 1280px;
  width: 100%;
  margin: 24px auto;
  padding: 0 24px;
}

.footer {
  text-align: center;
  padding: 16px;
  color: #909399;
  font-size: 12px;
  background: #fff;
  border-top: 1px solid #ebeef5;
}

/* 公共按钮 */
.el-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
  background: #fff;
  color: #606266;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.el-btn:hover {
  color: #409eff;
  border-color: #c6e2ff;
  background-color: #ecf5ff;
}

.el-btn.primary {
  background: #409eff;
  border-color: #409eff;
  color: #fff;
}

.el-btn.primary:hover {
  background: #66b1ff;
  border-color: #66b1ff;
  color: #fff;
}

.el-btn.danger {
  background: #f56c6c;
  border-color: #f56c6c;
  color: #fff;
}

.el-btn.danger:hover {
  background: #f78989;
  border-color: #f78989;
}

.el-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 公共表单 */
.el-input,
.el-select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
  background: #fff;
  outline: none;
  transition: border-color 0.2s;
}

.el-input:focus,
.el-select:focus {
  border-color: #409eff;
}

.el-card {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.el-card-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #303133;
}

/* 表格 */
.el-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.el-table th,
.el-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid #ebeef5;
}

.el-table th {
  background: #f5f7fa;
  color: #606266;
  font-weight: 500;
}

.el-table tr:hover td {
  background: #f5f7fa;
}

/* 提示信息 */
.el-alert {
  padding: 8px 16px;
  border-radius: 4px;
  margin-bottom: 16px;
  font-size: 14px;
}

.el-alert.success { background: #f0f9eb; color: #67c23a; }
.el-alert.warning { background: #fdf6ec; color: #e6a23c; }
.el-alert.error   { background: #fef0f0; color: #f56c6c; }
.el-alert.info    { background: #f4f4f5; color: #909399; }
</style>
