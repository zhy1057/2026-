<template>
  <div class="visual-page">
    <h2 class="page-title">📊 细胞嵌入可视化</h2>

    <!-- 控制面板 -->
    <div class="el-card control-bar">
      <div class="ctrl-group">
        <label>数据集</label>
        <select v-model="form.dataset_id" class="el-select" @change="loadEmbedding">
          <option value="" disabled>选择数据集</option>
          <option v-for="d in datasets" :key="d.id" :value="d.id">
            {{ d.name }} ({{ d.n_cells.toLocaleString() }})
          </option>
        </select>
      </div>

      <div class="ctrl-group">
        <label>嵌入</label>
        <select v-model="form.type" class="el-select" @change="loadEmbedding">
          <option value="umap">UMAP</option>
          <option value="tsne">t-SNE</option>
        </select>
      </div>

      <div class="ctrl-group">
        <label>采样点数</label>
        <select v-model.number="form.max_points" class="el-select" @change="loadEmbedding">
          <option :value="2000">2,000</option>
          <option :value="5000">5,000</option>
          <option :value="8000">8,000</option>
          <option :value="15000">15,000</option>
          <option :value="30000">30,000</option>
        </select>
      </div>

      <div class="ctrl-group">
        <label>着色字段</label>
        <select v-model="form.color_by" class="el-select" @change="loadEmbedding">
          <option v-for="col in colorByOptions" :key="col" :value="col">{{ col }}</option>
        </select>
      </div>

      <div class="ctrl-group ctrl-spacer">
        <button class="el-btn" @click="loadEmbedding" :disabled="loading">
          {{ loading ? '加载中...' : '🔄 刷新' }}
        </button>
      </div>
    </div>

    <!-- 检索高亮控制 -->
    <div class="el-card highlight-bar">
      <div class="ctrl-group">
        <label>高亮检索结果（细胞编号，逗号分隔）</label>
        <div class="hl-input-row">
          <input
            v-model="highlightText"
            class="el-input"
            placeholder="例如: 100, 200, 300"
          />
          <button class="el-btn primary" @click="applyHighlight">🔍 高亮检索</button>
          <button class="el-btn" @click="clearHighlight">清除</button>
        </div>
      </div>
    </div>

    <!-- 状态信息 -->
    <div v-if="embedding" class="status-bar">
      <span class="status-item">总细胞: <strong>{{ embedding.total_cells.toLocaleString() }}</strong></span>
      <span class="status-item">已渲染: <strong>{{ embedding.sampled_cells.toLocaleString() }}</strong></span>
      <span class="status-item">类别数: <strong>{{ embedding.num_categories }}</strong></span>
      <span v-if="embedding.sampled" class="status-item warning">已采样</span>
      <span v-if="highlightCount > 0" class="status-item highlight">
        高亮: <strong>{{ highlightCount }}</strong>
      </span>
    </div>

    <div v-if="error" class="el-alert error">{{ error }}</div>

    <!-- 散点图 -->
    <div class="el-card chart-wrapper">
      <div ref="chartRef" class="chart"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, nextTick, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { dataApi, visualApi } from '../api'

const route = useRoute()

const datasets = ref([])
const colorByOptions = ref(['cell_type'])
const embedding = ref(null)
const error = ref('')
const loading = ref(false)
const highlightText = ref('')
const highlightedIndices = ref([])
const highlightedCoords = ref([])

const chartRef = ref(null)
let chart = null

const form = reactive({
  dataset_id: '',
  type: 'umap',
  max_points: 8000,
  color_by: 'cell_type'
})

const highlightCount = computed(() => highlightedCoords.value.length)

// ============ 颜色生成 ============
// 一组对色觉友好且区分度高的颜色
const COLOR_PALETTE = [
  '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de',
  '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#5d6dba',
  '#a6cee3', '#1f78b4', '#b2df8a', '#33a02c', '#fb9a99',
  '#e31a1c', '#fdbf6f', '#ff7f00', '#cab2d6', '#6a3d9a',
  '#ffff99', '#b15928', '#8dd3c7', '#bebada', '#fb8072',
  '#80b1d3', '#fdb462', '#b3de69', '#fccde5', '#bc80bd'
]

