# Jellyfin JAV 电影管理系统

从 Jellyfin 同步 JAV 电影数据，展示榜单信息，管理电影库的 Web 应用。

## 功能特性

- **Jellyfin 同步**: 自动从 Jellyfin 同步电影数据
- **榜单管理**: 支持 JavDB、JavLibrary 等榜单
- **JavDB 评分**: 手动获取影片在 JavDB 的评分
- **权重分计算**: 根据榜单上榜情况和 JavDB 评分计算权重分
- **RSS 订阅**: 订阅演员更新，支持后台自动刷新
- **演员主页**: 查看演员信息及其所有影片

## 技术栈

- **后端**: Python 3.12, Flask
- **数据库**: SQLite
- **前端**: HTML + CSS + Vanilla JavaScript (Vue 3)
- **依赖**: requests, flask, curl_cffi

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

编辑 `config.py` 文件，配置 Jellyfin 连接信息：

```python
JELLYFIN_URL = "http://your-jellyfin:8096/"
JELLYFIN_API_KEY = "your-api-key"
```

获取 API Key 方法：Jellyfin Dashboard → API Keys → 创建 API Key

### 3. 运行

```bash
python app.py
```

访问 http://localhost:5002

## 配置说明

| 配置项 | 说明 |
|--------|------|
| JELLYFIN_URL | Jellyfin 服务器地址 |
| JELLYFIN_API_KEY | Jellyfin API Key |
| RSSHUB_URL | RSSHub 地址（可选） |
| JAVBUS_DOMAIN | JAVBus 域名 |
| RSS_UPDATE_ON_STARTUP | 启动时是否更新 RSS |

## 权重分计算规则

初始分 50 分，根据以下条件调整：

| 条件 | 分数调整 |
|------|----------|
| JavDB 评分 ≥ 4.5 | +20 |
| JavDB 评分 4.2-4.5 | +10 |
| JavDB 评分 3.9-4.2 | 0 |
| JavDB 评分 3.5-3.9 | -15 |
| JavDB 评分 < 3.5 | -25 |
| 同时上榜 JavDB + JavLibrary | +30 |
| 单独上榜 | +20 |
| 上榜年度榜单 | +10 |
| 多位演员 | +5 |
| 演员有 JAVBus ID | +15 |

## 目录结构

```
.
├── app.py              # 主应用入口
├── config.py           # 配置文件
├── data.db             # SQLite 数据库
├── requirements.txt    # Python 依赖
├── claude.md          # 开发规范
├── templates/
│   └── index.html      # 前端页面
└── static/
    └── style.css       # 样式文件
```

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 首页 |
| `/api/movies` | GET | 获取电影列表 |
| `/api/sync` | POST | 同步 Jellyfin |
| `/api/stats` | GET | 统计信息 |
| `/api/actors` | GET | 演员列表 |
| `/api/actor/<name>` | GET | 演员影片 |
| `/api/test_javdb/<code>` | GET | 获取 JavDB 评分 |

## License

MIT
