<template>
  <div class="dashboard-view">
    <!-- 欢迎区域 -->
    <div class="welcome-section">
      <h1 class="welcome-title">欢迎回来</h1>
      <p class="welcome-subtitle">管理你的影片收藏，追踪榜单动态</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div v-for="stat in statsList" :key="stat.key" class="stat-card" @click="navigateTo(stat.route)">
        <div class="stat-icon" :style="{ background: stat.bgColor }">
          <el-icon :size="24" :color="stat.iconColor">
            <component :is="stat.icon" />
          </el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
        <div class="stat-trend" v-if="stat.trend">
          <span :class="stat.trend > 0 ? 'trend-up' : 'trend-down'">
            {{ stat.trend > 0 ? '+' : '' }}{{ stat.trend }}
          </span>
        </div>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="dashboard-content">
      <!-- 左侧：榜单概览 -->
      <div class="content-left">
        <div class="section-header">
          <h2 class="section-title">
            <el-icon><Trophy /></el-icon>
            榜单概览
          </h2>
          <el-button text @click="$router.push('/charts')">
            查看全部
            <el-icon class="btn-icon"><ArrowRight /></el-icon>
          </el-button>
        </div>

        <div class="charts-grid">
          <div
            v-for="chart in charts.slice(0, 4)"
            :key="chart.name"
            class="chart-card"
            @click="$router.push(`/charts/${encodeURIComponent(chart.name)}`)"
          >
            <div class="chart-header">
              <h3 class="chart-name">{{ chart.display_name }}</h3>
              <span v-if="chart.year" class="chart-year">{{ chart.year }}</span>
            </div>

            <div class="chart-progress">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: chart.coverage_percent + '%' }"></div>
              </div>
              <span class="progress-text">{{ chart.coverage_percent }}%</span>
            </div>

            <div class="chart-stats">
              <div class="chart-stat">
                <span class="stat-num collected">{{ chart.collected }}</span>
                <span class="stat-desc">已收藏</span>
              </div>
              <div class="chart-stat">
                <span class="stat-num missing">{{ chart.missing }}</span>
                <span class="stat-desc">缺失</span>
              </div>
              <div class="chart-stat">
                <span class="stat-num">{{ chart.total_count }}</span>
                <span class="stat-desc">总数</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 最新报告 -->
        <div class="section-header" style="margin-top: 32px;">
          <h2 class="section-title">
            <el-icon><Document /></el-icon>
            最新报告
          </h2>
          <el-button text @click="$router.push('/discover')">
            查看全部
            <el-icon class="btn-icon"><ArrowRight /></el-icon>
          </el-button>
        </div>

        <div class="reports-grid" v-if="latestReports">
          <div
            v-for="(report, type) in reportList"
            :key="type"
            class="report-card"
            @click="$router.push('/discover')"
            v-show="latestReports[type]"
          >
            <div class="report-icon" :style="{ background: report.bgColor }">
              <el-icon :size="20" :color="report.iconColor">
                <component :is="report.icon" />
              </el-icon>
            </div>
            <div class="report-content">
              <h4 class="report-title">{{ report.title }}</h4>
              <p class="report-desc">{{ latestReports[type]?.data?.total_count || 0 }} {{ report.unit }}</p>
              <span class="report-date">{{ formatDate(latestReports[type]?.generated_at) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：快捷操作 -->
      <div class="content-right">
        <div class="action-panel">
          <h3 class="panel-title">快捷操作</h3>
          <div class="action-list">
            <button class="action-btn primary" @click="syncJellyfin" :disabled="syncing">
              <div class="action-icon" style="background: linear-gradient(135deg, #E8A598, #D4958A);">
                <el-icon :size="20"><Refresh /></el-icon>
              </div>
              <div class="action-info">
                <span class="action-name">同步 Jellyfin</span>
                <span class="action-desc">更新影片库</span>
              </div>
              <el-icon v-if="syncing" class="loading-icon"><Loading /></el-icon>
            </button>

            <button class="action-btn" @click="updateScores" :disabled="updatingScores">
              <div class="action-icon" style="background: linear-gradient(135deg, #8FB996, #7AA882);">
                <el-icon :size="20"><Star /></el-icon>
              </div>
              <div class="action-info">
                <span class="action-name">更新评分</span>
                <span class="action-desc">获取最新数据</span>
              </div>
            </button>

            <button class="action-btn" @click="generateWeeklyReport">
              <div class="action-icon" style="background: linear-gradient(135deg, #D4A574, #C49464);">
                <el-icon :size="20"><Document /></el-icon>
              </div>
              <div class="action-info">
                <span class="action-name">生成周报</span>
                <span class="action-desc">关注演员动态</span>
              </div>
            </button>

            <button class="action-btn" @click="$router.push('/todo')">
              <div class="action-icon" style="background: linear-gradient(135deg, #8FB8CD, #7AA8BD);">
                <el-icon :size="20"><List /></el-icon>
              </div>
              <div class="action-info">
                <span class="action-name">待看清单</span>
                <span class="action-desc">{{ stats.pending_todos || 0 }} 项待处理</span>
              </div>
            </button>
          </div>
        </div>

        <!-- 最近添加 -->
        <div class="recent-panel" v-if="recentMovies.length">
          <h3 class="panel-title">最近添加</h3>
          <div class="recent-list">
            <div
              v-for="movie in recentMovies"
              :key="movie.code"
              class="recent-item"
              @click="showMovieDetail(movie)"
            >
              <div class="recent-poster">
                <img v-if="movie.poster_url" :src="movie.poster_url" :alt="movie.code" />
                <el-icon v-else><Picture /></el-icon>
              </div>
              <div class="recent-info">
                <span class="recent-code">{{ movie.code }}</span>
                <span class="recent-title">{{ movie.title }}</span>
                <span v-if="movie.javdb_score" class="recent-score">
                  <el-icon><StarFilled /></el-icon>
                  {{ movie.javdb_score.toFixed(1) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Film,
  Star,
  User,
  List,
  Trophy,
  ArrowRight,
  Refresh,
  Document,
  Picture,
  StarFilled,
  Loading,
  TrendCharts
} from '@element-plus/icons-vue'
import { statsApi, reportsApi, chartsApi, tasksApi, moviesApi } from '../api'

const stats = ref({})
const latestReports = ref(null)
const charts = ref([])
const syncing = ref(false)
const updatingScores = ref(false)
const recentMovies = ref([])

const statsList = computed(() => [
  {
    key: 'movies',
    value: stats.value.total_movies || 0,
    label: '影片总数',
    icon: Film,
    route: '/library',
    bgColor: 'linear-gradient(135deg, #F5D5CE, #E8A598)',
    iconColor: '#fff'
  },
  {
    key: 'score',
    value: stats.value.avg_score || '-',
    label: '平均评分',
    icon: Star,
    route: '/charts',
    bgColor: 'linear-gradient(135deg, #F0E0D0, #D4A574)',
    iconColor: '#fff'
  },
  {
    key: 'actors',
    value: stats.value.followed_actors || 0,
    label: '关注演员',
    icon: User,
    route: '/actors',
    bgColor: 'linear-gradient(135deg, #E0E8F0, #8FB8CD)',
    iconColor: '#fff'
  },
  {
    key: 'todos',
    value: stats.value.pending_todos || 0,
    label: '待看清单',
    icon: List,
    route: '/todo',
    bgColor: 'linear-gradient(135deg, #E0E8E0, #8FB996)',
    iconColor: '#fff'
  }
])

const reportList = [
  {
    type: 'weekly',
    title: '周报',
    unit: '部新片',
    icon: TrendCharts,
    bgColor: 'linear-gradient(135deg, #F5D5CE, #E8A598)',
    iconColor: '#fff'
  },
  {
    type: 'monthly',
    title: '月报',
    unit: '部评分上升',
    icon: TrendCharts,
    bgColor: 'linear-gradient(135deg, #F0E0D0, #D4A574)',
    iconColor: '#fff'
  },
  {
    type: 'annual',
    title: '年报',
    unit: '部缺失',
    icon: Trophy,
    bgColor: 'linear-gradient(135deg, #E8E0E8, #B8A9C9)',
    iconColor: '#fff'
  }
]

const navigateTo = (route) => {
  if (route) {
    router.push(route)
  }
}

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

const fetchRecentMovies = async () => {
  try {
    const data = await moviesApi.list({ page: 1, per_page: 5, sort: 'date_added_desc' })
    recentMovies.value = data.items || []
  } catch (e) {
    console.error('Failed to fetch recent movies:', e)
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 7) return `${days} 天前`
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

const showMovieDetail = (movie) => {
  window.showMovieDetail(movie)
}

onMounted(() => {
  fetchStats()
  fetchReports()
  fetchCharts()
  fetchRecentMovies()
})
</script>

<style scoped>
.dashboard-view {
  max-width: 1400px;
  margin: 0 auto;
}

/* 欢迎区域 */
.welcome-section {
  margin-bottom: 32px;
}

.welcome-title {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.5px;
  margin-bottom: 8px;
}

.welcome-subtitle {
  font-size: 16px;
  color: var(--text-muted);
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 32px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  transition: all 0.3s ease;
  cursor: pointer;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-hover);
}

.stat-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: var(--text-tertiary);
  margin-top: 2px;
}

.stat-trend {
  font-size: 13px;
  font-weight: 600;
}

.trend-up {
  color: var(--accent-green);
}

.trend-down {
  color: #E8A598;
}

/* 主内容区 */
.dashboard-content {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 28px;
}

/* 区域标题 */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.section-title .el-icon {
  color: var(--primary-color);
}

.btn-icon {
  margin-left: 4px;
  transition: transform 0.2s ease;
}

button:hover .btn-icon {
  transform: translateX(4px);
}

/* 榜单卡片 */
.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.chart-card {
  padding: 20px;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  transition: all 0.3s ease;
  cursor: pointer;
}

.chart-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-hover);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.chart-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.chart-year {
  padding: 4px 10px;
  background: var(--bg-tertiary);
  border-radius: 20px;
  font-size: 12px;
  color: var(--text-tertiary);
  font-weight: 500;
}

.chart-progress {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: var(--bg-tertiary);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--primary-gradient);
  border-radius: 4px;
  transition: width 0.5s ease;
}

