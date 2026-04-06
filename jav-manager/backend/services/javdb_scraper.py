import logging
import random
import re
import time
from bs4 import BeautifulSoup
from typing import Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def _get_config():
    """延迟加载 config 避免循环导入"""
    from importlib import import_module
    return import_module('config')


class JavDBScraper:
    """JavDB 爬虫"""

    def __init__(self):
        # 延迟导入，避免循环导入
        from app import config
        self.domains = config.JAVDB_DOMAINS
        self.current_domain = random.choice(self.domains)
        # 使用配置中的统一延迟参数
        self.min_delay = config.REQUEST_MIN_DELAY
        self.max_delay = config.REQUEST_MAX_DELAY
        self.timeout = config.REQUEST_TIMEOUT
        self.enable_proxy = config.ENABLE_SYSTEM_PROXY
        self.proxy_url = config.SYSTEM_PROXY_URL

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

    def fetch(self, path: str, retries: int = 3) -> Optional[str]:
        """使用 curl_cffi 发起请求"""
        from curl_cffi import requests as curl_requests

        for attempt in range(retries):
            try:
                url = f"{self.get_base_url()}{path}"
                logger.info(f"[JavDBScraper] Fetching URL: {url}")

                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                }

                proxies = {}
                if self.enable_proxy and self.proxy_url:
                    proxies = {'http': self.proxy_url, 'https': self.proxy_url}
                    logger.info(f"[JavDBScraper] Using proxy: {self.proxy_url}")

                resp = curl_requests.get(
                    url,
                    headers=headers,
                    proxies=proxies,
                    impersonate='chrome110',
                    timeout=self.timeout
                )
                resp.raise_for_status()
                logger.info(f"[JavDBScraper] Response received: {resp.status_code}")

                # 随机延迟
                delay = random.uniform(self.min_delay, self.max_delay)
                logger.info(f"[JavDBScraper] Sleeping for {delay:.1f}s (delay: {self.min_delay}-{self.max_delay}s)")
                time.sleep(delay)

                return resp.text

            except Exception as e:
                logger.warning(f"[JavDBScraper] Request failed (attempt {attempt+1}/{retries}): {e}")
                if attempt < retries - 1:
                    self.rotate_domain()
                    time.sleep(2)
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
            return self.get_movie_detail(movie_link, code)

        return None

    def get_movie_detail(self, path, code=None):
        """获取影片详情

        Args:
            path: 影片详情页路径
            code: 影片番号（可选，用于验证）
        """
        html = self.fetch(path)

        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # 获取评分 - 使用正则表达式解析
        score = self._parse_score(html)

        # 获取 JavDB ID
        javdb_id_match = re.search(r'/v/([A-Za-z0-9]+)', path)
        javdb_id = javdb_id_match.group(1) if javdb_id_match else None

        # 获取标题: .title.is-4 .current-title
        title_elem = soup.select_one('.title.is-4 .current-title')
        if not title_elem:
            title_elem = soup.select_one('.video-title')
        title = title_elem.text.strip() if title_elem else None

        # 如果没有传入 code，从标题提取
        if not code and title:
            code_match = re.search(r'([A-Z]+-\d+)', title.upper())
            if code_match:
                code = code_match.group(1)

        # 获取演员: .panel-block 中 Actor(s): 下面的 female (♀)
        actors = []
        for panel in soup.select('.panel-block'):
            strong = panel.select_one('strong')
            if strong and 'Actor' in strong.text:  # Actor(s):
                # 获取所有 actor 链接，只保留 female
                for link in panel.select('a[href*="/actors/"]'):
                    # 检查是否是 female
                    symbol = link.find_next_sibling('strong', class_='symbol female')
                    if symbol:
                        actors.append(link.text.strip())

        # 获取封面: .video-cover
        cover_url = None
        cover = soup.select_one('.video-cover')
        if cover:
            cover_url = cover.get('src')

        return {
            'code': code,
            'title': title,
            'score': score,
            'javdb_id': javdb_id,
            'actors': ','.join(actors) if actors else None,
            'cover_url': cover_url
        }

    def _parse_score(self, html: str):
        """解析评分 - 基于 JavDB 5分制评分格式

        HTML样例: <span class="value"><span class="score-stars">...</span>&nbsp;4.29分, 由564人評價</span>
        返回: 5分制评分如 4.29
        """
        # 模式1: 匹配 JavDB 评分格式 X.XX分 (5分制)
        match = re.search(r'class="value"[^>]*>.*?&nbsp;(\d+\.\d{1,2})分', html, re.DOTALL)
        if match:
            return float(match.group(1))

        # 模式2: 匹配中文格式 X.X分
        match = re.search(r'>&nbsp;(\d+\.\d)\s*分', html)
        if match:
            return float(match.group(1))

        # 模式3: 匹配 X.X / 5 格式
        match = re.search(r'(\d+\.\d)\s*/\s*5', html)
        if match:
            return float(match.group(1))

        # 模式4: data-score 属性 (10分制，需除以2)
        match = re.search(r'data-score="(\d+\.?\d*)"', html)
        if match:
            score = float(match.group(1))
            if score > 10:  # 如果是10分制
                return round(score / 2, 2)
            return score

        return None


