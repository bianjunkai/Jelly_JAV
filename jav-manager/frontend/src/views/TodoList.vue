<template>
  <div class="todo-list-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">待看清单</h1>
        <div class="header-stats">
          <div class="stat-item">
            <span class="stat-dot pending"></span>
            <span class="stat-num">{{ stats.total_pending }}</span>
            <span class="stat-label">待看</span>
          </div>
          <div class="stat-item">
            <span class="stat-dot done"></span>
            <span class="stat-num">{{ stats.total_downloaded }}</span>
            <span class="stat-label">已完成</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 筛选 -->
    <div class="filter-section">
      <el-radio-group v-model="filterStatus" @change="fetchTodos" class="status-tabs">
        <el-radio-button label="pending">
          <span class="tab-dot pending"></span>
          待看 ({{ stats.total_pending }})
        </el-radio-button>
        <el-radio-button label="downloaded">
          <span class="tab-dot done"></span>
          已完成 ({{ stats.total_downloaded }})
        </el-radio-button>
        <el-radio-button label="all">全部</el-radio-button>
      </el-radio-group>

      <el-button v-if="filterStatus !== 'downloaded'" type="primary" @click="batchComplete">
        <el-icon><Check /></el-icon>
        批量完成
      </el-button>
    </div>

    <!-- 分组列表 -->
    <div v-loading="loading" class="todo-content">
      <div v-if="groups.length > 0" class="groups-container">
        <div
          v-for="group in groups"
          :key="group.source + group.source_detail"
          class="todo-group"
        >
          <div class="group-header" @click="toggleGroup(group)">
            <div class="group-icon" :style="{ background: getSourceColor(group.source) }">
              {{ getSourceIcon(group.source) }}
            </div>
            <div class="group-info">
              <h3 class="group-title">{{ getSourceName(group.source) }}</h3>
              <p v-if="group.source_detail" class="group-detail">{{ group.source_detail }}</p>
            </div>
            <span class="group-count">{{ group.items.length }} 部</span>
            <el-icon class="expand-icon" :class="{ expanded: !group.collapsed }">
              <ArrowDown />
            </el-icon>
          </div>

          <transition name="slide">
            <div v-show="!group.collapsed" class="group-items">
              <div
                v-for="item in group.items"
                :key="item.id"
                class="todo-item"
                :class="{ downloaded: item.status === 'downloaded', selected: selectedItems.includes(item.id) }"
              >
                <el-checkbox
                  v-if="filterStatus !== 'downloaded' && item.status === 'pending'"
                  v-model="selectedItems"
                  :label="item.id"
                  class="item-checkbox"
                >
                  {{ '' }}
                </el-checkbox>

                <div class="item-content" @click="showDetail(item)">
                  <div class="item-main">
                    <span class="item-code">{{ item.code }}</span>
                    <span v-if="item.title && item.title !== item.code" class="item-title">
                      {{ item.title }}
                    </span>
                  </div>
                  <div class="item-meta">
                    <span v-if="item.actors" class="item-actors">{{ item.actors }}</span>
                    <span class="item-date">{{ formatDate(item.added_at) }}</span>
                  </div>
                </div>

                <div class="item-actions">
                  <el-button
                    v-if="item.status === 'pending'"
                    size="small"
                    type="success"
                    circle
                    @click.stop="markDownloaded(item)"
                  >
                    <el-icon><Check /></el-icon>
                  </el-button>
                  <el-button
                    size="small"
                    type="danger"
                    circle
                    plain
                    @click.stop="deleteTodo(item)"
                  >
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>
          </transition>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="empty-state">
        <div class="empty-icon">
          <el-icon size="64"><DocumentChecked /></el-icon>
        </div>
        <h3 class="empty-title">清单为空</h3>
        <p class="empty-desc">去榜单或演员页面添加影片到待看清单</p>
        <el-button type="primary" @click="$router.push('/charts')">浏览榜单</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Check,
  Delete,
  ArrowDown,
  DocumentChecked
} from '@element-plus/icons-vue'
import { todosApi } from '../api'

const loading = ref(false)
const groups = ref([])
const stats = ref({ total_pending: 0, total_downloaded: 0 })
const filterStatus = ref('pending')
const selectedItems = ref([])

const sourceColors = {
  weekly: 'linear-gradient(135deg, #F5D5CE, #E8A598)',
  monthly: 'linear-gradient(135deg, #F0E0D0, #D4A574)',
  annual: 'linear-gradient(135deg, #E0E8F0, #8FB8CD)',
  manual: 'linear-gradient(135deg, #E0E8E0, #8FB996)'
}

const fetchTodos = async () => {
  loading.value = true
  try {
    const data = await todosApi.list({ status: filterStatus.value })
    groups.value = data.groups.map(g => ({ ...g, collapsed: false }))
    stats.value.total_pending = data.total_pending
    stats.value.total_downloaded = data.total_downloaded
    selectedItems.value = []
  } catch (e) {
    ElMessage.error('获取待看清单失败')
  } finally {
    loading.value = false
  }
}

