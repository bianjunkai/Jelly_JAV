import os
import json

# Jellyfin 配置
JELLYFIN_URL = os.getenv('JELLYFIN_URL', 'http://192.168.50.20:8096/')
JELLYFIN_API_KEY = os.getenv('JELLYFIN_API_KEY', '')

# 数据库
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "data.db")}')

# 爬虫配置
JAVDB_DOMAINS = ['javdb.com', 'javdb5.com', 'javdb4.com']
JAVBUS_DOMAINS = ['javbus.com', 'javbus5.com', 'javbus3.com']
JAVLIBRARY_DOMAINS = ['www.javlibrary.com']
REQUEST_MIN_DELAY = 3
REQUEST_MAX_DELAY = 6
REQUEST_TIMEOUT = 30

# 系统级代理配置 (启用后所有爬虫都走代理)
ENABLE_SYSTEM_PROXY = False
SYSTEM_PROXY_URL = 'http://192.168.1.15:7893'

# JavDB 配置
JAVDB_COOKIE = ''  # 登录 cookie，格式: "_jdb_session=xxx; locale=zh; over18=1"
JAVDB_YEAR_CHART_YEARS = [2025, 2026]  # 要抓取的年份榜单

# JavLibrary 配置
JAVLIBRARY_CSV_PATH = ''  # JavLibrary CSV 文件路径，用于导入榜单数据

# 启动配置
AUTO_SYNC_ON_STARTUP = False
AUTO_UPDATE_SCORES = False

# 评分权重（可配置）
WEIGHT_BASE = 50
WEIGHT_JAVDB_HIGH = 20       # >=4.5
WEIGHT_JAVDB_MEDIUM = 10    # 4.2-4.5
WEIGHT_JAVDB_LOW = -15      # 3.5-3.9
WEIGHT_JAVDB_VERY_LOW = -25 # <3.5
WEIGHT_DUAL_CHART = 30
WEIGHT_SINGLE_CHART = 20
WEIGHT_YEAR_CHART = 10
WEIGHT_MULTI_ACTOR = 5
WEIGHT_FOLLOWED_ACTOR = 10
