<template>
  <div class="report-detail-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <button class="back-btn" @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon>
          <span>返回</span>
        </button>
        <div class="report-badge" :class="report?.type">
          <el-icon v-if="report?.type === 'weekly'"><Calendar /></el-icon>
          <el-icon v-else-if="report?.type === 'monthly'"><TrendCharts /></el-icon>
          <el-icon v-else><Trophy /></el-icon>
          {{ getTypeName(report?.type) }}
        </div>
        <h1 class="page-title">{{ report?.title }}</h1>
      </div>
      <div class="header-actions">
        <el-button type="danger" plain size="small" @click="handleDelete">
          <el-icon><Delete /></el-icon>
          删除
        </el-button>
      </div>
    </div>

    <!-- 报告元信息 -->
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
      <!-- 加载骨架屏 -->
      <template v-if="loading">
        <div class="summary-skeleton">
          <div class="skeleton" style="width: 120px; height: 48px;"></div>
          <div class="skeleton" style="width: 80px; height: 48px;"></div>
        </div>
        <div class="movie-list">
          <div v-for="i in 8" :key="i" class="movie-card-skeleton">
            <div class="skeleton skeleton-rank"></div>
            <div class="skeleton skeleton-info">
              <div class="skeleton skeleton-code"></div>
              <div class="skeleton skeleton-title"></div>
            </div>
            <div class="skeleton skeleton-actions"></div>
          </div>
        </div>
      </template>

      <!-- 周报 -->
      <template v-else-if="report?.type === 'weekly'">
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
            <div class="actor-header">
              <div class="actor-info">
                <div class="actor-avatar">{{ actor.charAt(0) }}</div>
                <div class="actor-details">
                  <h3 class="actor-name">{{ actor }}</h3>
                  <span class="actor-count">{{ movies.length }} 部新片</span>
                </div>
              </div>
            </div>

            <div class="movie-list">
              <div
                v-for="(movie, index) in movies"
                :key="movie.code"
                class="movie-card"
                :style="{ animationDelay: `${index * 30}ms` }"
                @click="showMovieDetail(movie.code)"
              >
                <!-- 左侧：番号 + 评分 -->
                <div class="card-left">
                  <div class="rank-badge" v-if="movie.rank">#{{ movie.rank }}</div>
                  <div class="movie-code">{{ movie.code }}</div>
                  <div class="movie-score" v-if="movie.javdb_score">
                    <span class="score-star">★</span>
                    <span class="score-value">{{ movie.javdb_score.toFixed(2) }}</span>
                  </div>
                </div>

                <!-- 中间：影片信息 -->
                <div class="card-main">
                  <h4 class="movie-title">{{ movie.title || movie.code }}</h4>
                  <div class="movie-meta">
                    <span class="meta-tag date" v-if="movie.release_date">
                      <el-icon><Calendar /></el-icon>
                      {{ movie.release_date }}
                    </span>
                    <span class="meta-tag status" :class="{ released: movie.is_released }">
                      {{ movie.is_released ? '已发行' : '待发行' }}
                    </span>
                    <span class="meta-tag todo" v-if="movie.in_todo">
                      <el-icon><Check /></el-icon>
                      已添加待看
                    </span>
                  </div>
                </div>

                <!-- 右侧：操作按钮 -->
                <div class="card-actions">
                  <button class="action-btn primary" @click.stop="openJavBus(movie.code)" title="JavBus">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
                    <span>JavBus</span>
                  </button>
                  <button class="action-btn" @click.stop="openJavDb(movie.code, movie.javdb_id)" title="JavDB">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                    <span>JavDB</span>
                  </button>
                  <button class="action-btn add-todo" @click.stop="addToTodo(movie)" title="加入待看" v-if="!movie.in_todo">
                    <el-icon><Plus /></el-icon>
                    <span>待看</span>
                  </button>
                </div>
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
            <span class="stat-num">{{ report.data?.total_new_releases || 0 }}</span>
            <span class="stat-label">部新片</span>
          </div>
          <div class="summary-stat">
            <span class="stat-num accent">{{ report.data?.total_score_changes || 0 }}</span>
            <span class="stat-label">部涨分</span>
          </div>
        </div>

        <!-- 按演员分组显示 -->
        <div v-if="report.data?.by_actor" class="actor-sections">
          <div v-for="(movies, actor) in report.data.by_actor" :key="actor" class="actor-group">
            <div class="actor-header">
              <div class="actor-info">
                <div class="actor-avatar">{{ actor.charAt(0) }}</div>
                <div class="actor-details">
                  <h3 class="actor-name">{{ actor }}</h3>
                  <span class="actor-count">
                    {{ movies.filter(m => m.category === 'new_release').length }} 部新片
                    <span v-if="movies.filter(m => m.category === 'score_change').length > 0">
                      · {{ movies.filter(m => m.category === 'score_change').length }} 部涨分
                    </span>
                  </span>
                </div>
              </div>
            </div>

            <div class="movie-list">
              <div
                v-for="(movie, index) in movies"
                :key="movie.code"
                class="movie-card"
                :style="{ animationDelay: `${index * 30}ms` }"
                @click="showMovieDetail(movie.code)"
              >
                <div class="card-left">
                  <div class="movie-code">{{ movie.code }}</div>
                  <!-- 新片显示评分 -->
                  <div class="movie-score" v-if="movie.category === 'new_release' && movie.javdb_score">
                    <span class="score-star">★</span>
                    <span class="score-value">{{ movie.javdb_score.toFixed(2) }}</span>
                  </div>
                  <!-- 涨分显示分数变化 -->
                  <div v-if="movie.category === 'score_change'" class="score-comparison">
                    <span class="score-prev">{{ movie.prev_score?.toFixed(2) }}</span>
                    <span class="score-arrow">→</span>
                    <span class="score-curr">{{ movie.curr_score?.toFixed(2) }}</span>
                  </div>
                  <div class="score-change positive" v-if="movie.category === 'score_change'">
                    <span class="change-icon">↑</span>
                    <span>{{ Math.abs(movie.change).toFixed(2) }}</span>
                  </div>
                </div>

                <div class="card-main">
                  <h4 class="movie-title">{{ movie.title || movie.code }}</h4>
                  <div class="movie-meta">
                    <span class="meta-tag new-tag" v-if="movie.category === 'new_release' && movie.is_released === false">
                      <el-icon><Clock /></el-icon>
                      未入库
                    </span>
                    <span class="meta-tag new-tag" v-if="movie.category === 'new_release' && movie.release_date">
                      <el-icon><Calendar /></el-icon>
                      {{ movie.release_date }}
                    </span>
                    <span class="meta-tag rise-tag" v-if="movie.category === 'score_change'">
                      <el-icon><TrendCharts /></el-icon>
                      分数上升
                    </span>
                  </div>
                </div>

                <div class="card-actions">
                  <button class="action-btn primary" @click.stop="openJavBus(movie.code)">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
                    <span>JavBus</span>
                  </button>
                  <button class="action-btn" @click.stop="openJavDb(movie.code, movie.javdb_id)">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                    <span>JavDB</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <el-empty v-if="!report.data?.by_actor || Object.keys(report.data.by_actor).length === 0" description="暂无数据" />
      </template>

      <!-- 年报 -->
      <template v-else-if="report?.type === 'annual'">
        <div class="summary-card">
          <div class="summary-stat highlight">
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
            <div class="movie-list" v-if="report.data?.followed_missing?.length">
              <div
                v-for="(item, index) in report.data.followed_missing"
                :key="item.code"
                class="movie-card"
                :style="{ animationDelay: `${index * 25}ms` }"
                @click="showMovieDetail(item.code)"
              >
                <div class="card-left">
                  <div class="rank-badge">#{{ item.rank }}</div>
                  <div class="movie-code">{{ item.code }}</div>
                  <div class="movie-score" v-if="item.score">
                    <span class="score-star">★</span>
                    <span class="score-value">{{ item.score.toFixed(2) }}</span>
                  </div>
                </div>

                <div class="card-main">
                  <h4 class="movie-title">{{ item.title || item.code }}</h4>
                  <div class="movie-meta">
                    <span class="meta-tag" v-if="item.actors?.length">
                      <el-icon><User /></el-icon>
                      {{ item.actors.slice(0, 2).join(', ') }}
                    </span>
                    <span class="meta-tag followed" v-if="item.is_followed_actor">
                      <el-icon><Star /></el-icon>
                      关注演员
                    </span>
                  </div>
                </div>

                <div class="card-actions">
                  <button class="action-btn primary" @click.stop="openJavBus(item.code)">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
                    <span>JavBus</span>
                  </button>
                  <button class="action-btn" @click.stop="openJavDb(item.code)">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                    <span>JavDB</span>
                  </button>
                  <button class="action-btn add-todo" @click.stop="addToTodo(item)" v-if="!item.in_todo">
                    <el-icon><Plus /></el-icon>
                    <span>待看</span>
                  </button>
                </div>
              </div>
            </div>
            <el-empty v-else description="暂无关注演员缺失" />
          </el-tab-pane>

          <el-tab-pane label="高分缺失" name="highscore">
            <div class="movie-list" v-if="report.data?.high_score_missing?.length">
              <div
                v-for="(item, index) in report.data.high_score_missing"
                :key="item.code"
                class="movie-card"
                :style="{ animationDelay: `${index * 25}ms` }"
                @click="showMovieDetail(item.code)"
              >
                <div class="card-left">
                  <div class="rank-badge gold">#{{ item.rank }}</div>
                  <div class="movie-code">{{ item.code }}</div>
                  <div class="movie-score gold" v-if="item.score">
                    <span class="score-star">★</span>
                    <span class="score-value">{{ item.score.toFixed(2) }}</span>
                  </div>
                </div>

                <div class="card-main">
                  <h4 class="movie-title">{{ item.title || item.code }}</h4>
                  <div class="movie-meta">
                    <span class="meta-tag" v-if="item.actors?.length">
                      <el-icon><User /></el-icon>
                      {{ item.actors.slice(0, 2).join(', ') }}
                    </span>
                  </div>
                </div>

                <div class="card-actions">
                  <button class="action-btn primary" @click.stop="openJavBus(item.code)">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
                    <span>JavBus</span>
                  </button>
                  <button class="action-btn" @click.stop="openJavDb(item.code)">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                    <span>JavDB</span>
                  </button>
                  <button class="action-btn add-todo" @click.stop="addToTodo(item)" v-if="!item.in_todo">
                    <el-icon><Plus /></el-icon>
                    <span>待看</span>
                  </button>
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
import {
  ArrowLeft,
  Clock,
  Calendar,
  User,
  Delete,
  Trophy,
  TrendCharts,
  Plus,
  Check,
  Star,
  VideoCamera
} from '@element-plus/icons-vue'
import { reportsApi, moviesApi, todosApi } from '../api'
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

