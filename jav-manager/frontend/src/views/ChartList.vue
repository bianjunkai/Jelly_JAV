<template>
  <div class="chart-list-view">
    <div class="page-header">
      <h1 class="page-title">榜单中心</h1>
    </div>

    <div v-loading="loading" class="chart-grid">
      <el-card v-for="chart in charts" :key="chart.name" class="chart-card" shadow="hover">
        <div class="chart-header">
          <h3 class="chart-name">{{ chart.display_name }}</h3>
          <span class="chart-year" v-if="chart.year">{{ chart.year }}</span>
        </div>

        <div class="chart-stats">
          <div class="stat-item">
            <span class="stat-label">影片数</span>
            <span class="stat-value">{{ chart.total_count }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">已收藏</span>
            <span class="stat-value collected">{{ chart.collected }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">缺失</span>
            <span class="stat-value missing">{{ chart.missing }}</span>
          </div>
        </div>

        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: chart.coverage_percent + '%' }"></div>
        </div>
        <div class="progress-text">{{ chart.coverage_percent }}% 覆盖率</div>

        <div class="chart-actions">
          <el-button type="primary" @click="goToChart(chart.name)">
            查看榜单
          </el-button>
          <el-button @click="goToGaps(chart.name)">
            缺口分析
          </el-button>
          <el-button @click="refreshChart(chart.name)" :loading="refreshing === chart.name">
            更新
          </el-button>
        </div>

        <div class="chart-meta">
          <span v-if="chart.last_updated">上次更新: {{ formatDate(chart.last_updated) }}</span>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { chartsApi } from '../api'

const router = useRouter()
const charts = ref([])
const loading = ref(false)
const refreshing = ref(null)

const fetchCharts = async () => {
  loading.value = true
  try {
    charts.value = await chartsApi.list()
  } catch (e) {
    ElMessage.error('获取榜单列表失败')
  } finally {
    loading.value = false
  }
}

const goToChart = (name) => {
  router.push(`/charts/${encodeURIComponent(name)}`)
}

const goToGaps = (name) => {
  router.push(`/charts/${encodeURIComponent(name)}/gaps`)
}

const refreshChart = async (name) => {
  refreshing.value = name
  try {
    await chartsApi.refresh(name)
    ElMessage.success('榜单刷新已启动')
    // 延迟刷新列表
    setTimeout(fetchCharts, 2000)
  } catch (e) {
    ElMessage.error('刷新失败')
  } finally {
    refreshing.value = null
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}/${date.getDate()}`
}

onMounted(() => {
  fetchCharts()
})
</script>

<style scoped>
.chart-list-view {
  max-width: 1200px;
  margin: 0 auto;
}

.chart-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.chart-card {
  background: #1a1a1a;
  border: 1px solid #333;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.chart-name {
  font-size: 18px;
  font-weight: 600;
}

.chart-year {
  background: #e50914;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.chart-stats {
  display: flex;
  gap: 24px;
  margin-bottom: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 12px;
  color: #666;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
}

.stat-value.collected {
  color: #4ade80;
}

.stat-value.missing {
  color: #ef4444;
}

.progress-bar {
  height: 8px;
  background: #333;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #e50914, #ff6b6b);
  transition: width 0.3s;
}

.progress-text {
  font-size: 12px;
  color: #666;
  text-align: right;
  margin-bottom: 16px;
}

.chart-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.chart-meta {
  font-size: 12px;
  color: #666;
}
</style>
