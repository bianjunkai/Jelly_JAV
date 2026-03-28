# JAV Manager 技术设计方案

## 1. 项目概述

### 1.1 项目定位
轻量级个人 JAV 影片管理工具，用于：
- 同步 Jellyfin 影片库
- 获取 JavDB 评分并计算加权分数
- 追踪关注演员的新片和分数变化
- 分析榜单缺口并管理待看清单

### 1.2 技术选型

| 层级 | 技术 | 版本/说明 |
|------|------|-----------|
| 后端 | Flask | Python 3.10+ |
| 数据库 | SQLite | 单文件，零配置 |
| ORM | SQLAlchemy | 2.0+ |
| 定时任务 | APScheduler | 内置调度 |
| 前端 | Vue 3 | Composition API |
| 构建工具 | Vite | 4.x |
| UI 框架 | Element Plus | 2.x |
| HTTP 客户端 | Axios | 1.x |

### 1.3 运行环境
- Python 3.10+
- Node.js 18+
- 纯本地运行，无需 Docker

---

## 2. 目录结构

```
jav-manager/
├── backend/
│   ├── app.py                 # Flask 入口
│   ├── config.py              # 配置文件
│   ├── requirements.txt       # Python 依赖
│   ├── models/
│   │   ├── __init__.py
│   │   └── database.py        # SQLAlchemy 模型
│   ├── api/
│   │   ├── __init__.py
│   │   ├── movies.py          # 影片 API
│   │   ├── actors.py          # 演员 API
│   │   ├── charts.py          # 榜单 API
│   │   ├── reports.py         # 报告 API
│   │   ├── todos.py           # 待看清单 API
│   │   ├── tasks.py           # 任务 API
│   │   └── sync.py            # 同步 API
│   └── services/
│       ├── __init__.py
│       ├── jellyfin.py        # Jellyfin 同步
│       ├── javdb_scraper.py   # JavDB 爬虫
│       ├── chart_scraper.py   # 榜单抓取
│       ├── report_generator.py # 报告生成
│       └── score_calculator.py # 加权分计算
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── router/
│       │   └── index.js
│       ├── api/
│       │   └── index.js       # Axios 封装
│       ├── views/
│       │   ├── Library.vue    # 影片库
│       │   ├── ChartList.vue  # 榜单中心
│       │   ├── ChartDetail.vue # 榜单详情
│       │   ├── GapAnalysis.vue # 缺口分析
│       │   ├── Discover.vue   # 发现/报告
│       │   ├── TodoList.vue   # 待看清单
│       │   ├── ActorList.vue  # 演员列表
│       │   ├── ActorDetail.vue # 演员详情
│       │   └── Settings.vue   # 设置
│       └── components/
│           ├── MovieCard.vue      # 影片卡片
│           ├── MovieDetailModal.vue # 影片详情弹窗
│           ├── ReportCard.vue     # 报告卡片
│           ├── TodoItem.vue       # 待看项
│           ├── ActorCard.vue      # 演员卡片
│           └── GapList.vue        # 缺口列表
└── start.py                   # 一键启动脚本
```

---

## 3. 数据模型

### 3.1 数据库表结构

