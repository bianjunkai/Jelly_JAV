<template>
  <div class="actor-list-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">演员列表</h1>
        <span class="actor-count">{{ actors.length }} 位演员</span>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-section">
      <div class="search-box">
        <el-icon class="search-icon"><Search /></el-icon>
        <el-input
          v-model="searchKeyword"
          placeholder="搜索演员姓名..."
          clearable
          @input="fetchActors"
        />
      </div>

      <el-radio-group v-model="filterFollowed" @change="fetchActors" class="filter-tabs">
        <el-radio-button label="all">全部</el-radio-button>
        <el-radio-button label="followed">
          <el-icon><StarFilled /></el-icon>
          关注
        </el-radio-button>
        <el-radio-button label="unfollowed">未关注</el-radio-button>
      </el-radio-group>

      <el-select v-model="sortBy" class="sort-select" @change="fetchActors">
        <template #prefix>
          <el-icon><Sort /></el-icon>
        </template>
        <el-option label="影片数" value="movie_count_desc" />
        <el-option label="姓名" value="name" />
        <el-option label="平均评分" value="avg_score_desc" />
      </el-select>
    </div>

    <!-- 演员网格 -->
    <div v-loading="loading" class="actor-grid">
      <div
        v-for="actor in actors"
        :key="actor.id"
        class="actor-card"
        @click="goToDetail(actor)"
      >
        <div class="actor-avatar">
          <img
            v-if="actor.photo_url && !imageErrors.has(actor.name)"
            :src="actor.photo_url"
            :alt="actor.name"
            @error="handleImageError(actor.name)"
          />
          <div v-else class="avatar-placeholder">
            <span class="avatar-initial">{{ actor.name.charAt(0) }}</span>
          </div>
          <div v-if="actor.is_followed" class="followed-indicator">
            <el-icon><StarFilled /></el-icon>
          </div>
        </div>

        <div class="actor-info">
          <h3 class="actor-name">{{ actor.name }}</h3>
          <div class="actor-stats">
            <span class="stat">
              <el-icon><Film /></el-icon>
              {{ actor.movie_count }} 部
            </span>
            <span v-if="actor.avg_score" class="stat score">
              <el-icon><Star /></el-icon>
              {{ actor.avg_score.toFixed(1) }}
            </span>
          </div>
        </div>

        <div class="actor-actions" @click.stop>
          <button
            class="action-btn"
            :class="{ following: actor.is_followed }"
            @click="toggleFollow(actor)"
          >
            <el-icon v-if="actor.is_followed"><Check /></el-icon>
            <el-icon v-else><Plus /></el-icon>
            {{ actor.is_followed ? '已关注' : '关注' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!loading && actors.length === 0" class="empty-state">
      <div class="empty-icon">
        <el-icon size="64"><User /></el-icon>
      </div>
      <p class="empty-title">暂无演员</p>
      <p class="empty-desc">请先同步影片库数据</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Search,
  StarFilled,
  Sort,
  Film,
  Star,
  Check,
  Plus,
  User
} from '@element-plus/icons-vue'
import { actorsApi } from '../api'

const router = useRouter()
const loading = ref(false)
const actors = ref([])
const searchKeyword = ref('')
const filterFollowed = ref('all')
const sortBy = ref('movie_count_desc')
const imageErrors = ref(new Set())

const fetchActors = async () => {
  loading.value = true
  try {
    const params = { sort: sortBy.value }
    if (filterFollowed.value === 'followed') params.followed_only = 'true'
    if (searchKeyword.value) params.search = searchKeyword.value

    actors.value = await actorsApi.list(params)
  } catch (e) {
    ElMessage.error('获取演员列表失败')
  } finally {
    loading.value = false
  }
}

const toggleFollow = async (actor) => {
  try {
    await actorsApi.follow(actor.id)
    actor.is_followed = !actor.is_followed
    ElMessage.success(actor.is_followed ? '已关注' : '已取消关注')
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const goToDetail = (actor) => {
  router.push(`/actors/${encodeURIComponent(actor.name)}`)
}

const handleImageError = (actorName) => {
  imageErrors.value.add(actorName)
}

onMounted(() => {
  fetchActors()
})
</script>

<style scoped>
.actor-list-view {
  max-width: 1400px;
  margin: 0 auto;
}

/* 页面头部 */
.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 28px;
}

.page-title {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.5px;
}

.actor-count {
  color: var(--text-muted);
  font-size: 15px;
  font-weight: 500;
}

/* 筛选栏 */
.filter-section {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 28px;
  flex-wrap: wrap;
}

.search-box {
  position: relative;
  width: 280px;
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

.filter-tabs :deep(.el-radio-button__inner) {
  display: flex;
  align-items: center;
  gap: 6px;
}

.sort-select {
  width: 140px;
  margin-left: auto;
}

.sort-select :deep(.el-input__prefix) {
  color: var(--text-muted);
}

/* 演员网格 */
.actor-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 20px;
}

.actor-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}

.actor-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-hover);
}

.actor-avatar {
  position: relative;
  width: 100%;
  aspect-ratio: 1;
  overflow: hidden;
  background: linear-gradient(135deg, var(--bg-tertiary), var(--bg-secondary));
}

.actor-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s ease;
}

.actor-card:hover .actor-avatar img {
  transform: scale(1.05);
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
  opacity: 0.5;
}

.followed-indicator {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 32px;
  height: 32px;
  background: var(--primary-gradient);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 4px 12px rgba(232, 165, 152, 0.4);
}

.actor-info {
  padding: 16px;
  text-align: center;
}

.actor-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.actor-stats {
  display: flex;
  justify-content: center;
  gap: 16px;
}

.stat {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--text-tertiary);
}

.stat .el-icon {
  font-size: 14px;
}

.stat.score {
  color: var(--accent-gold);
  font-weight: 600;
}

.actor-actions {
  padding: 0 16px 16px;
}

.action-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px;
  background: var(--bg-secondary);
  border: none;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.action-btn.following {
  background: var(--primary-light);
  color: var(--primary-dark);
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 80px 20px;
}

.empty-icon {
  width: 120px;
  height: 120px;
  margin: 0 auto 24px;
  background: var(--bg-secondary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.empty-desc {
  font-size: 14px;
  color: var(--text-muted);
}

/* 响应式 */
@media (max-width: 1024px) {
  .actor-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  }
}

@media (max-width: 768px) {
  .page-title {
    font-size: 24px;
  }

  .search-box {
    width: 100%;
  }

  .sort-select {
    margin-left: 0;
    width: 100%;
  }

  .actor-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 12px;
  }

  .actor-info {
    padding: 12px;
  }

  .actor-name {
    font-size: 14px;
  }
}
</style>
