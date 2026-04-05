<template>
  <div class="chart-list-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">榜单中心</h1>
        <span class="chart-count">{{ charts.length }} 个榜单</span>
      </div>
    </div>

    <div v-loading="loading" class="charts-container">
      <!-- JavDB 榜单区 -->
      <div v-if="javdbCharts.length > 0" class="chart-section">
        <div class="section-header">
          <div class="section-icon javdb">
            <el-icon size="24"><Trophy /></el-icon>
          </div>
          <div class="section-info">
            <h2 class="section-title">JavDB 榜单</h2>
            <span class="section-desc">TOP250 + 年度榜单</span>
          </div>
        </div>

        <div class="charts-grid">
          <div
            v-for="chart in javdbCharts"
            :key="chart.name"
            class="chart-card"
            :class="{ 'is-year': chart.year }"
            @click="goToChart(chart.name)"
          >
            <div class="card-header">
              <div class="chart-icon javdb-icon">
                <el-icon size="24"><Trophy /></el-icon>
              </div>
              <div class="chart-meta">
                <h3 class="chart-name">{{ chart.display_name }}</h3>
                <span v-if="chart.year" class="chart-year">{{ chart.year }} 年</span>
                <span v-else class="chart-type">TOP250</span>
              </div>
            </div>

            <div class="coverage-section">
              <div class="coverage-header">
                <span class="coverage-label">收藏进度</span>
                <span class="coverage-percent">{{ chart.coverage_percent }}%</span>
              </div>
              <div class="progress-track">
                <div
                  class="progress-bar"
                  :style="{ width: chart.coverage_percent + '%' }"
                  :class="getProgressClass(chart.coverage_percent)"
                ></div>
              </div>
            </div>

            <div class="stats-row">
              <div class="stat-box">
                <span class="stat-value collected">{{ chart.collected }}</span>
                <span class="stat-label">已收藏</span>
              </div>
              <div class="stat-box">
                <span class="stat-value missing">{{ chart.missing }}</span>
                <span class="stat-label">缺失</span>
              </div>
              <div class="stat-box">
                <span class="stat-value">{{ chart.actual_count || chart.total_count }}</span>
                <span class="stat-label">总数</span>
              </div>
            </div>

            <div class="card-actions" @click.stop>
              <button class="action-btn secondary" @click="goToGaps(chart.name)">
                <el-icon><View /></el-icon>
                缺口
              </button>
              <button class="action-btn" :disabled="refreshing === chart.name" @click="refreshChart(chart.name)">
                <el-icon v-if="refreshing !== chart.name"><Refresh /></el-icon>
                <el-icon v-else class="spin"><Loading /></el-icon>
                更新
              </button>
            </div>

            <div v-if="chart.last_updated" class="update-time">
              <el-icon><Clock /></el-icon>
              {{ formatDate(chart.last_updated) }}
            </div>
          </div>
        </div>
      </div>

      <!-- JavLibrary 榜单区 -->
      <div v-if="javlibCharts.length > 0" class="chart-section">
        <div class="section-header">
          <div class="section-icon javlib">
            <el-icon size="24"><Trophy /></el-icon>
          </div>
          <div class="section-info">
            <h2 class="section-title">JavLibrary 榜单</h2>
            <span class="section-desc">TOP500</span>
          </div>
        </div>

        <div class="charts-grid">
          <div
            v-for="chart in javlibCharts"
            :key="chart.name"
            class="chart-card"
            @click="goToChart(chart.name)"
          >
            <div class="card-header">
              <div class="chart-icon javlib-icon">
                <el-icon size="24"><Trophy /></el-icon>
              </div>
              <div class="chart-meta">
                <h3 class="chart-name">{{ chart.display_name }}</h3>
                <span class="chart-type">TOP500</span>
              </div>
            </div>

            <div class="coverage-section">
              <div class="coverage-header">
                <span class="coverage-label">收藏进度</span>
                <span class="coverage-percent">{{ chart.coverage_percent }}%</span>
              </div>
              <div class="progress-track">
                <div
                  class="progress-bar"
                  :style="{ width: chart.coverage_percent + '%' }"
                  :class="getProgressClass(chart.coverage_percent)"
                ></div>
              </div>
            </div>

            <div class="stats-row">
              <div class="stat-box">
                <span class="stat-value collected">{{ chart.collected }}</span>
                <span class="stat-label">已收藏</span>
              </div>
              <div class="stat-box">
                <span class="stat-value missing">{{ chart.missing }}</span>
                <span class="stat-label">缺失</span>
              </div>
              <div class="stat-box">
                <span class="stat-value">{{ chart.actual_count || chart.total_count }}</span>
                <span class="stat-label">总数</span>
              </div>
            </div>

            <div class="card-actions" @click.stop>
              <button class="action-btn secondary" @click="goToGaps(chart.name)">
                <el-icon><View /></el-icon>
                缺口
              </button>
              <button class="action-btn" :disabled="refreshing === chart.name" @click="refreshChart(chart.name)">
                <el-icon v-if="refreshing !== chart.name"><Refresh /></el-icon>
                <el-icon v-else class="spin"><Loading /></el-icon>
                更新
              </button>
            </div>

            <div v-if="chart.last_updated" class="update-time">
              <el-icon><Clock /></el-icon>
              {{ formatDate(chart.last_updated) }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!loading && charts.length === 0" class="empty-state">
      <div class="empty-icon">
        <el-icon size="64"><Trophy /></el-icon>
      </div>
      <h3 class="empty-title">暂无榜单</h3>
      <p class="empty-desc">前往设置页面添加榜单数据源</p>
      <el-button type="primary" @click="$router.push('/settings')">前往设置</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Trophy,
  Refresh,
  View,
  Clock,
  Loading
} from '@element-plus/icons-vue'
import { chartsApi } from '../api'

