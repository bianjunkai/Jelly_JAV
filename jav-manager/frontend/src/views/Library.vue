<template>
  <div class="library-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">影片库</h1>
        <span class="movie-count">{{ total.toLocaleString() }} 部影片</span>
      </div>
      <div class="view-toggle">
        <button
          class="toggle-btn"
          :class="{ active: viewMode === 'grid' }"
          @click="viewMode = 'grid'"
        >
          <el-icon><Grid /></el-icon>
        </button>
        <button
          class="toggle-btn"
          :class="{ active: viewMode === 'list' }"
          @click="viewMode = 'list'"
        >
          <el-icon><List /></el-icon>
        </button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-section">
      <div class="filter-bar">
        <div class="search-box">
          <el-icon class="search-icon"><Search /></el-icon>
          <el-input
            v-model="searchKeyword"
            placeholder="搜索番号/演员..."
            clearable
            @input="handleSearch"
          />
        </div>

        <el-select v-model="filterScore" placeholder="评分" clearable class="filter-select" @change="handleSearch">
          <el-option label="全部评分" :value="0" class="score-all">全部评分</el-option>
          <el-option label="★ 4.5+ 分" :value="4.5" class="score-high">★ 4.5+ 分</el-option>
          <el-option label="★ 4.0+ 分" :value="4.0" class="score-mid">★ 4.0+ 分</el-option>
          <el-option label="★ 3.5+ 分" :value="3.5" class="score-normal">★ 3.5+ 分</el-option>
          <el-option label="★ 3.0+ 分" :value="3.0" class="score-low">★ 3.0+ 分</el-option>
        </el-select>

        <el-select v-model="filterList" placeholder="榜单" clearable class="filter-select" @change="handleSearch">
          <el-option label="全部榜单" :value="''" />
          <el-option v-for="chart in charts" :key="chart.name" :label="chart.display_name" :value="chart.name" />
        </el-select>

        <div class="sort-controls">
          <el-select v-model="sortBy" class="sort-select" @change="fetchMovies">
            <template #prefix>
              <el-icon><Sort /></el-icon>
            </template>
            <el-option label="添加时间" value="date_added" />
            <el-option label="发行时间" value="release_date" />
            <el-option label="加权评分" value="weighted_score" />
            <el-option label="JavDB评分" value="javdb_score" />
          </el-select>
          <button class="sort-order-btn" @click="toggleSortOrder" :title="sortOrder === 'desc' ? '降序' : '升序'">
            <el-icon>
              <Top v-if="sortOrder === 'desc'" />
              <Bottom v-else />
            </el-icon>
          </button>
        </div>
      </div>
    </div>

    <!-- 海报墙网格 -->
    <div v-if="viewMode === 'grid'" class="poster-wall">
      <div
        v-for="(movie, index) in movies"
        :key="movie.code"
        class="poster-card"
        :class="{ 'fade-in': true }"
        :style="{ animationDelay: `${(index % 24) * 30}ms` }"
        @click="showDetail(movie)"
      >
        <div class="poster-image">
          <img
            v-if="movie.poster_url"
            :src="movie.poster_url"
            :alt="movie.code"
            loading="lazy"
          />
          <div v-else class="poster-placeholder">
            <el-icon size="48"><Picture /></el-icon>
            <span>{{ movie.code }}</span>
          </div>

          <!-- 评分浮层 -->
          <div v-if="movie.javdb_score" class="score-overlay">
            <span class="score-star">★</span>
            <span class="score-value">{{ movie.javdb_score.toFixed(1) }}</span>
          </div>

          <!-- 榜单标签 -->
          <div v-if="movie.badges?.length" class="badges-overlay">
            <span v-for="badge in movie.badges.slice(0, 2)" :key="badge" class="poster-badge">
              {{ badge }}
            </span>
          </div>
        </div>

        <div class="poster-info">
          <h3 class="poster-code">{{ movie.code }}</h3>
          <p class="poster-title">{{ movie.title }}</p>
          <div class="poster-meta">
            <span v-if="movie.actors?.length" class="poster-actors">
              {{ movie.actors.slice(0, 2).join(', ') }}
            </span>
            <span v-if="movie.year" class="poster-year">{{ movie.year }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 列表视图 -->
    <div v-else class="list-view">
      <el-table :data="movies" stripe @row-click="showDetail" class="movie-table">
        <el-table-column label="封面" width="70">
          <template #default="{ row }">
            <div class="list-poster">
              <img v-if="row.poster_url" :src="row.poster_url" :alt="row.code" />
              <el-icon v-else><Picture /></el-icon>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="code" label="番号" width="110" sortable>
          <template #default="{ row }">
            <span class="list-code">{{ row.code }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="250" show-overflow-tooltip />
        <el-table-column label="演员" width="150">
          <template #default="{ row }">
            <span class="list-actors">{{ row.actors?.slice(0, 2).join(', ') }}</span>
          </template>
        </el-table-column>
        <el-table-column label="JavDB" width="90" sortable>
          <template #default="{ row }">
            <span v-if="row.javdb_score" class="score-badge" :class="getScoreClass(row.javdb_score)">
              ★ {{ row.javdb_score.toFixed(1) }}
            </span>
            <span v-else class="list-no-score">-</span>
          </template>
        </el-table-column>
        <el-table-column label="加权分" width="80" sortable prop="weighted_score">
          <template #default="{ row }">
            <span class="list-weighted">{{ row.weighted_score }}</span>
          </template>
        </el-table-column>
        <el-table-column label="榜单" width="100">
          <template #default="{ row }">
            <div v-if="row.badges?.length" class="list-badges">
              <span v-for="badge in row.badges" :key="badge" class="badge">{{ badge }}</span>
            </div>
            <span v-else class="list-no-badge">-</span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next, jumper"
        @current-change="fetchMovies"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Grid, List, Sort, Picture, Top, Bottom } from '@element-plus/icons-vue'
import { moviesApi, chartsApi } from '../api'

const movies = ref([])
const currentPage = ref(1)
const pageSize = ref(24)
const total = ref(0)
const viewMode = ref('grid')
const searchKeyword = ref('')
const filterScore = ref(0)
const filterList = ref('')
const sortBy = ref('date_added')
const sortOrder = ref('desc')
const charts = ref([])

const handleSearch = () => {
  currentPage.value = 1
  fetchMovies()
}

const toggleSortOrder = () => {
  sortOrder.value = sortOrder.value === 'desc' ? 'asc' : 'desc'
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
      sort: `${sortBy.value}_${sortOrder.value}`
    }

    if (searchKeyword.value) {
      params.search = searchKeyword.value
    }
    if (filterScore.value > 0) {
      params.min_score = filterScore.value
    }
    if (filterList.value) {
      params.list = filterList.value
    }

    const data = await moviesApi.list(params)
    movies.value = data.items
    total.value = data.total
  } catch (e) {
    ElMessage.error('获取影片列表失败')
  }
}

