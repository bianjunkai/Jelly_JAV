<template>
  <div class="settings-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">设置</h1>
      <p class="page-subtitle">管理你的系统配置和偏好</p>
    </div>

    <div class="settings-grid">
      <!-- Jellyfin 连接 -->
      <div class="settings-card">
        <div class="card-header">
          <div class="header-icon" style="background: linear-gradient(135deg, #8FB8CD, #7AA8BD);">
            <el-icon size="24" color="#fff"><Link /></el-icon>
          </div>
          <div class="header-content">
            <h2 class="card-title">Jellyfin 连接</h2>
            <p class="card-desc">配置你的 Jellyfin 服务器</p>
          </div>
        </div>

        <div class="form-section">
          <div class="form-group">
            <label class="form-label">服务器地址</label>
            <el-input
              v-model="config.jellyfin_url"
              placeholder="http://192.168.1.100:8096/"
              size="large"
            >
              <template #prefix>
                <el-icon><Link /></el-icon>
              </template>
            </el-input>
          </div>

          <div class="form-group">
            <label class="form-label">API Key</label>
            <el-input
              v-model="config.jellyfin_api_key"
              type="password"
              show-password
              placeholder="输入你的 API Key"
              size="large"
            >
              <template #prefix>
                <el-icon><Key /></el-icon>
              </template>
            </el-input>
          </div>

          <div class="form-actions">
            <el-button type="primary" size="large" @click="saveConfig">
              <el-icon><Check /></el-icon>
              保存配置
            </el-button>
            <el-button size="large" @click="testConnection">
              <el-icon><CircleCheckFilled /></el-icon>
              测试连接
            </el-button>
          </div>
        </div>
      </div>

      <!-- 爬虫域名 -->
      <div class="settings-card">
        <div class="card-header">
          <div class="header-icon" style="background: linear-gradient(135deg, #D4A574, #C49464);">
            <el-icon size="24" color="#fff"><Link /></el-icon>
          </div>
          <div class="header-content">
            <h2 class="card-title">爬虫域名</h2>
            <p class="card-desc">配置数据源域名</p>
          </div>
        </div>

        <div class="form-section">
          <div class="form-group">
            <label class="form-label">JavDB 域名</label>
            <div class="tag-input">
              <el-tag
                v-for="(domain, index) in config.javdb_domains"
                :key="domain"
                closable
                @close="removeDomain('javdb_domains', index)"
                class="domain-tag"
                size="large"
              >
                {{ domain }}
              </el-tag>
              <el-input
                v-model="newJavdbDomain"
                placeholder="添加域名"
                @keyup.enter="addDomain('javdb_domains')"
                class="tag-input-field"
              />
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">JavBus 域名</label>
            <div class="tag-input">
              <el-tag
                v-for="(domain, index) in config.javbus_domains"
                :key="domain"
                closable
                @close="removeDomain('javbus_domains', index)"
                class="domain-tag"
                size="large"
              >
                {{ domain }}
              </el-tag>
              <el-input
                v-model="newJavbusDomain"
                placeholder="添加域名"
                @keyup.enter="addDomain('javbus_domains')"
                class="tag-input-field"
              />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group flex-1">
              <label class="form-label">请求延迟 (秒)</label>
              <div class="range-input">
                <el-input-number v-model="config.request_min_delay" :min="1" :max="10" />
                <span class="range-separator">-</span>
                <el-input-number v-model="config.request_max_delay" :min="1" :max="30" />
              </div>
            </div>
            <div class="form-group flex-1">
              <label class="form-label">超时时间 (秒)</label>
              <el-input-number v-model="config.request_timeout" :min="10" :max="120" />
            </div>
          </div>

          <div class="form-actions">
            <el-button type="primary" size="large" @click="saveConfig">
              <el-icon><Check /></el-icon>
              保存域名设置
            </el-button>
          </div>
        </div>
      </div>

      <!-- 系统代理 -->
      <div class="settings-card">
        <div class="card-header">
          <div class="header-icon" style="background: linear-gradient(135deg, #6B8E9F, #5A7D8E);">
            <el-icon size="24" color="#fff"><Connection /></el-icon>
          </div>
          <div class="header-content">
            <h2 class="card-title">系统代理</h2>
            <p class="card-desc">配置后所有爬虫（JavDB、JavBus、JavLibrary）都走代理</p>
          </div>
        </div>

        <div class="form-section">
          <div class="form-group">
            <label class="form-label">启用代理</label>
            <el-switch v-model="config.enable_system_proxy" size="large" />
          </div>

          <div class="form-group">
            <label class="form-label">代理地址</label>
            <el-input
              v-model="config.system_proxy_url"
              placeholder="socks5://192.168.1.15:7893"
              size="large"
              :disabled="!config.enable_system_proxy"
            >
              <template #prefix>
                <el-icon><Link /></el-icon>
              </template>
            </el-input>
          </div>

          <div class="form-actions">
            <el-button type="primary" size="large" @click="saveConfig">
              <el-icon><Check /></el-icon>
              保存代理设置
            </el-button>
          </div>
        </div>
      </div>

      <!-- JavLibrary 导入配置 -->
      <div class="settings-card">
        <div class="card-header">
          <div class="header-icon" style="background: linear-gradient(135deg, #8FB8CD, #7AA8BD);">
            <el-icon size="24" color="#fff"><Document /></el-icon>
          </div>
          <div class="header-content">
            <h2 class="card-title">JavLibrary 导入</h2>
            <p class="card-desc">配置 CSV 文件路径用于 JavLibrary 榜单更新</p>
          </div>
        </div>

        <div class="form-section">
          <div class="form-group">
            <label class="form-label">CSV 文件路径</label>
            <el-input
              v-model="config.javlibrary_csv_path"
              placeholder="例如：javlibrary_bestrated_2026-04-02T14-40-47.csv 或 data/javlibrary.csv"
              size="large"
            >
              <template #prefix>
                <el-icon><Document /></el-icon>
              </template>
            </el-input>
            <p class="form-hint">填写 JavLibrary 榜单 CSV 文件路径（相对项目根目录或绝对路径），用于导入 TOP500 榜单数据</p>
          </div>

          <div class="form-actions">
            <el-button type="primary" size="large" @click="saveConfig">
              <el-icon><Check /></el-icon>
              保存路径
            </el-button>
            <el-button size="large" @click="testCsvPath">
              <el-icon><CircleCheckFilled /></el-icon>
              测试路径
            </el-button>
          </div>
        </div>
      </div>

      <!-- 榜单管理 -->
      <div class="settings-card">
        <div class="card-header">
          <div class="header-icon" style="background: linear-gradient(135deg, #E8A598, #D4958A);">
            <el-icon size="24" color="#fff"><Trophy /></el-icon>
          </div>
          <div class="header-content">
            <h2 class="card-title">榜单管理</h2>
            <p class="card-desc">添加和管理榜单数据源</p>
          </div>
        </div>

        <div class="form-section">
          <div class="chart-tags">
            <el-tag
              v-for="chart in charts"
              :key="chart.id"
              class="chart-tag-item"
              size="large"
            >
              {{ chart.display_name }}
            </el-tag>
            <span v-if="charts.length === 0" class="empty-charts">暂无自定义榜单</span>
          </div>

          <div class="add-chart-section">
            <div class="form-row">
              <el-select
                v-model="selectedChartType"
                placeholder="选择预设榜单"
                clearable
                size="large"
                class="flex-1"
              >
                <el-option
                  v-for="chart in availableCharts"
                  :key="chart.name"
                  :label="chart.name"
                  :value="chart.name"
                />
              </el-select>
              <span class="or-separator">或</span>
              <el-input
                v-model="newChartName"
                placeholder="自定义榜单名称"
                size="large"
                class="flex-1"
              />
            </div>
            <div class="form-row" style="margin-top: 12px;">
              <el-input-number
                v-model="newChartYear"
                placeholder="年份"
                :min="2000"
                :max="2099"
                size="large"
                style="width: 120px;"
              />
              <el-button
                type="primary"
                size="large"
                @click="addChart"
                :disabled="!selectedChartType && !newChartName"
              >
                <el-icon><Plus /></el-icon>
                添加榜单
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 评分权重 -->
      <div class="settings-card full-width">
        <div class="card-header">
          <div class="header-icon" style="background: linear-gradient(135deg, #8FB996, #7AA882);">
            <el-icon size="24" color="#fff"><Setting /></el-icon>
          </div>
          <div class="header-content">
            <h2 class="card-title">评分权重配置</h2>
            <p class="card-desc">自定义影片加权分计算规则</p>
          </div>
        </div>

        <div class="form-section">
          <div class="weight-grid">
            <div class="weight-group">
              <h4 class="group-title">基础分</h4>
              <div class="weight-item">
                <span class="weight-label">基础分值</span>
                <el-input-number v-model="config.weight_base" :min="0" :max="100" size="large" />
              </div>
            </div>

            <div class="weight-group">
              <h4 class="group-title">JavDB 评分</h4>
              <div class="weight-item">
                <span class="weight-label">≥ 4.5 分</span>
                <el-input-number v-model="config.weight_javdb_high" :min="-50" :max="50" size="large" />
              </div>
              <div class="weight-item">
                <span class="weight-label">4.2 - 4.5 分</span>
                <el-input-number v-model="config.weight_javdb_medium" :min="-50" :max="50" size="large" />
              </div>
              <div class="weight-item">
                <span class="weight-label">3.5 - 3.9 分</span>
                <el-input-number v-model="config.weight_javdb_low" :min="-50" :max="50" size="large" />
              </div>
              <div class="weight-item">
                <span class="weight-label">< 3.5 分</span>
                <el-input-number v-model="config.weight_javdb_very_low" :min="-50" :max="50" size="large" />
              </div>
            </div>

            <div class="weight-group">
              <h4 class="group-title">榜单加成</h4>
              <div class="weight-item">
                <span class="weight-label">双榜</span>
                <el-input-number v-model="config.weight_dual_chart" :min="0" :max="50" size="large" />
              </div>
              <div class="weight-item">
                <span class="weight-label">单榜</span>
                <el-input-number v-model="config.weight_single_chart" :min="0" :max="50" size="large" />
              </div>
              <div class="weight-item">
                <span class="weight-label">年度榜</span>
                <el-input-number v-model="config.weight_year_chart" :min="0" :max="50" size="large" />
              </div>
            </div>

            <div class="weight-group">
              <h4 class="group-title">其他</h4>
              <div class="weight-item">
                <span class="weight-label">多位演员</span>
                <el-input-number v-model="config.weight_multi_actor" :min="0" :max="20" size="large" />
              </div>
              <div class="weight-item">
                <span class="weight-label">演员有 JavBus ID</span>
                <el-input-number v-model="config.weight_javbus_id" :min="0" :max="30" size="large" />
              </div>
            </div>
          </div>

          <div class="form-actions">
            <el-button type="primary" size="large" @click="saveConfig">
              <el-icon><Check /></el-icon>
              保存权重配置
            </el-button>
            <el-button size="large" @click="recalculateWeightedScores">
              <el-icon><Refresh /></el-icon>
              重新计算加权分
            </el-button>
          </div>
        </div>
      </div>

      <!-- 数据管理 -->
      <div class="settings-card">
        <div class="card-header">
          <div class="header-icon" style="background: linear-gradient(135deg, #B8A9C9, #A899B9);">
            <el-icon size="24" color="#fff"><DataLine /></el-icon>
          </div>
          <div class="header-content">
            <h2 class="card-title">数据管理</h2>
            <p class="card-desc">查看统计数据和导出</p>
          </div>
        </div>

        <div class="form-section">
          <div class="stats-display">
            <div class="stat-item">
              <span class="stat-value">{{ stats.total_movies }}</span>
              <span class="stat-label">影片数</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ stats.total_actors }}</span>
              <span class="stat-label">演员数</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ stats.followed_actors }}</span>
              <span class="stat-label">已关注</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ stats.avg_score }}</span>
              <span class="stat-label">平均评分</span>
            </div>
          </div>

          <div class="form-actions">
            <el-button size="large" @click="exportData">
              <el-icon><Download /></el-icon>
              导出数据
            </el-button>
            <el-button size="large" @click="refreshStats">
              <el-icon><Refresh /></el-icon>
              刷新统计
            </el-button>
            <el-button
              type="primary"
              size="large"
              :loading="fetchingAllReleases"
              @click="fetchAllReleases"
            >
              <el-icon><VideoCamera /></el-icon>
              获取所有关注演员新片
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Link,
  Key,
  Check,
  CircleCheckFilled,
  Trophy,
  Plus,
  Setting,
  DataLine,
  Download,
  Refresh,
  Connection,
  Document,
  VideoCamera
} from '@element-plus/icons-vue'
import { statsApi, configApi, chartManageApi, chartsApi, tasksApi, actorsApi } from '../api'

