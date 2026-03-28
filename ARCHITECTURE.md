# JAV Manager 架构设计

## 1. 设计理念

**轻量化优先** - 这是一个个人工具，运行在 NAS 上，不需要 Docker/Kubernetes 等重量级基础设施。

## 2. 实际实现的架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Flask (单进程应用)                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────────────────────────────────────────────┐  │
│   │              Flask App (:5000)                       │  │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │  │
│   │  │  API路由  │  │ APScheduler│  │   静态文件托管   │ │  │
│   │  │  /api/*  │  │  定时任务  │  │  / (Vue 构建产物) │ │  │
│   │  └──────────┘  └──────────┘  └──────────────────────┘ │  │
│   └───────────────────────────────────────────────────────┘  │
│                           │                                  │
│   ┌───────────────────────▼───────────────────────────────┐  │
│   │            SQLite (data.db) 单文件                    │  │
│   │  movies · actors · charts · reports · todos          │  │
│   └───────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘

前端: Vue 3 + Vite 开发服务器 (:5173) 或构建后静态文件
```

## 3. 技术选型

| 组件 | 选择 | 理由 |
|------|------|------|
| **后端框架** | Flask | 轻量、成熟、够用 |
| **数据库** | SQLite | 单文件、零配置、备份简单 |
| **ORM** | SQLAlchemy 2.0 | 类型安全、迁移管理 |
| **定时任务** | APScheduler | 内置、无需额外服务 |
| **爬虫** | httpx + BeautifulSoup | 比 Scrapy 轻量、够用 |
| **前端框架** | Vue 3 | 现代化、组件化 |
| **UI 框架** | Element Plus | 组件丰富、主题定制 |
| **构建工具** | Vite | 快速开发体验 |

## 4. 目录结构

```
jav-manager/
├── backend/
│   ├── app.py                 # Flask 入口
│   ├── config.py              # 配置文件
│   ├── init_db.py             # 数据库初始化脚本
│   ├── requirements.txt        # Python 依赖
│   ├── data.db               # SQLite 数据库（运行时生成）
│   ├── models/
│   │   └── database.py        # SQLAlchemy 模型（7张表）
│   └── services/
│       ├── jellyfin.py        # Jellyfin 同步
│       ├── javdb_scraper.py   # JavDB 爬虫
│       ├── chart_scraper.py   # 榜单抓取
│       ├── report_generator.py # 报告生成
│       └── score_updater.py   # 评分更新
├── frontend/
│   ├── src/
│   │   ├── main.js           # Vue 入口
│   │   ├── App.vue           # 根组件
│   │   ├── api/index.js      # API 封装
│   │   ├── router/index.js   # 路由配置
│   │   ├── views/            # 页面组件
│   │   │   ├── Library.vue      # 影片库
│   │   │   ├── ChartList.vue    # 榜单中心
│   │   │   ├── ChartDetail.vue  # 榜单详情
│   │   │   ├── GapAnalysis.vue  # 缺口分析
│   │   │   ├── Discover.vue     # 发现/报告
│   │   │   ├── TodoList.vue     # 待看清单
│   │   │   ├── ActorList.vue    # 演员列表
│   │   │   ├── ActorDetail.vue  # 演员详情
│   │   │   └── Settings.vue      # 设置
│   │   ├── components/
│   │   │   └── MovieDetailModal.vue # 影片详情弹窗
│   │   └── styles/
│   │       └── global.css     # 全局样式
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── start.py                   # 一键启动脚本
└── README.md
```

## 5. 数据库设计

### 5.1 表结构

| 表名 | 说明 | 主要字段 |
|------|------|----------|
| movies | 影片 | code, title, actors, javdb_score, weighted_score |
| actors | 演员 | name, is_followed, movie_count |
| charts | 榜单定义 | name, display_name, source, total_count |
| chart_items | 榜单影片 | chart_id, rank, code, score |
| reports | 报告 | type, title, data(JSON), is_read |
| todo_items | 待看清单 | code, source, status |
| score_history | 评分历史 | movie_id, prev_score, curr_score |
| task_logs | 任务日志 | task_type, status, progress |

### 5.2 关系图

```
movies (1) ─── (N) todo_items
    │
    └── (1) ─── (N) chart_items
                    │
                    └── (N) ─── (1) charts

actors (1) ─── (N) movies
    │
    └── (1) ─── (N) score_history
```

## 6. API 设计

### 6.1 REST API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| /api/movies | GET | 影片列表（分页/筛选/排序） |
| /api/movies/:code | GET | 影片详情 |
| /api/movies/:code/refresh | POST | 刷新评分 |
| /api/actors | GET | 演员列表 |
| /api/actors/:name | GET | 演员详情 |
| /api/actors/:id/follow | PUT | 切换关注 |
| /api/charts | GET | 榜单列表 |
| /api/charts/:name | GET | 榜单详情 |
| /api/charts/:name/gaps | GET | 缺口分析 |
| /api/charts/:name/refresh | POST | 更新榜单 |
| /api/reports/latest | GET | 最新报告 |
| /api/reports/generate | POST | 生成报告 |
| /api/todos | GET/POST | 待看清单 |
| /api/todos/:id/status | PUT | 更新状态 |
| /api/tasks/sync | POST | 触发同步 |
| /api/stats | GET | 统计数据 |

## 7. 前端路由

```
/                   → 重定向到 /library
/library            → 影片库（网格/列表视图）
/charts             → 榜单中心
/charts/:name      → 榜单详情
/charts/:name/gaps → 缺口分析
/discover           → 发现（报告中心）
/todo               → 待看清单
/actors             → 演员列表
/actors/:name       → 演员详情
/settings           → 设置页面
```

## 8. 定时任务

| 任务 | 触发时间 | 功能 |
|------|----------|------|
| 周报生成 | 每周一 09:00 | 生成关注演员新片报告 |
| 月报生成 | 每月1日 09:00 | 生成分数上升旧片报告 |
| 年报生成 | 1月和7月1日 09:00 | 生成榜单缺口报告 |

## 9. 开发流程

```bash
# 1. 初始化数据库
cd backend
python init_db.py

# 2. 开发模式启动
# 终端1: 后端
python app.py

# 终端2: 前端
cd frontend
npm run dev

# 3. 生产构建
cd frontend
npm run build  # 输出到 backend/static/
```

## 10. 与原设计对比

| 维度 | 原设计（已废弃） | 实际实现 |
|------|-----------------|----------|
| 架构 | 微服务 + Docker | 单体应用 |
| 数据库 | PostgreSQL | SQLite |
| 任务队列 | Celery + Redis | APScheduler（内存） |
| 前端构建 | 独立运行 | Vite 开发服务器 或 Flask 托管 |
| 部署 | Docker Compose / K8s | 纯 Python + npm |
| 复杂度 | 高 | 低 |

## 11. 性能考虑

- SQLite 适合单用户，< 10万影片无压力
- 爬虫使用线程池，不阻塞主请求
- 前端图片懒加载
- 分页避免一次加载过多数据

## 12. 扩展可能性

如果未来需要更强的能力：
- SQLite → PostgreSQL（SQLAlchemy 支持）
- APScheduler → Celery + Redis（任务持久化）
- 单体 → 微服务（按需拆分爬虫服务）

---

*架构文档版本: 2.0*
*更新: 2026-03-28*
