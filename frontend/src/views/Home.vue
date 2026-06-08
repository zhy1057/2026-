<template>
  <div class="home">
    <div class="hero">
      <h1>🧬 单细胞 ANN 检索系统</h1>
      <p class="subtitle">基于 HNSWLIB 的高效近似最近邻检索 · 毫秒级查询</p>
      <div class="actions">
        <router-link to="/search" class="el-btn primary">开始检索</router-link>
        <router-link to="/visual" class="el-btn">可视化分析</router-link>
      </div>
    </div>

    <!-- 系统概览 -->
    <div v-if="isLoggedIn" class="overview">
      <div class="stat-card">
        <div class="stat-value">{{ stats.datasets }}</div>
        <div class="stat-label">已加载数据集</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.cells.toLocaleString() }}</div>
        <div class="stat-label">总细胞数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.indexes }}</div>
        <div class="stat-label">已构建索引</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.cellTypes }}</div>
        <div class="stat-label">细胞类型数</div>
      </div>
    </div>

    <!-- 功能卡片 -->
    <div class="features">
      <div class="feature-card">
        <div class="feature-icon">🔍</div>
        <h3>相似细胞检索</h3>
        <p>输入细胞编号或向量，毫秒级返回 Top-K 相似细胞，支持精确/近似两种模式</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">🧪</div>
        <h3>条件筛选</h3>
        <p>按细胞类型、组织、捐赠者等元数据条件过滤后再检索，精准定位</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">📊</div>
        <h3>UMAP 可视化</h3>
        <p>UMAP/t-SNE 散点图直观展示细胞分布，高亮检索结果</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">⚡</div>
        <h3>性能评估</h3>
        <p>对比 ANN 与暴力检索的速度与召回率，自由调整 ef 参数</p>
      </div>
    </div>

    <!-- 数据集列表 -->
    <div v-if="isLoggedIn && datasets.length > 0" class="el-card">
      <div class="el-card-title">可用数据集</div>
      <table class="el-table">
        <thead>
          <tr>
            <th>数据集 ID</th>
            <th>名称</th>
            <th>细胞数</th>
            <th>基因数</th>
            <th>PCA 维度</th>
            <th>索引</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in datasets" :key="d.dataset_id">
            <td>{{ d.dataset_id }}</td>
            <td>{{ d.name }}</td>
            <td>{{ d.n_cells.toLocaleString() }}</td>
            <td>{{ d.n_genes.toLocaleString() }}</td>
            <td>{{ d.pca_dim || '-' }}</td>
            <td>
              <span v-if="d.has_index" class="tag success">已建</span>
              <span v-else class="tag warning">未建</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { dataApi, searchApi } from '../api'
import { isLoggedIn } from '../store/user'

const datasets = ref([])
const stats = reactive({
  datasets: 0,
  cells: 0,
  indexes: 0,
  cellTypes: 0
})

async function loadOverview() {
  if (!isLoggedIn.value) return
  try {
    const res = await dataApi.list()
    datasets.value = res.data || []
    stats.datasets = datasets.value.length
    stats.cells = datasets.value.reduce((sum, d) => sum + (d.n_cells || 0), 0)
    stats.indexes = datasets.value.filter(d => d.has_index).length
    stats.cellTypes = datasets.value.reduce((sum, d) => sum + (d.n_cell_types || 0), 0)
  } catch (e) {
    console.error('加载数据集失败:', e.message)
  }
}

onMounted(loadOverview)
</script>

<style scoped>
.home {
  padding: 0;
}

.hero {
  text-align: center;
  padding: 40px 0 60px;
}

.hero h1 {
  font-size: 36px;
  color: #303133;
  margin-bottom: 12px;
}

.subtitle {
  color: #909399;
  font-size: 16px;
  margin-bottom: 32px;
}

.actions {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.overview {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 40px;
}

.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  text-align: center;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 4px;
}

.stat-label {
  color: #909399;
  font-size: 13px;
}

.features {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 40px;
}

.feature-card {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  transition: transform 0.2s;
}

.feature-card:hover {
  transform: translateY(-4px);
}

.feature-icon {
  font-size: 32px;
  margin-bottom: 12px;
}

.feature-card h3 {
  color: #303133;
  margin-bottom: 8px;
  font-size: 16px;
}

.feature-card p {
  color: #606266;
  font-size: 13px;
  line-height: 1.6;
}

.tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 12px;
}

.tag.success { background: #e1f3d8; color: #67c23a; }
.tag.warning { background: #fdf6ec; color: #e6a23c; }

@media (max-width: 768px) {
  .overview, .features {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
