# Claude 项目约束规范

## 项目概述

- **项目名称**: Jellyfin JAV 电影导出管理系统
- **项目类型**: Flask Web 应用 + SQLite 数据库
- **核心功能**: 从 Jellyfin 同步电影数据，展示榜单信息，管理电影库

## 技术栈

- **后端**: Python 3.12, Flask
- **数据库**: SQLite (data.db)
- **前端**: HTML + CSS + Vanilla JavaScript
- **依赖**: requests, flask

## 目录结构

```
.
├── app.py              # 主应用入口 (Flask)
├── config.py           # 配置文件 (Jellyfin URL/API Key)
├── data.db             # SQLite 数据库
├── templates/
│   └── index.html      # 前端页面
├── static/
│   └── style.css       # 样式文件
├── venv/               # Python 虚拟环境
├── *.csv               # 榜单数据文件
└── claude.md           # 本规范文件
```

## 数据库结构

### movies 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| code | TEXT | 影片番号 (如 ABC-123) |
| title | TEXT | 标题 |
| year | 生产年份 |
| actors | TEXT | 演员列表 (逗号分隔) |
| date_added | TEXT | 添加日期 |
| jellyfin_id | TEXT | Jellyfin 中的 ID |

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 首页 |
| `/api/movies` | GET | 获取电影列表 (分页、搜索) |
| `/api/list/<list_name>` | GET | 获取指定榜单电影 |
| `/api/sync` | POST | 同步 Jellyfin 数据 |
| `/api/stats` | GET | 获取统计信息 |
| `/api/actors` | GET | 获取演员列表 |
| `/api/actor/<name>` | GET | 获取指定演员的电影 |
| `/api/poster/<id>` | GET | 获取 Jellyfin 海报 |

## 开发规范

### 代码风格

- 使用 ruff 进行代码检查
- Python 类型提示可选但推荐
- 避免过度封装，保持简单

### 前端规范

- 使用原生 JavaScript，不引入框架
- CSS 使用现代布局 (Flexbox/Grid)
- 遵循现有样式风格 (深色主题)

### 安全规范

- **敏感信息**: API Key 存储在 `config.py`，不提交到版本控制
- **数据库**: 使用 SQLite，避免 SQL 注入 (使用参数化查询)
- **外部请求**: 设置超时 (10-30秒)

### Git 规范

- **不提交**: `venv/`, `data.db`, `config.py`, `*.csv`, `.ruff_cache/`, `__pycache__/`, `.DS_Store`
- **提交**: `app.py`, `templates/`, `static/`, `claude.md`

## 影片榜单配置

在 `app.py` 中定义 (`CSV_FILES` 字典):

```python
CSV_FILES = {
    "JavDB TOP250": "JAVDB TOP250.csv",
    "JavDB 2025 TOP250": "JAVDB 2025TOP250.csv",
    "JavDB 2024 TOP250": "JAVDB 2024TOP250.csv",
    "JavDB 2023 TOP250": "JAVDB 2023TOP250.csv",
    "JavLibray TOP500": "JAVLIBTOP500.csv",
}
```

## 运行方式

```bash
# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 启动应用
python app.py

# 访问 http://localhost:5002
```

## 配置修改

修改 `config.py` 中的 Jellyfin 连接信息:

```python
JELLYFIN_URL = "http://your-jellyfin:8096/"
JELLYFIN_API_KEY = "your-api-key"
```

## 注意事项

1. 影片番号提取规则: 匹配 `^[A-Z]+-\d+` 格式
2. CSV 文件编码: UTF-8，忽略解码错误
3. 图片代理: 通过 `/api/poster/` 端点转发 Jellyfin 图片
4. 启动时自动同步 Jellyfin 数据

---

本文档定义了项目的开发约束和规范，所有修改应遵循此文件。
