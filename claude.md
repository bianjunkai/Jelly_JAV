# Claude 项目约束规范

## 项目概述

- **项目名称**: Jellyfin JAV 影片管理系统
- **项目类型**: Flask Web 应用 + Vue 3 前端
- **核心功能**: 从 Jellyfin 同步电影数据，展示榜单信息，管理待看清单

## 当前版本

**活跃开发**: `jav-manager/` (v2.0)
**旧版本**: `legacy/` (v1.0) - 已归档

## 技术栈

### jav-manager/ (新版本)
- **后端**: Python 3.10+, Flask, SQLAlchemy, SQLite
- **前端**: Vue 3, Element Plus, Vite
- **爬虫**: httpx, BeautifulSoup

### legacy/ (旧版本)
- **后端**: Flask 单文件
- **前端**: Jinja2 模板
- **爬虫**: curl_cffi

## 目录结构

```
.
├── jav-manager/          # ✨ 新版本 v2.0 (当前活跃开发)
│   ├── backend/
│   │   ├── app.py        # Flask 入口
│   │   ├── config.py     # 配置
│   │   ├── init_db.py    # 数据库初始化
│   │   ├── requirements.txt
│   │   ├── models/       # 数据模型
│   │   └── services/      # 业务逻辑
│   ├── frontend/
│   │   ├── src/          # Vue 源码
│   │   │   ├── views/     # 页面组件
│   │   │   ├── components/# 复用组件
│   │   │   ├── api/      # API 封装
│   │   │   └── router/   # 路由
│   │   └── package.json
│   └── start.py           # 启动脚本
│
├── legacy/                # 📦 旧版本 v1.0 (已归档)
│   ├── app.py           # Flask 单文件应用
│   ├── scrapers/        # 爬虫模块
│   ├── templates/       # Jinja2 模板
│   ├── static/          # 静态文件
│   ├── *.csv            # 榜单数据
│   └── data.db         # SQLite 数据库
│
├── ARCHITECTURE.md      # 架构设计
├── DESIGN.md            # 技术设计
└── PRD.md              # 需求文档
```

## 新版本运行方式

```bash
# 安装后端依赖
cd jav-manager/backend
pip install -r requirements.txt

# 初始化数据库
python init_db.py

# 启动后端
python app.py

# 新终端 - 启动前端
cd jav-manager/frontend
npm install
npm run dev

# 访问 http://localhost:5173
```

## 配置修改

编辑 `jav-manager/backend/config.py`:

```python
JELLYFIN_URL = "http://your-jellyfin:8096/"
JELLYFIN_API_KEY = "your-api-key"
```

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/movies` | GET | 获取电影列表 |
| `/api/actors` | GET | 获取演员列表 |
| `/api/charts` | GET | 获取榜单列表 |
| `/api/reports/latest` | GET | 获取最新报告 |
| `/api/todos` | GET/POST | 待看清单 |
| `/api/tasks/sync` | POST | 同步 Jellyfin |

## 数据库结构

### movies 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| code | TEXT | 影片番号 (如 ABC-123) |
| title | TEXT | 标题 |
| actors | TEXT | 演员列表 (逗号分隔) |
| javdb_score | FLOAT | JavDB 评分 |
| weighted_score | INTEGER | 加权分 |
| jellyfin_id | TEXT | Jellyfin 中的 ID |

## Git 规范

- **不提交**: `venv/`, `data.db`, `config.py`, `*.csv`, `node_modules/`, `dist/`
- **提交**: `jav-manager/`, `ARCHITECTURE.md`, `DESIGN.md`, `PRD.md`, `claude.md`

## 注意事项

1. 影片番号提取: 匹配 `^[A-Z]+-\d+` 格式
2. CSV 文件编码: UTF-8
3. 启动时自动初始化数据库和榜单
4. 爬虫有请求延迟限制，避免被封

---

本文档定义了项目的开发约束和规范，所有修改应遵循此文件。
