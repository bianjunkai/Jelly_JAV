<template>
  <div class="library-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div>
        <h1 class="page-title">影片库</h1>
        <span class="movie-count">{{ total }} 部影片</span>
      </div>
      <div class="header-actions">
        <el-select v-model="viewMode" size="default" style="width: 120px">
          <el-option label="网格视图" value="grid" />
          <el-option label="列表视图" value="list" />
        </el-select>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索番号/标题..."
        clearable
        style="width: 240px"
        @input="handleSearch"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>

      <el-select v-model="filterActor" placeholder="演员" clearable style="width: 160px">
        <el-option v-for="actor in topActors" :key="actor" :label="actor" :value="actor" />
      </el-select>

      <el-select v-model="filterScore" placeholder="评分" clearable style="width: 140px">
        <el-option label="≥ 4.5" :value="4.5" />
        <el-option label="≥ 4.0" :value="4.0" />
        <el-option label="≥ 3.5" :value="3.5" />
        <el-option label="≥ 3.0" :value="3.0" />
      </el-select>

      <el-select v-model="filterList" placeholder="榜单" clearable style="width: 160px">
        <el-option label="JavDB TOP250" value="javdb250" />
        <el-option label="JavLibrary TOP500" value="javlib500" />
      </el-select>

      <el-select v-model="sortBy" style="width: 160px" @change="fetchMovies">
        <el-option label="最近添加" value="date_added_desc" />
        <el-option label="最早添加" value="date_added_asc" />
        <el-option label="评分最高" value="weighted_desc" />
        <el-option label="JavDB评分" value="javdb_desc" />
      </el-select>
    </div>

    <!-- 影片网格 -->
    <div v-if="viewMode === 'grid'" class="card-grid">
      <div v-for="movie in movies" :key="movie.code" class="card" @click="showDetail(movie)">
        <div class="card-poster">
          <img v-if="movie.poster_url" :src="movie.poster_url" :alt="movie.code" />
          <el-icon v-else size="40"><Picture /></el-icon>
        </div>
        <div class="card-info">
          <div class="card-score">
            <span v-if="movie.javdb_score" class="score-badge" :class="getScoreClass(movie.javdb_score)">
              ★ {{ movie.javdb_score.toFixed(1) }}
            </span>
            <span v-if="movie.badges?.length" class="badges">
              <span v-for="badge in movie.badges" :key="badge" class="badge">{{ badge }}</span>
            </span>
          </div>
          <div class="card-code">{{ movie.code }}</div>
          <div class="card-title">{{ movie.title }}</div>
          <div class="card-meta">
            <span v-if="movie.actors?.length">{{ movie.actors.slice(0, 2).join(', ') }}</span>
            <span>{{ movie.year }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 影片列表 -->
    <el-table v-else :data="movies" stripe @row-click="showDetail" class="movie-table">
      <el-table-column label="封面" width="80">
        <template #default="{ row }">
          <div class="table-poster">
            <img v-if="row.poster_url" :src="row.poster_url" :alt="row.code" />
            <el-icon v-else><Picture /></el-icon>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="code" label="番号" width="120" sortable />
      <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
      <el-table-column label="演员" width="150">
        <template #default="{ row }">
          {{ row.actors?.slice(0, 2).join(', ') }}
        </template>
      </el-table-column>
      <el-table-column label="JavDB" width="100" sortable>
        <template #default="{ row }">
          <span v-if="row.javdb_score" class="score-badge" :class="getScoreClass(row.javdb_score)">
            ★ {{ row.javdb_score.toFixed(1) }}
          </span>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="加权分" width="100" sortable prop="weighted_score" />
      <el-table-column label="榜单" width="80">
        <template #default="{ row }">
          <span v-if="row.badges?.length" class="badges">
            <span v-for="badge in row.badges" :key="badge" class="badge">{{ badge }}</span>
          </span>
          <span v-else>-</span>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="fetchMovies"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { moviesApi } from '../api'

const movies = ref([])
const currentPage = ref(1)
const pageSize = ref(24)
const total = ref(0)
const viewMode = ref('grid')
const searchKeyword = ref('')
const filterActor = ref('')
const filterScore = ref('')
const filterList = ref('')
const sortBy = ref('date_added_desc')
const topActors = ref([])

const handleSearch = () => {
  currentPage.value = 1
  fetchMovies()
}

const getScoreClass = (score) => {
  if (score >= 4.5) return 'score-high'
  if (score >= 4.0) return 'score-mid'
  return 'score-low'
}

const showDetail = (movie) => {
  window.showMovieDetail(movie)
}

const fetchMovies = async () => {
  try {
    const params = {
      page: currentPage.value,
      per_page: pageSize.value,
      sort: sortBy.value
    }

    if (searchKeyword.value) {
      // 简单实现，实际应该后端支持搜索
      params.actor = searchKeyword.value
    }
    if (filterActor.value) params.actor = filterActor.value
    if (filterScore.value) params.min_score = filterScore.value
    if (filterList.value) params.list = filterList.value

    const data = await moviesApi.list(params)
    movies.value = data.items
    total.value = data.total
  } catch (e) {
    ElMessage.error('获取影片列表失败')
  }
}

onMounted(() => {
  fetchMovies()
})
</script>

<style scoped>
.library-view {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin-right: 12px;
}

.movie-count {
  color: #666;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.card-score {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.badges {
  display: flex;
  gap: 4px;
}

.table-poster {
  width: 45px;
  height: 60px;
  background: #2a2a2a;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.table-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.movie-table {
  background: #1a1a1a;
  border-radius: 8px;
}

.movie-table :deep(.el-table__row) {
  cursor: pointer;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
</style>