```python
# models/database.py

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Movie(Base):
    """影片表"""
    __tablename__ = 'movies'

    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, index=True, nullable=False)
    title = Column(String(500))
    original_title = Column(String(500))
    year = Column(Integer)
    actors = Column(String(500))  # 逗号分隔
    date_added = Column(DateTime)  # Jellyfin 添加时间
    jellyfin_id = Column(String(50))
    jellyfin_path = Column(String(1000))

    # 评分相关
    javdb_score = Column(Float)
    javdb_id = Column(String(20))
    weighted_score = Column(Integer, default=50)
    discovered_at = Column(DateTime)  # 首次发现时间

    # 榜单标记
    in_javdb_top250 = Column(Boolean, default=False)
    in_javlib_top500 = Column(Boolean, default=False)
    in_year_chart = Column(Boolean, default=False)

    # 统计
    score_fetch_count = Column(Integer, default=0)
    last_score_update = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # 关联
    todo_items = relationship("TodoItem", back_populates="movie")
    score_history = relationship("ScoreHistory", back_populates="movie")


class Actor(Base):
    """演员表"""
    __tablename__ = 'actors'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    name_en = Column(String(100))
    javbus_id = Column(String(50))
    javdb_id = Column(String(50))
    photo_url = Column(String(500))

    # 关注状态（核心字段）
    is_followed = Column(Boolean, default=False)

    # 统计
    movie_count = Column(Integer, default=0)
    avg_score = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


class Chart(Base):
    """榜单定义"""
    __tablename__ = 'charts'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(100))
    source = Column(String(50))  # javdb / javlibrary
    description = Column(String(500))
    total_count = Column(Integer, default=0)
    year = Column(Integer)  # 年度榜年份
    is_active = Column(Boolean, default=True)
    last_updated = Column(DateTime)

    items = relationship("ChartItem", back_populates="chart", cascade="all, delete-orphan")


class ChartItem(Base):
    """榜单中的影片"""
    __tablename__ = 'chart_items'

    id = Column(Integer, primary_key=True)
    chart_id = Column(Integer, ForeignKey('charts.id'), nullable=False)
    rank = Column(Integer, nullable=False)
    code = Column(String(20), nullable=False)
    title = Column(String(500))
    score = Column(Float)
    actors = Column(String(500))
    year = Column(Integer)

    # 关联本地库
    movie_id = Column(Integer, ForeignKey('movies.id'), nullable=True)
    movie = relationship("Movie")

    __table_args__ = (
        Index('idx_chart_rank', 'chart_id', 'rank'),
        Index('idx_chart_code', 'chart_id', 'code'),
    )

    chart = relationship("Chart", back_populates="items")


class Report(Base):
    """报告表（周报/月报/年报）"""
    __tablename__ = 'reports'

    id = Column(Integer, primary_key=True)
    type = Column(String(20), nullable=False)  # weekly / monthly / annual
    generated_at = Column(DateTime, default=datetime.utcnow)
    title = Column(String(200))
    data = Column(Text)  # JSON 格式存储影片列表
    is_read = Column(Boolean, default=False)

    __table_args__ = (
        Index('idx_report_type_date', 'type', 'generated_at'),
    )


class TodoItem(Base):
    """待看清单"""
    __tablename__ = 'todo_items'

    id = Column(Integer, primary_key=True)
    code = Column(String(20), nullable=False)
    title = Column(String(500))
    actors = Column(String(500))

    # 来源
    source = Column(String(20), nullable=False)  # weekly / monthly / annual / manual
    source_detail = Column(String(100))  # 详细来源，如"周报-小明"

    # 关联本地影片（如果已入库）
    movie_id = Column(Integer, ForeignKey('movies.id'), nullable=True)
    movie = relationship("Movie", back_populates="todo_items")

    # 状态
    status = Column(String(20), default='pending')  # pending / downloaded
    added_at = Column(DateTime, default=datetime.utcnow)
    downloaded_at = Column(DateTime)
    user_note = Column(String(500))

    __table_args__ = (
        Index('idx_todo_status', 'status', 'added_at'),
    )


class ScoreHistory(Base):
    """评分历史（用于追踪分数变化）"""
    __tablename__ = 'score_history'

    id = Column(Integer, primary_key=True)
    movie_id = Column(Integer, ForeignKey('movies.id'), nullable=False)
    prev_score = Column(Float)
    curr_score = Column(Float)
    changed_at = Column(DateTime, default=datetime.utcnow)

    movie = relationship("Movie", back_populates="score_history")


class TaskLog(Base):
    """任务执行日志"""
    __tablename__ = 'task_logs'

    id = Column(Integer, primary_key=True)
    task_type = Column(String(50), nullable=False)  # sync / score_update / chart_crawl / report_gen
    status = Column(String(20), default='running')  # running / completed / failed
    progress = Column(Integer, default=0)  # 0-100
    message = Column(String(500))
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime)
    details = Column(Text)  # JSON 存储详细日志
```

### 3.2 JSON 数据格式示例

```python
# Report.data 字段格式（周报示例）
{
    "type": "weekly",
    "period": "2026-03-18 ~ 2026-03-24",
    "total_count": 5,
    "by_actor": {
        "小明": [
            {"code": "ABC-123", "title": "...", "score": 4.5, "discovered_at": "..."},
            ...
        ]
    },
    "movies": [
        {"code": "...", "title": "...", "actors": [...], "javdb_score": 4.5, ...}
    ]
}

# TaskLog.details 字段格式
{
    "total": 100,
    "processed": 45,
    "failed": 2,
    "current_item": "ABC-123",
    "errors": [{"code": "DEF-456", "error": "timeout"}]
}
```

---

