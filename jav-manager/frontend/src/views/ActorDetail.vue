<template>
  <div class="actor-detail-view" v-if="actor">
    <!-- 页面头部 -->
    <div class="page-header">
      <button class="back-btn" @click="$router.back()">
        <el-icon><ArrowLeft /></el-icon>
        <span>返回</span>
      </button>
    </div>

    <!-- 演员信息卡片 -->
    <div class="actor-profile">
      <div class="profile-avatar">
        <img v-if="actor.photo_url" :src="actor.photo_url" :alt="actor.name" />
        <div v-else class="avatar-placeholder">
          <span class="avatar-initial">{{ actor.name.charAt(0) }}</span>
        </div>
        <button
          v-if="actor.is_followed"
          class="followed-badge"
          @click="toggleFollow"
        >
          <el-icon><StarFilled /></el-icon>
          已关注
        </button>
      </div>

      <div class="profile-info">
        <h1 class="actor-name">{{ actor.name }}</h1>

        <div class="actor-stats">
          <div class="stat-box">
            <span class="stat-num">{{ actor.movie_count }}</span>
            <span class="stat-label">影片数</span>
          </div>
          <div class="stat-box">
            <span class="stat-num">{{ actor.avg_score?.toFixed(1) || '-' }}</span>
            <span class="stat-label">平均评分</span>
          </div>
        </div>

        <div class="actor-links">
          <el-button v-if="actor.javdb_id" size="large" @click="openJavDBMovie">
            <el-icon><Link /></el-icon>
            JavDB 影片
          </el-button>
          <el-button v-if="actor.javdb_id" size="large" @click="openJavDBActor">
            <el-icon><User /></el-icon>
            JavDB 演员页
          </el-button>
          <el-button
            v-if="actor.is_followed"
            size="large"
            type="primary"
            :loading="fetchingReleases"
            @click="fetchActorReleases"
          >
            <el-icon><Refresh /></el-icon>
            获取新片
          </el-button>
        </div>

        <button
          class="follow-btn"
          :class="{ following: actor.is_followed }"
          @click="toggleFollow"
        >
          <el-icon v-if="actor.is_followed"><Check /></el-icon>
          <el-icon v-else><Plus /></el-icon>
          {{ actor.is_followed ? '已关注' : '关注此演员' }}
        </button>
      </div>
    </div>

    <!-- 标签页 -->
    <el-tabs v-model="activeTab" class="actor-tabs">
      <!-- 影片列表 -->
      <el-tab-pane label="影片" name="movies">
        <div class="movies-grid">
          <div
            v-for="movie in actor.movies"
            :key="movie.code"
            class="movie-card"
            @click="showMovieDetail(movie)"
          >
            <div class="movie-poster">
              <img v-if="movie.poster_url" :src="movie.poster_url" :alt="movie.code" />
              <div v-else class="poster-placeholder">
                <el-icon size="32"><Picture /></el-icon>
              </div>
              <div v-if="movie.javdb_score" class="score-overlay">
                <span class="score-star">★</span>
                <span class="score-value">{{ movie.javdb_score.toFixed(1) }}</span>
              </div>
            </div>
            <div class="movie-info">
              <h4 class="movie-code">{{ movie.code }}</h4>
              <p class="movie-title">{{ movie.title }}</p>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 榜单成绩 -->
      <el-tab-pane label="榜单成绩" name="charts">
        <div v-if="actor.chart_appearances?.length" class="chart-appearances">
          <div v-for="(items, chartName) in groupedChartAppearances" :key="chartName" class="chart-group">
            <div class="chart-header">
              <el-icon><Trophy /></el-icon>
              <h4>{{ chartName }}</h4>
              <span class="chart-count">{{ items.length }} 部</span>
            </div>
            <div class="chart-items">
              <div
                v-for="item in items"
                :key="item.code"
                class="chart-item"
                @click="goToChart(item, chartName)"
              >
                <span class="item-rank">#{{ item.rank }}</span>
                <span class="item-code">{{ item.code }}</span>
                <span v-if="item.score" class="item-score">★ {{ item.score.toFixed(1) }}</span>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="empty-tab">
          <el-icon size="48"><Trophy /></el-icon>
          <p>暂无榜单记录</p>
        </div>
      </el-tab-pane>

      <!-- 缺失影片 -->
      <el-tab-pane label="缺失影片" name="missing">
        <div v-if="actor.missing_in_charts?.length" class="missing-list">
          <div v-for="item in actor.missing_in_charts" :key="item.code" class="missing-item">
            <span class="missing-rank">#{{ item.rank }}</span>
            <span class="missing-code">{{ item.code }}</span>
            <span v-if="item.score" class="score-badge" :class="getScoreClass(item.score)">
              ★ {{ item.score.toFixed(1) }}
            </span>
            <el-button size="small" type="primary" @click="addToTodo(item)">
              <el-icon><Plus /></el-icon>
              加入待看
            </el-button>
          </div>
        </div>
        <div v-else class="empty-tab">
          <el-icon size="48"><CircleCheck /></el-icon>
          <p>暂无缺失记录</p>
        </div>
      </el-tab-pane>

      <!-- 演员新片 -->
      <el-tab-pane label="演员新片" name="releases">
        <div v-if="actorReleases.length" class="releases-list">
          <div
            v-for="item in actorReleases"
            :key="item.code"
            class="release-item"
            :class="{ 'in-library': item.in_library, 'in-todo': item.in_todo }"
          >
            <div class="release-main">
              <span class="release-code">{{ item.code }}</span>
              <span class="release-title">{{ item.title || '未知标题' }}</span>
              <span v-if="item.release_date" class="release-date">{{ item.release_date }}</span>
              <el-tag v-if="item.is_released === false" size="small" type="warning">未发行</el-tag>
            </div>
            <div class="release-actions">
              <el-tag v-if="item.in_library" size="small" type="success">已入库</el-tag>
              <el-tag v-else-if="item.in_todo" size="small" type="info">已待看</el-tag>
              <el-button
                v-else
                size="small"
                type="primary"
                @click="addReleaseToTodo(item)"
              >
                <el-icon><Plus /></el-icon>
                加入待看
              </el-button>
            </div>
          </div>
        </div>
        <div v-else class="empty-tab">
          <el-icon size="48"><VideoCamera /></el-icon>
          <p>暂无追踪到的新片</p>
          <p class="empty-hint">点击"获取新片"按钮从 JavDB 获取</p>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft,
  StarFilled,
  Link,
  Check,
  Plus,
  Picture,
  Trophy,
  CircleCheck,
  Refresh,
  VideoCamera,
  User
} from '@element-plus/icons-vue'
import { actorsApi, todosApi } from '../api'

