<template>
  <div class="discover-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">发现</h1>
        <p class="page-subtitle">探索影片推荐和数据分析</p>
      </div>
    </div>

    <div v-loading="loading" class="discover-content">
      <!-- 报告卡片 -->
      <div class="reports-section">
        <div class="section-header">
          <h2 class="section-title">
            <el-icon><TrendCharts /></el-icon>
            最新报告
          </h2>
        </div>

        <div class="reports-grid">
          <!-- 周报 -->
          <div v-if="latestReports.weekly" class="report-card weekly" @click="showWeekly = true">
            <div class="report-icon">
              <el-icon size="32" color="#fff"><Calendar /></el-icon>
            </div>
            <div class="report-content">
              <div class="report-badge">周报</div>
              <h3 class="report-title">本周关注演员新片</h3>
              <p class="report-stat">
                <span class="stat-num">{{ latestReports.weekly.data?.total_count || 0 }}</span>
                <span class="stat-label">部新片</span>
              </p>
              <p class="report-date">{{ formatDate(latestReports.weekly.generated_at) }}</p>
            </div>
            <div class="report-preview" v-if="latestReports.weekly.data?.movies?.length">
              <div v-for="movie in latestReports.weekly.data.movies.slice(0, 3)" :key="movie.code" class="preview-item">
                <span class="preview-code">{{ movie.code }}</span>
                <span v-if="movie.javdb_score" class="preview-score">★ {{ movie.javdb_score.toFixed(1) }}</span>
              </div>
            </div>
            <button class="report-btn">查看详情</button>
          </div>

          <!-- 月报 -->
          <div v-if="latestReports.monthly" class="report-card monthly" @click="showMonthly = true">
            <div class="report-icon">
              <el-icon size="32" color="#fff"><TrendCharts /></el-icon>
            </div>
            <div class="report-content">
              <div class="report-badge">月报</div>
              <h3 class="report-title">本月评分上升</h3>
              <p class="report-stat">
                <span class="stat-num">{{ latestReports.monthly.data?.total_count || 0 }}</span>
                <span class="stat-label">部影片</span>
              </p>
              <p class="report-date">{{ formatDate(latestReports.monthly.generated_at) }}</p>
            </div>
            <div class="report-preview" v-if="latestReports.monthly.data?.items?.length">
              <div v-for="item in latestReports.monthly.data.items.slice(0, 3)" :key="item.movie.code" class="preview-item">
                <span class="preview-code">{{ item.movie.code }}</span>
                <span class="preview-change">↑ {{ item.change }}</span>
              </div>
            </div>
            <button class="report-btn">查看详情</button>
          </div>

          <!-- 年报 -->
          <div v-if="latestReports.annual" class="report-card annual">
            <div class="report-icon">
              <el-icon size="32" color="#fff"><Trophy /></el-icon>
            </div>
            <div class="report-content">
              <div class="report-badge">年报</div>
              <h3 class="report-title">榜单缺口分析</h3>
              <p class="report-stat">
                <span class="stat-num">{{ latestReports.annual.data?.total_missing || 0 }}</span>
                <span class="stat-label">部缺失</span>
              </p>
              <p class="report-substat" v-if="latestReports.annual.data?.followed_missing_count">
                关注演员缺失 {{ latestReports.annual.data.followed_missing_count }} 部
              </p>
              <p class="report-date">{{ formatDate(latestReports.annual.generated_at) }}</p>
            </div>
            <button class="report-btn" @click.stop="$router.push('/charts/JavDB%20TOP250/gaps')">查看缺口</button>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="actions-section">
        <h3 class="section-subtitle">生成报告</h3>
        <div class="action-buttons">
          <button
            class="action-btn"
            :class="{ loading: generating === 'weekly' }"
            @click="generateReport('weekly')"
            :disabled="generating"
          >
            <el-icon v-if="generating !== 'weekly'"><Calendar /></el-icon>
            <el-icon v-else class="spin"><Loading /></el-icon>
            <span>生成周报</span>
          </button>
          <button
            class="action-btn"
            :class="{ loading: generating === 'monthly' }"
            @click="generateReport('monthly')"
            :disabled="generating"
          >
            <el-icon v-if="generating !== 'monthly'"><TrendCharts /></el-icon>
            <el-icon v-else class="spin"><Loading /></el-icon>
            <span>生成月报</span>
          </button>
          <button
            class="action-btn"
            :class="{ loading: generating === 'annual' }"
            @click="generateReport('annual')"
            :disabled="generating"
          >
            <el-icon v-if="generating !== 'annual'"><Trophy /></el-icon>
            <el-icon v-else class="spin"><Loading /></el-icon>
            <span>生成年报</span>
          </button>
        </div>
      </div>

      <!-- 历史报告 -->
      <div class="history-section">
        <div class="section-header">
          <h2 class="section-title">
            <el-icon><Clock /></el-icon>
            历史报告
          </h2>
        </div>

        <div class="history-list">
          <div
            v-for="report in reports.slice(0, 10)"
            :key="report.id"
            class="history-item"
            :class="{ unread: !report.is_read }"
          >
            <div class="history-icon" :class="report.type">
              <el-icon size="18">
                <Calendar v-if="report.type === 'weekly'" />
                <TrendCharts v-else-if="report.type === 'monthly'" />
                <Trophy v-else />
              </el-icon>
            </div>
            <div class="history-content">
              <h4 class="history-title">{{ report.title }}</h4>
              <p class="history-meta">
                <span class="history-type" :class="report.type">{{ getTypeName(report.type) }}</span>
                <span class="history-date">{{ formatDate(report.generated_at) }}</span>
              </p>
            </div>
            <div class="history-status">
              <span v-if="!report.is_read" class="new-badge">NEW</span>
            </div>
          </div>
        </div>

        <div v-if="reports.length > 10" class="load-more">
          <el-button text>查看更多历史报告</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  TrendCharts,
  Calendar,
  Trophy,
  Clock,
  Loading
} from '@element-plus/icons-vue'
import { reportsApi } from '../api'

