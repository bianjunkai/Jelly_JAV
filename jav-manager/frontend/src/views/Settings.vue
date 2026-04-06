<template>
  <div class="settings-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">系统设置</h1>
      <p class="page-subtitle">配置你的数据源、爬虫参数和评分规则</p>
    </div>

    <div class="settings-layout">
      <!-- 左侧：设置导航 -->
      <aside class="settings-nav">
        <nav class="nav-list">
          <button
            v-for="item in navItems"
            :key="item.key"
            class="nav-item"
            :class="{ active: activeSection === item.key }"
            @click="activeSection = item.key"
          >
            <div class="nav-icon" :style="{ background: item.bgColor }">
              <el-icon :size="18" color="#fff">
                <component :is="item.icon" />
              </el-icon>
            </div>
            <div class="nav-text">
              <span class="nav-title">{{ item.title }}</span>
              <span class="nav-desc">{{ item.desc }}</span>
            </div>
            <el-icon class="nav-arrow"><ArrowRight /></el-icon>
          </button>
        </nav>

        <!-- 实时状态 -->
        <div class="nav-status">
          <div class="status-header">
            <el-icon><Connection /></el-icon>
            <span>系统状态</span>
          </div>
          <div class="status-items">
            <div class="status-item">
              <span class="status-dot" :class="config.enable_system_proxy ? 'online' : 'offline'"></span>
              <span class="status-label">{{ config.enable_system_proxy ? '代理已启用' : '直连' }}</span>
            </div>
            <div class="status-item">
              <span class="status-dot online"></span>
              <span class="status-label">Jellyfin {{ config.jellyfin_url ? '已配置' : '未配置' }}</span>
            </div>
          </div>
        </div>
      </aside>

      <!-- 右侧：设置内容 -->
      <main class="settings-content">

        <!-- 连接配置 -->
        <section v-show="activeSection === 'connection'" class="content-section">
          <div class="section-hero">
            <div class="hero-icon" style="background: linear-gradient(135deg, #8FB8CD, #7AA8BD);">
              <el-icon :size="28" color="#fff"><Monitor /></el-icon>
            </div>
            <div class="hero-text">
              <h2>Jellyfin 连接</h2>
              <p>连接你的 Jellyfin 服务器，同步影片库和元数据</p>
            </div>
          </div>

          <div class="config-card">
            <div class="config-row">
              <div class="config-field">
                <label class="field-label">服务器地址</label>
                <el-input
                  v-model="config.jellyfin_url"
                  placeholder="http://192.168.1.100:8096/"
                  size="large"
                >
                  <template #prefix><el-icon><Link /></el-icon></template>
                </el-input>
              </div>
              <div class="config-field">
                <label class="field-label">API Key</label>
                <el-input
                  v-model="config.jellyfin_api_key"
                  type="password"
                  show-password
                  placeholder="输入 Jellyfin API Key"
                  size="large"
                >
                  <template #prefix><el-icon><Key /></el-icon></template>
                </el-input>
              </div>
            </div>
            <div class="config-actions">
              <el-button type="primary" size="large" @click="saveConfig">
                <el-icon><Check /></el-icon>
                保存配置
              </el-button>
              <el-button size="large" @click="syncFromJellyfin" :loading="syncing">
                <el-icon><Refresh /></el-icon>
                立即同步
              </el-button>
            </div>
          </div>
        </section>

        <!-- 数据源配置 -->
        <section v-show="activeSection === 'datasource'" class="content-section">
          <div class="section-hero">
            <div class="hero-icon" style="background: linear-gradient(135deg, #D4A574, #C49464);">
              <el-icon :size="28" color="#fff"><Guide /></el-icon>
            </div>
            <div class="hero-text">
              <h2>数据源配置</h2>
              <p>管理 JavDB、JavBus 域名和爬虫请求策略</p>
            </div>
          </div>

          <!-- 域名管理 -->
          <div class="config-card">
            <h3 class="card-section-title">爬虫域名</h3>
            <div class="domain-grid">
              <div class="domain-block">
                <div class="domain-header">
                  <span class="domain-brand">JavDB</span>
                  <span class="domain-count">{{ config.javdb_domains.length }} 个域名</span>
                </div>
                <div class="domain-chips">
                  <el-tag
                    v-for="(domain, index) in config.javdb_domains"
                    :key="domain"
                    closable
                    @close="removeDomain('javdb_domains', index)"
                    class="domain-chip"
                    size="large"
                    type="warning"
                  >
                    {{ domain }}
                  </el-tag>
                </div>
                <div class="domain-add">
                  <el-input
                    v-model="newJavdbDomain"
                    placeholder="输入新域名后回车"
                    size="large"
                    @keyup.enter="addDomain('javdb_domains')"
                  >
                    <template #append>
                      <el-button @click="addDomain('javdb_domains')" :disabled="!newJavdbDomain">
                        <el-icon><Plus /></el-icon>
                      </el-button>
                    </template>
                  </el-input>
                </div>
              </div>

              <div class="domain-block">
                <div class="domain-header">
                  <span class="domain-brand">JavBus</span>
                  <span class="domain-count">{{ config.javbus_domains.length }} 个域名</span>
                </div>
                <div class="domain-chips">
                  <el-tag
                    v-for="(domain, index) in config.javbus_domains"
                    :key="domain"
                    closable
                    @close="removeDomain('javbus_domains', index)"
                    class="domain-chip"
                    size="large"
                    type="warning"
                  >
                    {{ domain }}
                  </el-tag>
                </div>
                <div class="domain-add">
                  <el-input
                    v-model="newJavbusDomain"
                    placeholder="输入新域名后回车"
                    size="large"
                    @keyup.enter="addDomain('javbus_domains')"
                  >
                    <template #append>
                      <el-button @click="addDomain('javbus_domains')" :disabled="!newJavbusDomain">
                        <el-icon><Plus /></el-icon>
                      </el-button>
                    </template>
                  </el-input>
                </div>
              </div>
            </div>
          </div>

          <!-- 请求策略 -->
          <div class="config-card">
            <h3 class="card-section-title">请求策略</h3>
            <div class="strategy-grid">
              <div class="strategy-item">
                <div class="strategy-header">
                  <label class="field-label">请求延迟</label>
                  <span class="strategy-value">{{ config.request_min_delay }}s - {{ config.request_max_delay }}s</span>
                </div>
                <div class="strategy-range">
                  <el-slider
                    v-model="delayRange"
                    range
                    :min="1"
                    :max="30"
                    :step="1"
                    :format-tooltip="val => val + 's'"
                  />
                </div>
                <p class="strategy-hint">随机等待时间，避免被封禁</p>
              </div>
              <div class="strategy-item">
                <div class="strategy-header">
                  <label class="field-label">超时时间</label>
                  <span class="strategy-value">{{ config.request_timeout }}s</span>
                </div>
                <el-slider
                  v-model="config.request_timeout"
                  :min="10"
                  :max="120"
                  :step="5"
                  :format-tooltip="val => val + 's'"
                />
                <p class="strategy-hint">单次请求最大等待时间</p>
              </div>
            </div>
          </div>

          <div class="config-actions">
            <el-button type="primary" size="large" @click="saveConfig">
              <el-icon><Check /></el-icon>
              保存数据源配置
            </el-button>
          </div>
        </section>

        <!-- 代理配置 -->
        <section v-show="activeSection === 'proxy'" class="content-section">
          <div class="section-hero">
            <div class="hero-icon" style="background: linear-gradient(135deg, #6B8E9F, #5A7D8E);">
              <el-icon :size="28" color="#fff"><Connection /></el-icon>
            </div>
            <div class="hero-text">
              <h2>系统代理</h2>
              <p>配置 HTTP/SOCKS5 代理，所有爬虫请求将经过代理</p>
            </div>
          </div>

          <div class="config-card">
            <div class="proxy-toggle">
              <div class="toggle-info">
                <span class="toggle-title">启用系统代理</span>
                <span class="toggle-desc">{{ config.enable_system_proxy ? '所有爬虫请求将经过代理服务器' : '爬虫将直接连接目标网站' }}</span>
              </div>
              <el-switch v-model="config.enable_system_proxy" size="large" />
            </div>

            <div class="config-field" style="margin-top: 24px;">
              <label class="field-label">代理地址</label>
              <el-input
                v-model="config.system_proxy_url"
                placeholder="socks5://192.168.1.15:7893 或 http://proxy:8080"
                size="large"
                :disabled="!config.enable_system_proxy"
              >
                <template #prefix><el-icon><Link /></el-icon></template>
              </el-input>
            </div>
          </div>

          <div class="config-actions">
            <el-button type="primary" size="large" @click="saveConfig">
              <el-icon><Check /></el-icon>
              保存代理配置
            </el-button>
          </div>
        </section>

        <!-- 评分权重 -->
        <section v-show="activeSection === 'scoring'" class="content-section">
          <div class="section-hero">
            <div class="hero-icon" style="background: linear-gradient(135deg, #8FB996, #7AA882);">
              <el-icon :size="28" color="#fff"><DataLine /></el-icon>
            </div>
            <div class="hero-text">
              <h2>评分权重配置</h2>
              <p>调整加权分计算规则，影响影片的推荐优先级</p>
            </div>
          </div>

          <div class="weight-grid">
            <!-- 基础分 -->
            <div class="weight-card weight-base">
              <div class="weight-card-header">
                <span class="weight-badge">基础</span>
                <span class="weight-card-name">影片基础分</span>
              </div>
              <div class="weight-big-value">{{ config.weight_base }}</div>
              <el-slider v-model="config.weight_base" :min="0" :max="100" :step="5" />
            </div>

            <!-- JavDB 评分 -->
            <div class="weight-card">
              <div class="weight-card-header">
                <span class="weight-badge javdb">JavDB</span>
                <span class="weight-card-name">JavDB 评分加成</span>
              </div>
              <div class="javdb-ranges">
                <div class="javdb-range-row">
                  <span class="javdb-range-label high">≥ 4.5</span>
                  <div class="javdb-bar-track">
                    <div class="javdb-bar-fill high" :style="{ width: (config.weight_javdb_high > 0 ? '+' : '') + config.weight_javdb_high }"></div>
                  </div>
                  <el-input-number v-model="config.weight_javdb_high" :min="-50" :max="50" size="small" controls-position="right" />
                </div>
                <div class="javdb-range-row">
                  <span class="javdb-range-label mid">4.2-4.5</span>
                  <div class="javdb-bar-track">
                    <div class="javdb-bar-fill mid" :style="{ width: (config.weight_javdb_medium > 0 ? '+' : '') + config.weight_javdb_medium }"></div>
                  </div>
                  <el-input-number v-model="config.weight_javdb_medium" :min="-50" :max="50" size="small" controls-position="right" />
                </div>
                <div class="javdb-range-row">
                  <span class="javdb-range-label low">3.5-3.9</span>
                  <div class="javdb-bar-track">
                    <div class="javdb-bar-fill low" :style="{ width: Math.abs(config.weight_javdb_low) }"></div>
                  </div>
                  <el-input-number v-model="config.weight_javdb_low" :min="-50" :max="50" size="small" controls-position="right" />
                </div>
                <div class="javdb-range-row">
                  <span class="javdb-range-label very-low">&lt; 3.5</span>
                  <div class="javdb-bar-track">
                    <div class="javdb-bar-fill very-low" :style="{ width: Math.abs(config.weight_javdb_very_low) }"></div>
                  </div>
                  <el-input-number v-model="config.weight_javdb_very_low" :min="-50" :max="50" size="small" controls-position="right" />
                </div>
              </div>
            </div>

            <!-- 榜单加成 -->
            <div class="weight-card">
              <div class="weight-card-header">
                <span class="weight-badge chart">榜单</span>
                <span class="weight-card-name">榜单加成</span>
              </div>
              <div class="chart-bonus-grid">
                <div class="bonus-item">
                  <div class="bonus-icon dual">
                    <el-icon><Trophy /></el-icon>
                  </div>
                  <div class="bonus-info">
                    <span class="bonus-name">双榜影片</span>
                    <span class="bonus-desc">同时在 JavDB 和 JavLibrary</span>
                  </div>
                  <el-input-number v-model="config.weight_dual_chart" :min="0" :max="50" size="small" />
                </div>
                <div class="bonus-item">
                  <div class="bonus-icon single">
                    <el-icon><Trophy /></el-icon>
                  </div>
                  <div class="bonus-info">
                    <span class="bonus-name">单榜影片</span>
                    <span class="bonus-desc">仅在其中一个榜单</span>
                  </div>
                  <el-input-number v-model="config.weight_single_chart" :min="0" :max="50" size="small" />
                </div>
                <div class="bonus-item">
                  <div class="bonus-icon year">
                    <el-icon><Calendar /></el-icon>
                  </div>
                  <div class="bonus-info">
                    <span class="bonus-name">年度榜</span>
                    <span class="bonus-desc">进入年度 TOP 榜单</span>
                  </div>
                  <el-input-number v-model="config.weight_year_chart" :min="0" :max="50" size="small" />
                </div>
              </div>
            </div>

            <!-- 其他加成 -->
            <div class="weight-card">
              <div class="weight-card-header">
                <span class="weight-badge other">其他</span>
                <span class="weight-card-name">其他加成</span>
              </div>
              <div class="other-items">
                <div class="other-item">
                  <span class="other-label">多位演员</span>
                  <el-input-number v-model="config.weight_multi_actor" :min="0" :max="20" size="small" />
                </div>
                <div class="other-item">
                  <span class="other-label">演员有 JavBus ID</span>
                  <el-input-number v-model="config.weight_javbus_id" :min="0" :max="30" size="small" />
                </div>
              </div>
            </div>
          </div>

          <div class="config-actions">
            <el-button type="primary" size="large" @click="saveConfig">
              <el-icon><Check /></el-icon>
              保存权重配置
            </el-button>
            <el-button size="large" @click="recalculateWeightedScores" :loading="recalculating">
              <el-icon><Refresh /></el-icon>
              重新计算加权分
            </el-button>
          </div>
        </section>

        <!-- 数据管理 -->
        <section v-show="activeSection === 'data'" class="content-section">
          <div class="section-hero">
            <div class="hero-icon" style="background: linear-gradient(135deg, #B8A9C9, #A899B9);">
              <el-icon :size="28" color="#fff"><FolderOpened /></el-icon>
            </div>
            <div class="hero-text">
              <h2>数据管理</h2>
              <p>查看数据库统计，导入导出数据，管理榜单</p>
            </div>
          </div>

          <!-- 统计概览 -->
          <div class="stats-row">
            <div class="stat-ring-card">
              <div class="ring-chart">
                <svg viewBox="0 0 100 100" class="ring-svg">
                  <circle cx="50" cy="50" r="40" fill="none" stroke="var(--bg-tertiary)" stroke-width="8"/>
                  <circle
                    cx="50" cy="50" r="40"
                    fill="none"
                    stroke="url(#ringGradient)"
                    stroke-width="8"
                    stroke-linecap="round"
                    :stroke-dasharray="`${ringFill} 252`"
                    stroke-dashoffset="63"
                    transform="rotate(-90 50 50)"
                  />
                  <defs>
                    <linearGradient id="ringGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stop-color="#E8A598"/>
                      <stop offset="100%" stop-color="#D4A574"/>
                    </linearGradient>
                  </defs>
                </svg>
                <div class="ring-center">
                  <span class="ring-value">{{ stats.total_movies || 0 }}</span>
                  <span class="ring-label">影片</span>
                </div>
              </div>
              <div class="ring-legend">
                <div class="legend-item">
                  <span class="legend-dot" style="background: var(--accent-green)"></span>
                  <span>已入库</span>
                </div>
                <div class="legend-item">
                  <span class="legend-dot" style="background: #E8A598"></span>
                  <span>缺失</span>
                </div>
              </div>
            </div>

            <div class="stat-mini-grid">
              <div class="stat-mini">
                <el-icon size="20" color="var(--accent-gold)"><Star /></el-icon>
                <div class="stat-mini-info">
                  <span class="stat-mini-value">{{ stats.avg_score?.toFixed(1) || '-' }}</span>
                  <span class="stat-mini-label">平均评分</span>
                </div>
              </div>
              <div class="stat-mini">
                <el-icon size="20" color="var(--accent-blue)"><User /></el-icon>
                <div class="stat-mini-info">
                  <span class="stat-mini-value">{{ stats.total_actors || 0 }}</span>
                  <span class="stat-mini-label">演员数</span>
                </div>
              </div>
              <div class="stat-mini">
                <el-icon size="20" color="var(--accent-purple)"><StarFilled /></el-icon>
                <div class="stat-mini-info">
                  <span class="stat-mini-value">{{ stats.followed_actors || 0 }}</span>
                  <span class="stat-mini-label">已关注</span>
                </div>
              </div>
              <div class="stat-mini">
                <el-icon size="20" color="var(--accent-red)"><List /></el-icon>
                <div class="stat-mini-info">
                  <span class="stat-mini-value">{{ stats.pending_todos || 0 }}</span>
                  <span class="stat-mini-label">待看</span>
                </div>
              </div>
            </div>
          </div>

          <!-- JavLibrary 导入 -->
          <div class="config-card">
            <h3 class="card-section-title">JavLibrary 数据导入</h3>
            <div class="csv-config">
              <el-input
                v-model="config.javlibrary_csv_path"
                placeholder="javlibrary_bestrated_2026-04-02T14-40-47.csv"
                size="large"
              >
                <template #prefix><el-icon><Document /></el-icon></template>
              </el-input>
              <el-button size="large" @click="testCsvPath">
                <el-icon><CircleCheckFilled /></el-icon>
                测试路径
              </el-button>
              <el-button type="primary" size="large" @click="saveConfig">
                <el-icon><Check /></el-icon>
                保存
              </el-button>
            </div>
            <p class="form-hint">填写 JavLibrary 榜单 CSV 文件路径，用于导入 TOP500 榜单数据</p>
          </div>

          <!-- 榜单管理 -->
          <div class="config-card">
            <h3 class="card-section-title">自定义榜单</h3>
            <div class="chart-list">
              <el-tag
                v-for="chart in charts"
                :key="chart.id"
                size="large"
                type="info"
                class="chart-chip"
              >
                {{ chart.display_name }}
                <span v-if="chart.year" class="chart-year-tag">{{ chart.year }}</span>
              </el-tag>
              <span v-if="charts.length === 0" class="empty-hint">暂无自定义榜单</span>
            </div>
            <div class="add-chart">
              <el-select v-model="selectedChartType" placeholder="选择预设榜单" clearable size="large" class="chart-select">
                <el-option v-for="c in availableCharts" :key="c.name" :label="c.name" :value="c.name" />
              </el-select>
              <el-input v-model="newChartName" placeholder="或输入自定义名称" size="large" class="chart-input" />
              <el-input-number v-model="newChartYear" :min="2000" :max="2099" size="large" placeholder="年份" />
              <el-button
                type="primary"
                size="large"
                @click="addChart"
                :disabled="!selectedChartType && !newChartName"
              >
                <el-icon><Plus /></el-icon>
                添加
              </el-button>
            </div>
          </div>

          <!-- 批量操作 -->
          <div class="config-card">
            <h3 class="card-section-title">批量操作</h3>
            <div class="batch-actions">
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
        </section>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Monitor,
  Link,
  Key,
  Check,
  Refresh,
  Plus,
  Guide,
  Connection,
  ArrowRight,
  Trophy,
  Calendar,
  DataLine,
  FolderOpened,
  Document,
  CircleCheckFilled,
  VideoCamera,
  Star,
  StarFilled,
  User,
  List
} from '@element-plus/icons-vue'
import { statsApi, configApi, chartManageApi, chartsApi, tasksApi, actorsApi } from '../api'