## 4. API 设计

### 4.1 影片库 API

```
GET    /api/movies              # 影片列表（分页、筛选、排序）
GET    /api/movies/:code        # 影片详情
POST   /api/movies/:code/refresh # 刷新单个影片评分
DELETE /api/movies/:code        # 删除影片（仅从数据库）

# 查询参数
GET /api/movies?page=1&per_page=24&sort=weighted_desc&actor=小明&min_score=4.0&list=javdb250
```

**响应格式：**
```json
{
  "total": 1234,
  "page": 1,
  "per_page": 24,
  "items": [
    {
      "id": 1,
      "code": "ABC-123",
      "title": "影片标题",
      "year": 2024,
      "actors": ["小明", "小红"],
      "javdb_score": 4.5,
      "weighted_score": 95,
      "badges": ["🔥", "💎"],
      "poster_url": "/api/poster/abc123",
      "in_library": true
    }
  ]
}
```

### 4.2 演员 API

```
GET    /api/actors              # 演员列表
GET    /api/actors/:name        # 演员详情
PUT    /api/actors/:id/follow   # 切换关注状态
PUT    /api/actors/:id          # 更新演员信息

# 查询参数
GET /api/actors?followed_only=true&sort=movie_count_desc
```

**演员详情响应：**
```json
{
  "id": 1,
  "name": "小明",
  "is_followed": true,
  "movie_count": 15,
  "avg_score": 4.2,
  "movies": [...],
  "chart_appearances": [
    {"chart_name": "JavDB TOP250", "items": [{"rank": 15, "code": "..."}]}
  ],
  "missing_in_charts": [
    {"chart_name": "JavDB TOP250", "items": [{"rank": 23, "code": "...", "score": 4.7}]}
  ]
}
```

### 4.3 榜单 API

```
GET    /api/charts              # 榜单列表
GET    /api/charts/:name        # 榜单详情（含收藏状态）
GET    /api/charts/:name/gaps   # 缺口分析
POST   /api/charts/:name/refresh # 重新抓取榜单
```

**缺口分析响应：**
```json
{
  "chart_name": "JavDB TOP250",
  "total": 250,
  "collected": 186,
  "missing": 64,
  "coverage_percent": 74.4,
  "by_score_range": {
    "high": {"count": 12, "items": [...]},    // >=4.5
    "medium": {"count": 35, "items": [...]},  // 4.0-4.5
    "low": {"count": 17, "items": [...]}      // <4.0
  },
  "by_followed_actor": {
    "小明": [{"rank": 15, "code": "ABC-015", "score": 4.9}],
    "小红": [...]
  },
  "all_missing": [...]
}
```

### 4.4 报告 API

```
GET    /api/reports             # 报告列表
GET    /api/reports/latest      # 最新报告（首页用）
GET    /api/reports/:id         # 报告详情
POST   /api/reports/generate    # 手动生成报告
PUT    /api/reports/:id/read    # 标记已读
DELETE /api/reports/:id         # 删除报告
```

**最新报告响应：**
```json
{
  "weekly": {
    "id": 1,
    "title": "本周关注演员新片",
    "generated_at": "2026-03-24T09:00:00",
    "total_count": 5,
    "is_read": false,
    "preview": [...]
  },
  "monthly": {...},
  "annual": {...}
}
```

### 4.5 待看清单 API

```
GET    /api/todos               # 待看清单（按分组）
POST   /api/todos               # 添加影片
PUT    /api/todos/:id/status    # 更新状态（pending/downloaded）
PUT    /api/todos/:id           # 更新备注
DELETE /api/todos/:id           # 删除

# 批量操作
POST   /api/todos/batch         # 批量添加
PUT    /api/todos/batch/status  # 批量更新状态
```

**待看清单分组响应：**
```json
{
  "groups": [
    {
      "source": "weekly",
      "source_detail": "周报-小明",
      "count": 2,
      "added_at": "2026-03-24",
      "items": [...]
    },
    {
      "source": "monthly",
      "source_detail": "月报-分数上升",
      "count": 1,
      "items": [...]
    }
  ],
  "total_pending": 12,
  "total_downloaded": 5
}
```

### 4.6 任务 API

```
GET    /api/tasks               # 当前任务状态
POST   /api/tasks/sync          # 触发 Jellyfin 同步
POST   /api/tasks/scores        # 触发评分更新
POST   /api/tasks/charts        # 触发榜单抓取
DELETE /api/tasks/:id           # 终止任务
```

