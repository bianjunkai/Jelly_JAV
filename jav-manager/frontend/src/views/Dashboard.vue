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
      <!-- 最近添加 - 横向海报展示（独立区块，全宽） -->
      <section class="section-recent" v-if="recentMovies.length">
        <div class="section-header">
          <h2 class="section-title">
            <el-icon><Picture /></el-icon>
            最近添加
          </h2>
          <el-button text @click="$router.push('/library')">
            查看全部
            <el-icon class="btn-icon"><ArrowRight /></el-icon>
          </el-button>
        </div>
        <div class="recent-scroll">
          <div
            v-for="movie in recentMovies"
            :key="movie.code"
            class="recent-card"
            @click="showMovieDetail(movie)"
          >
            <div class="recent-poster">
              <img v-if="movie.poster_url" :src="movie.poster_url" :alt="movie.code" />
              <div v-else class="poster-placeholder">
                <el-icon size="28"><Picture /></el-icon>
              </div>
              <div v-if="movie.javdb_score" class="score-overlay">
                <span class="score-star">★</span>
                <span class="score-value">{{ movie.javdb_score.toFixed(2) }}</span>
              </div>
            </div>
            <div class="recent-info">
              <span class="recent-code">{{ movie.code }}</span>
              <span class="recent-title">{{ movie.title }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 下方三栏：榜单概览 | 最新报告 | 快捷操作 -->
      <div class="bottom-grid">
        <!-- 榜单概览 -->
        <section class="section-block">
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
          <div class="charts-mini-grid">
            <div
              v-for="chart in charts.slice(0, 4)"
              :key="chart.name"
              class="chart-mini-card"
              @click="$router.push(`/charts/${encodeURIComponent(chart.name)}`)"
            >
              <div class="chart-mini-header">
                <span class="chart-mini-name">{{ chart.display_name }}</span>
                <span v-if="chart.year" class="chart-mini-year">{{ chart.year }}</span>
              </div>
              <div class="chart-mini-bar">
                <div class="bar-fill" :style="{ width: chart.coverage_percent + '%' }"></div>
              </div>
              <div class="chart-mini-stats">
                <span class="stat-collected">{{ chart.collected }} 已收藏</span>
                <span class="stat-missing">{{ chart.missing }} 缺失</span>
              </div>
            </div>
          </div>
        </section>

        <!-- 最新报告 -->
        <section class="section-block">
          <div class="section-header">
            <h2 class="section-title">
              <el-icon><Document /></el-icon>
              最新报告
            </h2>
            <el-button text @click="$router.push('/discover')">
              查看全部
              <el-icon class="btn-icon"><ArrowRight /></el-icon>
            </el-button>
          </div>
          <div class="reports-list">
            <div
              v-for="report in reportList"
              :key="report.type"
              class="report-row"
              :class="{ empty: !latestReports?.[report.type] }"
              @click="goToReport(report.type)"
            >
              <div class="report-row-icon" :style="{ background: report.bgColor }">
                <el-icon :size="18" :color="report.iconColor">
                  <component :is="report.icon" />
                </el-icon>
              </div>
              <div class="report-row-info">
                <span class="report-row-title">{{ report.title }}</span>
                <span class="report-row-meta" v-if="latestReports?.[report.type]">
                  {{ latestReports[report.type]?.data?.total_count || 0 }}{{ report.unit }}
                  · {{ formatDate(latestReports[report.type]?.generated_at) }}
                </span>
                <span class="report-row-meta empty" v-else>暂无报告</span>
              </div>
              <el-icon class="row-arrow"><ArrowRight /></el-icon>
            </div>
          </div>
        </section>

        <!-- 快捷操作 -->
        <section class="section-block">
          <div class="section-header">
            <h2 class="section-title">
              <el-icon><Grid /></el-icon>
              快捷操作
            </h2>
          </div>
          <div class="quick-actions">
            <button class="quick-btn primary" @click="syncJellyfin" :disabled="syncing">
              <div class="quick-icon" style="background: linear-gradient(135deg, #E8A598, #D4958A);">
                <el-icon :size="20"><Refresh /></el-icon>
              </div>
              <div class="quick-info">
                <span class="quick-name">同步 Jellyfin</span>
                <span class="quick-desc">更新影片库</span>
              </div>
              <el-icon v-if="syncing" class="loading-icon"><Loading /></el-icon>
            </button>
            <button class="quick-btn" @click="updateScores" :disabled="updatingScores">
              <div class="quick-icon" style="background: linear-gradient(135deg, #8FB996, #7AA882);">
                <el-icon :size="20"><Star /></el-icon>
              </div>
              <div class="quick-info">
                <span class="quick-name">更新评分</span>
                <span class="quick-desc">获取最新数据</span>
              </div>
            </button>
            <button class="quick-btn" @click="generateWeeklyReport">
              <div class="quick-icon" style="background: linear-gradient(135deg, #D4A574, #C49464);">
                <el-icon :size="20"><Document /></el-icon>
              </div>
              <div class="quick-info">
                <span class="quick-name">生成周报</span>
                <span class="quick-desc">关注演员动态</span>
              </div>
            </button>
            <button class="quick-btn" @click="$router.push('/todo')">
              <div class="quick-icon" style="background: linear-gradient(135deg, #8FB8CD, #7AA8BD);">
                <el-icon :size="20"><List /></el-icon>
              </div>
              <div class="quick-info">
                <span class="quick-name">待看清单</span>
                <span class="quick-desc">{{ stats.pending_todos || 0 }} 项待处理</span>
              </div>
            </button>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
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
  TrendCharts,
  Grid
} from '@element-plus/icons-vue'
import { statsApi, reportsApi, chartsApi, tasksApi, moviesApi } from '../api'

