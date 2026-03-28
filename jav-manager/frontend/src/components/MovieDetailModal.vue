<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    :title="movie?.code || '影片详情'"
    width="700px"
    class="movie-detail-dialog"
    :close-on-click-modal="true"
  >
    <div v-if="movie" class="movie-detail">
      <div class="detail-poster">
        <img v-if="movie.poster_url" :src="movie.poster_url" :alt="movie.code" @error="handleImgError" />
        <div v-else class="poster-placeholder">
          <el-icon size="64"><Picture /></el-icon>
        </div>
      </div>

      <div class="detail-content">
        <div class="movie-header">
          <h2 class="movie-code">{{ movie.code }}</h2>
          <div v-if="movie.badges?.length" class="movie-badges">
            <span v-for="badge in movie.badges" :key="badge" class="badge">{{ badge }}</span>
          </div>
        </div>

        <h3 class="movie-title">{{ movie.title }}</h3>

        <div class="movie-meta">
          <div v-if="movie.year" class="meta-item">
            <span class="meta-label">📅 年份</span>
            <span class="meta-value">{{ movie.year }}</span>
          </div>
          <div v-if="movie.date_added" class="meta-item">
            <span class="meta-label">📁 添加时间</span>
            <span class="meta-value">{{ formatDate(movie.date_added) }}</span>
          </div>
          <div v-if="movie.jellyfin_path" class="meta-item">
            <span class="meta-label">📂 路径</span>
            <span class="meta-value path">{{ movie.jellyfin_path }}</span>
          </div>
        </div>

        <div v-if="movie.actors?.length" class="movie-actors">
          <span class="meta-label">👤 演员</span>
          <div class="actors-list">
            <span
              v-for="actor in movie.actors"
              :key="actor"
              class="actor-tag"
              @click="goToActor(actor)"
            >
              {{ actor }}
            </span>
          </div>
        </div>

        <div class="movie-scores">
          <div class="score-item">
            <span class="score-label">⭐ JavDB</span>
            <span v-if="movie.javdb_score" class="score-badge" :class="getScoreClass(movie.javdb_score)">
              {{ movie.javdb_score.toFixed(1) }}/5
            </span>
            <span v-else class="score-none">-</span>
          </div>
          <div class="score-item">
            <span class="score-label">📊 加权分</span>
            <span class="score-value weighted">{{ movie.weighted_score }}</span>
          </div>
        </div>

        <div class="movie-actions">
          <el-button type="primary" @click="openInJellyfin" v-if="movie.jellyfin_id">
            <el-icon><VideoPlay /></el-icon>
            在 Jellyfin 中打开
          </el-button>
          <el-button @click="$emit('add-to-todo', movie)">
            <el-icon><Plus /></el-icon>
            加入待看清单
          </el-button>
          <el-button @click="$emit('refresh', movie.code)" :loading="refreshing">
            <el-icon><Refresh /></el-icon>
            刷新评分
          </el-button>
        </div>
      </div>
    </div>

    <template #footer v-if="movie">
      <el-button @click="$emit('update:modelValue', false)">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

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

const getScoreClass = (score) => {
  if (score >= 4.5) return 'score-high'
  if (score >= 4.0) return 'score-mid'
  return 'score-low'
}

const handleImgError = (e) => {
  e.target.style.display = 'none'
  e.target.parentElement.querySelector('.poster-placeholder')?.style.display='flex'
}

const goToActor = (actor) => {
  router.push(`/actors/${encodeURIComponent(actor)}`)
}

const openInJellyfin = () => {
  // TODO: 打开 Jellyfin
  console.log('Open in Jellyfin:', props.movie?.jellyfin_id)
}
</script>

<style scoped>
.movie-detail {
  display: flex;
  gap: 24px;
  padding: 8px 0;
}

.detail-poster {
  width: 220px;
  height: 330px;
  background: #242424;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.detail-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.poster-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
}

.detail-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.movie-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 4px;
}

.movie-code {
  font-size: 28px;
  font-weight: 700;
  color: #e50914;
}

.movie-badges {
  display: flex;
  gap: 4px;
}

.movie-badges .badge {
  font-size: 14px;
}

.movie-title {
  font-size: 16px;
  font-weight: normal;
  color: #a0a0a0;
  margin-bottom: 16px;
}

.movie-meta {
  margin-bottom: 16px;
}

.meta-item {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  align-items: flex-start;
}

.meta-label {
  color: #666;
  font-size: 13px;
  min-width: 70px;
}

.meta-value {
  color: #fff;
  font-size: 13px;
}

.meta-value.path {
  font-size: 12px;
  word-break: break-all;
  color: #888;
}

.movie-actors {
  margin-bottom: 16px;
}

.actors-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.actor-tag {
  padding: 4px 10px;
  background: #242424;
  border-radius: 16px;
  font-size: 13px;
  color: #fff;
  cursor: pointer;
  transition: all 0.2s;
}

.actor-tag:hover {
  background: #e50914;
  transform: scale(1.05);
}

.movie-scores {
  display: flex;
  gap: 32px;
  margin-bottom: 20px;
  padding: 16px;
  background: #242424;
  border-radius: 8px;
}

.score-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.score-label {
  font-size: 12px;
  color: #666;
}

.score-value {
  font-size: 24px;
  font-weight: 700;
}

.score-value.weighted {
  color: #e50914;
}

.score-none {
  font-size: 18px;
  color: #666;
}

.movie-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: auto;
}

.movie-actions .el-button {
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>

<style>
.movie-detail-dialog .el-dialog {
  background: #1a1a1a !important;
}

.movie-detail-dialog .el-dialog__header {
  border-bottom: 1px solid #333;
  padding: 16px 20px;
}

.movie-detail-dialog .el-dialog__title {
  color: #fff;
  font-size: 18px;
  font-weight: 600;
}

.movie-detail-dialog .el-dialog__body {
  padding: 20px;
}

.movie-detail-dialog .el-dialog__footer {
  border-top: 1px solid #333;
  padding: 16px 20px;
}
</style>
