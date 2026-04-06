<template>
  <div class="chart-detail-view">
    <div class="page-header">
      <div class="header-left">
        <button class="back-btn" @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon>
          <span>返回</span>
        </button>
        <h1 class="page-title">{{ chart?.display_name }}</h1>
      </div>
      <div class="header-stats">
        <div class="stat-item">
          <span class="stat-value">{{ total }}</span>
          <span class="stat-label">总数</span>
        </div>
        <div class="stat-item">
          <span class="stat-value collected">{{ collected }}</span>
          <span class="stat-label">已收藏</span>
        </div>
        <div class="stat-item">
          <span class="stat-value missing">{{ total - collected }}</span>
          <span class="stat-label">缺失</span>
        </div>
      </div>
    </div>

    <div class="filter-tabs">
      <el-radio-group v-model="filterType" @change="fetchChart">
        <el-radio-button label="all">全部 ({{ total }})</el-radio-button>
        <el-radio-button label="collected">已收藏 ({{ collected }})</el-radio-button>
        <el-radio-button label="missing">未收藏 ({{ total - collected }})</el-radio-button>
      </el-radio-group>
    </div>

    <el-table :data="items" stripe class="chart-table" @row-click="showDetail">
      <el-table-column label="排名" width="70" prop="rank" sortable>
        <template #default="{ row }">
          <span class="rank-num" :class="{ top: row.rank <= 3 }">#{{ row.rank }}</span>
        </template>
      </el-table-column>
      <el-table-column label="番号" width="110" prop="code">
        <template #default="{ row }">
          <span class="code-text">{{ row.code }}</span>
        </template>
      </el-table-column>
      <el-table-column label="标题" min-width="280" prop="title" show-overflow-tooltip />
      <el-table-column label="评分" width="90" sortable prop="score">
        <template #default="{ row }">
          <span v-if="row.score" class="score-badge" :class="getScoreClass(row.score)">
            ★ {{ row.score.toFixed(2) }}
          </span>
          <span v-else class="no-score">-</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <span class="status-tag" :class="row.in_library ? 'collected' : 'missing'">
            {{ row.in_library ? '✓ 已收藏' : '未收藏' }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <button class="table-action-btn primary" v-if="!row.in_library" @click.stop="addToTodo(row)" title="添加到待看">
            <el-icon><Plus /></el-icon>
          </button>
          <button class="table-action-btn" @click.stop="openJavBus(row.code)" title="打开 JavBus">
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
          </button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next, jumper"
        @current-change="fetchChart"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Plus } from '@element-plus/icons-vue'
import { chartsApi, todosApi, moviesApi } from '../api'
import { getJavBusUrl } from '../utils/movieUrl'

const route = useRoute()
const chart = ref(null)
const items = ref([])
const currentPage = ref(1)
const pageSize = ref(50)
const total = ref(0)
const collected = ref(0)
const coveragePercent = computed(() => total.value > 0 ? Math.round(collected.value / total.value * 100) : 0)
const filterType = ref('all')

const chartName = computed(() => decodeURIComponent(route.params.name))

const fetchChart = async () => {
  try {
    const data = await chartsApi.get(chartName.value, {
      page: currentPage.value,
      per_page: pageSize.value,
      filter: filterType.value
    })
    chart.value = data.chart
    items.value = data.items
    total.value = data.total
    collected.value = data.collected
  } catch (e) {
    ElMessage.error('获取榜单详情失败')
  }
}

const getScoreClass = (score) => {
  if (score >= 4.5) return 'score-high'
  if (score >= 4.0) return 'score-mid'
  return 'score-low'
}

const showDetail = (row) => {
  if (row.in_library) {
    moviesApi.get(row.code).then(movie => {
      window.showMovieDetail(movie)
    }).catch(() => {
      openJavBus(row.code)
    })
  } else {
    openJavBus(row.code)
  }
}

const openJavBus = (code) => {
  window.open(getJavBusUrl(code), '_blank')
}

const addToTodo = async (row) => {
  try {
    await todosApi.add({
      code: row.code,
      title: row.title,
      actors: '',
      source: 'manual',
      source_detail: `榜单-${chartName.value}`
    })
    ElMessage.success('已加入待看清单')
  } catch (e) {
    ElMessage.error('添加失败')
  }
}

onMounted(() => {
  fetchChart()
})
</script>

<style scoped>
.chart-detail-view {
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
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
  flex-wrap: wrap;
  gap: 16px;
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

.header-stats {
  display: flex;
  gap: 20px;
  padding: 12px 20px;
  background: var(--bg-card);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-value.collected {
  color: var(--accent-green);
}

.stat-value.missing {
  color: #E8A598;
}

.stat-label {
  font-size: 12px;
  color: var(--text-tertiary);
}

.filter-tabs {
  margin-bottom: 24px;
}

.chart-table {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-card);
}

.chart-table :deep(.el-table__row) {
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.chart-table :deep(.el-table__row:hover) {
  background-color: var(--bg-secondary);
}

.status-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.status-tag.collected {
  background: rgba(143, 185, 150, 0.15);
  color: var(--accent-green);
}

.status-tag.missing {
  background: rgba(232, 165, 152, 0.15);
  color: var(--text-tertiary);
}

.pagination-container {
  display: flex;
  justify-content: center;
  padding: 24px 0;
}

.table-action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
  margin-right: 4px;
}

.table-action-btn:hover {
  background: var(--bg-tertiary);
  border-color: var(--border-color);
}

.table-action-btn.primary {
  background: var(--primary-color);
  border-color: var(--primary-color);
  color: #fff;
}

.table-action-btn.primary:hover {
  background: #D4958A;
  border-color: #D4958A;
}

@media (max-width: 768px) {
  .page-title {
    font-size: 22px;
  }

  .header-stats {
    width: 100%;
    justify-content: space-around;
  }
}
</style>