const toggleGroup = (group) => {
  group.collapsed = !group.collapsed
}

const getSourceIcon = (source) => {
  const map = { weekly: '📊', monthly: '📈', annual: '🏆', manual: '✋' }
  return map[source] || '📋'
}

const getSourceColor = (source) => {
  return sourceColors[source] || sourceColors.manual
}

const getSourceName = (source) => {
  const map = { weekly: '周报推荐', monthly: '月报推荐', annual: '年报推荐', manual: '手动添加' }
  return map[source] || source
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 7) return `${days} 天前`
  return `${date.getMonth() + 1}月${date.getDate()}日`
}

const markDownloaded = async (item) => {
  try {
    await todosApi.updateStatus(item.id, 'downloaded')
    ElMessage.success('已标记为完成')
    fetchTodos()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const deleteTodo = async (item) => {
  try {
    await ElMessageBox.confirm(`确定删除 ${item.code}?`, '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await todosApi.delete(item.id)
    ElMessage.success('已删除')
    fetchTodos()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

const batchComplete = async () => {
  if (selectedItems.value.length === 0) {
    ElMessage.warning('请先选择要完成的影片')
    return
  }

  try {
    await ElMessageBox.confirm(`确定将选中的 ${selectedItems.value.length} 部影片标记为完成?`, '确认', {
      confirmButtonText: '确认',
      cancelButtonText: '取消'
    })
    // 批量更新
    for (const id of selectedItems.value) {
      await todosApi.updateStatus(id, 'downloaded')
    }
    ElMessage.success(`已完成 ${selectedItems.value.length} 部影片`)
    fetchTodos()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('操作失败')
  }
}

const showDetail = (item) => {
  // 可以显示影片详情弹窗
  console.log('Show detail:', item)
}

onMounted(() => {
  fetchTodos()
})
</script>

<style scoped>
.todo-list-view {
  max-width: 900px;
  margin: 0 auto;
}

/* 页面头部 */
.page-header {
  margin-bottom: 28px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 24px;
  flex-wrap: wrap;
}

.page-title {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.5px;
}

.header-stats {
  display: flex;
  gap: 20px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--bg-card);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
}

.stat-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.stat-dot.pending {
  background: var(--primary-color);
}

.stat-dot.done {
  background: var(--accent-green);
}

.stat-num {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-label {
  font-size: 13px;
  color: var(--text-tertiary);
}

/* 筛选栏 */
.filter-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 12px;
}

.status-tabs :deep(.el-radio-button__inner) {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tab-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.tab-dot.pending {
  background: var(--primary-color);
}

.tab-dot.done {
  background: var(--accent-green);
}

/* 分组容器 */
.groups-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.todo-group {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 20px;
  cursor: pointer;
  transition: background 0.2s ease;
}

.group-header:hover {
  background: var(--bg-hover);
}

.group-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.group-info {
  flex: 1;
  min-width: 0;
}

.group-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.group-detail {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 2px;
}

.group-count {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-tertiary);
  padding: 4px 12px;
  background: var(--bg-secondary);
  border-radius: 20px;
}

.expand-icon {
  color: var(--text-muted);
  transition: transform 0.3s ease;
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

/* 分组内容 */
.group-items {
  padding: 0 20px 16px;
}

.todo-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  margin-bottom: 8px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  transition: all 0.2s ease;
  cursor: pointer;
}

.todo-item:hover {
  background: var(--bg-tertiary);
}

.todo-item.downloaded {
  opacity: 0.7;
}

.todo-item.selected {
  background: var(--primary-light);
}

.item-checkbox {
  margin-right: 4px;
}

.item-checkbox :deep(.el-checkbox__label) {
  display: none;
}

.item-content {
  flex: 1;
  min-width: 0;
}

.item-main {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 4px;
}

.item-code {
  font-size: 15px;
  font-weight: 600;
  color: var(--primary-color);
  flex-shrink: 0;
}

.item-title {
  font-size: 14px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: var(--text-tertiary);
}

.item-actors {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}

.item-actions {
  display: flex;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.todo-item:hover .item-actions {
  opacity: 1;
}

/* 展开动画 */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
  max-height: 2000px;
  overflow: hidden;
}

.slide-enter-from,
.slide-leave-to {
  max-height: 0;
  opacity: 0;
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
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.empty-desc {
  font-size: 14px;
  color: var(--text-muted);
  margin-bottom: 24px;
}

/* 响应式 */
@media (max-width: 768px) {
  .page-title {
    font-size: 24px;
  }

  .header-stats {
    width: 100%;
  }

  .filter-section {
    flex-direction: column;
    align-items: stretch;
  }

  .group-header {
    padding: 12px 16px;
  }

  .group-items {
    padding: 0 16px 12px;
  }

  .todo-item {
    padding: 12px;
  }

  .item-actions {
    opacity: 1;
  }
}
</style>
