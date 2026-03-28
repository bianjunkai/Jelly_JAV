<template>
  <div class="app-container">
    <!-- 顶部导航 -->
    <header class="nav-header">
      <div class="nav-left">
        <router-link to="/" class="logo">
          <span class="logo-icon">🎬</span>
          <span class="logo-text">JAV Manager</span>
        </router-link>
      </div>
      <nav class="nav-menu">
        <router-link to="/" class="nav-item">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </router-link>
        <router-link to="/library" class="nav-item">
          <el-icon><Film /></el-icon>
          <span>影片库</span>
        </router-link>
        <router-link to="/charts" class="nav-item">
          <el-icon><Trophy /></el-icon>
          <span>榜单</span>
        </router-link>
        <router-link to="/discover" class="nav-item">
          <el-icon><Compass /></el-icon>
          <span>发现</span>
        </router-link>
        <router-link to="/todo" class="nav-item">
          <el-icon><List /></el-icon>
          <span>待看</span>
        </router-link>
        <router-link to="/actors" class="nav-item">
          <el-icon><User /></el-icon>
          <span>演员</span>
        </router-link>
        <router-link to="/settings" class="nav-item">
          <el-icon><Setting /></el-icon>
          <span>设置</span>
        </router-link>
      </nav>
      <div class="nav-right">
        <el-button type="primary" size="default" @click="syncJellyfin" :loading="syncing">
          <el-icon><Refresh /></el-icon>
          同步
        </el-button>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- 影片详情弹窗 -->
    <MovieDetailModal
      v-model="showMovieDetail"
      :movie="currentMovie"
      @refresh="refreshMovie"
      @add-to-todo="addToTodo"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import MovieDetailModal from './components/MovieDetailModal.vue'
import { moviesApi, tasksApi, todosApi } from './api'

const syncing = ref(false)
const showMovieDetail = ref(false)
const currentMovie = ref(null)

const syncJellyfin = async () => {
  try {
    syncing.value = true
    await tasksApi.sync()
    ElMessage.success('同步任务已启动')
  } catch (e) {
    ElMessage.error('同步失败')
  } finally {
    syncing.value = false
  }
}

const refreshMovie = async (code) => {
  try {
    await moviesApi.refresh(code)
    ElMessage.success('评分已刷新')
  } catch (e) {
    ElMessage.error('刷新失败')
  }
}

const addToTodo = async (movie) => {
  try {
    await todosApi.add({
      code: movie.code,
      title: movie.title,
      actors: Array.isArray(movie.actors) ? movie.actors.join(',') : movie.actors || '',
      source: 'manual'
    })
    ElMessage.success('已加入待看清单')
  } catch (e) {
    ElMessage.error('添加失败')
  }
}

onMounted(() => {
  // 全局事件监听，用于打开影片详情
  window.showMovieDetail = (movie) => {
    currentMovie.value = movie
    showMovieDetail.value = true
  }
})
</script>

<style>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 导航栏 */
.nav-header {
  background: #1a1a1a;
  border-bottom: 1px solid #333;
  padding: 0 24px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-left .logo {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
}

.logo-icon {
  font-size: 24px;
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  color: #e50914;
}

.nav-menu {
  display: flex;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  border-radius: 8px;
  color: #a0a0a0;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.nav-item:hover {
  background: #2a2a2a;
  color: #fff;
}

.nav-item.router-link-active {
  background: linear-gradient(135deg, #e50914, #f40612);
  color: #fff;
}

.nav-right {
  display: flex;
  gap: 12px;
}

/* 主内容 */
.main-content {
  flex: 1;
  padding: 24px;
  max-width: 1600px;
  margin: 0 auto;
  width: 100%;
}

/* 响应式 */
@media (max-width: 768px) {
  .nav-item span {
    display: none;
  }

  .nav-item {
    padding: 10px 12px;
  }

  .main-content {
    padding: 16px;
  }
}

/* 路由动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