const activeSection = ref('connection')
const syncing = ref(false)
const recalculating = ref(false)
const fetchingAllReleases = ref(false)

const delayRange = ref([3, 6])

const navItems = [
  { key: 'connection', title: 'Jellyfin 连接', desc: '服务器和 API 配置', icon: Monitor, bgColor: 'linear-gradient(135deg, #8FB8CD, #7AA8BD)' },
  { key: 'datasource', title: '数据源配置', desc: '域名和请求策略', icon: Guide, bgColor: 'linear-gradient(135deg, #D4A574, #C49464)' },
  { key: 'proxy', title: '系统代理', desc: 'HTTP/SOCKS5 代理', icon: Connection, bgColor: 'linear-gradient(135deg, #6B8E9F, #5A7D8E)' },
  { key: 'scoring', title: '评分权重', desc: '加权分计算规则', icon: DataLine, bgColor: 'linear-gradient(135deg, #8FB996, #7AA882)' },
  { key: 'data', title: '数据管理', desc: '统计、导入、榜单', icon: FolderOpened, bgColor: 'linear-gradient(135deg, #B8A9C9, #A899B9)' },
]

const config = ref({
  jellyfin_url: '',
  jellyfin_api_key: '',
  javdb_domains: ['javdb.com'],
  javbus_domains: ['javbus.com'],
  javlibrary_csv_path: '',
  request_min_delay: 3,
  request_max_delay: 6,
  request_timeout: 30,
  enable_system_proxy: false,
  system_proxy_url: '',
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

const stats = ref({ total_movies: 0, total_actors: 0, followed_actors: 0, avg_score: 0, pending_todos: 0 })
const charts = ref([])
const availableCharts = ref([])
const selectedChartType = ref('')
const newChartName = ref('')
const newChartYear = ref(null)
const newJavdbDomain = ref('')
const newJavbusDomain = ref('')

const ringFill = computed(() => {
  // 简单计算：假设 70% 已入库
  return 176
})

const fetchConfig = async () => {
  try {
    const data = await configApi.get()
    config.value = data
    delayRange.value = [data.request_min_delay || 3, data.request_max_delay || 6]
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
  // 同步延迟滑块值
  config.value.request_min_delay = delayRange.value[0]
  config.value.request_max_delay = delayRange.value[1]
  try {
    await configApi.update(config.value)
    ElMessage.success('配置已保存')
  } catch (e) {
    ElMessage.error('保存配置失败')
  }
}

const syncFromJellyfin = async () => {
  syncing.value = true
  try {
    await tasksApi.sync()
    ElMessage.success('同步任务已启动')
  } catch (e) {
    ElMessage.error('同步失败')
  } finally {
    syncing.value = false
  }
}

const refreshStats = async () => {
  await fetchStats()
  ElMessage.success('统计已刷新')
}

const testCsvPath = async () => {
  if (!config.value.javlibrary_csv_path) {
    ElMessage.warning('请先填写 CSV 文件路径')
    return
  }
  try {
    const result = await configApi.testCsvPath(config.value.javlibrary_csv_path)
    if (result.valid) {
      ElMessage.success(`路径有效，包含 ${result.count} 条记录`)
    } else {
      ElMessage.error(result.error || '路径无效')
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '测试失败')
  }
}

const recalculateWeightedScores = async () => {
  recalculating.value = true
  try {
    const result = await tasksApi.recalculateWeightedScores()
    ElMessage.success(`加权分已更新，共更新 ${result.updated} 部影片`)
  } catch (e) {
    ElMessage.error('更新加权分失败')
  } finally {
    recalculating.value = false
  }
}

const fetchAllReleases = async () => {
  fetchingAllReleases.value = true
  try {
    const result = await actorsApi.fetchAllReleases()
    if (result.status === 'started') {
      ElMessage.success('批量获取任务已启动')
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
  max-width: 1280px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 32px;
}

.page-title {
  font-size: 30px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.5px;
  margin-bottom: 6px;
}

.page-subtitle {
  font-size: 15px;
  color: var(--text-muted);
}

/* 布局 */
.settings-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 28px;
  align-items: start;
}

/* 左侧导航 */
.settings-nav {
  position: sticky;
  top: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.nav-list {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  overflow: hidden;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  text-align: left;
  width: 100%;
  transition: all 0.2s ease;
  position: relative;
}

.nav-item:hover {
  background: var(--bg-secondary);
}

.nav-item.active {
  background: linear-gradient(135deg, #F5D5CE30, #E8A59820);
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 60%;
  background: var(--primary-gradient);
  border-radius: 0 2px 2px 0;
}

.nav-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.nav-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.nav-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.nav-desc {
  font-size: 12px;
  color: var(--text-muted);
}

.nav-arrow {
  color: var(--text-muted);
  flex-shrink: 0;
  transition: transform 0.2s ease;
}

.nav-item:hover .nav-arrow,
.nav-item.active .nav-arrow {
  transform: translateX(3px);
  color: var(--primary-color);
}

/* 状态卡片 */
.nav-status {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  padding: 18px;
}

.status-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 14px;
}

.status-items {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--text-secondary);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-dot.online {
  background: var(--accent-green);
}

.status-dot.offline {
  background: var(--text-muted);
}

/* 内容区 */
.settings-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.content-section {
  animation: fadeIn 0.25s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Section Hero */
.section-hero {
  display: flex;
  align-items: center;
  gap: 18px;
  margin-bottom: 20px;
}

.hero-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.hero-text h2 {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.hero-text p {
  font-size: 14px;
  color: var(--text-muted);
}

/* Config Card */
.config-card {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  padding: 28px;
  margin-bottom: 16px;
}

.card-section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 20px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--border-light);
}

.config-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.config-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.config-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--border-light);
}

/* 域名管理 */
.domain-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.domain-block {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.domain-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.domain-brand {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.domain-count {
  font-size: 12px;
  color: var(--text-muted);
}

.domain-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  min-height: 40px;
  padding: 10px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.domain-chip {
  margin: 0;
}

.domain-add {
  margin-top: 4px;
}

/* 请求策略 */
.strategy-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
}

.strategy-item {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.strategy-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.strategy-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--primary-color);
  font-variant-numeric: tabular-nums;
}

.strategy-hint {
  font-size: 12px;
  color: var(--text-muted);
}

/* 代理 */
.proxy-toggle {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.toggle-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  display: block;
  margin-bottom: 4px;
}

.toggle-desc {
  font-size: 13px;
  color: var(--text-muted);
}

/* 权重可视化 */
.weight-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.weight-card {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  padding: 22px;
  min-height: 200px;
}

.weight-base {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  text-align: center;
  min-height: 200px;
}

.weight-big-value {
  font-size: 64px;
  font-weight: 700;
  color: var(--primary-color);
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.weight-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.weight-badge {
  padding: 4px 10px;
  background: var(--primary-light);
  color: var(--primary-dark);
  border-radius: 20px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
}

.weight-badge.javdb {
  background: var(--accent-gold-light);
  color: var(--accent-gold);
}

.weight-badge.chart {
  background: var(--accent-blue-light);
  color: var(--accent-blue);
}

.weight-badge.other {
  background: var(--accent-purple-light);
  color: var(--accent-purple);
}

.weight-card-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

/* JavDB 评分加成 */
.javdb-ranges {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
}

.javdb-range-row {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.javdb-range-label {
  font-size: 13px;
  font-weight: 600;
  min-width: 55px;
  flex-shrink: 0;
}

.javdb-range-label.high { color: var(--accent-green); }
.javdb-range-label.mid { color: var(--accent-gold); }
.javdb-range-label.low { color: var(--accent-red); }
.javdb-range-label.very-low { color: var(--text-muted); }

.javdb-bar-track {
  flex: 1;
  height: 8px;
  background: var(--bg-tertiary);
  border-radius: 4px;
  overflow: hidden;
  min-width: 80px;
}

.javdb-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.javdb-bar-fill.high { background: linear-gradient(90deg, var(--accent-green), #6FCF7F); }
.javdb-bar-fill.mid { background: linear-gradient(90deg, var(--accent-gold), #F2994A); }
.javdb-bar-fill.low { background: linear-gradient(90deg, var(--accent-red), #EB5757); opacity: 0.7; }
.javdb-bar-fill.very-low { background: var(--text-muted); opacity: 0.5; }

.javdb-ranges :deep(.el-input-number) {
  width: 80px;
  flex-shrink: 0;
}

.javdb-ranges :deep(.el-input-number .el-input__inner) {
  text-align: center;
  padding-left: 8px;
  padding-right: 8px;
}

/* 榜单加成卡片 */
.chart-bonus-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.bonus-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 14px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.bonus-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.bonus-icon.dual { background: linear-gradient(135deg, #8FB996, #7AA882); }
.bonus-icon.single { background: linear-gradient(135deg, #8FB8CD, #7AA8BD); }
.bonus-icon.year { background: linear-gradient(135deg, #D4A574, #C49464); }

.bonus-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.bonus-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.bonus-desc {
  font-size: 11px;
  color: var(--text-muted);
}

/* 其他加成 */
.other-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.other-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.other-label {
  font-size: 14px;
  color: var(--text-primary);
}

/* 统计数据 */
.stats-row {
  display: grid;
  grid-template-columns: 180px 1fr;
  gap: 20px;
  margin-bottom: 20px;
  align-items: stretch;
}

.stat-ring-card {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  width: 100%;
  min-height: 200px;
}

.ring-chart {
  position: relative;
  width: 120px;
  height: 120px;
}

.ring-svg {
  width: 100%;
  height: 100%;
  transform: rotate(0deg);
}

.ring-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.ring-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.ring-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
}

.ring-legend {
  display: flex;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.stat-mini-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: 12px;
  width: 100%;
  min-height: 200px;
}

.stat-mini {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 18px;
  display: flex;
  align-items: center;
  gap: 14px;
  min-height: 80px;
}

.stat-mini-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-mini-value {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
  line-height: 1;
}

.stat-mini-label {
  font-size: 12px;
  color: var(--text-muted);
}

/* CSV 配置 */
.csv-config {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.csv-config .el-input {
  flex: 1;
}

/* 榜单列表 */
.chart-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  min-height: 48px;
  padding: 14px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  margin-bottom: 16px;
}

.chart-chip {
  margin: 0;
}

.chart-year-tag {
  margin-left: 6px;
  padding: 2px 6px;
  background: var(--bg-tertiary);
  border-radius: 4px;
  font-size: 10px;
  color: var(--text-muted);
}

.empty-hint {
  font-size: 13px;
  color: var(--text-muted);
  padding: 8px;
}

.add-chart {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.chart-select {
  width: 200px;
}

.chart-input {
  width: 160px;
}

/* 批量操作 */
.batch-actions {
  display: flex;
  gap: 12px;
}

/* 响应式 */
@media (max-width: 1024px) {
  .settings-layout {
    grid-template-columns: 1fr;
  }

  .settings-nav {
    position: static;
  }

  .nav-list {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 8px;
  }

  .nav-item {
    flex: 1;
    min-width: 160px;
  }

  .nav-item.active::before {
    display: none;
  }

  .nav-desc {
    display: none;
  }

  .nav-arrow {
    display: none;
  }

  .nav-status {
    display: none;
  }

  .config-row {
    grid-template-columns: 1fr;
  }

  .domain-grid {
    grid-template-columns: 1fr;
  }

  .strategy-grid {
    grid-template-columns: 1fr;
  }

  .weight-grid {
    grid-template-columns: 1fr;
  }

  .weight-base {
    flex-direction: row;
    justify-content: space-between;
    text-align: left;
  }

  .stats-row {
    grid-template-columns: 1fr;
  }

  .stat-ring-card {
    flex-direction: row;
    justify-content: space-around;
    min-height: auto;
    padding: 20px;
  }

  .stat-mini-grid {
    min-height: auto;
    grid-template-rows: repeat(4, auto);
  }
}

@media (max-width: 640px) {
  .csv-config {
    flex-direction: column;
    align-items: stretch;
  }

  .add-chart {
    flex-wrap: wrap;
  }

  .chart-select,
  .chart-input {
    width: 100%;
  }

  .batch-actions {
    flex-direction: column;
  }

  .config-actions {
    flex-direction: column;
  }

  .config-actions .el-button {
    width: 100%;
  }
}
</style>
