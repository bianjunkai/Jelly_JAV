<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    :title="movie ? `${movie.code} - ${movie.title}` : '影片详情'"
    width="720px"
    class="movie-detail-dialog"
    :close-on-click-modal="true"
    destroy-on-close
  >
    <div v-if="movie" class="movie-detail">
      <!-- 海报区 -->
      <div class="detail-poster">
        <div class="poster-wrapper">
          <img v-if="movie.poster_url" :src="movie.poster_url" :alt="movie.code" @error="handleImgError" />
          <div v-else class="poster-placeholder">
            <el-icon size="48"><Picture /></el-icon>
            <span>{{ movie.code }}</span>
          </div>
        </div>

        <!-- 快捷操作 -->
        <div class="poster-actions">
          <button class="poster-btn primary" @click="openInJellyfin" v-if="movie.jellyfin_id">
            <el-icon><VideoPlay /></el-icon>
            播放
          </button>
          <button class="poster-btn" @click="$emit('add-to-todo', movie)">
            <el-icon><Plus /></el-icon>
            待看
          </button>
        </div>
      </div>

      <!-- 内容区 -->
      <div class="detail-content">
        <!-- 标题区 -->
        <div class="content-header">
          <div v-if="movie.badges?.length" class="movie-badges">
            <span v-for="badge in movie.badges" :key="badge" class="detail-badge">{{ badge }}</span>
          </div>
        </div>

        <!-- 评分卡片 -->
        <div class="scores-card">
          <div class="score-box">
            <span class="score-label">JavDB</span>
            <div v-if="movie.javdb_score" class="score-display">
              <el-icon class="score-star"><StarFilled /></el-icon>
              <span class="score-value">{{ movie.javdb_score.toFixed(1) }}</span>
              <span class="score-max">/5</span>
            </div>
            <span v-else class="score-empty">暂无评分</span>
          </div>
          <div class="score-divider"></div>
          <div class="score-box">
            <span class="score-label">加权分</span>
            <span class="score-value weighted">{{ movie.weighted_score || '-' }}</span>
          </div>
        </div>

        <!-- 元信息 -->
        <div class="meta-grid">
          <div v-if="movie.year" class="meta-item">
            <el-icon><Calendar /></el-icon>
            <div class="meta-content">
              <span class="meta-label">年份</span>
              <span class="meta-value">{{ movie.year }}</span>
            </div>
          </div>
          <div v-if="movie.date_added" class="meta-item">
            <el-icon><Clock /></el-icon>
            <div class="meta-content">
              <span class="meta-label">添加时间</span>
              <span class="meta-value">{{ formatDate(movie.date_added) }}</span>
            </div>
          </div>
          <div v-if="movie.actors?.length" class="meta-item full-width">
            <el-icon><User /></el-icon>
            <div class="meta-content">
              <span class="meta-label">演员</span>
              <div class="actors-inline">
                <div
                  v-for="actor in movie.actors"
                  :key="actor"
                  class="actor-item"
                  @click="goToActor(actor)"
                >
                  <img
                    v-if="movie.actor_images && movie.actor_images[actor]"
                    :src="movie.actor_images[actor]"
                    :alt="actor"
                    class="actor-avatar"
                    @error="handleActorImgError($event, actor)"
                  />
                  <div v-else class="actor-avatar-placeholder">
                    {{ actor.charAt(0) }}
                  </div>
                  <span class="actor-name">{{ actor }}</span>
                </div>
              </div>
            </div>
          </div>
          <div v-if="movie.jellyfin_path" class="meta-item full-width">
            <el-icon><Folder /></el-icon>
            <div class="meta-content">
              <span class="meta-label">文件路径</span>
              <span class="meta-value path">{{ movie.jellyfin_path }}</span>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="detail-actions">
          <el-button @click="$emit('refresh', movie.code)" :loading="refreshing">
            <el-icon><Refresh /></el-icon>
            刷新评分
          </el-button>
          <el-button @click="$emit('update:modelValue', false)">关闭</el-button>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  Picture,
  VideoPlay,
  Plus,
  StarFilled,
  Calendar,
  Clock,
  Folder,
  User,
  Refresh
} from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: Boolean,
  movie: Object
})

defineEmits(['update:modelValue', 'refresh', 'add-to-todo'])

const router = useRouter()
const refreshing = ref(false)

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

