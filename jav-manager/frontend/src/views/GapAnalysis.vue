<template>
  <div class="gap-analysis-view">
    <div class="page-header">
      <div class="header-left">
        <el-button text @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <h1 class="page-title">{{ chartName }} - 缺口分析</h1>
      </div>
    </div>

    <div v-loading="loading">
      <!-- 统计卡片 -->
      <div class="stats-cards">
        <el-card class="stat-card">
          <div class="stat-value missing">{{ gapData.missing }}</div>
          <div class="stat-label">缺失影片</div>
        </el-card>
        <el-card class="stat-card">
          <div class="stat-value">{{ gapData.coverage_percent }}%</div>
          <div class="stat-label">覆盖率</div>
        </el-card>
        <el-card class="stat-card">
          <div class="stat-value high">{{ gapData.by_score_range?.high?.length || 0 }}</div>
          <div class="stat-label">高分缺失 (≥4.5)</div>
        </el-card>
        <el-card class="stat-card">
          <div class="stat-value">{{ Object.keys(gapData.by_followed_actor || {}).length }}</div>
          <div class="stat-label">关注演员缺失</div>
        </el-card>
      </div>

      <!-- 按评分分布 -->
      <el-card class="section-card">
        <template #header>
          <div class="section-title">按评分分布</div>
        </template>
        <div class="score-distribution">
          <div class="dist-item high">
            <span class="dist-label">高分区 ≥4.5</span>
            <span class="dist-count">{{ gapData.by_score_range?.high?.length || 0 }}</span>
            <el-progress :percentage="getDistPercent(gapData.by_score_range?.high?.length)" :stroke-width="8" :show-text="false" />
            <el-button size="small" @click="showGapList('high')">查看</el-button>
          </div>
          <div class="dist-item medium">
            <span class="dist-label">中分区 4.0-4.5</span>
            <span class="dist-count">{{ gapData.by_score_range?.medium?.length || 0 }}</span>
            <el-progress :percentage="getDistPercent(gapData.by_score_range?.medium?.length)" :stroke-width="8" :show-text="false" />
            <el-button size="small" @click="showGapList('medium')">查看</el-button>
          </div>
          <div class="dist-item low">
            <span class="dist-label">低分区 &lt;4.0</span>
            <span class="dist-count">{{ gapData.by_score_range?.low?.length || 0 }}</span>
            <el-progress :percentage="getDistPercent(gapData.by_score_range?.low?.length)" :stroke-width="8" :show-text="false" />
            <el-button size="small" @click="showGapList('low')">查看</el-button>
          </div>
        </div>
      </el-card>

      <!-- 关注演员缺失 -->
      <el-card v-if="Object.keys(gapData.by_followed_actor || {}).length > 0" class="section-card">
        <template #header>
          <div class="section-title">⭐ 关注演员缺失</div>
        </template>
        <div v-for="(items, actor) in gapData.by_followed_actor" :key="actor" class="actor-group">
          <div class="actor-header">
            <span class="actor-name">{{ actor }}</span>
            <span class="actor-count">{{ items.length }} 部</span>
          </div>
          <div class="actor-movies">
            <div v-for="item in items.slice(0, 5)" :key="item.code" class="gap-item" @click="showGapDetail(item)">
              <span class="gap-rank">#{{ item.rank }}</span>
              <span class="gap-code">{{ item.code }}</span>
              <span v-if="item.score" class="score-badge" :class="getScoreClass(item.score)">★ {{ item.score.toFixed(1) }}</span>
              <el-button size="small" type="primary" @click.stop="addToTodo(item)">加入待看</el-button>
            </div>
            <el-button v-if="items.length > 5" text @click="viewActorGaps(actor)">
              查看全部 {{ items.length }} 部...
            </el-button>
          </div>
        </div>
      </el-card>

      <!-- 完整缺失列表 -->
      <el-card class="section-card">
        <template #header>
          <div class="section-title">完整缺失列表</div>
        </template>
        <div class="batch-actions">
          <el-button @click="selectAll">全选</el-button>
          <span>已选 {{ selectedItems.length }} 部</span>
          <el-button type="primary" :disabled="selectedItems.length === 0" @click="batchAddToTodo">
            批量加入待看
          </el-button>
          <el-button @click="exportCSV">导出 CSV</el-button>
        </div>
        <el-table ref="gapTable" :data="gapData.all_missing" @selection-change="handleSelection">
          <el-table-column type="selection" width="50" />
          <el-table-column label="排名" width="80" prop="rank" />
          <el-table-column label="番号" width="120" prop="code" />
          <el-table-column label="评分" width="100">
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
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button size="small" type="primary" @click="addToTodo(row)">加入待看</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { chartsApi, todosApi } from '../api'

const route = useRoute()
const loading = ref(false)
const gapData = ref({})
const selectedItems = ref([])
const gapTable = ref(null)
const chartName = computed(() => decodeURIComponent(route.params.name))

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
  gapTable.value?.toggleAllSelection()
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
  } catch (e) {
    ElMessage.error('批量添加失败')
  }
}

const exportCSV = () => {
  const csv = ['Rank,Code,Title,Score,Actors']
  gapData.value.all_missing?.forEach(item => {
    csv.push(`${item.rank},${item.code},"${item.title || ''}",${item.score || ''},"${(item.actors || []).join(',')}"`)
  })
  const blob = new Blob([csv.join('\n')], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${chartName.value}-missing.csv`
  a.click()
  URL.revokeObjectURL(url)
}

const showGapList = (type) => {
  // TODO: 打开对应评分区间的列表
}

const viewActorGaps = (actor) => {
  // TODO: 打开该演员的完整缺失列表
}

const showGapDetail = (item) => {
  // TODO: 显示影片详情
}

onMounted(() => {
  fetchGaps()
})
</script>

<style scoped>
.gap-analysis-view {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  text-align: center;
  background: #1a1a1a;
}

.stat-value {
  font-size: 32px;
  font-weight: 600;
}

.stat-value.missing {
  color: #ef4444;
}

.stat-value.high {
  color: #4ade80;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 4px;
}

.section-card {
  margin-bottom: 20px;
  background: #1a1a1a;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
}

.score-distribution {
  display: flex;
  gap: 24px;
}

.dist-item {
  flex: 1;
  padding: 16px;
  border-radius: 8px;
  background: #242424;
}

.dist-item.high {
  border-left: 4px solid #4ade80;
}

.dist-item.medium {
  border-left: 4px solid #facc15;
}

.dist-item.low {
  border-left: 4px solid #ef4444;
}

.dist-label {
  display: block;
  margin-bottom: 8px;
}

.dist-count {
  font-size: 24px;
  font-weight: 600;
  margin-right: 12px;
}

.actor-group {
  margin-bottom: 20px;
}

.actor-header {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  background: #242424;
  border-radius: 4px;
  margin-bottom: 8px;
}

.actor-name {
  font-weight: 600;
  color: #e50914;
}

.actor-count {
  color: #666;
}

.gap-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-bottom: 1px solid #333;
}

.gap-item:hover {
  background: #242424;
}

.gap-rank {
  width: 40px;
  color: #666;
}

.gap-code {
  flex: 1;
  font-weight: 600;
}

.batch-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 16px;
}
</style>