const loading = ref(false)
const generating = ref(null)
const latestReports = ref({ weekly: null, monthly: null, annual: null })
const reports = ref([])
const showWeekly = ref(false)
const showMonthly = ref(false)

const fetchReports = async () => {
  loading.value = true
  try {
    const data = await reportsApi.latest()
    latestReports.value = data
    reports.value = await reportsApi.list()
  } catch (e) {
    ElMessage.error('获取报告失败')
  } finally {
    loading.value = false
  }
}

const generateReport = async (type) => {
  generating.value = type
  try {
    await reportsApi.generate(type)
    ElMessage.success('报告生成成功')
    await fetchReports()
  } catch (e) {
    ElMessage.error('生成失败')
  } finally {
    generating.value = null
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
  return `${date.getMonth() + 1}月${date.getDate()}日`
}

const getTypeName = (type) => {
  const map = { weekly: '周报', monthly: '月报', annual: '年报' }
  return map[type] || type
}

onMounted(() => {
  fetchReports()
})
</script>

<style scoped>
.discover-view {
  max-width: 1200px;
  margin: 0 auto;
}

/* 页面头部 */
.page-header {
  margin-bottom: 32px;
}

.page-title {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.5px;
  margin-bottom: 8px;
}

.page-subtitle {
  font-size: 15px;
  color: var(--text-muted);
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

.section-subtitle {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

/* 报告网格 */
.reports-section {
  margin-bottom: 32px;
}

.reports-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.report-card {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}

.report-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-hover);
}

.report-icon {
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.report-card.weekly .report-icon {
  background: linear-gradient(135deg, #F5D5CE, #E8A598);
}

.report-card.monthly .report-icon {
  background: linear-gradient(135deg, #F0E0D0, #D4A574);
}

.report-card.annual .report-icon {
  background: linear-gradient(135deg, #E0E8F0, #8FB8CD);
}

.report-content {
  padding: 20px;
  text-align: center;
}

.report-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 12px;
}

.report-card.weekly .report-badge {
  background: #F5D5CE;
  color: #C97E75;
}

.report-card.monthly .report-badge {
  background: #F0E0D0;
  color: #A08050;
}

.report-card.annual .report-badge {
  background: #E0E8F0;
  color: #608090;
}

.report-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.report-stat {
  margin-bottom: 4px;
}

.stat-num {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-label {
  font-size: 14px;
  color: var(--text-tertiary);
  margin-left: 4px;
}

.report-substat {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.report-date {
  font-size: 12px;
  color: var(--text-muted);
}

.report-preview {
  padding: 0 20px 16px;
}

.preview-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
  margin-bottom: 8px;
}

.preview-item:last-child {
  margin-bottom: 0;
}

.preview-code {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.preview-score {
  font-size: 13px;
  color: var(--accent-gold);
  font-weight: 600;
}

.preview-change {
  font-size: 13px;
  color: var(--accent-green);
  font-weight: 600;
}

.report-btn {
  width: 100%;
  padding: 14px;
  background: var(--bg-secondary);
  border: none;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.report-btn:hover {
  background: var(--primary-color);
  color: #fff;
}

/* 操作区域 */
.actions-section {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 24px;
  margin-bottom: 32px;
  box-shadow: var(--shadow-card);
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px 24px;
  background: var(--bg-secondary);
  border: none;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:hover:not(:disabled) {
  background: var(--primary-color);
  color: #fff;
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 历史报告 */
.history-section {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 24px;
  box-shadow: var(--shadow-card);
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  transition: all 0.2s ease;
}

.history-item:hover {
  background: var(--bg-tertiary);
}

.history-item.unread {
  background: #F5D5CE30;
}

.history-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.history-icon.weekly {
  background: #F5D5CE;
  color: #C97E75;
}

.history-icon.monthly {
  background: #F0E0D0;
  color: #A08050;
}

.history-icon.annual {
  background: #E0E8F0;
  color: #608090;
}

.history-content {
  flex: 1;
  min-width: 0;
}

.history-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
}

.history-type {
  padding: 2px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.history-type.weekly {
  background: #F5D5CE;
  color: #C97E75;
}

.history-type.monthly {
  background: #F0E0D0;
  color: #A08050;
}

.history-type.annual {
  background: #E0E8F0;
  color: #608090;
}

.history-date {
  color: var(--text-muted);
}

.new-badge {
  padding: 4px 10px;
  background: var(--primary-color);
  border-radius: 20px;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
}

.load-more {
  text-align: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--border-light);
}

/* 响应式 */
@media (max-width: 1024px) {
  .reports-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .page-title {
    font-size: 24px;
  }

  .reports-grid {
    grid-template-columns: 1fr;
  }

  .action-buttons {
    flex-direction: column;
  }

  .history-item {
    flex-wrap: wrap;
  }

  .history-status {
    width: 100%;
    text-align: right;
    margin-top: 8px;
  }
}
</style>
