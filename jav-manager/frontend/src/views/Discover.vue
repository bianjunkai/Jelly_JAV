<template>
  <div class="discover-view">
    <div class="page-header">
      <h1 class="page-title">发现</h1>
    </div>

    <div v-loading="loading">
      <!-- 最新报告 -->
      <div class="reports-grid">
        <!-- 周报 -->
        <el-card v-if="latestReports.weekly" class="report-card">
          <template #header>
            <div class="report-header">
              <span class="report-type">📊 周报</span>
              <span class="report-subtitle">本周关注演员新片</span>
            </div>
          </template>
          <div class="report-meta">
            生成时间: {{ formatDate(latestReports.weekly.generated_at) }}
          </div>
          <div class="report-count">
            共发现 <strong>{{ latestReports.weekly.data?.total_count || 0 }}</strong> 部新片
          </div>
          <div v-if="latestReports.weekly.data?.movies?.length" class="report-preview">
            <div v-for="movie in latestReports.weekly.data.movies.slice(0, 3)" :key="movie.code" class="preview-item">
              <span class="preview-code">{{ movie.code }}</span>
              <span v-if="movie.javdb_score" class="score-badge" :class="getScoreClass(movie.javdb_score)">
                ★ {{ movie.javdb_score.toFixed(1) }}
              </span>
            </div>
          </div>
          <el-button type="primary" class="report-action" @click="showWeekly = true">
            查看全部
          </el-button>
        </el-card>

        <!-- 月报 -->
        <el-card v-if="latestReports.monthly" class="report-card">
          <template #header>
            <div class="report-header">
              <span class="report-type">📈 月报</span>
              <span class="report-subtitle">本月分数上升旧片</span>
            </div>
          </template>
          <div class="report-meta">
            生成时间: {{ formatDate(latestReports.monthly.generated_at) }}
          </div>
          <div class="report-count">
            共 <strong>{{ latestReports.monthly.data?.total_count || 0 }}</strong> 部影片评分上升
          </div>
          <div v-if="latestReports.monthly.data?.items?.length" class="report-preview">
            <div v-for="item in latestReports.monthly.data.items.slice(0, 3)" :key="item.movie.code" class="preview-item">
              <span class="preview-code">{{ item.movie.code }}</span>
              <span class="score-change">
                {{ item.prev_score?.toFixed(1) }} → {{ item.curr_score?.toFixed(1) }}
                <span class="change-up">↑{{ item.change }}</span>
              </span>
            </div>
          </div>
          <el-button type="primary" class="report-action" @click="showMonthly = true">
            查看全部
          </el-button>
        </el-card>

        <!-- 年报 -->
        <el-card v-if="latestReports.annual" class="report-card">
          <template #header>
            <div class="report-header">
              <span class="report-type">🏆 年报</span>
              <span class="report-subtitle">榜单缺口推荐</span>
            </div>
          </template>
          <div class="report-meta">
            生成时间: {{ formatDate(latestReports.annual.generated_at) }}
          </div>
          <div class="report-count">
            缺失 <strong>{{ latestReports.annual.data?.total_missing || 0 }}</strong> 部
            (关注演员: {{ latestReports.annual.data?.followed_missing_count || 0 }})
          </div>
          <el-button type="primary" class="report-action" @click="$router.push('/charts/JavDB%20TOP250/gaps')">
            查看缺口分析
          </el-button>
        </el-card>
      </div>

      <!-- 操作按钮 -->
      <el-card class="actions-card">
        <div class="action-buttons">
          <el-button type="primary" @click="generateReport('weekly')" :loading="generating === 'weekly'">
            生成周报
          </el-button>
          <el-button type="primary" @click="generateReport('monthly')" :loading="generating === 'monthly'">
            生成月报
          </el-button>
          <el-button @click="generateReport('annual')" :loading="generating === 'annual'">
            生成年报
          </el-button>
        </div>
      </el-card>

      <!-- 历史报告 -->
      <el-card class="history-card">
        <template #header>
          <div class="section-title">历史报告</div>
        </template>
        <el-table :data="reports" stripe>
          <el-table-column prop="type" label="类型" width="100">
            <template #default="{ row }">
              <el-tag :type="getTypeTagType(row.type)" size="small">
                {{ getTypeName(row.type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="title" label="标题" />
          <el-table-column prop="generated_at" label="生成时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.generated_at) }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag v-if="row.is_read" type="info" size="small">已读</el-tag>
              <el-tag v-else type="success" size="small">新</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button size="small" @click="viewReport(row)">查看</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { reportsApi } from '../api'

const loading = ref(false)
const generating = ref(null)
const latestReports = ref({ weekly: null, monthly: null, annual: null })
const reports = ref([])

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
  return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`
}

const getScoreClass = (score) => {
  if (score >= 4.5) return 'score-high'
  if (score >= 4.0) return 'score-mid'
  return 'score-low'
}

const getTypeTagType = (type) => {
  const map = { weekly: '', monthly: 'warning', annual: 'success' }
  return map[type] || ''
}

const getTypeName = (type) => {
  const map = { weekly: '周报', monthly: '月报', annual: '年报' }
  return map[type] || type
}

const viewReport = (report) => {
  // TODO: 打开报告详情弹窗
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

.reports-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.report-card {
  background: #1a1a1a;
}

.report-header {
  display: flex;
  flex-direction: column;
}

.report-type {
  font-size: 18px;
  font-weight: 600;
}

.report-subtitle {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

.report-meta {
  font-size: 12px;
  color: #666;
  margin-bottom: 12px;
}

.report-count {
  font-size: 14px;
  margin-bottom: 12px;
}

.report-preview {
  margin-bottom: 12px;
}

.preview-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid #333;
}

.preview-code {
  font-weight: 600;
}

.score-change {
  font-size: 12px;
  color: #666;
}

.change-up {
  color: #4ade80;
  margin-left: 4px;
}

.report-action {
  width: 100%;
}

.actions-card {
  margin-bottom: 24px;
  background: #1a1a1a;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.history-card {
  background: #1a1a1a;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
}
</style>