**任务状态响应：**
```json
{
  "running": [
    {
      "id": 1,
      "type": "score_update",
      "status": "running",
      "progress": 45,
      "message": "正在处理: ABC-123",
      "started_at": "2026-03-28T10:00:00"
    }
  ],
  "recent_completed": [...]
}
```

### 4.7 其他 API

```
GET    /api/stats               # 统计数据
GET    /api/config              # 获取配置
PUT    /api/config              # 更新配置
GET    /api/poster/:id          # 海报代理
```

---

## 5. 页面路由与组件

### 5.1 前端路由表

```javascript
// router/index.js
const routes = [
  { path: '/', redirect: '/library' },
  {
    path: '/library',
    component: () => import('@/views/Library.vue'),
    meta: { title: '影片库', icon: 'Film' }
  },
  {
    path: '/charts',
    component: () => import('@/views/ChartList.vue'),
    meta: { title: '榜单中心', icon: 'Trophy' }
  },
  {
    path: '/charts/:name',
    component: () => import('@/views/ChartDetail.vue'),
    meta: { title: '榜单详情' }
  },
  {
    path: '/charts/:name/gaps',
    component: () => import('@/views/GapAnalysis.vue'),
    meta: { title: '缺口分析' }
  },
  {
    path: '/discover',
    component: () => import('@/views/Discover.vue'),
    meta: { title: '发现', icon: 'Compass' }
  },
  {
    path: '/todo',
    component: () => import('@/views/TodoList.vue'),
    meta: { title: '待看清单', icon: 'List' }
  },
  {
    path: '/actors',
    component: () => import('@/views/ActorList.vue'),
    meta: { title: '演员', icon: 'User' }
  },
  {
    path: '/actors/:name',
    component: () => import('@/views/ActorDetail.vue'),
    meta: { title: '演员详情' }
  },
  {
    path: '/settings',
    component: () => import('@/views/Settings.vue'),
    meta: { title: '设置', icon: 'Setting' }
  }
]
```

### 5.2 组件清单

| 组件 | 路径 | 用途 |
|------|------|------|
| MovieCard | components/MovieCard.vue | 影片卡片（网格） |
| MovieListItem | components/MovieListItem.vue | 影片列表项 |
| MovieDetailModal | components/MovieDetailModal.vue | 影片详情弹窗 |
| ActorCard | components/ActorCard.vue | 演员卡片 |
| ChartCard | components/ChartCard.vue | 榜单卡片（进度条） |
| ChartTable | components/ChartTable.vue | 榜单表格 |
| GapList | components/GapList.vue | 缺口列表（可勾选） |
| ReportCard | components/ReportCard.vue | 报告预览卡片 |
| TodoItem | components/TodoItem.vue | 待看项卡片 |
| TodoGroup | components/TodoGroup.vue | 待看分组 |
| ScoreBadge | components/ScoreBadge.vue | 评分徽章 |
| Badges | components/Badges.vue | 榜单徽章（🔥⭐💎） |
| TaskStatus | components/TaskStatus.vue | 任务状态指示器 |
| EmptyState | components/EmptyState.vue | 空状态 |
| PageHeader | components/PageHeader.vue | 页面头部 |
| NavBar | components/NavBar.vue | 导航栏 |

---

## 6. 核心业务逻辑

### 6.1 加权分计算

```python
def calculate_weighted_score(movie):
    """计算影片加权分"""
    score = 50  # 基础分

    # JavDB 评分调整
    javdb = movie.javdb_score or 0
    if javdb >= 4.5:
        score += 20
    elif javdb >= 4.2:
        score += 10
    elif javdb >= 3.9:
        score += 0
    elif javdb >= 3.5:
        score -= 15
    else:
        score -= 25

    # 榜单加分
    if movie.in_javdb_top250 and movie.in_javlib_top500:
        score += 30  # 双榜
    elif movie.in_javdb_top250 or movie.in_javlib_top500:
        score += 20  # 单榜
    elif movie.in_year_chart:
        score += 10  # 年度榜

    # 多位演员
    actors = movie.actors.split(',') if movie.actors else []
    if len(actors) >= 2:
        score += 5

    # 演员有 JAVBus ID
    # 这里需要查询演员表

    return max(0, min(100, score))
```

### 6.2 报告生成逻辑

