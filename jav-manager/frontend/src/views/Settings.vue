<template>
  <div class="settings-view">
    <div class="page-header">
      <h1 class="page-title">设置</h1>
    </div>

    <el-form :model="config" label-width="140px" class="settings-form">
      <!-- Jellyfin 连接 -->
      <el-card class="settings-card">
        <template #header>
          <div class="card-title">Jellyfin 连接</div>
        </template>
        <el-form-item label="服务器地址">
          <el-input v-model="config.jellyfin_url" placeholder="http://192.168.1.100:8096/" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="config.jellyfin_api_key" type="password" show-password placeholder="API Key" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveConfig">保存</el-button>
          <el-button @click="testConnection">测试连接</el-button>
        </el-form-item>
      </el-card>

      <!-- 爬虫设置 -->
      <el-card class="settings-card">
        <template #header>
          <div class="card-title">爬虫设置</div>
        </template>
        <el-form-item label="JavDB 域名">
          <el-select v-model="config.javdb_domain" style="width: 200px">
            <el-option label="javdb.com" value="javdb.com" />
            <el-option label="javdb5.com" value="javdb5.com" />
            <el-option label="javdb4.com" value="javdb4.com" />
          </el-select>
        </el-form-item>
        <el-form-item label="请求延迟">
          <el-input-number v-model="config.request_min_delay" :min="1" :max="10" style="width: 100px" />
          <span style="margin: 0 8px">-</span>
          <el-input-number v-model="config.request_max_delay" :min="1" :max="30" style="width: 100px" />
          <span style="margin-left: 8px; color: #666">秒（随机）</span>
        </el-form-item>
        <el-form-item label="超时时间">
          <el-input-number v-model="config.request_timeout" :min="10" :max="120" style="width: 100px" />
          <span style="margin-left: 8px; color: #666">秒</span>
        </el-form-item>
      </el-card>

      <!-- 评分权重 -->
      <el-card class="settings-card">
        <template #header>
          <div class="card-title">评分权重配置</div>
        </template>
        <el-form-item label="基础分">
          <el-input-number v-model="config.weight_base" :min="0" :max="100" style="width: 100px" />
        </el-form-item>
        <el-form-item label="JavDB ≥4.5">
          <el-input-number v-model="config.weight_javdb_high" :min="-50" :max="50" style="width: 100px" />
        </el-form-item>
        <el-form-item label="JavDB 4.2-4.5">
          <el-input-number v-model="config.weight_javdb_medium" :min="-50" :max="50" style="width: 100px" />
        </el-form-item>
        <el-form-item label="JavDB 3.5-3.9">
          <el-input-number v-model="config.weight_javdb_low" :min="-50" :max="50" style="width: 100px" />
        </el-form-item>
        <el-form-item label="JavDB <3.5">
          <el-input-number v-model="config.weight_javdb_very_low" :min="-50" :max="50" style="width: 100px" />
        </el-form-item>
        <el-divider />
        <el-form-item label="双榜加分">
          <el-input-number v-model="config.weight_dual_chart" :min="0" :max="50" style="width: 100px" />
          <span style="margin-left: 8px; color: #666">(JavDB + JavLibrary)</span>
        </el-form-item>
        <el-form-item label="单榜加分">
          <el-input-number v-model="config.weight_single_chart" :min="0" :max="50" style="width: 100px" />
        </el-form-item>
        <el-form-item label="年度榜加分">
          <el-input-number v-model="config.weight_year_chart" :min="0" :max="50" style="width: 100px" />
        </el-form-item>
        <el-form-item label="多位演员">
          <el-input-number v-model="config.weight_multi_actor" :min="0" :max="20" style="width: 100px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveConfig">保存</el-button>
        </el-form-item>
      </el-card>

      <!-- 数据管理 -->
      <el-card class="settings-card">
        <template #header>
          <div class="card-title">数据管理</div>
        </template>
        <el-form-item label="影片数">
          <span>{{ stats.total_movies }}</span>
        </el-form-item>
        <el-form-item label="演员数">
          <span>{{ stats.total_actors }} (关注 {{ stats.followed_actors }})</span>
        </el-form-item>
        <el-form-item label="平均评分">
          <span>{{ stats.avg_score }}</span>
        </el-form-item>
        <el-form-item>
          <el-button @click="exportData">导出数据</el-button>
          <el-button @click="refreshStats">刷新统计</el-button>
        </el-form-item>
      </el-card>
    </el-form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { statsApi } from '../api'

const config = ref({
  jellyfin_url: 'http://192.168.50.20:8096/',
  jellyfin_api_key: '',
  javdb_domain: 'javdb.com',
  request_min_delay: 3,
  request_max_delay: 6,
  request_timeout: 30,
  weight_base: 50,
  weight_javdb_high: 20,
  weight_javdb_medium: 10,
  weight_javdb_low: -15,
  weight_javdb_very_low: -25,
  weight_dual_chart: 30,
  weight_single_chart: 20,
  weight_year_chart: 10,
  weight_multi_actor: 5
})

const stats = ref({
  total_movies: 0,
  total_actors: 0,
  followed_actors: 0,
  avg_score: 0
})

const fetchStats = async () => {
  try {
    stats.value = await statsApi.get()
  } catch (e) {
    console.error('Failed to fetch stats')
  }
}

const refreshStats = async () => {
  await fetchStats()
  ElMessage.success('统计已刷新')
}

const saveConfig = () => {
  // TODO: 保存到后端
  ElMessage.success('配置已保存')
}

const testConnection = async () => {
  ElMessage.info('测试连接功能待实现')
}

const exportData = () => {
  ElMessage.info('导出功能待实现')
}

onMounted(() => {
  fetchStats()
})
</script>

<style scoped>
.settings-view {
  max-width: 800px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
}

.settings-card {
  margin-bottom: 20px;
  background: #1a1a1a;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
}

.settings-form :deep(.el-form-item__label) {
  color: #a0a0a0;
}
</style>