const handleImgError = (e) => {
  e.target.style.display = 'none'
}

const handleActorImgError = (e, actorName) => {
  // 替换为占位符
  const parent = e.target.parentElement
  if (parent) {
    parent.innerHTML = `<div class="actor-avatar-placeholder">${actorName.charAt(0)}</div>`
  }
}

const goToActor = (actor) => {
  router.push(`/actors/${encodeURIComponent(actor)}`)
}

const openInJellyfin = () => {
  if (props.movie?.jellyfin_id) {
    window.open(`/jellyfin/web/#/details?id=${props.movie.jellyfin_id}`, '_blank')
  }
}
</script>

<style scoped>
.movie-detail {
  display: flex;
  gap: 28px;
  padding: 4px;
}

/* 海报区 */
.detail-poster {
  flex-shrink: 0;
  width: 240px;
}

.poster-wrapper {
  aspect-ratio: 2/3;
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--bg-tertiary);
  box-shadow: var(--shadow-card);
  margin-bottom: 16px;
}

.poster-wrapper img {
  width: 100%;
  height: 100%;
  object-fit: cover;
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
  font-size: 14px;
  font-weight: 500;
}

.poster-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.poster-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  background: var(--bg-secondary);
  border: none;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.poster-btn:hover {
  background: var(--bg-tertiary);
}

.poster-btn.primary {
  background: var(--primary-gradient);
  color: #fff;
}

.poster-btn.primary:hover {
  box-shadow: 0 4px 12px rgba(232, 165, 152, 0.35);
}

/* 内容区 */
.detail-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.content-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.movie-badges {
  display: flex;
  gap: 6px;
}

.detail-badge {
  padding: 4px 10px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

/* 评分卡片 */
.scores-card {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 20px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  margin-bottom: 20px;
}

.score-box {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.score-label {
  font-size: 12px;
  color: var(--text-tertiary);
  font-weight: 500;
}

.score-display {
  display: flex;
  align-items: center;
  gap: 6px;
}

.score-star {
  color: var(--accent-gold);
}

.score-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
}

.score-value.weighted {
  color: var(--primary-color);
}

.score-max {
  font-size: 14px;
  color: var(--text-muted);
}

.score-empty {
  font-size: 16px;
  color: var(--text-muted);
}

.score-divider {
  width: 1px;
  height: 40px;
  background: var(--border-color);
}

/* 元信息网格 */
.meta-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.meta-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.meta-item.full-width {
  grid-column: 1 / -1;
}

.meta-item .el-icon {
  color: var(--text-muted);
  margin-top: 2px;
}

.meta-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.meta-label {
  font-size: 12px;
  color: var(--text-tertiary);
}

.meta-value {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.meta-value.path {
  font-size: 12px;
  word-break: break-all;
  color: var(--text-secondary);
}

.actors-inline {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.actor-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.actor-item:hover {
  transform: translateY(-2px);
}

.actor-item:hover .actor-name {
  color: var(--primary-color);
}

.actor-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
  background: var(--bg-tertiary);
}

.actor-avatar-placeholder {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary-color), #E8A598);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 600;
  color: #fff;
}

.actor-name {
  font-size: 11px;
  color: var(--text-secondary);
  max-width: 56px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: center;
}

/* 操作按钮 */
.detail-actions {
  display: flex;
  gap: 12px;
  margin-top: auto;
  padding-top: 20px;
}
</style>

<style>
/* 对话框样式覆盖 */
.movie-detail-dialog .el-dialog {
  border-radius: var(--radius-xl);
  overflow: hidden;
}

.movie-detail-dialog .el-dialog__header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-light);
}

.movie-detail-dialog .el-dialog__title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.movie-detail-dialog .el-dialog__body {
  padding: 24px;
}

.movie-detail-dialog .el-dialog__headerbtn:hover .el-dialog__close {
  color: var(--primary-color);
}

/* 响应式 */
@media (max-width: 768px) {
  .movie-detail {
    flex-direction: column;
    align-items: center;
  }

  .detail-poster {
    width: 200px;
  }

  .poster-actions {
    flex-direction: row;
  }

  .meta-grid {
    grid-template-columns: 1fr;
  }

  .scores-card {
    flex-direction: column;
    gap: 16px;
  }

  .score-divider {
    width: 100%;
    height: 1px;
  }
}
</style>
