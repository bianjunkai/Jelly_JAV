#!/usr/bin/env python3
"""
JavDB 批量评分更新工具（仅修改此文件）

使用方法:
    python batch_score_updater.py                    # 更新下一批
    python batch_score_updater.py --status          # 查看状态
    python batch_score_updater.py --reset           # 重置进度
    python batch_score_updater.py --batch 50        # 每批50条（默认30）
    python batch_score_updater.py --all             # 一次性更新全部
"""

import argparse
import json
import sys
import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data.db")
STATE_FILE = os.path.join(BASE_DIR, "update_state.json")

sys.path.insert(0, BASE_DIR)

# 检查是否在正确的虚拟环境中运行
try:
    import flask
except ImportError:
    venv_python = os.path.join(BASE_DIR, '.venv', 'Scripts', 'python.exe')
    print(f"错误: 当前 Python 环境缺少 'flask' 模块。")
    print(f"请使用虚拟环境中的 Python 运行本脚本:")
    print(f"  {venv_python} {os.path.basename(__file__)} --all")
    sys.exit(1)

# 由于 javdb_scraper 会延迟 import app.config，首次加载 Flask 堆栈可能较慢
print("[初始化] 正在加载评分模块，请稍候...")
from services.javdb_scraper import fetch_movie_score
print("[初始化] 评分模块加载完成")


def get_conn():
    return sqlite3.connect(DB_PATH)


def get_pending_movies(batch_size, last_code=None):
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if last_code:
        sql = """
            SELECT id, code, javdb_score FROM movies
            WHERE code IS NOT NULL AND javdb_score IS NULL AND code > ?
            ORDER BY code LIMIT ?
        """
        cursor.execute(sql, (last_code, batch_size))
    else:
        sql = """
            SELECT id, code, javdb_score FROM movies
            WHERE code IS NOT NULL AND javdb_score IS NULL
            ORDER BY code LIMIT ?
        """
        cursor.execute(sql, (batch_size,))

    movies = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return movies


def get_stats():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM movies WHERE code IS NOT NULL")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM movies WHERE code IS NOT NULL AND javdb_score IS NOT NULL")
    with_score = cursor.fetchone()[0]
    conn.close()
    without_score = total - with_score
    return {
        'total': total,
        'with_score': with_score,
        'without_score': without_score,
        'coverage': round(with_score / total * 100, 1) if total > 0 else 0
    }


