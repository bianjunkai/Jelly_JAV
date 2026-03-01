JELLYFIN_URL = "http://192.168.50.20:8096/"
JELLYFIN_API_KEY = "f7885a8704d94788883acc69d20e3780"

# RSSHub 地址 (NAS 上 Docker 部署)
RSSHUB_URL = "http://192.168.50.20:5200"
# JAVBus 配置
JAVBUS_DOMAINS = ["busjav.cyou", "cdnbus.cyou", "javbus.com"]  # 可配置多个域名，遇到超时时轮换使用
JAVBUS_LANGUAGE = ""  # 语言: 空=中文, en=英语, ja=日语, ko=韩语

AUTO_REFRESH_ON_STARTUP = True
RSS_UPDATE_ON_STARTUP = False  # 启动时是否更新RSS订阅

# RSS Rate Limiting (避免 429 错误)
RSS_REQUEST_DELAY = 2.0  # 每次请求间隔（秒）
RSS_MAX_RETRIES = 3      # 429 错误最大重试次数
RSS_RETRY_BASE_DELAY = 5 # 指数退避基础延迟（秒）