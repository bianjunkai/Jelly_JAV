<template>
  <div class="report-detail-view">
    <div class="page-header">
      <div class="header-left">
        <button class="back-btn" @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon>
          <span>返回</span>
        </button>
        <div class="report-badge" :class="report?.type">{{ getTypeName(report?.type) }}</div>
        <h1 class="page-title">{{ report?.title }}</h1>
      </div>
      <div class="header-actions">
        <el-button type="danger" plain size="small" @click="handleDelete">
          <el-icon><Delete /></el-icon>
          删除
        </el-button>
      </div>
    </div>

    <div class="report-meta">
      <span class="meta-item">
        <el-icon><Clock /></el-icon>
        {{ formatDate(report?.generated_at) }}
      </span>
      <span class="meta-item" v-if="report?.period">
        <el-icon><Calendar /></el-icon>
        {{ report.period }}
      </span>
    </div>

    <div v-loading="loading" class="report-content">
      <!-- 周报 -->
      <template v-if="report?.type === 'weekly'">
        <div class="summary-card">
          <div class="summary-stat">
            <span class="stat-num">{{ report.data?.total_count || 0 }}</span>
            <span class="stat-label">部新片</span>
          </div>
          <div class="summary-stat">
            <span class="stat-num">{{ actorCount }}</span>
            <span class="stat-label">位演员</span>
          </div>
        </div>

        <div v-if="report.data?.by_actor" class="actor-sections">
          <div v-for="(movies, actor) in report.data.by_actor" :key="actor" class="actor-group">
            <h3 class="actor-name">
              <el-icon><User /></el-icon>
              {{ actor }}
              <span class="actor-count">{{ movies.length }} 部</span>
            </h3>
            <div class="movie-grid">
              <div v-for="movie in movies" :key="movie.code" class="movie-card" @click="showMovieDetail(movie.code)">
                <div class="movie-header">
                  <div class="movie-code">{{ movie.code }}</div>
                  <div class="movie-links">
                    <button class="link-btn" @click.stop="openJavBus(movie.code)" title="打开 JavBus">
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                      <span>Bus</span>
                    </button>
                    <button class="link-btn javdb" @click.stop="openJavDb(movie.code, movie.javdb_id)" title="打开 JavDB">
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                      <span>DB</span>
                    </button>
                  </div>
                </div>
                <div class="movie-title">{{ movie.title || movie.code }}</div>
                <div class="movie-date">{{ movie.release_date }}</div>
                <div class="movie-score" v-if="movie.javdb_score">
                  <span class="score">★ {{ movie.javdb_score.toFixed(1) }}</span>
                </div>
                <div class="in-todo-badge" v-if="movie.in_todo">待看</div>
              </div>
            </div>
          </div>
        </div>
        <el-empty v-else description="暂无数据" />
      </template>

      <!-- 月报 -->
      <template v-else-if="report?.type === 'monthly'">
        <div class="summary-card">
          <div class="summary-stat">
            <span class="stat-num">{{ report.data?.total_count || 0 }}</span>
            <span class="stat-label">部影片</span>
          </div>
          <div class="summary-stat">
            <span class="stat-num accent">{{ risingCount }}</span>
            <span class="stat-label">部上升</span>
          </div>
        </div>

        <el-table :data="report.data?.items || []" stripe class="report-table" @row-click="row => showMovieDetail(row.movie.code)">
          <el-table-column label="番号" width="120" prop="movie.code">
            <template #default="{ row }">
              <span class="code-text" style="cursor:pointer;">{{ row.movie.code }}</span>
              <el-button size="small" circle style="margin-left:4px;" @click.stop="openJavBus(row.movie.code)" title="JavBus">
                <span style="font-size:10px;font-weight:700;">JB</span>
              </el-button>
            </template>
          </el-table-column>
          <el-table-column label="标题" min-width="200" prop="movie.title" show-overflow-tooltip />
          <el-table-column label="原评分" width="80" align="center">
            <template #default="{ row }">
              <span class="score-prev">{{ row.prev_score?.toFixed(1) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="新评分" width="80" align="center">
            <template #default="{ row }">
              <span class="score-curr">{{ row.curr_score?.toFixed(1) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="涨幅" width="80" align="center">
            <template #default="{ row }">
              <span class="score-change">↑ {{ row.change }}</span>
            </template>
          </el-table-column>
        </el-table>
      </template>

      <!-- 年报 -->
      <template v-else-if="report?.type === 'annual'">
        <div class="summary-card">
          <div class="summary-stat">
            <span class="stat-num">{{ report.data?.total_missing || 0 }}</span>
            <span class="stat-label">部缺失</span>
          </div>
          <div class="summary-stat" v-if="report.data?.followed_missing_count">
            <span class="stat-num accent">{{ report.data.followed_missing_count }}</span>
            <span class="stat-label">关注演员</span>
          </div>
        </div>

        <el-tabs v-model="activeTab" class="annual-tabs">
          <el-tab-pane label="关注演员缺失" name="followed">
            <div class="movie-grid" v-if="report.data?.followed_missing?.length">
              <div v-for="item in report.data.followed_missing" :key="item.code" class="movie-card" @click="showMovieDetail(item.code)">
                <div class="movie-header">
                  <div class="movie-rank">#{{ item.rank }}</div>
                  <div class="movie-links">
                    <el-button size="small" circle @click.stop="openJavBus(item.code)" title="JavBus">
                      <span style="font-size:11px;font-weight:700;">JB</span>
                    </el-button>
                    <el-button size="small" circle @click.stop="openJavDb(item.code)" title="JavDB">
                      <span style="font-size:11px;font-weight:700;">JD</span>
                    </el-button>
                  </div>
                </div>
                <div class="movie-code">{{ item.code }}</div>
                <div class="movie-title">{{ item.title }}</div>
                <div class="movie-score" v-if="item.score">
                  <span class="score">★ {{ item.score.toFixed(1) }}</span>
                </div>
              </div>
            </div>
            <el-empty v-else description="暂无关注演员缺失" />
          </el-tab-pane>
          <el-tab-pane label="高分缺失" name="highscore">
            <div class="movie-grid" v-if="report.data?.high_score_missing?.length">
              <div v-for="item in report.data.high_score_missing" :key="item.code" class="movie-card" @click="showMovieDetail(item.code)">
                <div class="movie-header">
                  <div class="movie-rank">#{{ item.rank }}</div>
                  <div class="movie-links">
                    <el-button size="small" circle @click.stop="openJavBus(item.code)" title="JavBus">
                      <span style="font-size:11px;font-weight:700;">JB</span>
                    </el-button>
                    <el-button size="small" circle @click.stop="openJavDb(item.code)" title="JavDB">
                      <span style="font-size:11px;font-weight:700;">JD</span>
                    </el-button>
                  </div>
                </div>
                <div class="movie-code">{{ item.code }}</div>
                <div class="movie-title">{{ item.title }}</div>
                <div class="movie-score">
                  <span class="score">★ {{ item.score.toFixed(1) }}</span>
                </div>
              </div>
            </div>
            <el-empty v-else description="暂无高分缺失" />
          </el-tab-pane>
        </el-tabs>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Clock, Calendar, User, Delete } from '@element-plus/icons-vue'
import { reportsApi, moviesApi } from '../api'
import { getJavBusUrl, getJavDbUrl } from '../utils/movieUrl'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const report = ref(null)
const activeTab = ref('followed')

const actorCount = computed(() => Object.keys(report.value?.data?.by_actor || {}).length)
const risingCount = computed(() => (report.value?.data?.items || []).filter(i => i.change > 0).length)

const getTypeName = (type) => {
  const map = { weekly: '周报', monthly: '月报', annual: '年报' }
  return map[type] || type
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日 ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

const fetchReport = async () => {
  loading.value = true
  try {
    const reports = await reportsApi.list()
    const id = parseInt(route.params.id)
    report.value = reports.find(r => r.id === id)
    if (!report.value) {
      ElMessage.error('报告不存在')
      router.push('/discover')
    }
  } catch (e) {
    ElMessage.error('获取报告失败')
  } finally {
    loading.value = false
  }
}

const showMovieDetail = (code) => {
  moviesApi.get(code).then(movie => {
    window.showMovieDetail(movie)
  }).catch(() => {
    window.open(getJavBusUrl(code), '_blank')
  })
}

const openJavBus = (code) => {
  window.open(getJavBusUrl(code), '_blank')
}

const openJavDb = (code, javdbId) => {
  window.open(getJavDbUrl(code, javdbId), '_blank')
}

const handleDelete = async () => {
  try {
    await ElMessageBox.confirm('确定要删除这份报告吗？', '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    const id = parseInt(route.params.id)
    await reportsApi.delete(id)
    ElMessage.success('已删除')
    router.push('/discover')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

onMounted(() => {
  fetchReport()
})
</script>

<style scoped>
.report-detail-view {
  max-width: 1100px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: var(--bg-secondary);
  border: none;
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 14px;
}

.back-btn:hover {
  background: var(--bg-tertiary);
}

.report-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.report-badge.weekly { background: #F5D5CE; color: #C97E75; }
.report-badge.monthly { background: #F0E0D0; color: #A08050; }
.report-badge.annual { background: #E0E8F0; color: #608090; }

.page-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
}

.report-meta {
  display: flex;
  gap: 20px;
  margin-bottom: 24px;
  color: var(--text-muted);
  font-size: 14px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.summary-card {
  display: flex;
  gap: 40px;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 24px 32px;
  margin-bottom: 24px;
  box-shadow: var(--shadow-card);
}

.summary-stat {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.stat-num {
  font-size: 36px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-num.accent {
  color: var(--accent-gold);
}

.stat-label {
  font-size: 14px;
  color: var(--text-muted);
}

.actor-sections {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.actor-group {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-card);
}

.actor-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.actor-count {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-muted);
  background: var(--bg-secondary);
  padding: 2px 8px;
  border-radius: 10px;
}

.movie-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}

.movie-card {
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.movie-card:hover {
  background: var(--bg-tertiary);
  transform: translateY(-2px);
}

.movie-rank {
  font-size: 11px;
  color: var(--text-muted);
}

.movie-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.movie-links {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.link-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 11px;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.link-btn:hover {
  background: var(--primary-color);
  border-color: var(--primary-color);
  color: #fff;
}

.link-btn.javdb:hover {
  background: #E8A598;
  border-color: #E8A598;
}

.link-btn svg {
  flex-shrink: 0;
}

.movie-code {
  font-size: 14px;
  font-weight: 700;
  color: var(--primary-color);
  margin-bottom: 6px;
}

.movie-title {
  font-size: 13px;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 6px;
}

.movie-date {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.movie-score .score {
  font-size: 13px;
  color: var(--accent-gold);
  font-weight: 600;
}

.in-todo-badge {
  position: absolute;
  bottom: 8px;
  right: 8px;
  font-size: 10px;
  background: var(--primary-color);
  color: #fff;
  padding: 2px 6px;
  border-radius: 8px;
}

.report-table {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
}

.code-text {
  font-weight: 600;
  color: var(--primary-color);
}

.score-prev {
  color: var(--text-muted);
  text-decoration: line-through;
}

.score-curr {
  color: var(--accent-gold);
  font-weight: 600;
}

.score-change {
  color: var(--accent-green);
  font-weight: 600;
}

.annual-tabs {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-card);
}
</style>