const fetchCharts = async () => {
  try {
    const data = await chartsApi.list()
    charts.value = data || []
  } catch (e) {
    console.error('Failed to fetch charts:', e)
  }
}

onMounted(() => {
  fetchMovies()
  fetchCharts()
})

// 监听筛选条件变化
watch([filterScore, filterList], () => {
  currentPage.value = 1
  fetchMovies()
})
</script>

<style scoped>
.library-view {
  max-width: 1600px;
  margin: 0 auto;
}

/* 页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: 16px;
}

.page-title {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.5px;
}

.movie-count {
  color: var(--text-muted);
  font-size: 15px;
  font-weight: 500;
}

.view-toggle {
  display: flex;
  gap: 8px;
  padding: 4px;
  background: var(--bg-secondary);
  border-radius: 12px;
}

.toggle-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.toggle-btn:hover {
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.5);
}

.toggle-btn.active {
  background: #fff;
  color: var(--primary-color);
  box-shadow: 0 2px 8px rgba(74, 74, 74, 0.08);
}

/* 筛选栏 */
.filter-section {
  margin-bottom: 28px;
}

.filter-bar {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}

.search-box {
  position: relative;
  flex: 1;
  min-width: 240px;
  max-width: 320px;
}

.search-box :deep(.el-input__wrapper) {
  padding-left: 40px;
}

.search-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  z-index: 1;
}

