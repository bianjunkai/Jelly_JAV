<template>
  <div class="dashboard-view">
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <el-card class="stat-card">
        <div class="stat-icon">📁</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_movies || 0 }}</div>
          <div class="stat-label">影片总数</div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-icon">⭐</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.avg_score || 0 }}</div>
          <div class="stat-label">平均评分</div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-icon">👥</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.followed_actors || 0 }}</div>
          <div class="stat-label">关注演员</div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-icon">📝</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.pending_todos || 0 }}</div>
          <div class="stat-label">待看清单</div>
        </div>
      </el-card>
    </div>

    <!-- 最新报告 -->
    <div class="section" v-if="latestReports">
      <h2 class="section-title">📊 最新报告</h2>
      <div class="reports-row">
        <el-card v-if="latestReports.weekly" class="report-card" @click="$router.push('/discover')">
          <div class="report-type">📊 周报</div>
          <div class="report-info">
            <span>{{ latestReports.weekly.data?.total_count || 0 }} 部新片</span>
            <span class="report-date">{{ formatDate(latestReports.weekly.generated_at) }}</span>
          </div>
        </el-card>

        <el-card v-if="latestReports.monthly" class="report-card" @click="$router.push('/discover')">
          <div class="report-type">📈 月报</div>
          <div class="report-info">
            <span>{{ latestReports.monthly.data?.total_count || 0 }} 部评分上升</span>
            <span class="report-date">{{ formatDate(latestReports.monthly.generated_at) }}</span>
          </div>
        </el-card>

        <el-card v-if="latestReports.annual" class="report-card" @click="$router.push('/discover')">
          <div class="report-type">🏆 年报</div>
          <div class="report-info">
            <span>{{ latestReports.annual.data?.total_missing || 0 }} 部缺失</span>
            <span class="report-date">{{ formatDate(latestReports.annual.generated_at) }}</span>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 榜单概览 -->
    <div class="section">
      <h2 class="section-title">🏆 榜单概览</h2>
      <div class="charts-preview" v-if="charts.length">
        <el-card
          v-for="chart in charts.slice(0, 4)"
          :key="chart.name"
          class="chart-preview-card"
          @click="$router.push(`/charts/${encodeURIComponent(chart.name)}`)"
        >
          <div class="chart-name">{{ chart.display_name }}</div>
          <div class="chart-progress">
            <el-progress
              :percentage="chart.coverage_percent"
              :stroke-width="8"
              :show-text="false"
            />
          </div>
          <div class="chart-stats">
            <span>{{ chart.collected }}/{{ chart.total_count }}</span>
            <span class="coverage">{{ chart.coverage_percent }}%</span>
          </div>
        </el-card>
      </div>
      <el-button v-if="charts.length > 4" text @click="$router.push('/charts')">
        查看全部榜单...
      </el-button>
    </div>

    <!-- 快捷操作 -->
    <div class="section">
      <h2 class="section-title">⚡ 快捷操作</h2>
      <div class="actions-row">
        <el-button type="primary" @click="syncJellyfin" :loading="syncing">
          <el-icon><Refresh /></el-icon>
          同步 Jellyfin
        </el-button>
        <el-button @click="updateScores" :loading="updatingScores">
          <el-icon><Star /></el-icon>
          更新评分
        </el-button>
        <el-button @click="generateWeeklyReport">
          <el-icon><Document /></el-icon>
          生成周报
        </el-button>
        <el-button @click="$router.push('/todo')">
          <el-icon><List /></el-icon>
          查看待看清单
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { statsApi, reportsApi, chartsApi, tasksApi } from '../api'

const stats = ref({})
const latestReports = ref(null)
const charts = ref([])
const syncing = ref(false)
const updatingScores = ref(false)

const fetchStats = async () => {
  try {
    stats.value = await statsApi.get()
  } catch (e) {
    console.error('Failed to fetch stats:', e)
  }
}

const fetchReports = async () => {
  try {
    latestReports.value = await reportsApi.latest()
  } catch (e) {
    console.error('Failed to fetch reports:', e)
  }
}

const fetchCharts = async () => {
  try {
    charts.value = await chartsApi.list()
  } catch (e) {
    console.error('Failed to fetch charts:', e)
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}/${date.getDate()}`
}

const syncJellyfin = async () => {
  syncing.value = true
  try {
    await tasksApi.sync()
    ElMessage.success('同步任务已启动')
  } catch (e) {
    ElMessage.error('同步失败')
  } finally {
    syncing.value = false
  }
}

const updateScores = async () => {
  updatingScores.value = true
  try {
    await tasksApi.updateScores()
    ElMessage.success('评分更新任务已启动')
  } catch (e) {
    ElMessage.error('更新失败')
  } finally {
    updatingScores.value = false
  }
}

const generateWeeklyReport = async () => {
  try {
    await reportsApi.generate('weekly')
    ElMessage.success('周报生成成功')
    await fetchReports()
  } catch (e) {
    ElMessage.error('生成失败')
  }
}

onMounted(() => {
  fetchStats()
  fetchReports()
  fetchCharts()
})
</script>

<style scoped>
.dashboard-view {
  max-width: 1200px;
  margin: 0 auto;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: #1a1a1a;
}

.stat-icon {
  font-size: 32px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #fff;
}

.stat-label {
  font-size: 13px;
  color: #666;
}

.section {
  margin-bottom: 32px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
}

.reports-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.report-card {
  background: #1a1a1a;
  cursor: pointer;
  transition: all 0.2s;
}

.report-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

.report-type {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}

.report-info {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #666;
}

.charts-preview {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.chart-preview-card {
  background: #1a1a1a;
  cursor: pointer;
  transition: all 0.2s;
}

.chart-preview-card:hover {
  transform: translateY(-2px);
}

.chart-name {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
}

.chart-progress {
  margin-bottom: 8px;
}

.chart-stats {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #666;
}

.coverage {
  color: #4ade80;
  font-weight: 600;
}

.actions-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

@media (max-width: 768px) {
  .stats-grid,
  .reports-row,
  .charts-preview {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
