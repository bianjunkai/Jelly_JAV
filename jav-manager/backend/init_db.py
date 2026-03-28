#!/usr/bin/env python3
"""
数据库初始化脚本
用于首次运行或重建数据库
"""
import os
import sys

# 添加 backend 目录到 path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from app import app, db
from models import Movie, Actor, Chart, ChartItem, Report, TodoItem, ScoreHistory, TaskLog
from services.chart_scraper import init_default_charts

def reset_database():
    """重建数据库（删除所有表后重建）"""
    with app.app_context():
        print("正在删除所有表...")
        db.drop_all()
        print("正在创建所有表...")
        db.create_all()
        print("正在初始化默认榜单...")
        init_default_charts()
        print("数据库初始化完成!")

def init_database():
    """初始化数据库（如果不存在则创建）"""
    with app.app_context():
        db.create_all()
        init_default_charts()
        print("数据库初始化完成!")

if __name__ == '__main__':
    if '--reset' in sys.argv:
        confirm = input("警告：这将删除所有现有数据！是否继续？(y/N): ")
        if confirm.lower() == 'y':
            reset_database()
        else:
            print("已取消")
    else:
        init_database()
