# PRD: 智能影片价值评估与发现系统

## 一、项目概述

### 1.1 背景
用户拥有大量本地 JAV 影片（存储在 Jellyfin/NAS），数量多且疏于整理，需要一套系统帮助：
- 评估每部影片的保留价值
- 发现关注演员的新片
- 识别高分旧片
- 对比榜单缺口并补全

### 1.2 目标用户
**个人用户**，有大量 JAV 收藏，关注特定演员，重视影片质量（JavDB 评分），希望系统化管理。

### 1.3 核心价值
- **自动化价值评估**：基于多维度评分，减少人工判断成本
- **智能发现**：每周推送新片、每月推送分数上升旧片
- **持续监控**：榜单对比，发现收藏缺口
- **决策支持**：待看清单管理，辅助下载决策

---

## 二、用户画像

| 角色 | 特征 | 目标 |
|------|------|------|
| **收藏家** | 有 1000+ 影片，关注 20+ 演员，注重质量 | 清理低质量影片，补全高分经典 |
| **追新者** | 只关注少数几个喜欢的演员 | 第一时间获取新作，不错过 |
| **性价比派** | 时间有限，只看高分片 | 快速筛选出值得观看的影片 |

---

## 三、核心决策逻辑

### 3.1 保留判断规则
```
IF 演员 ∈ 关注列表 THEN 保留（一票通过）
ELSE IF JavDB 评分 < 3.8 THEN 基本删除
ELSE
    加权分 ≥ 80 → 保留
    加权分 60-80 → 犹豫（待看清单）
    加权分 < 60 → 删除
```

### 3.2 加权分计算公式
```
基础分：50
+ JavDB 评分调整（≥4.5: +20, 4.2-4.5: +10, 3.9-4.2: 0, 3.5-3.9: -15, <3.5: -25）
+ 榜单加分（双榜：+30，单榜：+20，年度榜：+10）
+ 多位演员（≥2）：+5
+ 演员有 JAVBus ID：+15
```

---

## 四、功能需求

### 4.1 主页面（Dashboard）

#### 4.1.1 顶部报告横幅（周报/月报/年报）
- **周报**：标题「本周关注演员新片（共 X 部）」
  - 每部影片卡片：封面、番号、标题、演员、JavDB 评分、加权分
  - 按钮：「加入待看清单」
  - 未显示按钮的影片视为忽略
- **月报**：标题「本月旧片分数上升（≥4.3，共 X 部）」
  - 每部影片卡片：封面、番号、标题、演员、分数变化（3.2 → 4.3）
  - 按钮：「加入待看清单」
- **年报（半年）**：标题「年度榜单缺口（JavDB 2026 TOP250 缺失 X 部）」
  - 列表：番号、标题、排名、评分
  - 按钮：每部影片旁「加入待看清单」→ 逐个确认
- **关闭按钮**：可手动关闭报告横幅

#### 4.1.2 待看清单预览
- 显示最近添加的 5 部影片
- 点击「查看全部」进入待看清单页面

#### 4.1.3 统计概览
- 总收藏数、覆盖率（vs. JavDB TOP250）、平均 JavDB 评分
- 待看清单数量

#### 4.1.4 操作入口
- 「同步 Jellyfin」按钮
- 「更新 JavDB 评分」按钮（独立任务）
- 「抓取榜单」按钮

---

### 4.2 待看清单页面

#### 4.2.1 分组展示
按「来源 + 演员」分组：
- 周报-小明
- 月报-分数上升-小红
- 榜单补全-JavDB 2026
- 手动添加

每组显示影片数量、添加时间。

#### 4.2.2 影片卡片
- 封面、番号、标题、演员、JavDB 评分、加权分、来源标签
- 操作：「标记为已下载」（从清单移除，不删除数据）

#### 4.2.3 重复处理
同一影片出现在多个分组时**分别显示**，不合并。

---

### 4.3 报告页面（可选，作为历史查看）

