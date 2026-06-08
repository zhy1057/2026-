import { createRouter, createWebHistory } from 'vue-router'
import userState, { isLoggedIn, isAdmin } from '../store/user'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue'),
    meta: { title: '首页', icon: '🏠' }
  },
  {
    path: '/search',
    name: 'Search',
    component: () => import('../views/Search.vue'),
    meta: { title: '相似检索', icon: '🔍', requireAuth: true }
  },
  {
    path: '/visual',
    name: 'Visual',
    component: () => import('../views/Visual.vue'),
    meta: { title: '可视化', icon: '📊', requireAuth: true }
  },
  {
    path: '/data',
    name: 'DataManage',
    component: () => import('../views/DataManage.vue'),
    meta: { title: '数据管理', icon: '🗂️', requireAuth: true }
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('../views/Admin.vue'),
    meta: { title: '系统管理', icon: '⚙️', requireAdmin: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { title: '登录', hideInMenu: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { title: '注册', hideInMenu: true }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFound.vue'),
    meta: { title: '404', hideInMenu: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 设置标题
  document.title = to.meta.title
    ? `${to.meta.title} - 单细胞 ANN 检索系统`
    : '单细胞 ANN 检索系统'

  // 需要管理员
  if (to.meta.requireAdmin) {
    if (!isLoggedIn.value) {
      return next({ path: '/login', query: { redirect: to.fullPath } })
    }
    if (!isAdmin.value) {
      alert('需要管理员权限')
      return next(from.fullPath || '/')
    }
    return next()
  }

  // 需要登录
  if (to.meta.requireAuth && !isLoggedIn.value) {
    return next({ path: '/login', query: { redirect: to.fullPath } })
  }

  next()
})

export default router
