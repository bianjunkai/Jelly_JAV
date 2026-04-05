# JavDB 批量评分更新工具

> 独立运行的小工具，用于分批更新影片库的 JavDB 评分

## 使用方法

### 1. 进入目录
```bash
cd jav-manager/backend
```

### 2. 查看状态
```bash
python batch_score_updater.py --status
```

### 3. 更新一小批（默认30个）
```bash
python batch_score_updater.py
```

### 4. 更新指定数量
```bash
python batch_score_updater.py --batch 10
```

### 5. 自动更新全部（推荐）
```bash
python batch_score_updater.py --all
```
- 每批30个
- 每批处理完后休息 45-75 分钟（随机）
- 可随时按 `Ctrl+C` 中断
- 支持断点续传：中断后运行相同命令会从上次位置继续

### 6. 自定义参数
```bash
# 每批50个，每批休息 30-60 分钟
python batch_score_updater.py --all --batch 50 --rest-min 30 --rest-max 60
```

### 7. 重置进度
```bash
python batch_score_updater.py --reset
```

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--status, -s` | - | 查看当前状态 |
| `--reset, -r` | - | 重置进度（重新开始） |
| `--batch, -b` | 30 | 每批处理数量 |
| `--all, -a` | - | 自动更新全部（分批执行） |
| `--rest-min` | 45 | 批次间休息分钟（最小） |
| `--rest-max` | 75 | 批次间休息分钟（最大） |

## 机制说明

### 单次模式 (`--batch N`)
```
更新 N 个影片 → 完成
```
- 不会自动继续
- 不会自动休息

### 自动模式 (`--all`)
```
第1批(30个) → 休息45-75分钟 → 第2批(30个) → 休息45-75分钟 → ...
```
- 每批处理完会暂停等待
- 休息期间每分钟显示倒计时
- 按 `Ctrl+C` 可停止

### 断点续传
- 进度保存在 `update_state.json`
- 中断后运行相同命令会自动继续
- 使用 `--reset` 可重新开始

## 数据安全

- **不伤害已有数据**：只更新 `javdb_score` 字段
- **批量提交**：每处理完一个影片立即提交
- **错误隔离**：单个影片出错不会影响其他影片

## 预估时间

| 影片数量 | 每批 | 预计总时间 |
|---------|------|-----------|
| 1877 | 30 | ~25 小时（含休息） |
| 1877 | 50 | ~15 小时（含休息） |

每部影片约需 8-10 秒（含延迟）

## 依赖配置

确保 `config.json` 中已配置：
- `ENABLE_SYSTEM_PROXY: true`
- `SYSTEM_PROXY_URL: "http://192.168.1.15:7893"`
- `JAVDB_COOKIE: "..."`