function colorAt(i) {
  return COLOR_PALETTE[i % COLOR_PALETTE.length]
}

// ============ 数据加载 ============

async function loadDatasets() {
  try {
    const res = await dataApi.list()
    datasets.value = (res.data || []).filter(d => d.has_umap !== false)
    if (datasets.value.length > 0 && !form.dataset_id) {
      form.dataset_id = datasets.value[0].id
      await loadDatasetCols()
      await loadEmbedding()
    }
  } catch (e) {
    error.value = e.message || '加载数据集失败'
  }
}

async function loadDatasetCols() {
  if (!form.dataset_id) return
  try {
    const res = await dataApi.detail(form.dataset_id)
    if (res.data?.obs_columns) {
      // 仅保留几个适合分类着色的字段
      const candidates = ['cell_type', 'donor_id', 'sex', 'tissue', 'disease',
                          'AgeGroup', 'Phase', 'Treatment', 'assay']
      colorByOptions.value = candidates.filter(c => res.data.obs_columns.includes(c))
      if (colorByOptions.value.length === 0) {
        colorByOptions.value = ['cell_type']
      }
      if (!colorByOptions.value.includes(form.color_by)) {
        form.color_by = colorByOptions.value[0]
      }
    }
  } catch (e) {
    /* silent */
  }
}

async function loadEmbedding() {
  if (!form.dataset_id) return
  await loadDatasetCols()
  loading.value = true
  error.value = ''
  try {
    const res = await visualApi.embedding(form.dataset_id, {
      type: form.type,
      max_points: form.max_points,
      color_by: form.color_by
    })
    if (res.code === 0) {
      embedding.value = res.data
      renderChart()
    } else {
      error.value = res.message || '加载失败'
    }
  } catch (e) {
    error.value = e.message || '加载嵌入失败'
  } finally {
    loading.value = false
  }
}

// ============ 渲染 ============

function renderChart() {
  if (!chart || !embedding.value) return

  const series = embedding.value.series.map((s, idx) => ({
    name: `${s.name} (${s.count})`,
    type: 'scatter',
    data: s.data,
    symbolSize: 4,
    large: true,
    largeThreshold: 1000,
    progressive: 4000,
    progressiveThreshold: 6000,
    itemStyle: {
      color: colorAt(idx),
      opacity: 0.7
    },
    emphasis: {
      itemStyle: { opacity: 1, borderColor: '#000', borderWidth: 1 }
    }
  }))

  // 高亮 series
  if (highlightedCoords.value.length > 0) {
    series.push({
      name: '🔍 检索结果',
      type: 'scatter',
      data: highlightedCoords.value.map(c => [c.x, c.y, c.cell_index, c.cell_type]),
      symbolSize: 16,
      symbol: 'pin',
      itemStyle: {
        color: '#ff4d4f',
        borderColor: '#fff',
        borderWidth: 2,
        shadowBlur: 8,
        shadowColor: 'rgba(255, 77, 79, 0.6)'
      },
      label: {
        show: true,
        formatter: (p) => `#${p.value[2]}`,
        fontSize: 10,
        position: 'top',
        backgroundColor: 'rgba(255,255,255,0.8)',
        padding: [2, 4],
        borderRadius: 2
      },
      z: 100
    })
  }

  const option = {
    title: {
      text: `${form.type.toUpperCase()} · ${form.color_by}`,
      left: 'center',
      top: 8,
      textStyle: { fontSize: 14, color: '#606266' }
    },
    tooltip: {
      trigger: 'item',
      formatter: (p) => {
        if (p.seriesName.startsWith('🔍')) {
          return `<b>检索结果</b><br/>细胞 #${p.value[2]}<br/>类型: ${p.value[3] || '-'}`
        }
        return `<b>${p.seriesName}</b><br/>细胞 #${p.value[2]}<br/>(${p.value[0].toFixed(2)}, ${p.value[1].toFixed(2)})`
      }
    },
    legend: {
      type: 'scroll',
      orient: 'vertical',
      right: 10,
      top: 50,
      bottom: 30,
      itemWidth: 12,
      itemHeight: 12,
      textStyle: { fontSize: 12 }
    },
    grid: {
      left: 50,
      right: 220,
      top: 50,
      bottom: 60
    },
    xAxis: {
      name: form.type === 'umap' ? 'UMAP-1' : 't-SNE-1',
      nameLocation: 'middle',
      nameGap: 25,
      type: 'value',
      scale: true,
      axisLine: { lineStyle: { color: '#909399' } },
      splitLine: { lineStyle: { type: 'dashed', color: '#ebeef5' } }
    },
    yAxis: {
      name: form.type === 'umap' ? 'UMAP-2' : 't-SNE-2',
      nameLocation: 'middle',
      nameGap: 35,
      type: 'value',
      scale: true,
      axisLine: { lineStyle: { color: '#909399' } },
      splitLine: { lineStyle: { type: 'dashed', color: '#ebeef5' } }
    },
    dataZoom: [
      { type: 'inside', xAxisIndex: 0 },
      { type: 'inside', yAxisIndex: 0 }
    ],
    toolbox: {
      right: 10,
      top: 8,
      feature: {
        dataZoom: { yAxisIndex: 'all' },
        restore: {},
        saveAsImage: { title: '保存图片' }
      }
    },
    animation: false,
    series
  }

  chart.setOption(option, true)
}