def fetch_movie_score(code):
    """获取单个影片评分"""
    scraper = JavDBScraper()
    detail = scraper.search_movie(code)
    return detail.get('score') if detail else None


def fetch_movie_details(code):
    """获取影片完整信息"""
    scraper = JavDBScraper()
    return scraper.search_movie(code)


def fetch_actor_releases(actor_id: int, db=None, limit_months: int = 3) -> dict:
    """从 JavDB 获取演员最近新作

    Args:
        actor_id: 数据库中 actor 的 id
        limit_months: 限制获取最近几个月的影片

    Returns:
        结果 Dict，包含 success、items_added 等
    """
    import urllib.parse
    from datetime import datetime, timedelta
    from bs4 import BeautifulSoup

    if db is None:
        from app import db
    from models import Actor, ActorRelease, Movie

    logger.info(f"[ActorReleases] Function called for actor_id={actor_id}, limit_months={limit_months}")

    actor = db.session.query(Actor).get(actor_id)
    if not actor:
        logger.warning(f"[ActorReleases] Actor not found for actor_id={actor_id}")
        return {"success": False, "error": "Actor not found", "actor_id": actor_id}

    logger.info(f"[ActorReleases] Found actor: {actor.name} (id={actor_id})")

    scraper = JavDBScraper()
    new_items = []
    existing_codes = set()

    # 获取该演员已知的影片码
    existing_releases = db.session.query(ActorRelease).filter_by(actor_id=actor_id).all()
    for release in existing_releases:
        existing_codes.add(release.code)

    # 也检查 movies 表中该演员参演的影片
    movies_with_actor = db.session.query(Movie).filter(Movie.actors.contains(actor.name)).all()
    for movie in movies_with_actor:
        if movie.code:
            existing_codes.add(movie.code)

    logger.info(f"[ActorReleases] Existing releases: {len(existing_releases)}, Movies in library: {len(movies_with_actor)}, Unique codes: {len(existing_codes)}")

    # 确定演员的 JavDB 链接
    actor_javdb_link = None

    # 优先使用已有的 javdb_id
    if actor.javdb_id:
        actor_javdb_link = f"/actors/{actor.javdb_id}"
        logger.info(f"[ActorReleases] Using existing javdb_id for actor {actor.name}: {actor_javdb_link}")
    else:
        # 否则从影片中查找（仅针对新关注的演员）
        sample_movie = None
        for m in movies_with_actor:
            if m.code and '-' in m.code:
                sample_movie = m
                break

        if not sample_movie:
            return {"success": False, "error": "No movie found for actor", "actor_id": actor_id}

        # 搜索影片获取演员链接
        search_url = f"/search?q={urllib.parse.quote(sample_movie.code)}&f=all"
        html = scraper.fetch(search_url)
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            movie_link = soup.select_one('a[href^="/v/"]')
            if movie_link:
                movie_href = movie_link.get('href')
                detail_html = scraper.fetch(movie_href)
                if detail_html:
                    detail_soup = BeautifulSoup(detail_html, 'html.parser')
                    for al in detail_soup.select('a[href^="/actors/"]'):
                        href = al.get('href')
                        if 'censored' not in href and 'uncensored' not in href and 'western' not in href:
                            next_elem = al.find_next_sibling('strong')
                            if next_elem and 'female' in str(next_elem.get('class', [])):
                                # 检查演员名字是否匹配
                                linked_actor_name = al.text.strip()
                                if linked_actor_name == actor.name:
                                    # 找到了，保存 javdb_id
                                    actor_javdb_id = href.split('/')[-1]
                                    actor.javdb_id = actor_javdb_id
                                    db.session.commit()
                                    logger.info(f"Found and saved javdb_id for actor {actor.name}: {actor_javdb_id}")
                                    actor_javdb_link = href
                                    break

    if not actor_javdb_link:
        logger.warning(f"[ActorReleases] Could not find JavDB link for actor {actor.name}")
        return {"success": False, "error": "Could not find actor JavDB link", "actor_id": actor_id}

    try:
        # 计算日期范围
        today = datetime.utcnow()
        date_limit = today - timedelta(days=limit_months * 30)

        logger.info(f"[ActorReleases] Starting to fetch actor page for {actor.name}: {actor_javdb_link} (limit: {limit_months} months)")

        # 抓取演员页面（只抓取第一页，因为是按时间排序的）
        actor_html = scraper.fetch(actor_javdb_link)
        if not actor_html:
            logger.error(f"[ActorReleases] Failed to fetch actor page for {actor.name}: {actor_javdb_link}")
            return {"success": False, "error": "Could not fetch actor page", "actor_id": actor_id}

        logger.info(f"[ActorReleases] Successfully fetched actor page for {actor.name}")
        if not actor_html:
            return {"success": False, "error": "Could not fetch actor page", "actor_id": actor_id}

        actor_soup = BeautifulSoup(actor_html, 'html.parser')
        movie_items = actor_soup.select('.movie-list .item')

        logger.info(f"[ActorReleases] Found {len(movie_items)} movie items on actor page for {actor.name}")

        for item in movie_items:
            title_elem = item.select_one('.video-title')
            meta = item.select_one('.meta')

            if not meta:
                continue

            date_str = meta.text.strip()
            try:
                movie_date = datetime.strptime(date_str, '%m/%d/%Y')
                # 检查是否在日期范围内
                if movie_date < date_limit:
                    # 列表是按时间排序的，后面的都不会在范围内
                    break

                if movie_date <= today:
                    code = ''
                    # 尝试从 .video-title strong 中提取 code
                    if title_elem:
                        strong = title_elem.select_one('strong')
                        if strong:
                            code_match = re.search(r'([A-Z]+-\d+)', strong.text.strip())
                            if code_match:
                                code = code_match.group(1)
                        else:
                            code_match = re.search(r'([A-Z]+-\d+)', title_elem.text.strip())
                            if code_match:
                                code = code_match.group(1)

                    if code and code not in existing_codes:
                        new_items.append({
                            'code': code,
                            'title': title_elem.text.strip() if title_elem else '',
                            'release_date': date_str
                        })
                        existing_codes.add(code)
            except ValueError:
                pass

        logger.info(f"[ActorReleases] Parsed {len(new_items)} new releases within date range for {actor.name}")

        # 保存新影片
        for movie in new_items:
            existing_movie = db.session.query(Movie).filter_by(code=movie['code']).first()

            release = ActorRelease(
                actor_id=actor_id,
                code=movie['code'],
                title=movie.get('title', ''),
                release_date=movie.get('release_date', ''),
                source_type='javdb',
                is_released=existing_movie is not None,
                detected_at=datetime.utcnow()
            )
            db.session.add(release)

        db.session.commit()
        logger.info(f"[ActorReleases] Successfully saved {len(new_items)} new releases for actor {actor.name} to database")

    except Exception as e:
        logger.error(f"[ActorReleases] Error fetching actor releases from JavDB for {actor.name}: {e}")
        db.session.rollback()
        return {"success": False, "error": str(e), "actor_id": actor_id}

    logger.info(f"[ActorReleases] Completed for actor {actor.name}: {len(new_items)} items added")
    return {
        "success": True,
        "items_added": len(new_items),
        "actor_id": actor_id,
        "actor_name": actor.name
    }