def update_batch(batch_size=100):
    stats = get_stats()
    print(f"\n{'='*50}")
    print(f" JavDB 批量评分更新工具")
    print(f"{'='*50}")
    print(f" 总影片数: {stats['total']}")
    print(f" 已评分: {stats['with_score']} ({stats['coverage']}%)")
    print(f" 未评分: {stats['without_score']}")
    print(f" 本批数量: {batch_size}")
    print(f"{'='*50}\n")

    if stats['without_score'] == 0:
        print(" 所有影片都已评分！")
        return

    last_code = None
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
            last_code = state.get('last_code')

    print(f" 从 code: {last_code or '开头'}  开始...\n")

    movies = get_pending_movies(batch_size, last_code)

    if not movies:
        print(" 没有更多影片需要更新")
        if last_code:
            print(" 尝试运行 --reset 重置进度")
        return

    updated = 0
    errors = 0
    no_score_found = 0
    start_time = datetime.now()

    for i, movie in enumerate(movies):
        code = movie['code']
        old_score = movie['javdb_score']
        try:
            new_score = fetch_movie_score(code)

            if new_score:
                if new_score != old_score:
                    conn = get_conn()
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE movies
                        SET javdb_score = ?,
                            last_score_update = ?,
                            score_fetch_count = COALESCE(score_fetch_count, 0) + 1
                        WHERE id = ?
                    """, (new_score, datetime.utcnow(), movie['id']))
                    conn.commit()
                    conn.close()
                    updated += 1
                    print(f"  [{i+1}/{len(movies)}] {code}: {old_score} → {new_score}")
                else:
                    print(f"  [{i+1}/{len(movies)}] {code}: {new_score} (无变化)")
            else:
                no_score_found += 1
                print(f"  [{i+1}/{len(movies)}] {code}: 未找到评分")

        except Exception as e:
            errors += 1
            print(f"  [{i+1}/{len(movies)}] {code}: 错误 - {e}")

        # 保存进度
        last_code = code
        with open(STATE_FILE, 'w') as f:
            json.dump({'last_code': last_code, 'updated': updated, 'errors': errors}, f)

    # 只有当这是最后一批（不足 batch_size）时才清除断点
    if len(movies) < batch_size:
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)

    elapsed = (datetime.now() - start_time).total_seconds()

    print(f"\n{'='*50}")
    print(f" 完成!")
    print(f"  更新: {updated} 部")
    print(f"  无变化: {len(movies) - updated - no_score_found} 部")
    print(f"  未找到评分: {no_score_found} 部")
    print(f"  错误: {errors} 部")
    print(f"  耗时: {elapsed:.1f} 秒")
    print(f"{'='*50}")


def show_status():
    stats = get_stats()

    last_code = None
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
            last_code = state.get('last_code')

    print(f"\n{'='*50}")
    print(f" JavDB 评分更新状态")
    print(f"{'='*50}")
    print(f" 总影片数: {stats['total']}")
    print(f" 已评分: {stats['with_score']} ({stats['coverage']}%)")
    print(f" 未评分: {stats['without_score']}")
    print(f" 当前进度: {'已暂停' if last_code else '已完成'}")
    if last_code:
        print(f"  上次处理到: {last_code}")
        print(f"  可用命令: python batch_score_updater.py (继续)")
    print(f"{'='*50}\n")


def reset_progress():
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
        print(" 进度已重置")
    else:
        print(" 没有需要重置的进度")


def main():
    parser = argparse.ArgumentParser(description='JavDB 批量评分更新工具')
    parser.add_argument('--status', '-s', action='store_true', help='查看状态')
    parser.add_argument('--reset', '-r', action='store_true', help='重置进度')
    parser.add_argument('--batch', '-b', type=int, default=30, help='每批数量（默认30）')
    parser.add_argument('--all', '-a', action='store_true', help='更新全部（慎用！）')
    parser.add_argument('--rest-min', type=int, default=45, help='每批休息分钟最小值（默认45）')
    parser.add_argument('--rest-max', type=int, default=75, help='每批休息分钟最大值（默认75）')

    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.reset:
        reset_progress()
    elif args.all:
        print(" 警告: 这将更新所有影片评分，可能需要很长时间！")
        print(" 每批数量: {}  |  休息间隔: {}-{} 分钟".format(
            args.batch, args.rest_min, args.rest_max))
        print(" 按 Ctrl+C 取消，或等待 5 秒继续...")
        import time
        try:
            time.sleep(5)
        except KeyboardInterrupt:
            print("\n 已取消")
            return

        import random
        batch_size = args.batch

        while True:
            stats = get_stats()

            if stats['without_score'] == 0:
                print("\n 所有影片都已评分！")
                break

            update_batch(batch_size)

            # 随机休息 45-75 分钟
            rest_minutes = random.uniform(args.rest_min, args.rest_max)
            rest_seconds = int(rest_minutes * 60)

            remaining = get_stats()['without_score']

            print("\n" + "="*50)
            print(f" 本批完成! 休息 {rest_minutes:.1f} 分钟 ({rest_seconds} 秒)")
            print(f" 剩余未评分: {remaining}")
            print(f" 按 Ctrl+C 停止，或等待自动继续...")
            print("="*50 + "\n")

            # 倒计时显示进度
            for i in range(rest_seconds):
                if i % 60 == 0 and i > 0:
                    print(f"  剩余休息时间: {rest_seconds - i} 秒...")
                time.sleep(1)
    else:
        update_batch(args.batch)


if __name__ == '__main__':
    main()