const config = ref({
  jellyfin_url: 'http://192.168.50.20:8096/',
  jellyfin_api_key: '',
  javdb_domains: ['javdb.com'],
  javbus_domains: ['javbus.com'],
  javlibrary_csv_path: '',
  request_min_delay: 3,
  request_max_delay: 6,
  request_timeout: 30,
  enable_system_proxy: false,
  system_proxy_url: 'socks5://192.168.1.15:7893',
  weight_base: 50,
  weight_javdb_high: 20,
  weight_javdb_medium: 10,
  weight_javdb_low: -15,
  weight_javdb_very_low: -25,
  weight_dual_chart: 30,
  weight_single_chart: 20,
  weight_year_chart: 10,
  weight_multi_actor: 5,
  weight_javbus_id: 15
})

const stats = ref({
  total_movies: 0,
  total_actors: 0,
  followed_actors: 0,
  avg_score: 0
})

const charts = ref([])
const availableCharts = ref([])
const selectedChartType = ref('')
const newChartName = ref('')
const newChartYear = ref(null)
const newJavdbDomain = ref('')
const newJavbusDomain = ref('')
const fetchingAllReleases = ref(false)

const fetchConfig = async () => {
  try {
    const data = await configApi.get()
    config.value = data
  } catch (e) {
    console.error('Failed to fetch config:', e)
  }
}

