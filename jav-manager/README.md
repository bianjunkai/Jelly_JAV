# JAV Manager

个人 JAV 影片管理系统，用于管理 Jellyfin 中的影片库，支持 JavDB 评分获取、榜单追踪和待看清单管理。

## 功能特性

- 📁 **影片库管理** - 网格/列表视图，支持筛选和排序
- 🏆 **榜单中心** - JavDB TOP250、年度榜等，支持缺口分析
- ⭐ **关注演员** - 追踪关注演员的新片和分数变化
- 📝 **待看清单** - 按来源分组，支持批量操作
- 📊 **智能报告** - 周报/月报/年报，自动生成
- 🔍 **评分系统** - JavDB 评分 + 加权分计算

## 技术栈

- **后端**: Flask + SQLAlchemy + SQLite
- **前端**: Vue 3 + Element Plus + Vite
- **爬虫**: httpx + BeautifulSoup

## 快速开始

### 1. 安装依赖

**后端:**
```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

**前端:**
```bash
cd frontend
npm install
```

### 2. 配置

编辑 `backend/config.py`:

```python
JELLYFIN_URL = "http://your-jellyfin:8096/"
JELLYFIN_API_KEY = "your-api-key"
```

获取 Jellyfin API Key:
1. 登录 Jellyfin 网页端
2. 进入 管理控制台 → API Keys
3. 创建新的 API Key

### 3. 初始化数据库

```bash
cd backend
python init_db.py
```

可选参数 `--reset` 会重建数据库（删除所有数据）。

### 4. 启动

**方式一: 一键启动**
```bash
python start.py
```

**方式二: 分别启动**
```bash
# 终端 1 - 后端
cd backend
python app.py

# 终端 2 - 前端
cd frontend
npm run dev
```

### 5. 访问

- 前端: http://localhost:5173
- 后端 API: http://localhost:5000/api

## 启动选项

```bash
# 首次运行，初始化数据库
python init_db.py

# 重建数据库（谨慎使用）
python init_db.py --reset

# 开发模式启动
python start.py

# 直接运行后端（生产模式）
cd backend
python app.py --production
```

## 页面说明

| 页面 | 路径 | 说明 |
|------|------|------|
| 影片库 | /library | 影片列表，网格/列表视图 |
| 榜单中心 | /charts | 所有榜单及覆盖率 |
| 榜单详情 | /charts/:name | 单个榜单影片列表 |
| 缺口分析 | /charts/:name/gaps | 缺失影片分析 |
| 发现 | /discover | 周报/月报/年报 |
| 待看清单 | /todo | 待看影片管理 |
| 演员列表 | /actors | 演员管理 |
| 演员详情 | /actors/:name | 单个演员信息 |
| 设置 | /settings | 配置管理 |

## API 文档

### 影片
- `GET /api/movies` - 影片列表
  - 参数: `page`, `per_page`, `sort`, `actor`, `min_score`, `list`
- `GET /api/movies/:code` - 影片详情
- `POST /api/movies/:code/refresh` - 刷新评分
- `DELETE /api/movies/:code` - 删除影片

### 演员
- `GET /api/actors` - 演员列表
  - 参数: `followed_only`, `sort`, `search`
- `GET /api/actors/:name` - 演员详情
- `PUT /api/actors/:id/follow` - 切换关注状态

### 榜单
- `GET /api/charts` - 榜单列表
- `GET /api/charts/:name` - 榜单详情
  - 参数: `page`, `per_page`, `filter` (all/collected/missing)
- `GET /api/charts/:name/gaps` - 缺口分析
- `POST /api/charts/:name/refresh` - 更新榜单

### 报告
- `GET /api/reports/latest` - 最新报告
- `GET /api/reports` - 报告列表
- `POST /api/reports/generate` - 生成报告
  - 参数: `type` (weekly/monthly/annual)
- `PUT /api/reports/:id/read` - 标记已读

### 待看
- `GET /api/todos` - 待看清单
  - 参数: `status` (pending/downloaded/all)
- `POST /api/todos` - 添加待看
- `PUT /api/todos/:id/status` - 更新状态
- `DELETE /api/todos/:id` - 删除

### 任务
- `GET /api/tasks` - 当前任务状态
- `POST /api/tasks/sync` - 触发 Jellyfin 同步
- `POST /api/tasks/scores` - 触发评分更新

### 统计
- `GET /api/stats` - 统计数据

## 定时任务

- 每周一 09:00 - 生成周报（关注演员新片）
- 每月1日 09:00 - 生成月报（分数上升旧片）
- 每半年（1月和7月）1日 09:00 - 生成年报（榜单缺口）

## 数据模型

### movies
| 字段 | 类型 | 说明 |
|------|------|------|
| code | String | 影片番号 (唯一) |
| title | String | 标题 |
| actors | String | 演员(逗号分隔) |
| year | Integer | 年份 |
| date_added | DateTime | Jellyfin 添加时间 |
| jellyfin_id | String | Jellyfin ID |
| jellyfin_path | String | 文件路径 |
| javdb_score | Float | JavDB 评分 |
| weighted_score | Integer | 加权分 |
| in_javdb_top250 | Boolean | 是否在 TOP250 |
| in_javlib_top500 | Boolean | 是否在 JavLibrary TOP500 |
| discovered_at | DateTime | 首次发现时间 |

### actors
| 字段 | 类型 | 说明 |
|------|------|------|
| name | String | 演员名 (唯一) |
| is_followed | Boolean | 是否关注 |
| movie_count | Integer | 影片数 |
| avg_score | Float | 平均评分 |
| javbus_id | String | JAVBus ID |
| javdb_id | String | JavDB ID |

## 加权分计算

```
基础分: 50

