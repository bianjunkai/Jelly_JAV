<template>
  <div class="todo-list-view">
    <div class="page-header">
      <h1 class="page-title">待看清单</h1>
      <div class="header-stats">
        <span>待看: {{ stats.total_pending }}</span>
        <span>已完成: {{ stats.total_downloaded }}</span>
      </div>
    </div>

    <!-- 筛选 -->
    <div class="filter-tabs">
      <el-radio-group v-model="filterStatus" @change="fetchTodos">
        <el-radio-button label="pending">待看 ({{ stats.total_pending }})</el-radio-button>
        <el-radio-button label="downloaded">已完成 ({{ stats.total_downloaded }})</el-radio-button>
        <el-radio-button label="all">全部</el-radio-button>
      </el-radio-group>
    </div>

    <div v-loading="loading">
      <!-- 分组展示 -->
      <div v-if="groups.length > 0">
        <div v-for="group in groups" :key="group.source + group.source_detail" class="todo-group">
          <div class="group-header">
            <span class="group-icon">{{ getSourceIcon(group.source) }}</span>
            <span class="group-title">{{ getSourceName(group.source) }}</span>
            <span v-if="group.source_detail" class="group-detail">- {{ group.source_detail }}</span>
            <span class="group-count">({{ group.count }})</span>
          </div>

          <div class="group-items">
            <div v-for="item in group.items" :key="item.id" class="todo-item" :class="{ downloaded: item.status === 'downloaded' }">
              <div class="item-info">
                <span class="item-code">{{ item.code }}</span>
                <span v-if="item.title && item.title !== item.code" class="item-title">{{ item.title }}</span>
                <span class="item-actors">{{ item.actors?.slice(0, 2).join(', ') }}</span>
                <span class="item-date">添加: {{ formatDate(item.added_at) }}</span>
              </div>
              <div class="item-actions">
                <el-button
                  v-if="item.status === 'pending'"
                  size="small"
                  type="success"
                  @click="markDownloaded(item)"
                >
                  标记已下载
                </el-button>
                <el-button size="small" type="danger" @click="deleteTodo(item)">
                  删除
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="empty-state">
        <el-icon size="48"><Document /></el-icon>
        <p>暂无待看项目</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { todosApi } from '../api'

const loading = ref(false)
const groups = ref([])
const stats = ref({ total_pending: 0, total_downloaded: 0 })
const filterStatus = ref('pending')

const fetchTodos = async () => {
  loading.value = true
  try {
    const data = await todosApi.list({ status: filterStatus.value })
    groups.value = data.groups
    stats.value.total_pending = data.total_pending
    stats.value.total_downloaded = data.total_downloaded
  } catch (e) {
    ElMessage.error('获取待看清单失败')
  } finally {
    loading.value = false
  }
}

const markDownloaded = async (item) => {
  try {
    await todosApi.updateStatus(item.id, 'downloaded')
    ElMessage.success('已标记为下载')
    fetchTodos()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const deleteTodo = async (item) => {
  try {
    await ElMessageBox.confirm(`确定删除 ${item.code}?`, '确认删除')
    await todosApi.delete(item.id)
    ElMessage.success('已删除')
    fetchTodos()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}/${date.getDate()}`
}

const getSourceIcon = (source) => {
  const map = { weekly: '📊', monthly: '📈', annual: '🏆', manual: '✋' }
  return map[source] || '📋'
}

const getSourceName = (source) => {
  const map = { weekly: '周报', monthly: '月报', annual: '年报', manual: '手动' }
  return map[source] || source
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

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
}

.header-stats {
  display: flex;
  gap: 24px;
  color: #666;
  font-size: 14px;
}

.filter-tabs {
  margin-bottom: 24px;
}

.todo-group {
  margin-bottom: 24px;
  background: #1a1a1a;
  border-radius: 8px;
  overflow: hidden;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #242424;
  border-bottom: 1px solid #333;
}

.group-icon {
  font-size: 16px;
}

.group-title {
  font-weight: 600;
}

.group-detail {
  color: #e50914;
}

.group-count {
  color: #666;
  margin-left: auto;
}

.group-items {
  padding: 8px 0;
}

.todo-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #333;
  transition: background 0.2s;
}

.todo-item:last-child {
  border-bottom: none;
}

.todo-item:hover {
  background: #242424;
}

.todo-item.downloaded {
  opacity: 0.6;
}

.item-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.item-code {
  font-weight: 600;
  color: #e50914;
}

.item-title {
  font-size: 13px;
  color: #a0a0a0;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-actors {
  font-size: 12px;
  color: #666;
}

.item-date {
  font-size: 11px;
  color: #555;
}

.item-actions {
  display: flex;
  gap: 8px;
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