虽然需求是不保留历史，但可考虑临时缓存最近 3 期报告数据，供用户回看。

---

### 4.4 后台任务

#### 4.4.1 JavDB 评分更新任务
- **手动触发**，独立运行
- **断点续传**：记录已处理的影片编号，中断后继续
- **进度显示**：实时显示「已完成 X/Y」，可查看日志
- **限速**：3-5 秒间隔，避免反爬
- **关闭提示**：关闭页面时提示任务未完成

#### 4.4.2 榜单抓取任务
- 手动触发，首页顶部按钮
- 后台运行，完成后页面提示
- 重试 3 次，失败降级（使用旧数据）

#### 4.4.3 报告生成任务
- 自动触发（每周一凌晨生成周报，每月 1 号生成月报，每年 1 月生成年报）
- 完成后首页横幅展示

---

### 4.5 数据同步

#### 4.5.1 Jellyfin 同步
- 手动触发或启动时自动同步
- 更新影片数据、演员列表
- 自动计算加权分

---

### 4.6 关注演员管理

- **关注状态**：actors 表新增 `is_followed BOOLEAN DEFAULT 0`
- **默认关注规则**：
  - 新同步的演员：默认 `is_followed = 0`
  - **迁移规则**：老版本中维护了 RSS 连接（`javbus_id IS NOT NULL AND rss_url IS NOT NULL`）的演员，升级后自动设为 `is_followed = 1`
- 演员列表展示，可手动切换关注状态
- 关注演员才有资格出现在周报/月报中

---

### 4.7 新片发现逻辑

- **新片定义**：首次出现在 JavDB 评分数据库（通过 `discovered_at` 字段记录首次抓取时间）
- **监控范围**：仅关注演员的影片
- **周报生成**：上周内 `discovered_at` 更新的影片

### 4.8 旧片分数上升监控

- **监控范围**：仅关注演员的影片
- **触发条件**：当前 `javdb_score ≥ 4.3` 且上一次记录的分数 < 4.0（或从未记录）
- **月报生成**：过去一个月内分数上升的影片

---

### 4.9 删除保护

- **不允许自动删除**任何影片数据
- 删除操作必须由用户**在 NAS 上手动执行**
- 系统只提供「标记为已下载」功能，用于从待看清单移除

---

## 五、数据模型

### 5.1 movies 表（已有）
```sql
CREATE TABLE movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE,
    title TEXT,
    year TEXT,
    actors TEXT,
    date_added TEXT,
    jellyfin_id TEXT,
    score INTEGER DEFAULT 50,
    javdb_score REAL,
    discovered_at TEXT
);
```
新增字段：
- `discovered_at`：首次在 JavDB 发现的时间（用于新片识别）

### 5.2 actors 表（已有，更新）
```sql
CREATE TABLE actors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    javbus_id TEXT,
    rss_url TEXT,
    is_watched BOOLEAN DEFAULT 0,
    last_updated TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    is_followed BOOLEAN DEFAULT 0
);
```
新增字段：
- `is_followed BOOLEAN DEFAULT 0`：是否关注

### 5.3 reports 表（新增）
```sql
CREATE TABLE reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT CHECK(type IN ('weekly', 'monthly', 'annual')),
    generated_at TEXT,
    data JSON,
    is_read BOOLEAN DEFAULT 0
);
```

### 5.4 todo_list 表（待看清单）
```sql
CREATE TABLE todo_list (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT,
    title TEXT,
    actors TEXT,
    source TEXT CHECK(source IN ('weekly', 'monthly', 'annual', 'manual')),
    added_at TEXT DEFAULT CURRENT_TIMESTAMP,
    status TEXT CHECK(status IN ('pending', 'downloaded')),
    user_note TEXT,
    UNIQUE(code, source)
);
```

### 5.5 tasks 表（任务状态）
```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type TEXT CHECK(task_type IN ('score_update', 'crawl_lists')),
    status TEXT CHECK(status IN ('running', 'completed', 'failed')),
    progress TEXT,
    started_at TEXT,
    finished_at TEXT,
    last_processed_code TEXT
);
```