const addToTodo = async (movie) => {
  try {
    await todosApi.add({
      code: movie.code,
      title: movie.title || movie.code,
      actors: movie.actors ? movie.actors.join(',') : '',
      source: report.value?.type === 'weekly' ? 'weekly' : report.value?.type === 'monthly' ? 'monthly' : 'annual',
      source_detail: `${report.value?.title || ''}`
    })
    ElMessage.success(`已加入待看清单`)
    movie.in_todo = true
  } catch (e) {
    ElMessage.error('添加失败')
  }
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
  max-width: 1200px;
  margin: 0 auto;
}

/* 页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 16px;
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
  padding: 8px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all var(--duration-fast) var(--ease-default);
}

.back-btn:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border-color: var(--border-focus);
}

.report-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: var(--radius-badge);
  font-size: 12px;
  font-weight: 600;
}

.report-badge.weekly {
  background: linear-gradient(135deg, #F5D5CE, #E8A598);
  color: #fff;
}

.report-badge.monthly {
  background: linear-gradient(135deg, #F0E0D0, #D4A574);
  color: #fff;
}

.report-badge.annual {
  background: linear-gradient(135deg, #E0E8F0, #8FB8CD);
  color: #fff;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.3px;
}

/* 报告元信息 */
.report-meta {
  display: flex;
  gap: 24px;
  margin-bottom: 28px;
  color: var(--text-tertiary);
  font-size: 14px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 摘要卡片 */
.summary-card {
  display: flex;
  gap: 48px;
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  padding: 24px 32px;
  margin-bottom: 24px;
  box-shadow: var(--shadow-card);
}

.summary-stat {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.summary-stat.highlight .stat-num {
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-num {
  font-size: 40px;
  font-weight: 800;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
  line-height: 1;
}

.stat-num.accent {
  background: var(--accent-gold-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-label {
  font-size: 14px;
  color: var(--text-muted);
}

/* 演员分组 */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 0 12px 0;
  border-bottom: 1px solid var(--border-light);
  margin-bottom: 16px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.section-count {
  font-size: 13px;
  color: var(--text-muted);
  background: var(--bg-secondary);
  padding: 4px 10px;
  border-radius: 12px;
}

.actor-sections {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.actor-group {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  padding: 20px 24px;
  box-shadow: var(--shadow-card);
}

.actor-header {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-light);
}

.actor-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.actor-avatar {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-full);
  background: linear-gradient(135deg, var(--primary-light), var(--primary-color));
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 16px;
  font-weight: 700;
}

.actor-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.actor-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.actor-count {
  font-size: 12px;
  color: var(--text-muted);
}

/* 影片列表 - 横向卡片 */
.movie-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.movie-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--duration-normal) var(--ease-default);
  animation: fadeInLeft var(--duration-slow) var(--ease-out) both;
  border: 1px solid transparent;
}

.movie-card:hover {
  background: var(--bg-card);
  border-color: var(--primary-light);
  box-shadow: var(--shadow-sm);
  transform: translateX(4px);
}

@keyframes fadeInLeft {
  from {
    opacity: 0;
    transform: translateX(-12px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* 卡片左侧 - 番号区 */
.card-left {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 100px;
  flex-shrink: 0;
}

.rank-badge {
  padding: 2px 8px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  font-size: 11px;
  font-weight: 600;
  color: var(--text-secondary);
}

.rank-badge.gold {
  background: linear-gradient(135deg, #F0E0D0, #D4A574);
  color: #fff;
}

.movie-code {
  font-family: var(--font-mono);
  font-size: 15px;
  font-weight: 700;
  color: var(--primary-color);
  letter-spacing: 0;
}

.movie-score {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 13px;
  font-weight: 600;
  color: var(--accent-gold);
}

.movie-score.gold {
  background: linear-gradient(135deg, #F0E0D0, #D4A574);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.score-star {
  font-size: 11px;
}

.score-value {
  font-variant-numeric: tabular-nums;
}

/* 月报分数对比 */
.score-comparison {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.score-prev {
  color: var(--text-muted);
  text-decoration: line-through;
}

.score-arrow {
  color: var(--text-tertiary);
}

.score-curr {
  color: var(--accent-gold);
  font-weight: 600;
}

.score-change {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 12px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-variant-numeric: tabular-nums;
}

.score-change.positive {
  background: var(--accent-green-light);
  color: var(--accent-green);
}

.score-change.negative {
  background: var(--accent-red-light);
  color: var(--accent-red);
}

.score-change.neutral {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.change-icon {
  font-size: 10px;
}

/* 卡片中间 - 信息区 */
.card-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.movie-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.4;
}

.movie-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.meta-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  font-size: 11px;
  color: var(--text-tertiary);
}

.meta-tag.date {
  color: var(--text-secondary);
}

.meta-tag.status {
  background: var(--accent-gold-light);
  color: var(--accent-gold);
}

.meta-tag.status.released {
  background: var(--accent-green-light);
  color: var(--accent-green);
}

.meta-tag.todo {
  background: var(--primary-light);
  color: var(--primary-dark);
}

.meta-tag.followed {
  background: var(--accent-purple-light);
  color: var(--accent-purple);
}

.meta-tag.new-tag {
  background: var(--accent-green-light);
  color: var(--accent-green);
}

.meta-tag.rise-tag {
  background: var(--accent-gold-light);
  color: var(--accent-gold);
}

.release-date {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 4px;
}

/* 卡片右侧 - 操作按钮 */
.card-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
  opacity: 0;
  transition: opacity var(--duration-fast) var(--ease-default);
}

.movie-card:hover .card-actions {
  opacity: 1;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-default);
  white-space: nowrap;
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.action-btn.primary {
  background: var(--primary-gradient);
  border-color: transparent;
  color: #fff;
}

.action-btn.primary:hover {
  background: var(--primary-gradient-hover);
  box-shadow: var(--shadow-primary);
}

.action-btn.add-todo {
  background: var(--accent-green);
  border-color: transparent;
  color: #fff;
}

.action-btn.add-todo:hover {
  background: #7AA882;
}

/* 年度标签页 */
.annual-tabs {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  padding: 20px 24px;
  box-shadow: var(--shadow-card);
}

.annual-tabs :deep(.el-tabs__header) {
  margin-bottom: 20px;
}

.annual-tabs :deep(.el-tabs__item) {
  font-weight: 600;
}

.annual-tabs :deep(.el-tabs__item.is-active) {
  color: var(--primary-color);
}

.annual-tabs :deep(.el-tabs__active-bar) {
  background: var(--primary-gradient);
}

/* 骨架屏 */
.summary-skeleton {
  display: flex;
  gap: 48px;
  margin-bottom: 24px;
}

.movie-card-skeleton {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
}

.skeleton-rank {
  width: 60px;
  height: 50px;
}

.skeleton-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton-code {
  width: 80px;
  height: 18px;
}

.skeleton-title {
  width: 100%;
  height: 14px;
}

.skeleton-actions {
  width: 120px;
  height: 34px;
}

/* 响应式 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .page-title {
    font-size: 20px;
  }

  .summary-card {
    flex-direction: column;
    gap: 16px;
    padding: 20px;
  }

  .stat-num {
    font-size: 32px;
  }

  .movie-card {
    flex-wrap: wrap;
    padding: 12px;
  }

  .card-left {
    min-width: auto;
    flex-direction: row;
    gap: 12px;
  }

  .card-main {
    flex-basis: calc(100% - 130px);
  }

  .card-actions {
    opacity: 1;
    flex-wrap: wrap;
  }

  .action-btn span {
    display: none;
  }

  .action-btn {
    padding: 8px;
  }

  .annual-tabs {
    padding: 12px;
  }
}
</style>
