<template>
  <div class="actor-list-view">
    <div class="page-header">
      <h1 class="page-title">演员列表</h1>
      <span class="actor-count">{{ actors.length }} 人</span>
    </div>

    <!-- 筛选 -->
    <div class="filter-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索演员..."
        clearable
        style="width: 240px"
        @input="fetchActors"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>

      <el-radio-group v-model="filterFollowed" @change="fetchActors">
        <el-radio-button label="all">全部</el-radio-button>
        <el-radio-button label="followed">关注</el-radio-button>
        <el-radio-button label="unfollowed">未关注</el-radio-button>
      </el-radio-group>

      <el-select v-model="sortBy" style="width: 140px" @change="fetchActors">
        <el-option label="影片数" value="movie_count_desc" />
        <el-option label="姓名" value="name" />
        <el-option label="平均评分" value="avg_score_desc" />
      </el-select>
    </div>

    <div v-loading="loading" class="actor-grid">
      <el-card v-for="actor in actors" :key="actor.id" class="actor-card" shadow="hover">
        <div class="actor-avatar">
          <img v-if="actor.photo_url" :src="actor.photo_url" :alt="actor.name" />
          <el-icon v-else size="32"><User /></el-icon>
        </div>
        <div class="actor-info">
          <div class="actor-name">
            <span v-if="actor.is_followed" class="followed-badge">★</span>
            {{ actor.name }}
          </div>
          <div class="actor-stats">
            <span>{{ actor.movie_count }} 部</span>
            <span v-if="actor.avg_score">★ {{ actor.avg_score.toFixed(1) }}</span>
          </div>
        </div>
        <div class="actor-actions">
          <el-button
            :type="actor.is_followed ? 'default' : 'primary'"
            size="small"
            @click="toggleFollow(actor)"
          >
            {{ actor.is_followed ? '取消关注' : '关注' }}
          </el-button>
          <el-button size="small" @click="goToDetail(actor)">
            查看
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 空状态 -->
    <div v-if="!loading && actors.length === 0" class="empty-state">
      <el-icon size="48"><User /></el-icon>
      <p>暂无演员</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { actorsApi } from '../api'

const router = useRouter()
const loading = ref(false)
const actors = ref([])
const searchKeyword = ref('')
const filterFollowed = ref('all')
const sortBy = ref('movie_count_desc')

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

onMounted(() => {
  fetchActors()
})
</script>

<style scoped>
.actor-list-view {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
}

.actor-count {
  color: #666;
  font-size: 14px;
}

.filter-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.actor-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.actor-card {
  background: #1a1a1a;
  text-align: center;
}

.actor-avatar {
  width: 80px;
  height: 80px;
  margin: 0 auto 12px;
  border-radius: 50%;
  background: #2a2a2a;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.actor-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.actor-name {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.followed-badge {
  color: #e50914;
  margin-right: 4px;
}

.actor-stats {
  display: flex;
  justify-content: center;
  gap: 12px;
  font-size: 13px;
  color: #666;
  margin-bottom: 12px;
}

.actor-actions {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #666;
}

.empty-state .el-icon {
  font-size: 48px;
  margin-bottom: 16px;
}
</style>
