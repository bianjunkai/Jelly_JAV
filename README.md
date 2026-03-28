# JAV Manager

个人 JAV 影片管理系统。

## 项目结构

```
.
├── jav-manager/          # ✨ 新版本 (v2.0) - 当前活跃开发
│   ├── backend/          # Flask 后端
│   ├── frontend/        # Vue 3 前端
│   ├── start.py          # 启动脚本
│   └── README.md         # 详细文档
│
├── legacy/              # 📦 旧版本 (v1.0)
│   ├── app.py           # Flask 单文件应用
│   ├── scrapers/        # 爬虫模块
│   ├── templates/       # Jinja2 模板
│   ├── static/           # 静态文件
│   ├── venv/            # Python 虚拟环境
│   ├── *.csv            # 榜单数据
│   └── data.db          # SQLite 数据库
│
├── ARCHITECTURE.md      # 架构设计文档
├── DESIGN.md            # 技术设计方案
├── PRD.md               # 需求文档
└── claude.md            # Claude 项目规范
```

## 快速开始（新版本）

```bash
cd jav-manager

# 安装后端依赖
cd backend
pip install -r requirements.txt

# 初始化数据库
python init_db.py

# 启动后端
python app.py

# 新终端 - 启动前端
cd ../frontend
npm install
npm run dev
```

访问 http://localhost:5173

## 新版本特性

- 📁 **影片库管理** - 网格/列表视图，支持筛选和排序
- 🏆 **榜单中心** - JavDB TOP250、年度榜等，支持缺口分析
- ⭐ **关注演员** - 追踪关注演员的新片和分数变化
- 📝 **待看清单** - 按来源分组，支持批量操作
- 📊 **智能报告** - 周报/月报/年报，自动生成
- 🔍 **评分系统** - JavDB 评分 + 加权分计算

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | Flask + SQLAlchemy + SQLite |
| 前端 | Vue 3 + Element Plus + Vite |
| 爬虫 | httpx + BeautifulSoup |

## 详细文档

- [ARCHITECTURE.md](./ARCHITECTURE.md) - 架构设计
- [DESIGN.md](./DESIGN.md) - 技术设计方案
- [PRD.md](./PRD.md) - 需求文档
- [jav-manager/README.md](./jav-manager/README.md) - 新版本详细文档
