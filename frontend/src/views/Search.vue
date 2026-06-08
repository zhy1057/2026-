<template>
  <div class="search-page">
    <h2 class="page-title">🔍 相似细胞检索</h2>

    <div class="layout">
      <!-- 左侧：检索参数面板 -->
      <div class="panel">
        <div class="el-card">
          <div class="el-card-title">检索参数</div>

          <!-- 数据集选择 -->
          <div class="form-group">
            <label>数据集</label>
            <select v-model="form.dataset_id" class="el-select" @change="onDatasetChange">
              <option value="" disabled>请选择数据集</option>
              <option v-for="d in datasets" :key="d.id" :value="d.id">
                {{ d.name }} ({{ d.n_cells.toLocaleString() }} cells)
                {{ d.has_index ? ' ✓' : ' ✗' }}
              </option>
            </select>
            <div v-if="currentDataset && !currentDataset.has_index" class="el-alert warning" style="margin-top: 8px;">
              该数据集尚未构建索引，将使用暴力精确检索
            </div>
          </div>

          <!-- 查询方式 -->
          <div class="form-group">
            <label>查询方式</label>
            <div class="radio-group">
              <label class="radio-item">
                <input type="radio" v-model="form.query_type" value="cell_index" />
                按细胞编号
              </label>
              <label class="radio-item">
                <input type="radio" v-model="form.query_type" value="vector" />
                按自定义向量
              </label>
            </div>
          </div>

          <!-- 输入参数 -->
          <div v-if="form.query_type === 'cell_index'" class="form-group">
            <label>
              细胞编号
              <span v-if="currentDataset" class="hint-inline">
                (0 - {{ currentDataset.n_cells - 1 }})
              </span>
            </label>
            <div class="input-row">
              <input
                v-model.number="form.cell_index"
                class="el-input"
                type="number"
                :min="0"
                :max="currentDataset ? currentDataset.n_cells - 1 : 0"
                placeholder="例如 100"
              />
              <button class="el-btn" @click="randomCell" :disabled="!currentDataset">随机</button>
            </div>
          </div>

          <div v-else class="form-group">
            <label>
              向量
              <span v-if="currentDataset" class="hint-inline">
                ({{ currentDataset.pca_dim }} 维, 逗号分隔)
              </span>
            </label>
            <textarea
              v-model="form.vector_text"
              class="el-input"
              rows="4"
              placeholder="例如: 1.2, 0.5, -0.3, ..."
            ></textarea>
          </div>

          <!-- Top-K -->
          <div class="form-group">
            <label>Top-K = {{ form.k }}</label>
            <input
              v-model.number="form.k"
              type="range"
              min="1"
              max="50"
              class="slider"
            />
          </div>

          <!-- 检索模式 -->
          <div class="form-group">
            <label>检索模式</label>
            <div class="radio-group">
              <label class="radio-item">
                <input type="radio" v-model="form.exact" :value="false" />
                ANN 近似（快）
              </label>
              <label class="radio-item">
                <input type="radio" v-model="form.exact" :value="true" />
                精确暴力（准）
              </label>
            </div>
          </div>

          <!-- 条件过滤 -->
          <div class="form-group">
            <label>
              条件过滤（可选）
              <button v-if="filterRows.length < 3" class="btn-mini" @click="addFilter">+ 添加</button>
            </label>
            <div v-for="(f, idx) in filterRows" :key="idx" class="filter-row">
              <select v-model="f.key" class="el-select" style="flex: 1;">
                <option value="" disabled>选择字段</option>
                <option v-for="col in obsCols" :key="col" :value="col">{{ col }}</option>
              </select>
              <select v-if="f.key === 'cell_type' && cellTypes.length" v-model="f.value" class="el-select" style="flex: 1.5;">
                <option value="" disabled>选择值</option>
                <option v-for="t in cellTypes" :key="t.type" :value="t.type">
                  {{ t.type }} ({{ t.count }})
                </option>
              </select>
              <input v-else v-model="f.value" class="el-input" placeholder="值" style="flex: 1.5;" />
              <button class="btn-mini-danger" @click="removeFilter(idx)">×</button>
            </div>
          </div>

          <button
            class="el-btn primary search-btn"
            :disabled="!canSearch || searching"
            @click="handleSearch"
          >
            {{ searching ? '检索中...' : '🔍 开始检索' }}
          </button>

          <button class="el-btn" style="width: 100%; margin-top: 8px;" @click="resetForm">
            重置
          </button>
        </div>
      </div>

      <!-- 右侧：结果面板 -->
      <div class="panel-result">
        <div v-if="error" class="el-alert error">{{ error }}</div>

        <div v-if="result" class="result-meta el-card">
          <div class="meta-grid">
            <div class="meta-item">
              <div class="meta-label">检索方法</div>
              <div class="meta-value">
                <span class="tag" :class="result.method === 'ann' ? 'success' : 'warning'">
                  {{ result.method === 'ann' ? 'ANN 近似' : '暴力精确' }}
                </span>
              </div>
            </div>
            <div class="meta-item">
              <div class="meta-label">距离度量</div>
              <div class="meta-value">{{ result.space }}</div>
            </div>
            <div class="meta-item">
              <div class="meta-label">查询耗时</div>
              <div class="meta-value highlight">{{ result.query_time_ms.toFixed(2) }} ms</div>
            </div>
            <div class="meta-item">
              <div class="meta-label">返回结果</div>
              <div class="meta-value">{{ result.returned }} / {{ result.k }}</div>
            </div>
          </div>
        </div>

        <div v-if="result && result.results.length > 0" class="el-card result-list">
          <div class="el-card-title" style="display: flex; justify-content: space-between; align-items: center;">
            <span>检索结果</span>
            <button class="el-btn" @click="viewInChart">📊 在可视化中查看</button>
          </div>
          <table class="el-table">
            <thead>
              <tr>
                <th>#</th>
                <th>细胞编号</th>
                <th>细胞ID</th>
                <th>细胞类型</th>
                <th>距离</th>
                <th>相似度</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in result.results" :key="r.cell_index" :class="{ self: r.distance < 0.001 }">
                <td>{{ r.rank }}</td>
                <td>{{ r.cell_index }}</td>
                <td class="mono">{{ truncate(r.cell_id, 24) }}</td>
                <td>
                  <span class="cell-type-badge">{{ r.metadata.cell_type || '-' }}</span>
                </td>
                <td class="mono">{{ r.distance.toFixed(4) }}</td>
                <td>
                  <div class="sim-bar">
                    <div class="sim-bar-fill" :style="{ width: (r.similarity * 100) + '%' }"></div>
                    <span class="sim-text">{{ (r.similarity * 100).toFixed(1) }}%</span>
                  </div>
                </td>
                <td>
                  <button class="btn-mini" @click="showDetail(r)">详情</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-else-if="result && result.results.length === 0" class="el-card">
          <div class="empty-state">未找到匹配的结果，请调整筛选条件</div>
        </div>

        <div v-else-if="!error" class="el-card empty-card">
          <div class="empty-state">
            <div class="empty-icon">🔬</div>
            <p>请在左侧设置检索参数后点击「开始检索」</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 详情对话框 -->
    <div v-if="detailItem" class="modal-overlay" @click.self="detailItem = null">
      <div class="modal" style="width: 560px;">
        <h3>细胞详情 #{{ detailItem.rank }}</h3>
        <table class="el-table" style="margin-top: 12px;">
          <tbody>
            <tr><th style="width: 35%;">细胞编号</th><td>{{ detailItem.cell_index }}</td></tr>
            <tr><th>细胞ID</th><td class="mono">{{ detailItem.cell_id }}</td></tr>
            <tr><th>距离</th><td>{{ detailItem.distance.toFixed(6) }}</td></tr>
            <tr><th>相似度</th><td>{{ (detailItem.similarity * 100).toFixed(2) }}%</td></tr>
            <tr v-for="(v, k) in detailItem.metadata" :key="k">
              <th>{{ k }}</th>
              <td>{{ v ?? '-' }}</td>
            </tr>
          </tbody>
        </table>
        <div class="modal-footer">
          <button class="el-btn primary" @click="useAsQuery(detailItem)">以此为查询</button>
          <button class="el-btn" @click="detailItem = null">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { dataApi, searchApi } from '../api'