const fetchStats = async () => {
  try {
    stats.value = await statsApi.get()
  } catch (e) {
    console.error('Failed to fetch stats')
  }
}

const fetchCharts = async () => {
  try {
    charts.value = await chartsApi.list()
  } catch (e) {
    console.error('Failed to fetch charts:', e)
  }
}

const fetchAvailableCharts = async () => {
  try {
    availableCharts.value = await configApi.getCharts()
  } catch (e) {
    console.error('Failed to fetch available charts:', e)
  }
}

const addDomain = (type) => {
  if (type === 'javdb_domains' && newJavdbDomain.value) {
    if (!config.value.javdb_domains.includes(newJavdbDomain.value)) {
      config.value.javdb_domains.push(newJavdbDomain.value)
    }
    newJavdbDomain.value = ''
  } else if (type === 'javbus_domains' && newJavbusDomain.value) {
    if (!config.value.javbus_domains.includes(newJavbusDomain.value)) {
      config.value.javbus_domains.push(newJavbusDomain.value)
    }
    newJavbusDomain.value = ''
  }
}

const removeDomain = (type, index) => {
  config.value[type].splice(index, 1)
}

const addChart = async () => {
  let chartName = selectedChartType.value
  let year = null
  let source = 'javdb'
  let totalCount = 250

  if (chartName && availableCharts.value.find(c => c.name === chartName)) {
    const chartInfo = availableCharts.value.find(c => c.name === chartName)
    year = chartInfo.year
    source = chartInfo.source || 'javdb'
    totalCount = chartInfo.total || 250
  } else if (newChartName.value) {
    chartName = newChartName.value
    year = newChartYear.value || null
  } else {
    ElMessage.warning('请选择或输入榜单名称')
    return
  }

  try {
    await chartManageApi.create({
      name: chartName,
      display_name: chartName,
      source: source,
      description: `${chartName} 影片`,
      total_count: totalCount,
      year: year
    })
    ElMessage.success(`已添加榜单: ${chartName}`)
    selectedChartType.value = ''
    newChartName.value = ''
    newChartYear.value = null
    await fetchCharts()
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '添加榜单失败')
  }
}

