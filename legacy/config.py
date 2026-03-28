JELLYFIN_URL = "http://192.168.50.20:8096/"
JELLYFIN_API_KEY = "f7885a8704d94788883acc69d20e3780"

# JAVBus 配置
JAVBUS_DOMAINS = ["javsee.cyou", "buscdn.bond", "javbus.com"]  # 可配置多个域名，遇到超时时轮换使用
JAVBUS_LANGUAGE = ""  # 语言: 空=中文, en=英语, ja=日语, ko=韩语

# JAVDB 配置（多域名备选）
JAVDB_DOMAINS = ["javdb.com", "javdb5.com", "javdb4.com"]

# 爬虫 Rate Limiting
SCRAPE_MIN_DELAY = 3
SCRAPE_MAX_DELAY = 6
SCRAPE_MAX_RETRIES = 3

AUTO_REFRESH_ON_STARTUP = True
RSS_UPDATE_ON_STARTUP = True  # 启动时是否更新订阅

# RSS Rate Limiting (避免 429 错误) - 保留给现有 RSS 功能
RSS_REQUEST_DELAY = 2.0  # 每次请求间隔（秒）
RSS_MAX_RETRIES = 3      # 429 错误最大重试次数
RSS_RETRY_BASE_DELAY = 5 # 指数退避基础延迟（秒）

# 增量爬取开关
SCRAPE_ON_STARTUP = True  # 启动时自动爬取演员新片
SCRAPE_PAGES_LIMIT = 2   # 每次爬取最多页数