const router = useRouter()

const datasets = ref([])
const cellTypes = ref([])
const obsCols = ref(['cell_type', 'donor_id', 'sex', 'tissue'])

const form = reactive({
  dataset_id: '',
  query_type: 'cell_index',
  cell_index: 0,
  vector_text: '',
  k: 10,
  exact: false
})

const filterRows = ref([])
const result = ref(null)
const error = ref('')
const searching = ref(false)
const detailItem = ref(null)

const currentDataset = computed(() => datasets.value.find(d => d.id === form.dataset_id))

const canSearch = computed(() => {
  if (!form.dataset_id) return false
  if (form.query_type === 'cell_index') {
    return form.cell_index !== null && form.cell_index !== undefined && form.cell_index >= 0
  }
  return form.vector_text.trim().length > 0
})

async function loadDatasets() {
  try {
    const res = await dataApi.list()
    datasets.value = res.data || []
    if (datasets.value.length > 0 && !form.dataset_id) {
      form.dataset_id = datasets.value[0].id
      onDatasetChange()
    }
  } catch (e) {
    error.value = e.message || '加载数据集失败'
  }
}

async function onDatasetChange() {
  if (!form.dataset_id) return
  try {
    const res = await dataApi.cellTypes(form.dataset_id)
    cellTypes.value = res.data || []
  } catch (e) {
    cellTypes.value = []
  }
  // 加载数据集详情，获取 obs 列
  try {
    const res = await dataApi.detail(form.dataset_id)
    if (res.data?.obs_columns) {
      obsCols.value = res.data.obs_columns
    }
  } catch (e) {
    // 静默
  }
}

function randomCell() {
  if (!currentDataset.value) return
  form.cell_index = Math.floor(Math.random() * currentDataset.value.n_cells)
}