const saveConfig = async () => {
  try {
    await configApi.update(config.value)
    ElMessage.success('配置已保存')
  } catch (e) {
    ElMessage.error('保存配置失败')
  }
}

const refreshStats = async () => {
  await fetchStats()
  ElMessage.success('统计已刷新')
}

const testConnection = async () => {
  ElMessage.info('测试连接功能待实现')
}

const testCsvPath = async () => {
  if (!config.value.javlibrary_csv_path) {
    ElMessage.warning('请先填写 CSV 文件路径')
    return
  }
  try {
    const result = await configApi.testCsvPath(config.value.javlibrary_csv_path)
    if (result.valid) {
      const pathInfo = result.resolved_path ? `(${result.resolved_path})` : ''
      ElMessage.success(`路径有效 ${pathInfo}，包含 ${result.count} 条记录`)
    } else {
      ElMessage.error(result.error || '路径无效')
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '测试失败')
  }
}

const exportData = () => {
  ElMessage.info('导出功能待实现')
}

const recalculateWeightedScores = async () => {
  try {
    ElMessage.info('正在重新计算加权分...')
    const result = await tasksApi.recalculateWeightedScores()
    ElMessage.success(`加权分已更新，共更新 ${result.updated} 部影片`)
  } catch (e) {
    ElMessage.error('更新加权分失败')
  }
}