.progress-text {
  font-size: 14px;
  font-weight: 600;
  color: var(--primary-color);
  min-width: 40px;
  text-align: right;
}

.chart-stats {
  display: flex;
  gap: 24px;
}

.chart-stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-num {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-num.collected {
  color: var(--accent-green);
}

.stat-num.missing {
  color: #E8A598;
}

.stat-desc {
  font-size: 12px;
  color: var(--text-tertiary);
}

/* 报告卡片 */
.reports-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.report-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  transition: all 0.3s ease;
  cursor: pointer;
}

.report-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-hover);
}

.report-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.report-content {
  flex: 1;
}

.report-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.report-desc {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.report-date {
  font-size: 12px;
  color: var(--text-muted);
}

/* 右侧面板 */
.action-panel,
.recent-panel {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 24px;
  margin-bottom: 20px;
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
}

/* 快捷操作 */
.action-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px;
  background: var(--bg-secondary);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
  width: 100%;
}

.action-btn:hover {
  background: var(--bg-tertiary);
  transform: translateX(4px);
}

.action-btn.primary {
  background: linear-gradient(135deg, #F5D5CE20, #E8A59820);
  border: 1px solid var(--primary-light);
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.action-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.action-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.action-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.action-desc {
  font-size: 12px;
  color: var(--text-tertiary);
}

.loading-icon {
  animation: spin 1s linear infinite;
  color: var(--primary-color);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 最近添加 */
.recent-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recent-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
}

.recent-item:hover {
  background: var(--bg-secondary);
}

.recent-poster {
  width: 48px;
  height: 64px;
  border-radius: var(--radius-sm);
  background: var(--bg-tertiary);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  flex-shrink: 0;
}

.recent-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.recent-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.recent-code {
  font-size: 14px;
  font-weight: 600;
  color: var(--primary-color);
}

.recent-title {
  font-size: 13px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-score {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--accent-gold);
  font-weight: 600;
}

.recent-score .el-icon {
  font-size: 12px;
}

/* 响应式 */
@media (max-width: 1200px) {
  .dashboard-content {
    grid-template-columns: 1fr;
  }

  .content-right {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
  }

  .action-panel,
  .recent-panel {
    margin-bottom: 0;
  }
}

@media (max-width: 900px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }

  .reports-grid {
    grid-template-columns: 1fr;
  }

  .content-right {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .welcome-title {
    font-size: 24px;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }

  .stat-card {
    padding: 16px;
  }

  .stat-icon {
    width: 40px;
    height: 40px;
  }

  .stat-value {
    font-size: 20px;
  }
}
</style>
