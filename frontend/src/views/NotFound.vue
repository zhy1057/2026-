<template>
  <div class="not-found">
    <div class="error-code">404</div>
    <p class="error-msg">页面不存在</p>
    <router-link to="/" class="el-btn primary">返回首页</router-link>
  </div>
</template>

<style scoped>
.not-found {
  text-align: center;
  padding: 100px 0;
}

.error-code {
  font-size: 96px;
  font-weight: bold;
  color: #409eff;
  line-height: 1;
}

.error-msg {
  font-size: 18px;
  color: #909399;
  margin: 16px 0 32px;
}
</style>