const fetchAllReleases = async () => {
  fetchingAllReleases.value = true
  try {
    const result = await actorsApi.fetchAllReleases()
    if (result.status === 'started') {
      ElMessage.success('批量获取任务已启动，将在后台为所有关注演员获取新片')
    } else {
      ElMessage.info(result.message || '任务已启动')
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '启动任务失败')
  } finally {
    fetchingAllReleases.value = false
  }
}

onMounted(() => {
  fetchConfig()
  fetchStats()
  fetchCharts()
  fetchAvailableCharts()
})
</script>

<style scoped>
.settings-view {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 32px;
}

.page-title {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.5px;
  margin-bottom: 8px;
}

.page-subtitle {
  font-size: 15px;
  color: var(--text-muted);
}

/* 设置网格 */
.settings-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.settings-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.settings-card.full-width {
  grid-column: 1 / -1;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  background: var(--bg-secondary);
}

.header-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.card-desc {
  font-size: 13px;
  color: var(--text-tertiary);
}

.form-section {
  padding: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.form-hint {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 6px;
}

.form-row {
  display: flex;
  gap: 16px;
  align-items: flex-end;
}

.flex-1 {
  flex: 1;
  min-width: 0;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

/* Tag 输入 */
.tag-input {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  min-height: 48px;
  align-items: center;
}

.domain-tag {
  margin: 0;
}

.tag-input-field {
  flex: 1;
  min-width: 100px;
}

.tag-input-field :deep(.el-input__wrapper) {
  background: transparent;
  box-shadow: none;
}

.range-input {
  display: flex;
  align-items: center;
  gap: 12px;
}

.range-separator {
  color: var(--text-tertiary);
}

/* 榜单标签 */
.chart-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  margin-bottom: 20px;
  min-height: 60px;
}

.chart-tag-item {
  margin: 0;
}

.empty-charts {
  color: var(--text-muted);
  font-size: 14px;
  padding: 8px;
}

.add-chart-section {
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.or-separator {
  color: var(--text-tertiary);
  font-size: 14px;
  padding: 0 8px;
}

/* 权重配置 */
.weight-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

.weight-group {
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.group-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

.weight-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.weight-item:last-child {
  margin-bottom: 0;
}

.weight-label {
  font-size: 13px;
  color: var(--text-secondary);
}

/* 数据显示 */
.stats-display {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-item {
  text-align: center;
  padding: 20px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.stat-value {
  display: block;
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  color: var(--text-tertiary);
}

/* 响应式 */
@media (max-width: 1024px) {
  .settings-grid {
    grid-template-columns: 1fr;
  }

  .weight-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .stats-display {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .page-title {
    font-size: 24px;
  }

  .form-row {
    flex-direction: column;
    align-items: stretch;
  }

  .or-separator {
    text-align: center;
    padding: 8px 0;
  }

  .weight-grid {
    grid-template-columns: 1fr;
  }

  .stats-display {
    grid-template-columns: repeat(2, 1fr);
  }

  .form-actions {
    flex-direction: column;
  }

  .form-actions .el-button {
    width: 100%;
  }
}
</style>