// ============ 高亮 ============

async function applyHighlight() {
  error.value = ''
  if (!form.dataset_id) {
    error.value = '请先选择数据集'
    return
  }
  const indices = highlightText.value
    .split(/[,\s]+/)
    .filter(s => s.length > 0)
    .map(s => parseInt(s, 10))
    .filter(n => !isNaN(n))

  if (indices.length === 0) {
    error.value = '请输入有效的细胞编号'
    return
  }

  highlightedIndices.value = indices
  try {
    const res = await visualApi.cellsCoords(form.dataset_id, indices, form.type)
    if (res.code === 0) {
      highlightedCoords.value = res.data || []
      renderChart()
    } else {
      error.value = res.message || '高亮失败'
    }
  } catch (e) {
    error.value = e.message || '高亮失败'
  }
}

function clearHighlight() {
  highlightText.value = ''
  highlightedIndices.value = []
  highlightedCoords.value = []
  renderChart()
}

// ============ 生命周期 ============

function handleResize() {
  chart && chart.resize()
}

onMounted(async () => {
  await nextTick()
  chart = echarts.init(chartRef.value)
  window.addEventListener('resize', handleResize)
  await loadDatasets()

  // 从路由查询参数读取高亮信息（来自 Search 页面跳转）
  if (route.query.highlight) {
    highlightText.value = String(route.query.highlight)
    if (route.query.dataset_id) {
      form.dataset_id = String(route.query.dataset_id)
    }
    // 等数据加载完后自动高亮
    watch(embedding, (val) => {
      if (val && highlightText.value) {
        applyHighlight()
      }
    }, { once: true })
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chart && chart.dispose()
  chart = null
})
</script>

<style scoped>
.visual-page {
  padding: 0;
}

.page-title {
  font-size: 22px;
  color: #303133;
  margin-bottom: 16px;
}

.control-bar,
.highlight-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: flex-end;
  padding: 16px 24px;
  margin-bottom: 12px;
}

.highlight-bar {
  padding: 12px 24px;
}

.highlight-bar .ctrl-group {
  flex: 1;
  min-width: 0;
}

.ctrl-group {
  display: flex;
  flex-direction: column;
  min-width: 140px;
}

.ctrl-group label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.ctrl-spacer {
  margin-left: auto;
  justify-content: flex-end;
}

.hl-input-row {
  display: flex;
  gap: 8px;
}

.hl-input-row .el-input {
  flex: 1;
}

.status-bar {
  display: flex;
  gap: 16px;
  align-items: center;
  padding: 8px 16px;
  font-size: 13px;
  color: #606266;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 12px;
}

.status-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.status-item.warning {
  color: #e6a23c;
  background: #fdf6ec;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
}

.status-item.highlight {
  color: #f56c6c;
}

.chart-wrapper {
  padding: 8px;
}

.chart {
  width: 100%;
  height: 640px;
}

@media (max-width: 768px) {
  .ctrl-group {
    min-width: 120px;
  }
  .chart {
    height: 480px;
  }
}
</style>
