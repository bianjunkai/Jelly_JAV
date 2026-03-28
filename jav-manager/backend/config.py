import os

# Jellyfin 配置
JELLYFIN_URL = os.getenv('JELLYFIN_URL', 'http://192.168.50.20:8096/')
JELLYFIN_API_KEY = os.getenv('JELLYFIN_API_KEY', '')

# 数据库
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "data.db")}')

# 爬虫配置
JAVDB_DOMAINS = ['javdb.com', 'javdb5.com', 'javdb4.com']
JAVBUS_DOMAINS = ['javbus.com', 'javbus5.com', 'javbus3.com']
REQUEST_MIN_DELAY = 3
REQUEST_MAX_DELAY = 6
REQUEST_TIMEOUT = 30

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
WEIGHT_JAVBUS_ID = 15