### 5.6 score_history 表（分数历史，用于月报）
```sql
CREATE TABLE score_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT,
    prev_score REAL,
    curr_score REAL,
    changed_at TEXT DEFAULT CURRENT_TIMESTAMP,
    actor_name TEXT
);
```

---

## 六、API 需求

### 6.1 报告相关
```
GET  /api/reports/latest          # 获取最新报告
POST /api/reports/generate        # 手动生成报告（管理员）
GET  /api/reports/list            # 报告历史（如果保留）
```

### 6.2 待看清单相关
```
GET  /api/todos                  # 获取清单（按分组）
POST /api/todos                  # 添加影片（加来源）
PUT  /api/todos/:id/status       # 更新状态（标记已下载）
DELETE /api/todos/:id            # 删除
```

### 6.3 任务相关
```
GET  /api/tasks                  # 当前任务状态
POST /api/tasks/score_update     # 触发评分更新
POST /api/tasks/crawl_lists      # 触发榜单抓取
DELETE /api/tasks/:id            # 终止任务
```

### 6.4 关注演员相关
```
GET  /api/actors/followed        # 获取关注的演员
PUT  /api/actors/:id/follow      # 标记关注/取消
```

### 6.5 分数历史相关
```
GET  /api/score_changes          # 获取近期分数变化（月报数据源）
```

---

## 七、非功能需求

- **性能**：1000+ 影片列表加载 < 2s
- **可用性**：后台任务独立进程，网页关闭后任务继续运行
- **鲁棒性**：反爬重试、数据降级、异常通知
- **安全性**：页面内提示，无需登录

---

## 八、实施计划（分阶段）

### Phase 1（MVP，2 周）
- [ ] 数据库调整（添加 `is_followed`, `todo_list`, `reports`, `tasks`, `score_history`, `discovered_at`）
- [ ] 待看清单页面（B 分组，重复显示，标记已下载）
- [ ] 报告数据结构与生成（周报、月报、年报）
- [ ] 首页横幅展示最新报告
- [ ] 榜单抓取手动触发 + 后台任务
- [ ] 关注演员管理（标记关注状态 + 迁移逻辑）
- [ ] 新片发现逻辑（`discovered_at` 记录）
- [ ] 分数变化追踪（`score_history` 表）
- [ ] 文档和部署脚本

### Phase 2（体验优化，1 周）
- [ ] 评分更新任务断点续传 + 进度显示
- [ ] 批量操作（年度榜单逐个确认）
- [ ] 关闭页面提示任务未完成
- [ ] 优化首页加载速度

### Phase 3（自动化，1 周）
- [ ] 自动生成报告（定时任务）
- [ ] 自动更新评分（可选，低频）
- [ ] 字典项设置页（权重、频率）

---

## 九、确认事项

1. **新片定义**：首次出现在 JavDB 评分（通过 `discovered_at` 追踪）✅
2. **监控范围**：仅关注演员 ✅
3. **删除保护**：不允许自动删除 ✅
4. **关注演员迁移**：老版本有 RSS 连接的自动设为关注 ✅
5. **榜单抓取失败通知**：仅页面提示 ✅
6. **新片频率**：周报 ✅
7. **旧片分数上升**：月报 ✅
8. **年度榜单对比**：半年一次 ✅
9. **待看清单分组**：按来源+演员分组，重复显示 ✅
10. **操作方式**：报告中有「加入待看清单」按钮，未显示视为忽略 ✅
11. **年度榜单操作**：逐个确认加入 ✅
12. **评分更新触发**：手动触发，后台运行 ✅
13. **榜单抓取触发**：手动触发，首页顶部按钮 ✅
14. **榜单频率**：每月一次 ✅
15. **榜单存储**：只保留最新 ✅
16. **榜单失败处理**：重试3次，使用旧数据，页面提示 ✅

---

**生成时间**: 2026-03-24
**版本**: v1.0