```python
def generate_weekly_report():
    """生成周报：本周关注演员新片"""
    # 上周一到周日
    last_week_start = get_last_monday()
    last_week_end = last_week_start + timedelta(days=6)

    # 关注演员名单
    followed_actors = [a.name for a in Actor.query.filter_by(is_followed=True).all()]

    # 本周发现的影片（按演员分组）
    new_movies = Movie.query.filter(
        Movie.discovered_at >= last_week_start,
        Movie.discovered_at <= last_week_end,
        Movie.actors.in_(followed_actors)  # 需要处理逗号分隔
    ).all()

    # 按演员分组
    by_actor = {}
    for movie in new_movies:
        for actor in movie.actors.split(','):
            if actor in followed_actors:
                by_actor.setdefault(actor, []).append(movie)

    return {
        'type': 'weekly',
        'period': f'{last_week_start.date()} ~ {last_week_end.date()}',
        'total_count': len(new_movies),
        'by_actor': by_actor,
        'movies': [m.to_dict() for m in new_movies]
    }


def generate_monthly_report():
    """生成月报：本月分数上升旧片"""
    # 上个月1号到月底
    month_start = get_first_day_of_last_month()
    month_end = get_last_day_of_last_month()

    # 关注演员
    followed_actors = [a.name for a in Actor.query.filter_by(is_followed=True).all()]

    # 分数上升记录
    score_changes = ScoreHistory.query.filter(
        ScoreHistory.changed_at >= month_start,
        ScoreHistory.changed_at <= month_end,
        ScoreHistory.curr_score >= 4.3,
        ScoreHistory.prev_score < 4.0
    ).all()

    # 筛选关注演员的影片
    result = []
    for change in score_changes:
        movie = change.movie
        actors = movie.actors.split(',') if movie.actors else []
        if any(a in followed_actors for a in actors):
            result.append({
                'movie': movie,
                'prev_score': change.prev_score,
                'curr_score': change.curr_score,
                'change': round(change.curr_score - change.prev_score, 1)
            })

    return {
        'type': 'monthly',
        'period': f'{month_start.date()} ~ {month_end.date()}',
        'total_count': len(result),
        'items': result
    }
```

### 6.3 缺口分析算法

```python
def analyze_chart_gaps(chart_name):
    """分析榜单缺口"""
    chart = Chart.query.filter_by(name=chart_name).first()
    if not chart:
        return None

    # 本地库所有番号
    local_codes = {m.code for m in Movie.query.all()}

    # 榜单中的影片
    chart_items = ChartItem.query.filter_by(chart_id=chart.id).order_by(ChartItem.rank).all()

    # 缺失的
    missing = []
    for item in chart_items:
        if item.code not in local_codes:
            # 检查是否关注演员
            actors = item.actors.split(',') if item.actors else []
            is_followed = Actor.query.filter(
                Actor.name.in_(actors),
                Actor.is_followed == True
            ).first() is not None

            missing.append({
                'rank': item.rank,
                'code': item.code,
                'title': item.title,
                'score': item.score,
                'actors': actors,
                'is_followed_actor': is_followed
            })

    # 按关注演员分组
    by_followed_actor = {}
    for item in missing:
        if item['is_followed_actor']:
            for actor in item['actors']:
                if Actor.query.filter_by(name=actor, is_followed=True).first():
                    by_followed_actor.setdefault(actor, []).append(item)

    return {
        'total': len(chart_items),
        'collected': len(chart_items) - len(missing),
        'missing': len(missing),
        'coverage_percent': round((len(chart_items) - len(missing)) / len(chart_items) * 100, 1),
        'by_score_range': {
            'high': [m for m in missing if m['score'] and m['score'] >= 4.5],
            'medium': [m for m in missing if m['score'] and 4.0 <= m['score'] < 4.5],
            'low': [m for m in missing if m['score'] and m['score'] < 4.0]
        },
        'by_followed_actor': by_followed_actor,
        'all_missing': missing
    }
```

### 6.4 定时任务配置

```python
# APScheduler 配置
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

# 每周一 09:00 生成周报
scheduler.add_job(
    generate_weekly_report,
    'cron',
    day_of_week='mon',
    hour=9,
    minute=0,
    id='weekly_report'
)

# 每月1日 09:00 生成月报
scheduler.add_job(
    generate_monthly_report,
    'cron',
    day=1,
    hour=9,
    minute=0,
    id='monthly_report'
)

# 每半年（1月和7月）生成年报
scheduler.add_job(
    generate_annual_report,
    'cron',
    month='1,7',
    day=1,
    hour=9,
    minute=0,
    id='annual_report'
)
```

