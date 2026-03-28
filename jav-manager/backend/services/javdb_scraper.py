import httpx
import random
import re
import time
from bs4 import BeautifulSoup


class JavDBScraper:
    """JavDB 爬虫"""

    def __init__(self):
        # 延迟导入，避免循环导入
        from app import config
        self.domains = config.JAVDB_DOMAINS
        self.current_domain = random.choice(self.domains)
        self.min_delay = config.REQUEST_MIN_DELAY
        self.max_delay = config.REQUEST_MAX_DELAY
        self.timeout = config.REQUEST_TIMEOUT

    def get_base_url(self):
        return f"https://{self.current_domain}"

    def rotate_domain(self):
        """轮换域名"""
        try:
            current_idx = self.domains.index(self.current_domain)
        except ValueError:
            current_idx = 0
        next_idx = (current_idx + 1) % len(self.domains)
        self.current_domain = self.domains[next_idx]

    def fetch(self, path, retries=3):
        """发起请求"""
        for attempt in range(retries):
            try:
                url = f"{self.get_base_url()}{path}"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                }

                resp = httpx.get(url, headers=headers, timeout=self.timeout)
                resp.raise_for_status()

                # 随机延迟
                time.sleep(random.uniform(self.min_delay, self.max_delay))

                return resp.text

            except Exception as e:
                if attempt < retries - 1:
                    self.rotate_domain()
                    time.sleep(1)
                else:
                    raise e

        return None

    def search_movie(self, code):
        """搜索影片"""
        html = self.fetch(f"/search?q={code}&f=all")

        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # 查找搜索结果
        movie_link = None
        for item in soup.select('.movie-list .item'):
            title = item.select_one('.video-title')
            if title and code.upper() in title.text.upper():
                link = item.select_one('a')
                if link:
                    movie_link = link.get('href')
                    break

        if not movie_link:
            # 尝试精确匹配
            for item in soup.select('.movie-list .item'):
                title = item.select_one('.video-title')
                if title:
                    title_text = title.text.strip()
                    # 移除后缀（如高清、无码等）
                    title_text = re.sub(r'\s*\[.*?\]\s*$', '', title_text)
                    if code.upper().replace('-', '') in title_text.upper().replace('-', ''):
                        link = item.select_one('a')
                        if link:
                            movie_link = link.get('href')
                            break

        if movie_link:
            return self.get_movie_detail(movie_link)

        return None

    def get_movie_detail(self, path):
        """获取影片详情"""
        html = self.fetch(path)

        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # 获取评分
        score_elem = soup.select_one('.score .value')
        score = float(score_elem.text) if score_elem else None

        # 获取 JavDB ID
        javdb_id_match = re.search(r'/v/([A-Z0-9]+)', path)
        javdb_id = javdb_id_match.group(1) if javdb_id_match else None

        # 获取标题
        title_elem = soup.select_one('.movie-title')
        title = title_elem.text.strip() if title_elem else None

        # 获取演员
        actors = []
        for actor_link in soup.select('.panel-block .actor a'):
            actors.append(actor_link.text.strip())

        # 获取封面
        cover_elem = soup.select_one('.cover img')
        cover_url = cover_elem.get('src') if cover_elem else None

        return {
            'code': None,  # 需要从标题提取
            'title': title,
            'score': score,
            'javdb_id': javdb_id,
            'actors': actors,
            'cover_url': cover_url
        }


def fetch_movie_score(code):
    """获取单个影片评分"""
    scraper = JavDBScraper()
    detail = scraper.search_movie(code)
    return detail.get('score') if detail else None


def fetch_movie_details(code):
    """获取影片完整信息"""
    scraper = JavDBScraper()
    return scraper.search_movie(code)
