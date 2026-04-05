# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

**项目名称**: Jellyfin JAV 影片管理系统
**项目类型**: Flask Web 应用 + Vue 3 前端
**核心功能**: 从 Jellyfin 同步电影数据，展示榜单信息（JavDB、JavLibrary），管理待看清单

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 后端框架 | Flask + SQLAlchemy 2.0 | 单进程应用 |
| 数据库 | SQLite | 单文件 `data.db` |
| 前端框架 | Vue 3 + Element Plus + Vite | 组件化开发 |
| 爬虫 | httpx + BeautifulSoup |榜单数据抓取 |
| 定时任务 | APScheduler | 内存中运行 |

## 环境配置

**Python 环境**: 使用 uv 管理的虚拟环境
- 路径: `jav-manager/backend/.venv`
- Python 运行: `jav-manager/backend/.venv/Scripts/python.exe`
- 安装包: `cd jav-manager/backend && uv pip install <package> --python .venv`

## 目录结构

```
jav-manager/
├── backend/
│   ├── app.py              # Flask 入口（所有 API 路由在此）
│   ├── config.py           # 配置文件
│   ├── init_db.py          # 数据库初始化
│   ├── requirements.txt    # Python 依赖
│   ├── config.json         # 运行时配置（自动生成）
│   ├── data.db            # SQLite 数据库（运行时生成）
│   ├── models/
│   │   └── database.py     # SQLAlchemy 模型（7张表）
│   └── services/
│       ├── chart_scraper.py   # 榜单爬虫（JavDB）
│       ├── javdb_scraper.py  # JavDB 单片评分
│       ├── jellyfin.py        # Jellyfin 同步
│       ├── report_generator.py # 报告生成
│       └── score_updater.py   # 批量评分更新
├── frontend/
│   ├── src/
│   │   ├── main.js         # Vue 入口
│   │   ├── App.vue         # 根组件
│   │   ├── api/index.js    # API 封装
│   │   ├── router/index.js # 路由配置
│   │   ├── views/          # 页面组件
│   │   │   ├── Library.vue     # 影片库
│   │   │   ├── ChartList.vue   # 榜单中心
│   │   │   ├── ChartDetail.vue # 榜单详情
│   │   │   ├── GapAnalysis.vue # 缺口分析
│   │   │   ├── Discover.vue    # 发现/报告
│   │   │   ├── TodoList.vue   # 待看清单
│   │   │   ├── ActorList.vue   # 演员列表
│   │   │   ├── ActorDetail.vue # 演员详情
│   │   │   └── Settings.vue    # 设置
│   │   └── components/
│   │       └── MovieDetailModal.vue
│   └── package.json
└── start.py                 # 一键启动脚本

legacy/                      # v1.0 已归档
```

## 常用命令

```bash
# 后端依赖安装
cd jav-manager/backend
uv pip install -r requirements.txt --python .venv

# 数据库初始化
uv pip install -r requirements.txt --python .venv
python init_db.py           # 初始化
python init_db.py --reset   # 重建数据库

# 后端运行
python app.py

# 前端运行
cd jav-manager/frontend
npm install
npm run dev

# 一键启动（前后端同时）
python start.py
```

## API 架构

Flask 应用托管所有 API 和静态文件：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/movies` | GET | 影片列表（分页/筛选/排序） |
| `/api/movies/:code` | GET | 影片详情 |
| `/api/movies/:code/refresh` | POST | 刷新评分 |
| `/api/actors` | GET | 演员列表 |
| `/api/actors/:name` | GET | 演员详情 |
| `/api/charts` | GET | 榜单列表 |
| `/api/charts/:name` | GET | 榜单详情 |
| `/api/charts/:name/gaps` | GET | 缺口分析 |
| `/api/charts/:name/refresh` | POST | 更新榜单 |
| `/api/reports/latest` | GET | 最新报告 |
| `/api/todos` | GET/POST | 待看清单 |
| `/api/tasks/sync` | POST | Jellyfin 同步 |
| `/api/config` | GET/PUT | 配置管理 |

**前端开发服务器**: `:5173` → 代理到 `:5000`（Flask）

## 数据库模型

核心模型位于 `models/database.py`：

- **Movie** - 影片（code 唯一索引，actors 逗号分隔存储）
- **Actor** - 演员（is_followed 关注状态）
- **Chart** - 榜单定义（JavDB TOP250、JavLibrary TOP500）
- **ChartItem** - 榜单影片（rank 排名，关联 Movie）
- **Report** - 报告（weekly/monthly/annual）
- **TodoItem** - 待看清单
- **ScoreHistory** - 评分历史

**榜单来源**: `source` 字段区分 `javdb` 和 `javlibrary`

## 榜单抓取

- **JavDB**: `services/chart_scraper.py` - 多域名轮换，支持 TOP250 和年度榜
- **JavLibrary**: `services/chart_scraper.py` - `source='javlibrary'`，需 Cloudflare 绕过

**影片番号正则**: `^[A-Z]+-\d+` 格式（如 `ABC-123`）

## 定时任务

| 任务 | 触发时间 | 功能 |
|------|----------|------|
| 周报 | 每周一 09:00 | 关注演员新片 |
| 月报 | 每月1日 09:00 | 分数上升旧片 |
| 年报 | 1月和7月1日 09:00 | 榜单缺口分析 |

## 前端路由

```
/                → 重定向 /library
/library         → 影片库
/charts          → 榜单中心
/charts/:name   → 榜单详情
/charts/:name/gaps → 缺口分析
/discover        → 发现/报告
/todo            → 待看清单
/actors          → 演员列表
/actors/:name    → 演员详情
/settings        → 设置
```

## 配置

配置文件 `config.py` 支持运行时修改和持久化：

- `JELLYFIN_URL` / `JELLYFIN_API_KEY` - Jellyfin 连接
- `JAVDB_DOMAINS` / `JAVBUS_DOMAINS` - 多域名轮换
- `REQUEST_MIN_DELAY` / `REQUEST_MAX_DELAY` - 请求延迟
- `WEIGHT_*` - 加权分参数

配置变更自动保存到 `config.json`。

## Git 规范

**不提交**: `venv/`, `.venv/`, `data.db`, `config.json`, `*.csv`, `node_modules/`, `dist/`, `backend/static/`
**提交**: `jav-manager/`, `legacy/`, `ARCHITECTURE.md`, `DESIGN.md`, `PRD.md`, `claude.md`

## 注意事项

1. **番号格式**: `ABC-123` 大写字母 + 连字符 + 数字
2. **请求延迟**: 爬虫有 3-6 秒随机延迟，避免被封
3. **Cloudflare**: JavLibrary 有反爬，需使用 Scrapling 或代理绕过
4. **SQLite**: 单文件数据库，备份直接复制 `data.db`