---

## 7. 部署方案

### 7.1 开发环境启动

```bash
# 1. 克隆项目
git clone <repo> jav-manager
cd jav-manager

# 2. 启动后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py  # 默认 http://localhost:5000

# 3. 启动前端（新终端）
cd ../frontend
npm install
npm run dev  # 默认 http://localhost:5173
```

### 7.2 生产环境部署

```bash
# 构建前端
cd frontend
npm run build  # 输出到 backend/static/

# 启动（Flask 托管前端）
cd ../backend
python app.py --production  # 或设置 FLASK_ENV=production
```

### 7.3 配置文件

```python
# backend/config.py
import os

# Jellyfin 配置
JELLYFIN_URL = os.getenv('JELLYFIN_URL', 'http://localhost:8096/')
JELLYFIN_API_KEY = os.getenv('JELLYFIN_API_KEY', '')

# 数据库
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data.db')

# 爬虫配置
JAVDB_DOMAINS = ['javdb.com', 'javdb5.com', 'javdb4.com']
REQUEST_MIN_DELAY = 3
REQUEST_MAX_DELAY = 6
REQUEST_TIMEOUT = 30

# 定时任务
AUTO_SYNC_ON_STARTUP = True
AUTO_UPDATE_SCORES = False

# 评分权重（可配置）
WEIGHT_BASE = 50
WEIGHT_JAVDB_HIGH = 20      # >=4.5
WEIGHT_JAVDB_MEDIUM = 10    # 4.2-4.5
WEIGHT_JAVDB_LOW = -15      # 3.5-3.9
WEIGHT_JAVDB_VERY_LOW = -25 # <3.5
WEIGHT_DUAL_CHART = 30
WEIGHT_SINGLE_CHART = 20
WEIGHT_YEAR_CHART = 10
WEIGHT_MULTI_ACTOR = 5
WEIGHT_JAVBUS_ID = 15
```

---

## 8. 开发计划

### Phase 1: 基础骨架（1周）
- [ ] 项目初始化，目录结构搭建
- [ ] 数据库模型设计与迁移
- [ ] Flask 基础 API 框架
- [ ] Vue 项目初始化，Element Plus 集成
- [ ] 基础布局与导航

### Phase 2: 核心功能（2周）
- [ ] Jellyfin 同步服务
- [ ] 影片库页面（网格/列表视图）
- [ ] 影片详情弹窗
- [ ] JavDB 爬虫与评分获取
- [ ] 加权分计算
- [ ] 演员列表与关注功能

### Phase 3: 榜单与发现（1.5周）
- [ ] 榜单抓取服务
- [ ] 榜单中心页面
- [ ] 榜单详情与缺口分析
- [ ] 报告生成逻辑（周报/月报）
- [ ] 发现页面（报告展示）

### Phase 4: 待看清单与优化（1周）
- [ ] 待看清单 CRUD
- [ ] 分组展示
- [ ] 定时任务集成
- [ ] 设置页面
- [ ] 性能优化与 Bug 修复

### Phase 5: 完善（0.5周）
- [ ] 数据迁移工具
- [ ] 文档完善
- [ ] 测试与发布

---

## 9. 命名规范

### 9.1 数据库
- 表名：小写，复数形式（movies, actors, charts）
- 字段：小写下划线（javdb_score, is_followed, created_at）
- 外键：关联表名单数 + _id（chart_id, movie_id）
- 索引：idx_表名_字段名

### 9.2 API
- URL：小写，资源名复数（/api/movies, /api/charts）
- 参数：小写下划线（min_score, actor_name）
- 动作：POST 创建，PUT 更新，DELETE 删除

### 9.3 前端
- 组件：PascalCase（MovieCard.vue, ChartDetail.vue）
- 方法：camelCase（fetchMovies, handleSubmit）
- 样式：小写短横线（movie-card, chart-detail）

---

## 10. 注意事项

1. **数据安全**：SQLite 文件定期备份
2. **爬虫礼貌**：严格遵守延迟设置，避免被封
3. **错误处理**：API 统一返回格式，前端统一错误提示
4. **性能**：影片列表分页，图片懒加载
5. **兼容性**：浏览器支持 Chrome/Firefox/Edge 最新两版

---

**文档版本**: 1.0
**创建时间**: 2026-03-28
**适用项目**: JAV Manager v2.0