const router = useRouter()
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

const goToReport = (type) => {
  const report = latestReports.value?.[type]
  if (report?.id) {
    router.push(`/reports/${type}/${report.id}`)
  } else {
    router.push('/discover')
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
    const data = await moviesApi.list({ page: 1, per_page: 12, sort: 'date_added_desc' })
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
  margin-bottom: 28px;
}

.welcome-title {
  font-size: 30px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.5px;
  margin-bottom: 6px;
}

.welcome-subtitle {
  font-size: 15px;
  color: var(--text-muted);
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 20px;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  cursor: pointer;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-hover);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-content {
  flex: 1;
  min-width: 0;
}

.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
  font-variant-numeric: tabular-nums;
}

.stat-label {
  font-size: 13px;
  color: var(--text-tertiary);
  margin-top: 2px;
}

/* 主内容区 */
.dashboard-content {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* ========== 最近添加 - 横向海报 ========== */
.section-recent {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  padding: 24px;
  box-shadow: var(--shadow-card);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 17px;
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

.el-button:hover .btn-icon {
  transform: translateX(3px);
}

/* 横向滚动海报 */
.recent-scroll {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding-bottom: 8px;
  scroll-snap-type: x mandatory;
  scrollbar-width: thin;
}

.recent-scroll::-webkit-scrollbar {
  height: 6px;
}

.recent-scroll::-webkit-scrollbar-track {
  background: var(--bg-secondary);
  border-radius: 3px;
}

.recent-scroll::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

.recent-card {
  flex-shrink: 0;
  width: 130px;
  cursor: pointer;
  scroll-snap-align: start;
  transition: transform 0.2s ease;
}

.recent-card:hover {
  transform: translateY(-3px);
}

.recent-poster {
  position: relative;
  aspect-ratio: 2/3;
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--bg-tertiary);
  margin-bottom: 10px;
}

.recent-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.poster-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
}

.score-overlay {
  position: absolute;
  bottom: 6px;
  right: 6px;
  display: flex;
  align-items: center;
  gap: 3px;
  padding: 3px 8px;
  background: rgba(255, 255, 255, 0.92);
  border-radius: 10px;
  backdrop-filter: blur(4px);
}

.score-star {
  font-size: 11px;
  color: var(--accent-gold);
}

.score-value {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-primary);
}

.recent-info {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 0 2px;
}

.recent-code {
  font-size: 13px;
  font-weight: 600;
  color: var(--primary-color);
  font-family: var(--font-mono);
}

.recent-title {
  font-size: 12px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ========== 下方三栏布局 ========== */
.bottom-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 280px;
  gap: 24px;
  align-items: start;
}

.section-block {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  padding: 22px;
  box-shadow: var(--shadow-card);
}

/* 榜单迷你卡片 */
.charts-mini-grid {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.chart-mini-card {
  padding: 14px 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
}

.chart-mini-card:hover {
  background: var(--bg-tertiary);
  transform: translateX(3px);
}

.chart-mini-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.chart-mini-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.chart-mini-year {
  font-size: 11px;
  color: var(--text-muted);
  background: var(--bg-tertiary);
  padding: 2px 8px;
  border-radius: 10px;
}

.chart-mini-bar {
  height: 6px;
  background: var(--bg-tertiary);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 8px;
}

.bar-fill {
  height: 100%;
  background: var(--primary-gradient);
  border-radius: 3px;
  transition: width 0.5s ease;
}

.chart-mini-stats {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.stat-collected {
  color: var(--accent-green);
  font-weight: 600;
}

.stat-missing {
  color: #E8A598;
  font-weight: 600;
}

/* 报告列表 */
.reports-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.report-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
}

.report-row:hover {
  background: var(--bg-tertiary);
  transform: translateX(3px);
}

.report-row.empty {
  opacity: 0.5;
  cursor: default;
}

.report-row.empty:hover {
  transform: none;
  background: var(--bg-secondary);
}

.report-row-icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.report-row-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.report-row-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.report-row-meta {
  font-size: 12px;
  color: var(--text-secondary);
}

.report-row-meta.empty {
  color: var(--text-muted);
  font-style: italic;
}

.row-arrow {
  color: var(--text-muted);
  flex-shrink: 0;
  transition: transform 0.2s ease;
}

.report-row:hover .row-arrow {
  transform: translateX(3px);
  color: var(--primary-color);
}

/* 快捷操作 */
.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.quick-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  background: var(--bg-secondary);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
  width: 100%;
}

.quick-btn:hover {
  background: var(--bg-tertiary);
  transform: translateX(3px);
}

.quick-btn.primary {
  background: linear-gradient(135deg, #F5D5CE15, #E8A59815);
  border: 1px solid var(--primary-light);
}

.quick-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
}

.quick-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.quick-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.quick-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.quick-desc {
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

/* ========== 响应式 ========== */
@media (max-width: 1100px) {
  .bottom-grid {
    grid-template-columns: 1fr 1fr;
  }

  .section-block:last-child {
    grid-column: span 2;
  }
}

@media (max-width: 768px) {
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
    font-size: 22px;
  }

  .welcome-title {
    font-size: 24px;
  }

  .bottom-grid {
    grid-template-columns: 1fr;
  }

  .section-block:last-child {
    grid-column: span 1;
  }

  .recent-card {
    width: 110px;
  }
}
</style>