const route = useRoute()
const actor = ref(null)
const activeTab = ref('movies')
const fetchingReleases = ref(false)
const actorReleases = ref([])

const actorName = computed(() => decodeURIComponent(route.params.name))

const fetchActor = async () => {
  try {
    actor.value = await actorsApi.get(actorName.value)
  } catch (e) {
    ElMessage.error('获取演员详情失败')
  }
}

const groupedChartAppearances = computed(() => {
  if (!actor.value?.chart_appearances) return {}
  const groups = {}
  for (const item of actor.value.chart_appearances) {
    const chartName = item.chart_name
    if (!groups[chartName]) groups[chartName] = []
    groups[chartName].push(item)
  }
  return groups
})

const getScoreClass = (score) => {
  if (score >= 4.5) return 'score-high'
  if (score >= 4.0) return 'score-mid'
  return 'score-low'
}

const toggleFollow = async () => {
  try {
    await actorsApi.follow(actor.value.id)
    actor.value.is_followed = !actor.value.is_followed
    ElMessage.success(actor.value.is_followed ? '已关注' : '已取消关注')
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const loadActorReleases = async () => {
  if (!actor.value?.id) return
  try {
    const result = await actorsApi.getReleases(actor.value.id)
    actorReleases.value = result.releases || []
  } catch (e) {
    console.error('获取演员新片失败:', e)
  }
}

const addReleaseToTodo = async (item) => {
  try {
    await todosApi.add({
      code: item.code,
      title: item.title,
      actors: actorName.value,
      source: 'actor_release',
      source_detail: `演员新片-${actorName.value}`
    })
    ElMessage.success('已加入待看清单')
    item.in_todo = true
  } catch (e) {
    ElMessage.error('添加失败')
  }
}

const showMovieDetail = (movie) => {
  window.showMovieDetail(movie)
}

const goToChart = (item, chartName) => {
  // TODO: 跳转到榜单对应位置
}

const addToTodo = async (item) => {
  try {
    await todosApi.add({
      code: item.code,
      title: item.title,
      actors: actorName.value,
      source: 'manual',
      source_detail: `演员缺失-${actorName.value}`
    })
    ElMessage.success('已加入待看清单')
  } catch (e) {
    ElMessage.error('添加失败')
  }
}

const openJavDBMovie = () => {
  // 打开该演员在 JavDB 的影片页面（使用第一个影片的链接逻辑）
  if (actor.value?.movies?.length > 0 && actor.value.movies[0].javdb_id) {
    window.open(`https://javdb.com/v/${actor.value.movies[0].javdb_id}`)
  } else {
    ElMessage.info('暂无 JavDB 影片链接')
  }
}

const openJavDBActor = () => {
  // 打开 JavDB 演员页面
  window.open(`https://javdb.com/actors/${actor.value.javdb_id}`)
}

const fetchActorReleases = async () => {
  if (!actor.value?.id) return
  fetchingReleases.value = true
  try {
    const result = await actorsApi.fetchReleases(actor.value.id)
    if (result.status === 'started') {
      ElMessage.success('新片获取任务已启动，将在后台执行，请稍后查看')
      // 延迟 3 秒后自动刷新新片列表并切换到新片标签页
      setTimeout(() => {
        loadActorReleases()
        activeTab.value = 'releases'
      }, 3000)
    } else {
      ElMessage.info(result.message || '任务已启动')
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '启动任务失败')
  } finally {
    fetchingReleases.value = false
  }
}

// 监听标签页切换，切换到新片标签时加载数据
watch(activeTab, (tab) => {
  if (tab === 'releases') {
    loadActorReleases()
  }
})

onMounted(() => {
  fetchActor()
})
</script>

<style scoped>
.actor-detail-view {
  max-width: 1000px;
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
  margin-bottom: 24px;
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

/* 演员信息卡片 */
.actor-profile {
  display: flex;
  gap: 32px;
  padding: 32px;
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  margin-bottom: 28px;
}

.profile-avatar {
  position: relative;
  width: 160px;
  height: 160px;
  border-radius: 24px;
  overflow: hidden;
  flex-shrink: 0;
  background: linear-gradient(135deg, var(--bg-tertiary), var(--bg-secondary));
}

.profile-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-initial {
  font-size: 64px;
  font-weight: 700;
  color: var(--text-muted);
}

.followed-badge {
  position: absolute;
  bottom: 12px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  background: var(--primary-gradient);
  border: none;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(232, 165, 152, 0.4);
}

.profile-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.actor-name {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 20px;
  letter-spacing: -0.5px;
}

.actor-stats {
  display: flex;
  gap: 32px;
  margin-bottom: 24px;
}

.stat-box {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-num {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-label {
  font-size: 13px;
  color: var(--text-tertiary);
}

.actor-links {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.follow-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px 32px;
  background: var(--primary-gradient);
  border: none;
  border-radius: var(--radius-md);
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-top: auto;
  width: fit-content;
}

.follow-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(232, 165, 152, 0.4);
}

.follow-btn.following {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.follow-btn.following:hover {
  background: var(--bg-secondary);
  box-shadow: none;
}

/* 标签页 */
.actor-tabs {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 24px;
  box-shadow: var(--shadow-card);
}

/* 影片网格 */
.movies-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 16px;
}

.movie-card {
  cursor: pointer;
  transition: transform 0.3s ease;
}

.movie-card:hover {
  transform: translateY(-4px);
}

.movie-poster {
  position: relative;
  aspect-ratio: 2/3;
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--bg-tertiary);
  margin-bottom: 10px;
}

.movie-poster img {
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
  top: 8px;
  right: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  backdrop-filter: blur(4px);
}

.score-star {
  font-size: 12px;
  color: var(--accent-gold);
}

.score-value {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
}

.movie-info {
  padding: 0 4px;
}

.movie-code {
  font-size: 14px;
  font-weight: 600;
  color: var(--primary-color);
  margin-bottom: 4px;
}

.movie-title {
  font-size: 12px;
  color: var(--text-tertiary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 榜单成绩 */
.chart-appearances {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.chart-group {
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.chart-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  background: var(--bg-tertiary);
}

.chart-header .el-icon {
  color: var(--accent-gold);
}

.chart-header h4 {
  flex: 1;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.chart-count {
  font-size: 13px;
  color: var(--text-tertiary);
}

.chart-items {
  padding: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chart-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: var(--bg-card);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s ease;
}

.chart-item:hover {
  background: var(--primary-light);
}

.item-rank {
  font-size: 12px;
  color: var(--text-muted);
}

.item-code {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.item-score {
  font-size: 12px;
  color: var(--accent-gold);
  font-weight: 600;
}

/* 缺失列表 */
.missing-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.missing-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.missing-rank {
  width: 50px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-muted);
}

.missing-code {
  flex: 1;
  font-size: 15px;
  font-weight: 600;
  color: var(--primary-color);
}

/* 演员新片列表 */
.releases-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.release-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  transition: all 0.2s ease;
}

.release-item:hover {
  background: var(--bg-tertiary);
}

.release-item.in-library {
  opacity: 0.6;
  background: var(--bg-card);
}

.release-main {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.release-code {
  font-size: 15px;
  font-weight: 600;
  color: var(--primary-color);
  min-width: 100px;
}

.release-title {
  font-size: 14px;
  color: var(--text-primary);
  flex: 1;
}

.release-date {
  font-size: 13px;
  color: var(--text-muted);
}

.release-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.empty-hint {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 8px;
}

/* 空状态 */
.empty-tab {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-muted);
}

.empty-tab .el-icon {
  font-size: 56px;
  margin-bottom: 16px;
  color: var(--border-color);
}

/* 响应式 */
@media (max-width: 768px) {
  .actor-profile {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .profile-avatar {
    width: 120px;
    height: 120px;
  }

  .actor-stats {
    justify-content: center;
  }

  .actor-links {
    justify-content: center;
  }

  .follow-btn {
    width: 100%;
  }

  .movies-grid {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  }
}
</style>
