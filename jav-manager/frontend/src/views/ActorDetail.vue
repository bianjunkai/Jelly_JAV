<template>
  <div class="actor-detail-view" v-if="actor">
    <div class="page-header">
      <el-button text @click="$router.back()">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
    </div>

    <el-card class="actor-profile">
      <div class="profile-content">
        <div class="profile-avatar">
          <img v-if="actor.photo_url" :src="actor.photo_url" :alt="actor.name" />
          <el-icon v-else size="64"><User /></el-icon>
        </div>
        <div class="profile-info">
          <h1 class="actor-name">
            <span v-if="actor.is_followed" class="followed-star">★</span>
            {{ actor.name }}
          </h1>
          <div class="actor-stats">
            <div class="stat-item">
              <span class="stat-value">{{ actor.movie_count }}</span>
              <span class="stat-label">影片数</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ actor.avg_score?.toFixed(1) || '-' }}</span>
              <span class="stat-label">平均评分</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ actor.is_followed ? '已关注' : '未关注' }}</span>
              <span class="stat-label">关注状态</span>
            </div>
          </div>
          <div class="actor-links">
            <el-button v-if="actor.javdb_id" size="small" @click="openJavDB">
              JavDB
            </el-button>
            <el-button v-if="actor.javbus_id" size="small" @click="openJavBus">
              JAVBus
            </el-button>
          </div>
          <div class="actor-actions">
            <el-button :type="actor.is_followed ? 'default' : 'primary'" @click="toggleFollow">
              {{ actor.is_followed ? '取消关注' : '关注' }}
            </el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 标签页 -->
    <el-tabs v-model="activeTab" class="actor-tabs">
      <!-- 影片列表 -->
      <el-tab-pane label="影片" name="movies">
        <div class="card-grid">
          <div v-for="movie in actor.movies" :key="movie.code" class="card" @click="showMovieDetail(movie)">
            <div class="card-poster">
              <img v-if="movie.poster_url" :src="movie.poster_url" :alt="movie.code" />
              <el-icon v-else size="40"><Picture /></el-icon>
            </div>
            <div class="card-info">
              <div class="card-score">
                <span v-if="movie.javdb_score" class="score-badge" :class="getScoreClass(movie.javdb_score)">
                  ★ {{ movie.javdb_score.toFixed(1) }}
                </span>
              </div>
              <div class="card-code">{{ movie.code }}</div>
              <div class="card-title">{{ movie.title }}</div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 榜单成绩 -->
      <el-tab-pane label="榜单成绩" name="charts">
        <div v-if="actor.chart_appearances?.length" class="chart-appearances">
          <div v-for="(items, chartName) in groupedChartAppearances" :key="chartName" class="chart-group">
            <div class="chart-group-header">{{ chartName }}: {{ items.length }} 部</div>
            <div class="chart-items">
              <div v-for="item in items" :key="item.code" class="chart-item" @click="goToChart(item, chartName)">
                <span class="item-rank">#{{ item.rank }}</span>
                <span class="item-code">{{ item.code }}</span>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="empty-tab">暂无榜单记录</div>
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
            <el-button size="small" type="primary" @click="addToTodo(item)">加入待看</el-button>
          </div>
        </div>
        <div v-else class="empty-tab">暂无缺失记录</div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { actorsApi, todosApi } from '../api'

const route = useRoute()
const actor = ref(null)
const activeTab = ref('movies')

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

const openJavDB = () => {
  window.open(`https://javdb.com/actors/${actor.value.javdb_id}`)
}

const openJavBus = () => {
  window.open(`https://javbus.com/actor/${actor.value.javbus_id}`)
}

onMounted(() => {
  fetchActor()
})
</script>

<style scoped>
.actor-detail-view {
  max-width: 1000px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 16px;
}

.actor-profile {
  background: #1a1a1a;
  margin-bottom: 24px;
}

.profile-content {
  display: flex;
  gap: 32px;
}

.profile-avatar {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: #2a2a2a;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
}

.profile-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.actor-name {
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 16px;
}

.followed-star {
  color: #e50914;
}

.actor-stats {
  display: flex;
  gap: 32px;
  margin-bottom: 16px;
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
}

.stat-label {
  font-size: 12px;
  color: #666;
}

.actor-links {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.actor-tabs {
  background: #1a1a1a;
  border-radius: 8px;
  padding: 16px;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 16px;
}

.card {
  background: #242424;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s;
}

.card:hover {
  transform: translateY(-4px);
}

.card-poster {
  aspect-ratio: 2/3;
  background: #333;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.card-info {
  padding: 8px;
}

.card-score {
  margin-bottom: 4px;
}

.card-code {
  font-size: 13px;
  font-weight: 600;
  color: #e50914;
}

.card-title {
  font-size: 12px;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chart-group {
  margin-bottom: 16px;
}

.chart-group-header {
  font-weight: 600;
  padding: 8px 0;
  border-bottom: 1px solid #333;
}

.chart-items {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 0;
}

.chart-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  background: #242424;
  border-radius: 4px;
  cursor: pointer;
}

.chart-item:hover {
  background: #333;
}

.item-rank {
  color: #666;
  font-size: 12px;
}

.item-code {
  font-weight: 600;
}

.missing-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.missing-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: #242424;
  border-radius: 4px;
}

.missing-rank {
  color: #666;
  width: 40px;
}

.missing-code {
  flex: 1;
  font-weight: 600;
}

.empty-tab {
  text-align: center;
  padding: 40px;
  color: #666;
}
</style>