const router = useRouter()
const charts = ref([])
const loading = ref(false)
const refreshing = ref(null)

const javdbCharts = computed(() => {
  return charts.value.filter(c => c.source === 'javdb' || c.name.includes('javdb') || c.name.includes('JavDB'))
})

const javlibCharts = computed(() => {
  return charts.value.filter(c => c.source === 'javlibrary' || c.name.includes('javlib') || c.name.includes('JavLibrary'))
})

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
    setTimeout(fetchCharts, 2000)
  } catch (e) {
    ElMessage.error('刷新失败')
  } finally {
    refreshing.value = null
  }
}

const getProgressClass = (percent) => {
  if (percent >= 80) return 'excellent'
  if (percent >= 50) return 'good'
  if (percent >= 20) return 'normal'
  return 'low'
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) return '今天更新'
  if (days === 1) return '昨天更新'
  if (days < 7) return `${days} 天前更新`
  return `${date.getMonth() + 1}月${date.getDate()}日更新`
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

/* 页面头部 */
.page-header {
  margin-bottom: 28px;
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: 16px;
}

.page-title {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.5px;
}

.chart-count {
  color: var(--text-muted);
  font-size: 15px;
  font-weight: 500;
}

/* 榜单分区容器 */
.charts-container {
  display: flex;
  flex-direction: column;
  gap: 40px;
}

/* 榜单分区 */
.chart-section {
  background: var(--bg-secondary);
  border-radius: var(--radius-xl);
  padding: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-light);
}

.section-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.section-icon.javdb {
  background: linear-gradient(135deg, #E8A598, #D4958A);
}

.section-icon.javlib {
  background: linear-gradient(135deg, #8FB8CD, #7AA8BD);
}

.section-info {
  flex: 1;
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.section-desc {
  font-size: 13px;
  color: var(--text-tertiary);
}

/* 榜单网格 */
.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.chart-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 20px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}

.chart-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-hover);
}

.chart-card.is-year {
  border-left: 3px solid #E8A598;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.chart-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chart-icon.javdb-icon {
  background: linear-gradient(135deg, #E8A598, #D4958A);
}

.chart-icon.javlib-icon {
  background: linear-gradient(135deg, #8FB8CD, #7AA8BD);
}

.chart-meta {
  flex: 1;
}

.chart-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.chart-year {
  font-size: 12px;
  color: #E8A598;
  font-weight: 500;
}

.chart-type {
  font-size: 12px;
  color: var(--text-tertiary);
  padding: 2px 8px;
  background: var(--bg-tertiary);
  border-radius: 10px;
}

/* 进度条 */
.coverage-section {
  margin-bottom: 16px;
}

.coverage-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.coverage-label {
  font-size: 12px;
  color: var(--text-tertiary);
}

.coverage-percent {
  font-size: 18px;
  font-weight: 700;
  color: var(--primary-color);
}

.progress-track {
  height: 8px;
  background: var(--bg-tertiary);
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.progress-bar.excellent {
  background: linear-gradient(90deg, #8FB996, #7AA882);
}

.progress-bar.good {
  background: linear-gradient(90deg, #D4A574, #C49464);
}

.progress-bar.normal {
  background: linear-gradient(90deg, #E8A598, #D4958A);
}

.progress-bar.low {
  background: linear-gradient(90deg, #B8A9C9, #A899B9);
}

/* 统计行 */
.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 16px;
}

.stat-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 8px;
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.stat-value.collected {
  color: var(--accent-green);
}

.stat-value.missing {
  color: #E8A598;
}

.stat-label {
  font-size: 11px;
  color: var(--text-tertiary);
}

/* 操作按钮 */
.card-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 8px;
  background: var(--primary-gradient);
  border: none;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
  color: #fff;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(232, 165, 152, 0.35);
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.action-btn.secondary {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.action-btn.secondary:hover {
  background: var(--border-color);
  box-shadow: none;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 更新时间 */
.update-time {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border-light);
  font-size: 11px;
  color: var(--text-muted);
}

.update-time .el-icon {
  font-size: 12px;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 80px 20px;
}

.empty-icon {
  width: 120px;
  height: 120px;
  margin: 0 auto 24px;
  background: var(--bg-secondary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
}

.empty-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.empty-desc {
  font-size: 14px;
  color: var(--text-muted);
  margin-bottom: 24px;
}

/* 响应式 */
@media (max-width: 768px) {
  .page-title {
    font-size: 24px;
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }

  .chart-section {
    padding: 16px;
  }

  .chart-card {
    padding: 16px;
  }
}
</style>
