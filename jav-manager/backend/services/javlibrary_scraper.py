# """
# JavLibrary 爬虫
# 用于抓取 JavLibrary 榜单数据
#
# JavLibrary 有 Cloudflare 反爬保护，需要通过代理或 Playwright 绕过
# 已暂停开发，等待代理可用
# """

# import httpx
# import random
# import re
# import time
# from bs4 import BeautifulSoup
# from typing import Optional, List, Dict, Any


# class JavLibraryScraper:
#     """JavLibrary 爬虫"""
#
#     def __init__(self):
#         from app import config
#         self.domains = config.JAVLIBRARY_DOMAINS
#         self.current_domain = random.choice(self.domains)
#         self.min_delay = config.REQUEST_MIN_DELAY
#         self.max_delay = config.REQUEST_MAX_DELAY
#         self.timeout = config.REQUEST_TIMEOUT
#         self.use_proxy = config.USE_PROXY
#         self.proxy_url = config.PROXY_URL
#         self.scraper_mode = config.SCRAPER_MODE
#
#     def get_base_url(self):
#         return f"https://{self.current_domain}"
#
#     def rotate_domain(self):
#         """轮换域名"""
#         try:
#             current_idx = self.domains.index(self.current_domain)
#         except ValueError:
#             current_idx = 0
#         next_idx = (current_idx + 1) % len(self.domains)
#         self.current_domain = self.domains[next_idx]
#
#     def fetch_with_curl(self, path: str, retries: int = 3) -> Optional[str]:
#         """使用 curl_cffi 发起请求"""
#         from curl_cffi import requests as curl_requests
#
#         for attempt in range(retries):
#             try:
#                 url = f"{self.get_base_url()}{path}"
#                 headers = {
#                     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
#                     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#                     'Accept-Language': 'en-US,en;q=0.5',
#                 }
#
#                 proxies = {}
#                 if self.use_proxy and self.proxy_url:
#                     proxies = {'http': self.proxy_url, 'https': self.proxy_url}
#
#                 resp = curl_requests.get(
#                     url,
#                     headers=headers,
#                     proxies=proxies,
#                     impersonate='chrome110',
#                     timeout=self.timeout
#                 )
#                 resp.raise_for_status()
#
#                 time.sleep(random.uniform(self.min_delay, self.max_delay))
#
#                 return resp.text
#
#             except Exception as e:
#                 if attempt < retries - 1:
#                     self.rotate_domain()
#                     time.sleep(2)
#                 else:
#                     print(f"[JavLibrary] curl_cffi failed: {e}")
#
#         return None
#
#     def fetch_with_playwright(self, path: str, retries: int = 3) -> Optional[str]:
#         """使用 Playwright 发起请求"""
#         from playwright.sync_api import sync_playwright
#
#         for attempt in range(retries):
#             try:
#                 url = f"{self.get_base_url()}{path}"
#                 headers = {
#                     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
#                 }
#
#                 with sync_playwright() as p:
#                     browser_config = {}
#                     if self.use_proxy and self.proxy_url:
#                         browser_config['proxy'] = {'server': self.proxy_url}
#
#                     browser = p.chromium.launch(headless=True, **browser_config)
#                     context = browser.new_context(user_agent=headers['User-Agent'])
#                     page = context.new_page()
#
#                     page.goto(url, timeout=60000)
#                     page.wait_for_load_state('networkidle', timeout=30000)
#
#                     content = page.content()
#                     browser.close()
#
#                     time.sleep(random.uniform(self.min_delay, self.max_delay))
#                     return content
#
#             except Exception as e:
#                 if attempt < retries - 1:
#                     self.rotate_domain()
#                     time.sleep(2)
#                 else:
#                     print(f"[JavLibrary] Playwright failed: {e}")
#
#         return None
#
#     def fetch(self, path: str, retries: int = 3) -> Optional[str]:
#         """发起请求 (自动选择模式)"""
#         if self.scraper_mode == 'playwright':
#             return self.fetch_with_playwright(path, retries)
#         else:
#             return self.fetch_with_curl(path, retries)
#
#     def parse_movie_code(self, title: str) -> Optional[str]:
#         """从标题中提取影片番号"""
#         # JavLibrary 格式: ABC-123 或类似的
#         match = re.search(r'([A-Z]+-\d+)', title.upper())
#         if match:
#             return match.group(1)
#         return None
#
#     def parse_best_rated_page(self, html: str) -> List[Dict[str, Any]]:
#         """解析最佳评分榜单页面"""
#         soup = BeautifulSoup(html, 'html.parser')
#         items = []
#
#         # JavLibrary 榜单页面结构
#         # 每行是一个视频条目
#         for video_item in soup.select('.video-item'):
#             try:
#                 # 提取排名
#                 rank_elem = video_item.select_one('.rank')
#                 rank = int(rank_elem.text.strip()) if rank_elem else 0
#
#                 # 提取标题和链接
#                 title_elem = video_item.select_one('.video-title')
#                 if not title_elem:
#                     continue
#
#                 title = title_elem.text.strip()
#                 link_elem = title_elem.select_one('a')
#                 href = link_elem.get('href', '') if link_elem else ''
#
#                 # 提取番号
#                 code = self.parse_movie_code(title)
#
#                 # 提取演员
#                 actors = []
#                 for actor_link in video_item.select('.actor a'):
#                     actors.append(actor_link.text.strip())
#
#                 # 提取评分
#                 score_elem = video_item.select_one('.score')
#                 score = None
#                 if score_elem:
#                     score_text = score_elem.text.strip()
#                     score_match = re.search(r'([\d.]+)', score_text)
#                     if score_match:
#                         score = float(score_match.group(1))
#
#                 items.append({
#                     'rank': rank,
#                     'code': code,
#                     'title': title,
#                     'actors': actors,
#                     'score': score,
#                     'href': href
#                 })
#
#             except Exception as e:
#                 print(f"[JavLibrary] Error parsing item: {e}")
#                 continue
#
#         return items
#
#     def scrape_best_rated(self, page: int = 1) -> List[Dict[str, Any]]:
#         """抓取最佳评分榜单"""
#         path = f"/cn/vl_bestrated.php?&mode=2&page={page}"
#         html = self.fetch(path)
#
#         if not html:
#             print(f"[JavLibrary] Failed to fetch page {page}")
#             return []
#
#         return self.parse_best_rated_page(html)
#
#     def scrape_all_best_rated(self, total_pages: int = 10) -> List[Dict[str, Any]]:
#         """抓取完整榜单 (多页)"""
#         all_items = []
#
#         for page in range(1, total_pages + 1):
#             items = self.scrape_best_rated(page)
#             if not items:
#                 print(f"[JavLibrary] No more items on page {page}")
#                 break
#
#             all_items.extend(items)
#             print(f"[JavLibrary] Scraped page {page}: {len(items)} items")
#
#             # 最后一页可能不满
#             if len(items) < 40:
#                 break
#
#         return all_items


# def scrape_javlibrary_chart(chart) -> List[Dict[str, Any]]:
#     """抓取 JavLibrary 榜单"""
#     scraper = JavLibraryScraper()
#
#     # 计算需要抓取的页数
#     # JavLibrary 每页大约 40 部
#     pages = (chart.total_count + 39) // 40
#     pages = min(pages, 20)  # 最多 20 页
#
#     items = scraper.scrape_all_best_rated(pages)
#     return items


# if __name__ == '__main__':
#     # 测试爬虫
#     print("[JavLibrary] Testing scraper...")
#     scraper = JavLibraryScraper()
#
#     # 测试单页
#     html = scraper.fetch("/cn/vl_bestrated.php?&mode=2&page=1")
#     if html:
#         print(f"[JavLibrary] Fetched {len(html)} bytes")
#         items = scraper.parse_best_rated_page(html)
#         print(f"[JavLibrary] Parsed {len(items)} items")
#         for item in items[:5]:
#             print(f"  Rank {item['rank']}: {item['code']} - {item['title']}")
#             print(f"    Actors: {item['actors']}")
#     else:
#         print("[JavLibrary] Failed to fetch page")