.filter-select,
.sort-select {
  width: 140px;
}

.filter-select :deep(.el-input__wrapper),
.sort-select :deep(.el-input__wrapper) {
  border-radius: 10px;
  background: var(--bg-secondary);
  box-shadow: none;
  border: 1px solid transparent;
  transition: all 0.2s ease;
}

.filter-select :deep(.el-input__wrapper:hover),
.sort-select :deep(.el-input__wrapper:hover) {
  border-color: var(--border-color);
}

.filter-select :deep(.el-input__wrapper.is-focus),
.sort-select :deep(.el-input__wrapper.is-focus) {
  border-color: var(--primary-color);
  background: var(--bg-card);
}

.sort-select :deep(.el-input__prefix) {
  color: var(--text-muted);
}

:deep(.el-select-dropdown__item.score-all) {
  color: var(--text-secondary);
}

:deep(.el-select-dropdown__item.score-high) {
  color: #E8A598;
}

:deep(.el-select-dropdown__item.score-mid) {
  color: #D4A574;
}

:deep(.el-select-dropdown__item.score-normal) {
  color: #888;
}

:deep(.el-select-dropdown__item.score-low) {
  color: #777;
}

/* 排序控制 */
.sort-controls {
  display: flex;
  gap: 8px;
  align-items: center;
}

.sort-order-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: var(--bg-secondary);
  color: var(--text-secondary);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sort-order-btn:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.sort-order-btn.active {
  background: var(--primary-color);
  color: #fff;
}

/* 海报墙 */
.poster-wall {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.poster-card {
  cursor: pointer;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: fadeIn 0.5s ease-out both;
}

.poster-card:hover {
  transform: translateY(-8px);
}

.poster-card:hover .poster-image {
  box-shadow: 0 16px 40px rgba(74, 74, 74, 0.18);
}

.poster-image {
  position: relative;
  aspect-ratio: 2/3;
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--bg-tertiary);
  box-shadow: var(--shadow-card);
  transition: box-shadow 0.3s ease;
}

.poster-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s ease;
}

.poster-card:hover .poster-image img {
  transform: scale(1.03);
}

.poster-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-muted);
  background: linear-gradient(135deg, var(--bg-tertiary), var(--bg-secondary));
}

.poster-placeholder span {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-tertiary);
}

.score-overlay {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  border-radius: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.score-star {
  color: var(--score-high);
  font-size: 12px;
}

.score-value {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
}

.badges-overlay {
  position: absolute;
  bottom: 10px;
  left: 10px;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.poster-badge {
  padding: 4px 10px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-secondary);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
}

.poster-info {
  padding: 12px 4px;
}

.poster-code {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
  letter-spacing: -0.3px;
}

.poster-title {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.4;
  height: 36px;
}

.poster-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-tertiary);
}

.poster-actors {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 120px;
}

.poster-year {
  padding: 2px 6px;
  background: var(--bg-tertiary);
  border-radius: 4px;
}

/* 列表视图 */
.list-view {
  margin-bottom: 32px;
}

.movie-table {
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.list-poster {
  width: 45px;
  height: 60px;
  border-radius: var(--radius-sm);
  background: var(--bg-tertiary);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
}

.list-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.list-code {
  font-weight: 600;
  color: var(--primary-color);
}

.list-actors {
  color: var(--text-secondary);
}

.list-weighted {
  font-weight: 600;
  color: var(--primary-color);
}

.list-badges {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.list-no-score,
.list-no-badge {
  color: var(--text-muted);
}

/* 分页 */
.pagination-container {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}

/* 动画 */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式 */
@media (max-width: 1400px) {
  .poster-wall {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 20px;
  }
}

@media (max-width: 1024px) {
  .poster-wall {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 16px;
  }

  .filter-bar {
    gap: 8px;
  }

  .filter-select,
  .sort-select {
    width: 120px;
  }
}

@media (max-width: 768px) {
  .page-title {
    font-size: 24px;
  }

  .poster-wall {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 12px;
  }

  .poster-info {
    padding: 8px 2px;
  }

  .poster-title {
    font-size: 12px;
    height: 32px;
  }

  .filter-select,
  .sort-select {
    width: 100px;
  }
}
</style>