JavDB 评分调整:
  >= 4.5: +20
  4.2-4.5: +10
  3.9-4.2: 0
  3.5-3.9: -15
  < 3.5: -25

榜单加分:
  双榜 (JavDB + JavLibrary): +30
  单榜: +20
  年度榜: +10

其他:
  多位演员: +5
  演员有 JAVBus ID: +15
```

## 项目结构

```
jav-manager/
├── backend/
│   ├── app.py              # Flask 入口
│   ├── config.py           # 配置文件
│   ├── init_db.py          # 数据库初始化
│   ├── requirements.txt    # Python 依赖
│   ├── models/             # 数据模型
│   │   └── database.py     # SQLAlchemy 模型
│   ├── api/                # API 路由
│   └── services/           # 业务逻辑
│       ├── jellyfin.py     # Jellyfin 同步
│       ├── javdb_scraper.py # JavDB 爬虫
│       ├── chart_scraper.py # 榜单抓取
│       ├── report_generator.py # 报告生成
│       └── score_updater.py # 评分更新
├── frontend/
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   ├── components/     # 复用组件
│   │   ├── api/            # API 封装
│   │   ├── router/         # 路由配置
│   │   └── styles/          # 全局样式
│   ├── package.json
│   └── vite.config.js
├── start.py                # 启动脚本
└── README.md
```

## 注意事项

1. **首次运行**: 需要先运行 `python init_db.py` 初始化数据库
2. **Jellyfin API Key**: 必须配置正确的 API Key 才能同步数据
3. **爬虫礼貌**: 系统有请求延迟限制，请勿频繁刷新
4. **数据备份**: 定期备份 `data.db` 文件

## 获取 JavDB API Key（可选）

系统使用 httpx 直接爬取 JavDB，不需要额外 API Key。
如需更稳定访问，可考虑:
1. 使用代理
2. 配置多域名轮换

## 故障排除

### 数据库锁定
```bash
# 删除锁文件
rm backend/data.db-journal
```

### 前端无法连接后端
检查 Vite 代理配置是否正确，端口是否为 5000。

### Jellyfin 同步失败
1. 检查 API Key 是否正确
2. 检查 Jellyfin 服务器是否可访问
3. 查看后端日志

## 许可证

MIT
