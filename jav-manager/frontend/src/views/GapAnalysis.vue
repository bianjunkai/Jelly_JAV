<template>
  <div class="gap-analysis-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <button class="back-btn" @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon>
          <span>返回</span>
        </button>
        <h1 class="page-title">{{ chartName }} - 缺口分析</h1>
      </div>
    </div>

    <div v-loading="loading" class="analysis-content">
      <!-- 统计卡片 -->
      <div class="stats-grid">
        <div class="stat-card missing">
          <div class="stat-icon">
            <el-icon size="28" color="#E8A598"><Box /></el-icon>
          </div>
          <div class="stat-content">
            <span class="stat-value">{{ gapData.missing || 0 }}</span>
            <span class="stat-label">缺失影片</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon size="28" color="#8FB996"><PieChart /></el-icon>
          </div>
          <div class="stat-content">
            <span class="stat-value">{{ gapData.coverage_percent || 0 }}%</span>
            <span class="stat-label">覆盖率</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon size="28" color="#D4A574"><Star /></el-icon>
          </div>
          <div class="stat-content">
            <span class="stat-value">{{ gapData.by_score_range?.high?.length || 0 }}</span>
            <span class="stat-label">高分缺失 (≥4.5)</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon size="28" color="#8FB8CD"><User /></el-icon>
          </div>
          <div class="stat-content">
            <span class="stat-value">{{ Object.keys(gapData.by_followed_actor || {}).length }}</span>
            <span class="stat-label">关注演员缺失</span>
          </div>
        </div>
      </div>

      <!-- 评分分布 -->
      <div class="score-distribution">
        <h3 class="section-title">按评分分布</h3>
        <div class="dist-grid">
          <div class="dist-card high">
            <div class="dist-header">
              <span class="dist-label">高分区</span>
              <span class="dist-badge">≥ 4.5</span>
            </div>
            <div class="dist-count">{{ gapData.by_score_range?.high?.length || 0 }} 部</div>
            <div class="dist-bar">
              <div class="dist-progress" :style="{ width: getDistPercent(gapData.by_score_range?.high?.length) + '%' }"></div>
            </div>
            <el-button size="small" @click="showGapList('high')">查看列表</el-button>
          </div>

          <div class="dist-card medium">
            <div class="dist-header">
              <span class="dist-label">中分区</span>
              <span class="dist-badge">4.0 - 4.5</span>
            </div>
            <div class="dist-count">{{ gapData.by_score_range?.medium?.length || 0 }} 部</div>
            <div class="dist-bar">
              <div class="dist-progress" :style="{ width: getDistPercent(gapData.by_score_range?.medium?.length) + '%' }"></div>
            </div>
            <el-button size="small" @click="showGapList('medium')">查看列表</el-button>
          </div>

          <div class="dist-card low">
            <div class="dist-header">
              <span class="dist-label">低分区</span>
              <span class="dist-badge">&lt; 4.0</span>
            </div>
            <div class="dist-count">{{ gapData.by_score_range?.low?.length || 0 }} 部</div>
            <div class="dist-bar">
              <div class="dist-progress" :style="{ width: getDistPercent(gapData.by_score_range?.low?.length) + '%' }"></div>
            </div>
            <el-button size="small" @click="showGapList('low')">查看列表</el-button>
          </div>
        </div>
      </div>

      <!-- 关注演员缺失 -->
      <div v-if="Object.keys(gapData.by_followed_actor || {}).length > 0" class="actor-gaps">
        <h3 class="section-title">
          <el-icon><StarFilled /></el-icon>
          关注演员缺失影片
        </h3>
        <div class="actor-cards">
          <div v-for="(items, actor) in gapData.by_followed_actor" :key="actor" class="actor-card">
            <div class="actor-header">
              <div class="actor-avatar">
                <span class="avatar-text">{{ actor.charAt(0) }}</span>
              </div>
              <div class="actor-info">
                <h4 class="actor-name">{{ actor }}</h4>
                <span class="actor-count">{{ items.length }} 部缺失</span>
              </div>
              <el-button size="small" @click="viewActorGaps(actor)">查看全部</el-button>
            </div>
            <div class="actor-movies">
              <div v-for="item in items.slice(0, 5)" :key="item.code" class="movie-item">
                <span class="movie-rank">#{{ item.rank }}</span>
                <span class="movie-code">{{ item.code }}</span>
                <span v-if="item.score" class="movie-score">★ {{ item.score.toFixed(1) }}</span>
                <el-button size="small" type="primary" @click="addToTodo(item)">加入待看</el-button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 完整缺失列表 -->
      <div class="full-list">
        <h3 class="section-title">完整缺失列表</h3>
        <div class="list-actions">
          <div class="action-left">
            <el-button @click="selectAll">{{ allSelected ? '取消全选' : '全选' }}</el-button>
            <span class="selected-count">已选 {{ selectedItems.length }} 部</span>
          </div>
          <div class="action-right">
            <el-button type="primary" :disabled="selectedItems.length === 0" @click="batchAddToTodo">
              <el-icon><Plus /></el-icon>
              批量加入待看
            </el-button>
            <el-button @click="exportCSV">
              <el-icon><Download /></el-icon>
              导出 CSV
            </el-button>
          </div>
        </div>
        <el-table
          ref="gapTable"
          :data="gapData.all_missing"
          @selection-change="handleSelection"
          class="gap-table"
        >
          <el-table-column type="selection" width="50" />
          <el-table-column label="排名" width="70" prop="rank">
            <template #default="{ row }">
              <span class="rank-badge" :class="{ top: row.rank <= 10 }">#{{ row.rank }}</span>
            </template>
          </el-table-column>
          <el-table-column label="番号" width="110" prop="code">
            <template #default="{ row }">
              <span class="code-text">{{ row.code }}</span>
            </template>
          </el-table-column>
          <el-table-column label="评分" width="90">
            <template #default="{ row }">
              <span v-if="row.score" class="score-badge" :class="getScoreClass(row.score)">
                ★ {{ row.score.toFixed(1) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="演员" min-width="150">
            <template #default="{ row }">
              {{ row.actors?.slice(0, 2).join(', ') }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button size="small" type="primary" @click="addToTodo(row)">加入待看</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  Box,
  PieChart,
  Star,
  User,
  StarFilled,
  Plus,
  Download
} from '@element-plus/icons-vue'
import { chartsApi, todosApi } from '../api'

const route = useRoute()
const loading = ref(false)
const gapData = ref({})
const selectedItems = ref([])
const gapTable = ref(null)
const chartName = computed(() => decodeURIComponent(route.params.name))
const allSelected = computed(() => {
  return selectedItems.value.length === (gapData.value.all_missing?.length || 0) && selectedItems.value.length > 0
})

const fetchGaps = async () => {
  loading.value = true
  try {
    gapData.value = await chartsApi.gaps(chartName.value)
  } catch (e) {
    ElMessage.error('获取缺口分析失败')
  } finally {
    loading.value = false
  }
}

const getDistPercent = (count) => {
  if (!gapData.value.missing) return 0
  return Math.round((count || 0) / gapData.value.missing * 100)
}

const getScoreClass = (score) => {
  if (score >= 4.5) return 'score-high'
  if (score >= 4.0) return 'score-mid'
  return 'score-low'
}

const handleSelection = (selection) => {
  selectedItems.value = selection
}

const selectAll = () => {
  if (allSelected.value) {
    gapTable.value?.clearSelection()
  } else {
    gapTable.value?.toggleAllSelection()
  }
}

const addToTodo = async (item) => {
  try {
    await todosApi.add({
      code: item.code,
      title: item.title,
      actors: item.actors?.join(',') || '',
      source: 'manual',
      source_detail: `榜单补全-${chartName.value}`
    })
    ElMessage.success('已加入待看清单')
  } catch (e) {
    ElMessage.error('添加失败')
  }
}

const batchAddToTodo = async () => {
  try {
    const items = selectedItems.value.map(item => ({
      code: item.code,
      title: item.title,
      actors: item.actors?.join(',') || '',
      source: 'manual',
      source_detail: `榜单补全-${chartName.value}`
    }))
    const result = await todosApi.batchAdd(items)
    ElMessage.success(`已添加 ${result.added} 部到待看清单`)
    selectedItems.value = []
    gapTable.value?.clearSelection()
  } catch (e) {
    ElMessage.error('批量添加失败')
  }
}

const exportCSV = () => {
  const csv = ['Rank,Code,Title,Score,Actors']
  gapData.value.all_missing?.forEach(item => {
    csv.push(`${item.rank},${item.code},"${item.title || ''}",${item.score || ''},"${(item.actors || []).join(',')}"`)
  })
  const blob = new Blob([csv.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${chartName.value}-missing.csv`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}

const showGapList = (type) => {
  // TODO: 打开对应评分区间的列表弹窗
}

const viewActorGaps = (actor) => {
  // TODO: 打开该演员的完整缺失列表
}

onMounted(() => {
  fetchGaps()
})
</script>

<style scoped>
.gap-analysis-view {
  max-width: 1200px;
  margin: 0 auto;
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.page-header {
  margin-bottom: 28px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 14px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.back-btn:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.5px;
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
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-hover);
}

.stat-card.missing {
  background: linear-gradient(135deg, #F5D5CE20, #E8A59810);
  border: 1px solid #F5D5CE;
}

.stat-icon {
  width: 56px;
  height: 56px;
  background: var(--bg-secondary);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-content {
  flex: 1;
}

.stat-value {
  display: block;
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: var(--text-tertiary);
}

/* 评分分布 */
.score-distribution {
  margin-bottom: 32px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 20px;
}

.section-title .el-icon {
  color: var(--primary-color);
}

.dist-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.dist-card {
  padding: 24px;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.dist-card.high {
  border-left: 4px solid var(--accent-green);
}

.dist-card.medium {
  border-left: 4px solid var(--accent-gold);
}

.dist-card.low {
  border-left: 4px solid var(--text-muted);
}

.dist-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.dist-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
}

.dist-badge {
  padding: 4px 10px;
  background: var(--bg-tertiary);
  border-radius: 20px;
  font-size: 12px;
  color: var(--text-tertiary);
}

.dist-count {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.dist-bar {
  height: 8px;
  background: var(--bg-tertiary);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 16px;
}

.dist-progress {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.dist-card.high .dist-progress {
  background: var(--accent-green);
}

.dist-card.medium .dist-progress {
  background: var(--accent-gold);
}

.dist-card.low .dist-progress {
  background: var(--text-muted);
}

/* 演员缺失 */
.actor-gaps {
  margin-bottom: 32px;
}

.actor-cards {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.actor-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.actor-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: var(--bg-secondary);
}

.actor-avatar {
  width: 48px;
  height: 48px;
  background: var(--primary-gradient);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 20px;
  font-weight: 700;
}

.actor-info {
  flex: 1;
}

.actor-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.actor-count {
  font-size: 13px;
  color: var(--text-tertiary);
}

.actor-movies {
  padding: 16px 20px;
}

.movie-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  margin-bottom: 8px;
}

.movie-item:last-child {
  margin-bottom: 0;
}

.movie-rank {
  width: 50px;
  font-size: 13px;
  color: var(--text-tertiary);
  font-weight: 600;
}

.movie-code {
  flex: 1;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.movie-score {
  font-size: 13px;
  color: var(--accent-gold);
  font-weight: 600;
}

/* 完整列表 */
.full-list {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 24px;
}

.list-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.action-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.selected-count {
  font-size: 14px;
  color: var(--text-secondary);
}

.action-right {
  display: flex;
  gap: 12px;
}

.gap-table {
  border-radius: var(--radius-md);
  overflow: hidden;
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 24px;
  background: var(--bg-tertiary);
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

.rank-badge.top {
  background: var(--primary-gradient);
  color: #fff;
}

.code-text {
  font-weight: 600;
  color: var(--primary-color);
}

/* 响应式 */
@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .dist-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .page-title {
    font-size: 20px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .list-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .action-left,
  .action-right {
    justify-content: space-between;
  }
}
</style>