function addFilter() {
  filterRows.value.push({ key: 'cell_type', value: '' })
}

function removeFilter(idx) {
  filterRows.value.splice(idx, 1)
}

function buildFilters() {
  const filters = {}
  filterRows.value.forEach(f => {
    if (f.key && f.value !== '' && f.value !== null && f.value !== undefined) {
      filters[f.key] = f.value
    }
  })
  return filters
}

async function handleSearch() {
  error.value = ''
  result.value = null
  searching.value = true

  const params = {
    dataset_id: form.dataset_id,
    query_type: form.query_type,
    k: form.k,
    exact: form.exact,
    filters: buildFilters()
  }

  if (form.query_type === 'cell_index') {
    params.cell_index = form.cell_index
  } else {
    try {
      const vec = form.vector_text.split(/[,\s]+/).filter(s => s).map(Number)
      if (vec.some(isNaN)) {
        throw new Error('向量包含非数字')
      }
      params.vector = vec
    } catch (e) {
      error.value = '向量解析失败：' + e.message
      searching.value = false
      return
    }
  }

  try {
    const res = await searchApi.query(params)
    if (res.code === 0) {
      result.value = res.data
    } else {
      error.value = res.message || '检索失败'
    }
  } catch (e) {
    error.value = e.message || '检索失败'
  } finally {
    searching.value = false
  }
}

function resetForm() {
  form.cell_index = 0
  form.vector_text = ''
  form.k = 10
  form.exact = false
  filterRows.value = []
  result.value = null
  error.value = ''
}

function showDetail(item) {
  detailItem.value = item
}

function useAsQuery(item) {
  form.query_type = 'cell_index'
  form.cell_index = item.cell_index
  detailItem.value = null
  handleSearch()
}

function truncate(s, n) {
  if (!s) return '-'
  return s.length > n ? s.slice(0, n) + '...' : s
}

function viewInChart() {
  if (!result.value || result.value.results.length === 0) return
  const ids = result.value.results.map(r => r.cell_index).join(',')
  router.push({
    path: '/visual',
    query: { dataset_id: form.dataset_id, highlight: ids }
  })
}

onMounted(loadDatasets)
</script>

<style scoped>
.search-page {
  padding: 0;
}

.page-title {
  font-size: 22px;
  color: #303133;
  margin-bottom: 20px;
}

.layout {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 20px;
  align-items: flex-start;
}

.panel-result {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  font-size: 13px;
  color: #606266;
  font-weight: 500;
}

.hint-inline {
  font-weight: normal;
  color: #909399;
  font-size: 12px;
}

.radio-group {
  display: flex;
  gap: 12px;
}

.radio-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  cursor: pointer;
}

.input-row {
  display: flex;
  gap: 8px;
}

.input-row .el-input {
  flex: 1;
}

.slider {
  width: 100%;
  cursor: pointer;
}

.search-btn {
  width: 100%;
  padding: 10px;
  font-size: 15px;
  justify-content: center;
  margin-top: 8px;
}

.btn-mini {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 3px;
  border: 1px solid #dcdfe6;
  background: #fff;
  cursor: pointer;
  color: #409eff;
}

.btn-mini:hover { background: #ecf5ff; }

.btn-mini-danger {
  font-size: 14px;
  padding: 2px 8px;
  border-radius: 3px;
  border: 1px solid #fde2e2;
  background: #fef0f0;
  cursor: pointer;
  color: #f56c6c;
  line-height: 1;
}

.filter-row {
  display: flex;
  gap: 6px;
  margin-bottom: 6px;
  align-items: center;
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.meta-item {
  text-align: center;
}

.meta-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.meta-value {
  font-size: 16px;
  color: #303133;
  font-weight: 500;
}

.meta-value.highlight {
  color: #409eff;
  font-weight: bold;
  font-size: 18px;
}

.tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 12px;
}

.tag.success { background: #e1f3d8; color: #67c23a; }
.tag.warning { background: #fdf6ec; color: #e6a23c; }

.result-list .el-table th:first-child {
  width: 40px;
}

.mono {
  font-family: 'Consolas', monospace;
  font-size: 13px;
}

tr.self td {
  background-color: #ecf5ff !important;
}

.cell-type-badge {
  display: inline-block;
  padding: 2px 8px;
  background: #f4f4f5;
  border-radius: 10px;
  font-size: 12px;
  color: #606266;
}

.sim-bar {
  position: relative;
  width: 100px;
  height: 18px;
  background: #f4f4f5;
  border-radius: 9px;
  overflow: hidden;
}

.sim-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #67c23a, #409eff);
  transition: width 0.3s;
}

.sim-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 11px;
  color: #303133;
  font-weight: 500;
}

.empty-card {
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-state {
  text-align: center;
  color: #909399;
  padding: 40px 0;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

/* Modal */
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
  max-height: 80vh;
  overflow-y: auto;
}

.modal h3 {
  margin-bottom: 8px;
  color: #303133;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}

@media (max-width: 900px) {
  .layout {
    grid-template-columns: 1fr;
  }
  .meta-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
