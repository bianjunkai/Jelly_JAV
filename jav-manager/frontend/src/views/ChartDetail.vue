<template>
  <div class="chart-detail-view">
    <div class="page-header">
      <div class="header-left">
        <el-button text @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <h1 class="page-title">{{ chart?.display_name }}</h1>
      </div>
      <div class="header-stats">
        <span>共 {{ total }} 部</span>
        <span>已收藏 {{ collected }} ({{ coveragePercent }}%)</span>
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
      <el-table-column label="排名" width="80" prop="rank" sortable />
      <el-table-column label="番号" width="120" prop="code" />
      <el-table-column label="标题" min-width="200" prop="title" show-overflow-tooltip />
      <el-table-column label="演员" width="150">
        <template #default="{ row }">
          {{ row.actors?.slice(0, 2).join(', ') }}
        </template>
      </el-table-column>
      <el-table-column label="评分" width="100" sortable prop="score">
        <template #default="{ row }">
          <span v-if="row.score" class="score-badge" :class="getScoreClass(row.score)">
            ★ {{ row.score.toFixed(1) }}
          </span>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.in_library" type="success" size="small">已收藏</el-tag>
          <el-tag v-else type="info" size="small">未收藏</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button v-if="!row.in_library" size="small" type="primary" @click.stop="addToTodo(row)">
            加入待看
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="fetchChart"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { chartsApi, todosApi } from '../api'

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
  if (row.in_library && row.movie_id) {
    // TODO: 显示本地影片详情
  }
}

const addToTodo = async (row) => {
  try {
    await todosApi.add({
      code: row.code,
      title: row.title,
      actors: row.actors?.join(',') || '',
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
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
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

.header-stats {
  display: flex;
  gap: 24px;
  color: #666;
  font-size: 14px;
}

.filter-tabs {
  margin-bottom: 20px;
}

.chart-table {
  background: #1a1a1a;
  border-radius: 8px;
}

.chart-table :deep(.el-table__row) {
  cursor: pointer;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
</style>
