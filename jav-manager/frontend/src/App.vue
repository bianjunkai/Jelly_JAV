<template>
  <div class="app-container">
    <!-- 顶部导航 -->
    <header class="nav-header">
      <div class="nav-left">
        <router-link to="/" class="logo">
          <div class="logo-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z" fill="currentColor"/>
            </svg>
          </div>
          <span class="logo-text">JAV Manager</span>
        </router-link>
      </div>

      <nav class="nav-menu">
        <router-link v-for="item in navItems" :key="item.path" :to="item.path" class="nav-item" :class="{ active: $route.path === item.path || $route.path.startsWith(item.path + '/') }">
          <el-icon :size="18">
            <component :is="item.icon" />
          </el-icon>
          <span class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="nav-right">
        <el-button type="primary" class="sync-btn" @click="syncJellyfin" :loading="syncing">
          <el-icon><Refresh /></el-icon>
          <span class="btn-text">同步</span>
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
import {
  HomeFilled,
  Film,
  Trophy,
  Compass,
  List,
  User,
  Setting,
  Refresh
} from '@element-plus/icons-vue'
import MovieDetailModal from './components/MovieDetailModal.vue'
import { moviesApi, tasksApi, todosApi } from './api'

const navItems = [
  { path: '/', label: '首页', icon: HomeFilled },
  { path: '/library', label: '影片库', icon: Film },
  { path: '/charts', label: '榜单', icon: Trophy },
  { path: '/discover', label: '发现', icon: Compass },
  { path: '/todo', label: '待看', icon: List },
  { path: '/actors', label: '演员', icon: User },
  { path: '/settings', label: '设置', icon: Setting },
]

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
  background: var(--bg-primary);
}

/* 导航栏 */
.nav-header {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border-light);
  padding: 0 32px;
  height: 72px;
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
  gap: 12px;
  text-decoration: none;
  transition: transform 0.2s ease;
}

.nav-left .logo:hover {
  transform: scale(1.02);
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: var(--primary-gradient);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 4px 12px rgba(232, 165, 152, 0.3);
}

.logo-icon svg {
  width: 24px;
  height: 24px;
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.5px;
}

.nav-menu {
  display: flex;
  gap: 8px;
  padding: 6px;
  background: var(--bg-secondary);
  border-radius: 16px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  border-radius: 12px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.6);
  color: var(--text-primary);
}

.nav-item.active {
  background: #fff;
  color: var(--primary-color);
  box-shadow: 0 2px 8px rgba(74, 74, 74, 0.08);
}

.nav-item .el-icon {
  transition: transform 0.2s ease;
}

.nav-item:hover .el-icon {
  transform: scale(1.1);
}

.nav-right {
  display: flex;
  gap: 12px;
}

.sync-btn {
  padding: 10px 20px;
  font-weight: 500;
}

.sync-btn .el-icon {
  margin-right: 6px;
}

/* 主内容 */
.main-content {
  flex: 1;
  padding: 32px;
  max-width: 1600px;
  margin: 0 auto;
  width: 100%;
}

/* 路由动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

/* 响应式 */
@media (max-width: 1024px) {
  .nav-header {
    padding: 0 20px;
  }

  .nav-menu {
    gap: 4px;
  }

  .nav-item {
    padding: 10px 14px;
  }

  .nav-label {
    display: none;
  }

  .main-content {
    padding: 20px;
  }
}

@media (max-width: 768px) {
  .nav-header {
    height: 64px;
    padding: 0 16px;
  }

  .logo-text {
    display: none;
  }

  .nav-menu {
    gap: 2px;
    padding: 4px;
    border-radius: 12px;
  }

  .nav-item {
    padding: 8px 12px;
    border-radius: 8px;
  }

  .btn-text {
    display: none;
  }

  .sync-btn {
    padding: 10px 12px;
  }

  .main-content {
    padding: 16px;
  }
}
</style>
