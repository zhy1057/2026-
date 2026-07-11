<template>
  <div class="data-page">
    <div class="page-header">
      <h2 class="page-title">📦 数据集管理</h2>
      <button class="el-btn primary" @click="showUploadModal = true">
        ⬆️ 导入数据集
      </button>
    </div>

    <div v-if="error" class="el-alert error">{{ error }}</div>
    <div v-if="success" class="el-alert success">{{ success }}</div>

    <div class="layout-grid">
      <!-- 左：数据集列表 -->
      <div class="el-card list-panel">
        <div class="el-card-title">
          数据集列表
          <span class="badge">{{ datasets.length }}</span>
        </div>

        <div v-if="loading" class="loading-tip">加载中...</div>
        <div v-else-if="datasets.length === 0" class="empty-tip">
          暂无数据集，请{{ isAdmin ? '点击右上方上传' : '联系管理员上传' }}
        </div>

        <div v-else class="dataset-list">
          <div
            v-for="d in datasets"
            :key="d.id"
            class="dataset-item"
            :class="{ active: selectedId === d.id }"
            @click="selectDataset(d.id)"
          >
            <div class="dataset-name">
              {{ d.name }}
              <span :class="['idx-tag', d.has_index ? 'green' : 'gray']">
                {{ d.has_index ? '已建索引' : '未建索引' }}
              </span>
            </div>
            <div class="dataset-meta">
              <span>{{ d.n_cells.toLocaleString() }} cells</span>
              <span>·</span>
              <span>{{ d.n_genes.toLocaleString() }} genes</span>
              <span>·</span>
              <span>PCA {{ d.pca_dim }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右：详情 + 索引管理 -->
      <div class="detail-area">
        <div v-if="!selectedId" class="el-card empty-detail">
          <div class="empty-tip">请从左侧选择一个数据集</div>
        </div>

        <template v-else>
          <!-- 数据集详情 -->
          <div class="el-card detail-card">
            <div class="el-card-title">
              数据集详情
              <button v-if="isAdmin" class="el-btn danger small" @click="confirmDeleteDataset">
                🗑️ 删除数据集
              </button>
            </div>

            <div v-if="detailLoading" class="loading-tip">加载中...</div>
            <div v-else-if="detail" class="detail-grid">
              <div class="detail-row"><label>ID</label><span>{{ detail.id || selectedId }}</span></div>
              <div class="detail-row"><label>名称</label><span>{{ detail.name }}</span></div>
              <div class="detail-row"><label>文件名</label><span>{{ detail.filename }}</span></div>
              <div class="detail-row"><label>细胞数</label><span>{{ detail.n_cells?.toLocaleString() }}</span></div>
              <div class="detail-row"><label>基因数</label><span>{{ detail.n_genes?.toLocaleString() }}</span></div>
              <div class="detail-row"><label>PCA 维度</label><span>{{ detail.pca_dim }}</span></div>
              <div class="detail-row"><label>UMAP</label><span>{{ detail.has_umap ? '✓' : '✗' }}</span></div>
              <div class="detail-row"><label>t-SNE</label><span>{{ detail.has_tsne ? '✓' : '✗' }}</span></div>
              <div class="detail-row full">
                <label>细胞类型</label>
                <div class="tag-list">
                  <span v-for="t in (detail.cell_types || []).slice(0, 30)" :key="t" class="tag">{{ t }}</span>
                  <span v-if="(detail.cell_types || []).length > 30" class="tag more">
                    +{{ detail.cell_types.length - 30 }}
                  </span>
                </div>
              </div>
              <div class="detail-row full">
                <label>obs 列 ({{ (detail.obs_columns || []).length }})</label>
                <div class="tag-list">
                  <span v-for="c in (detail.obs_columns || []).slice(0, 20)" :key="c" class="tag gray">{{ c }}</span>
                  <span v-if="(detail.obs_columns || []).length > 20" class="tag more">
                    +{{ detail.obs_columns.length - 20 }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- 索引管理 -->
          <div class="el-card index-card">
            <div class="el-card-title">
              索引管理
              <div class="title-actions">
                <button class="el-btn small" @click="loadIndexStatus">🔄 刷新</button>
                <button v-if="isAdmin && indexStatus?.has_index" class="el-btn danger small" @click="confirmDeleteIndex">
                  删除索引
                </button>
              </div>
            </div>

            <div v-if="indexLoading" class="loading-tip">加载中...</div>

            <div v-else-if="indexStatus?.has_index" class="index-info">
              <div class="status-grid">
                <div class="status-cell">
                  <div class="label">距离</div>
                  <div class="value">{{ indexStatus.space?.toUpperCase() }}</div>
                </div>
                <div class="status-cell">
                  <div class="label">M</div>
                  <div class="value">{{ indexStatus.M }}</div>
                </div>
                <div class="status-cell">
                  <div class="label">ef_construction</div>
                  <div class="value">{{ indexStatus.ef_construction }}</div>
                </div>
                <div class="status-cell">
                  <div class="label">当前 ef</div>
                  <div class="value">{{ indexStatus.ef }}</div>
                </div>
                <div class="status-cell">
                  <div class="label">维度</div>
                  <div class="value">{{ indexStatus.dim }}</div>
                </div>
                <div class="status-cell">
                  <div class="label">元素数</div>
                  <div class="value">{{ indexStatus.num_elements?.toLocaleString() }}</div>
                </div>
                <div class="status-cell">
                  <div class="label">文件大小</div>
                  <div class="value">{{ formatSize(indexStatus.file_size) }}</div>
                </div>
                <div class="status-cell">
                  <div class="label">已加载到内存</div>
                  <div class="value">{{ indexStatus.loaded_in_memory ? '✓' : '✗' }}</div>
                </div>
              </div>

              <div v-if="isAdmin" class="ef-tuner">
                <label>调整查询时 ef（影响召回率与速度）</label>
                <div class="ef-row">
                  <input
                    v-model.number="newEf"
                    type="number"
                    min="10"
                    max="2000"
                    step="10"
                    class="el-input"
                  />
                  <button class="el-btn primary small" @click="updateEf">应用</button>
                  <span class="hint">推荐 50~300，越大召回越高</span>
                </div>
              </div>

              <div v-else class="hint" style="margin-top: 12px;">
                只有管理员可调整索引参数
              </div>
            </div>

            <div v-else class="no-index">
              <div class="empty-tip">该数据集尚未构建索引</div>
              <div v-if="isAdmin" class="build-form">
                <h4>构建索引</h4>
                <div class="form-row">
                  <label>space</label>
                  <select v-model="buildForm.space" class="el-select">
                    <option value="l2">L2 (欧氏距离)</option>
                    <option value="cosine">cosine (余弦)</option>
                    <option value="ip">ip (内积)</option>
                  </select>
                </div>
                <div class="form-row">
                  <label>M (双向连接数, 默认 16)</label>
                  <input v-model.number="buildForm.M" type="number" min="4" max="64" class="el-input" />
                </div>
                <div class="form-row">
                  <label>ef_construction (构建质量, 默认 200)</label>
                  <input v-model.number="buildForm.ef_construction" type="number" min="40" max="2000" class="el-input" />
                </div>
                <div class="form-row">
                  <label>ef (查询时, 默认 50)</label>
                  <input v-model.number="buildForm.ef" type="number" min="10" max="1000" class="el-input" />
                </div>
                <button class="el-btn primary" :disabled="building" @click="buildIndex">
                  {{ building ? '构建中... (可能需要数十秒)' : '🚀 开始构建' }}
                </button>
              </div>
              <div v-else class="hint">只有管理员可构建索引</div>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- 导入数据弹窗 -->
    <div v-if="showUploadModal" class="modal-mask" @click.self="closeUploadModal">
      <div class="modal-card">
        <div class="modal-title">📂 从本地导入数据集</div>
        <div class="modal-body">
          <div class="form-row">
            <label>数据集名称（可选，留空则使用文件名）</label>
            <input v-model="uploadForm.name" class="el-input" placeholder="例如: liver、pbmc3k" />
          </div>
          <div class="form-row">
            <label>选择 .h5ad 文件</label>
            <div
              class="drop-zone"
              :class="{ dragover: isDragOver }"
              @dragover.prevent="isDragOver = true"
              @dragleave.prevent="isDragOver = false"
              @drop.prevent="onDrop"
              @click="fileInput?.click()"
            >
              <input ref="fileInput" type="file" accept=".h5ad" style="display:none" @change="onFileChange" />
              <div v-if="!uploadForm.file" class="drop-hint">
                <span class="drop-icon">📁</span>
                <span>点击选择文件 或 拖拽 .h5ad 文件到此处</span>
                <span class="drop-sub">支持格式：AnnData (.h5ad)</span>
              </div>
              <div v-else class="drop-selected">
                <span class="file-icon">📄</span>
                <div class="file-detail">
                  <span class="file-name">{{ uploadForm.file.name }}</span>
                  <span class="file-size">{{ formatSize(uploadForm.file.size) }}</span>
                </div>
                <button class="el-btn small" @click.stop="clearFile">重选</button>
              </div>
            </div>
            <div v-if="fileError" class="el-alert error" style="margin-top:8px;padding:8px 12px;">{{ fileError }}</div>
          </div>
          <div v-if="uploading" class="upload-progress">
            <div class="progress-bar">
              <div class="progress-inner" :style="{ width: uploadProgress + '%' }"></div>
            </div>
            <div class="progress-label">{{ uploadProgress }}% · 正在导入中，请勿关闭页面...</div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="el-btn" @click="closeUploadModal" :disabled="uploading">取消</button>
          <button class="el-btn primary" :disabled="uploading || !uploadForm.file || !!fileError" @click="uploadFile">
            {{ uploading ? '导入中...' : '🚀 开始导入' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 通用确认弹窗 -->
    <div v-if="confirmDialog.visible" class="modal-mask" @click.self="cancelConfirm">
      <div class="modal-card sm">
        <div class="modal-title">{{ confirmDialog.title }}</div>
        <div class="modal-body">{{ confirmDialog.message }}</div>
        <div class="modal-footer">
          <button class="el-btn" @click="cancelConfirm">取消</button>
          <button class="el-btn danger" @click="confirmAction">确认</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { dataApi, searchApi } from '../api'
import { isAdmin as isAdminRef } from '../store/user'

const isAdmin = computed(() => isAdminRef.value)

// ============ State ============
const datasets = ref([])
const loading = ref(false)
const selectedId = ref('')
const detail = ref(null)
const detailLoading = ref(false)
const indexStatus = ref(null)
const indexLoading = ref(false)
const newEf = ref(50)
const error = ref('')
const success = ref('')

const buildForm = reactive({
  space: 'l2',
  M: 16,
  ef_construction: 200,
  ef: 50
})
const building = ref(false)

// 导入
const showUploadModal = ref(false)
const fileInput = ref(null)
const uploadForm = reactive({ name: '', file: null })
const uploading = ref(false)
const uploadProgress = ref(0)
const isDragOver = ref(false)
const fileError = ref('')

// 确认弹窗
const confirmDialog = reactive({
  visible: false,
  title: '',
  message: '',
  action: null
})

// ============ Helpers ============

function formatSize(bytes) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let v = bytes
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024
    i++
  }
  return `${v.toFixed(2)} ${units[i]}`
}

function showSuccess(msg) {
  success.value = msg
  error.value = ''
  setTimeout(() => { success.value = '' }, 3000)
}

function showError(msg) {
  error.value = msg
  success.value = ''
}

// ============ 列表 / 详情 ============

async function loadDatasets() {
  loading.value = true
  try {
    const res = await dataApi.list()
    datasets.value = res.data || []
    if (datasets.value.length > 0 && !selectedId.value) {
      selectDataset(datasets.value[0].id)
    } else if (selectedId.value && !datasets.value.find(d => d.id === selectedId.value)) {
      selectedId.value = ''
      detail.value = null
      indexStatus.value = null
    }
  } catch (e) {
    showError(e.message || '加载数据集失败')
  } finally {
    loading.value = false
  }
}

async function selectDataset(id) {
  selectedId.value = id
  detail.value = null
  indexStatus.value = null
  await Promise.all([loadDetail(), loadIndexStatus()])
}

async function loadDetail() {
  if (!selectedId.value) return
  detailLoading.value = true
  try {
    const res = await dataApi.detail(selectedId.value)
    detail.value = res.data
  } catch (e) {
    showError(e.message || '加载数据集详情失败')
  } finally {
    detailLoading.value = false
  }
}

async function loadIndexStatus() {
  if (!selectedId.value) return
  indexLoading.value = true
  try {
    const res = await searchApi.indexStatus(selectedId.value)
    indexStatus.value = res.data
    if (res.data?.has_index) {
      newEf.value = res.data.ef || 50
    }
  } catch (e) {
    showError(e.message || '加载索引状态失败')
  } finally {
    indexLoading.value = false
  }
}

// ============ 索引操作 ============

async function buildIndex() {
  if (!selectedId.value) return
  building.value = true
  try {
    const res = await searchApi.indexBuild(selectedId.value, { ...buildForm })
    if (res.code === 0) {
      showSuccess(`索引构建成功：${res.data?.num_elements} 元素，${formatSize(res.data?.file_size || 0)}`)
      await loadIndexStatus()
      await loadDatasets()
    } else {
      showError(res.message || '构建失败')
    }
  } catch (e) {
    showError(e.message || '构建失败')
  } finally {
    building.value = false
  }
}

async function updateEf() {
  if (!selectedId.value) return
  if (newEf.value < 10 || newEf.value > 2000) {
    showError('ef 取值范围为 10-2000')
    return
  }
  try {
    const res = await searchApi.indexUpdateEf(selectedId.value, newEf.value)
    if (res.code === 0) {
      showSuccess(`ef 已更新为 ${res.data.ef}`)
      await loadIndexStatus()
    } else {
      showError(res.message || '更新失败')
    }
  } catch (e) {
    showError(e.message || '更新失败')
  }
}

function confirmDeleteIndex() {
  confirmDialog.title = '删除索引'
  confirmDialog.message = `确定删除数据集 "${selectedId.value}" 的索引？此操作不可撤销。`
  confirmDialog.action = async () => {
    try {
      const res = await searchApi.indexDelete(selectedId.value)
      if (res.code === 0) {
        showSuccess('索引已删除')
        await loadIndexStatus()
        await loadDatasets()
      } else {
        showError(res.message || '删除失败')
      }
    } catch (e) {
      showError(e.message || '删除失败')
    }
  }
  confirmDialog.visible = true
}

// ============ 数据集操作 ============

function confirmDeleteDataset() {
  confirmDialog.title = '删除数据集'
  confirmDialog.message = `确定删除数据集 "${selectedId.value}"？将同时删除其文件和索引，且不可撤销。`
  confirmDialog.action = async () => {
    const targetId = selectedId.value
    try {
      const res = await dataApi.delete(targetId)
      if (res.code === 0) {
        showSuccess('数据集已删除')
        selectedId.value = ''
        detail.value = null
        indexStatus.value = null
        await loadDatasets()
      } else {
        showError(res.message || '删除失败')
      }
    } catch (e) {
      showError(e.message || '删除失败')
    }
  }
  confirmDialog.visible = true
}

function cancelConfirm() {
  confirmDialog.visible = false
  confirmDialog.action = null
}

async function confirmAction() {
  const action = confirmDialog.action
  confirmDialog.visible = false
  confirmDialog.action = null
  if (action) await action()
}

// ============ 数据导入 ============

function validateFile(file) {
  if (!file) return '请选择文件'
  if (!file.name.endsWith('.h5ad')) return '仅支持 .h5ad 格式文件'
  // 警告大文件（>2GB）
  if (file.size > 2 * 1024 * 1024 * 1024) return '文件超过 2GB，导入可能耗时较长'
  return ''
}

function setFile(file) {
  const err = validateFile(file)
  // 超过 2GB 只是警告，不阻止
  if (err && !err.includes('耗时')) {
    fileError.value = err
    uploadForm.file = null
    return
  }
  fileError.value = err  // 可能是警告
  uploadForm.file = file
}

function onFileChange(e) {
  const file = e.target.files[0]
  if (file) setFile(file)
}

function onDrop(e) {
  isDragOver.value = false
  const file = e.dataTransfer?.files[0]
  if (file) setFile(file)
}

function clearFile() {
  uploadForm.file = null
  fileError.value = ''
  if (fileInput.value) fileInput.value.value = ''
}

function closeUploadModal() {
  if (uploading.value) return
  showUploadModal.value = false
  uploadForm.name = ''
  uploadForm.file = null
  uploadProgress.value = 0
  fileError.value = ''
  isDragOver.value = false
  if (fileInput.value) fileInput.value.value = ''
}

async function uploadFile() {
  if (!uploadForm.file) {
    showError('请选择文件')
    return
  }
  const formData = new FormData()
  formData.append('file', uploadForm.file)
  if (uploadForm.name) formData.append('name', uploadForm.name)

  uploading.value = true
  uploadProgress.value = 0
  try {
    const res = await dataApi.upload(formData, {
      onUploadProgress: (e) => {
        if (e.total) {
          uploadProgress.value = Math.floor((e.loaded / e.total) * 100)
        }
      }
    })
    if (res.code === 0) {
      showSuccess('数据集导入成功！')
      closeUploadModal()
      await loadDatasets()
    } else {
      showError(res.message || '上传失败')
    }
  } catch (e) {
    showError(e.message || '上传失败')
  } finally {
    uploading.value = false
  }
}

onMounted(loadDatasets)
</script>

<style scoped>
.data-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-title {
  font-size: 22px;
  color: #303133;
  margin: 0;
}

.layout-grid {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 16px;
  align-items: flex-start;
}

/* ===== 列表 ===== */
.list-panel {
  position: sticky;
  top: 16px;
}

.badge {
  display: inline-block;
  background: #ecf5ff;
  color: #409eff;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;
  margin-left: 6px;
  font-weight: normal;
}

.dataset-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: calc(100vh - 220px);
  overflow-y: auto;
}

.dataset-item {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.dataset-item:hover {
  border-color: #c6e2ff;
  background: #f5faff;
}

.dataset-item.active {
  border-color: #409eff;
  background: #ecf5ff;
}

.dataset-name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.dataset-meta {
  font-size: 12px;
  color: #909399;
  display: flex;
  gap: 4px;
}

.idx-tag {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 8px;
  font-weight: normal;
}

.idx-tag.green {
  background: #e1f3d8;
  color: #67c23a;
}

.idx-tag.gray {
  background: #f4f4f5;
  color: #909399;
}

/* ===== 详情区 ===== */
.detail-area {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.empty-detail,
.empty-tip {
  padding: 40px 20px;
  text-align: center;
  color: #909399;
}

.loading-tip {
  padding: 20px;
  text-align: center;
  color: #909399;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 24px;
}

.detail-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.detail-row.full {
  grid-column: 1 / -1;
  flex-direction: column;
  gap: 6px;
}

.detail-row label {
  color: #909399;
  font-size: 13px;
  min-width: 80px;
}

.detail-row span {
  color: #303133;
  font-size: 14px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag {
  font-size: 12px;
  padding: 2px 8px;
  background: #ecf5ff;
  color: #409eff;
  border-radius: 10px;
}

.tag.gray {
  background: #f4f4f5;
  color: #606266;
}

.tag.more {
  background: #fdf6ec;
  color: #e6a23c;
}

/* ===== 索引区 ===== */
.title-actions {
  display: flex;
  gap: 8px;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.status-cell {
  background: #f5f7fa;
  border-radius: 4px;
  padding: 10px 12px;
}

.status-cell .label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.status-cell .value {
  font-size: 16px;
  color: #303133;
  font-weight: 600;
}

.ef-tuner {
  border-top: 1px dashed #ebeef5;
  padding-top: 12px;
}

.ef-tuner > label {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
  color: #606266;
}

.ef-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.ef-row .el-input {
  width: 140px;
}

.hint {
  font-size: 12px;
  color: #909399;
}

.build-form {
  margin-top: 16px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 6px;
}

.build-form h4 {
  margin: 0 0 12px;
  color: #303133;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 12px;
}

.form-row label {
  font-size: 12px;
  color: #909399;
}

/* ===== 弹窗 ===== */
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-card {
  background: #fff;
  border-radius: 8px;
  width: 480px;
  max-width: 90vw;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.modal-card.sm {
  width: 380px;
}

.modal-title {
  padding: 16px 20px;
  border-bottom: 1px solid #ebeef5;
  font-size: 16px;
  font-weight: 600;
}

.modal-body {
  padding: 20px;
}

.modal-footer {
  padding: 12px 20px;
  border-top: 1px solid #ebeef5;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.file-info {
  margin-top: 8px;
  font-size: 12px;
  color: #67c23a;
}

/* ===== 拖拽导入区域 ===== */
.drop-zone {
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  padding: 32px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  background: #fafbfc;
}

.drop-zone:hover {
  border-color: #409eff;
  background: #f5faff;
}

.drop-zone.dragover {
  border-color: #409eff;
  background: #ecf5ff;
  box-shadow: 0 0 0 4px rgba(64, 158, 255, 0.1);
}

.drop-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #909399;
}

.drop-icon {
  font-size: 36px;
}

.drop-sub {
  font-size: 12px;
  color: #c0c4cc;
}

.drop-selected {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: center;
}

.file-icon {
  font-size: 28px;
}

.file-detail {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.file-name {
  color: #303133;
  font-weight: 600;
  font-size: 14px;
}

.file-size {
  color: #909399;
  font-size: 12px;
}

.upload-progress {
  margin-top: 12px;
}

.progress-bar {
  height: 8px;
  background: #ebeef5;
  border-radius: 4px;
  overflow: hidden;
}

.progress-inner {
  height: 100%;
  background: linear-gradient(90deg, #67c23a, #409eff);
  transition: width 0.2s;
}

.progress-label {
  font-size: 12px;
  color: #606266;
  margin-top: 4px;
  text-align: right;
}

.no-index {
  padding: 8px 0;
}

@media (max-width: 768px) {
  .layout-grid {
    grid-template-columns: 1fr;
  }
  .list-panel {
    position: static;
  }
  .detail-grid {
    grid-template-columns: 1fr;
  }
  .status-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
