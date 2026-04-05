"""
JavBus 爬虫服务

用于获取演员新片信息，基于 curl_cffi 实现。
"""

import re
import time
import random
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

DEFAULT_DOMAINS = ["javbus.com", "javbus.bond", "cdnbus.bond", "dmmbus.cyou"]


class JavBusScraper:
    """JavBus 爬虫"""

    def __init__(
        self,
        domains: Optional[List[str]] = None,
        min_delay: float = 3.0,
        max_delay: float = 6.0,
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.domains = domains or DEFAULT_DOMAINS
        self.domain_index = 0
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = None
        self._init_session()

    def _init_session(self):
        """初始化 curl_cffi session"""
        try:
            from curl_cffi import requests as curl_requests
            self.curl_requests = curl_requests
            self.session = curl_requests.Session(impersonate="chrome", timeout=self.timeout)
        except ImportError:
            logger.warning("curl_cffi not installed, trying with httpx")
            self.curl_requests = None
            self.session = None

    def get_current_domain(self) -> str:
        """获取当前域名"""
        return self.domains[self.domain_index % len(self.domains)]

    def rotate_domain(self):
        """轮换域名"""
        self.domain_index = (self.domain_index + 1) % len(self.domains)
        logger.info(f"Rotated to domain: {self.get_current_domain()}")

    def random_delay(self):
        """随机延迟"""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)

    def _get_base_url(self) -> str:
        """获取基础 URL"""
        return f"https://{self.get_current_domain()}"

    def _handle_error(self, error: Exception, retry_count: int) -> bool:
        """处理错误，决定是否重试"""
        error_str = str(error).lower()
        status_code = getattr(error, 'response', None)

        if status_code == 429 or "rate" in error_str or "too many" in error_str:
            logger.warning(f"Rate limited on {self.get_current_domain()}")
            self.rotate_domain()
            if retry_count < self.max_retries:
                time.sleep(5 * (retry_count + 1))
                return True
            return False

        if status_code == 403 or "403" in error_str or "forbidden" in error_str:
            logger.warning(f"403 Forbidden on {self.get_current_domain()}")
            self.rotate_domain()
            if retry_count < self.max_retries:
                time.sleep(2 * (retry_count + 1))
                return True
            return False

        if "timeout" in error_str or "timed out" in error_str:
            logger.warning(f"Timeout on {self.get_current_domain()}")
            self.rotate_domain()
            if retry_count < self.max_retries:
                return True
            return False

        return False

    def get_actor_page(self, actor_id: str, page: int = 1) -> Dict[str, Any]:
        """获取演员页面

        Args:
            actor_id: JavBus 演员 ID
            page: 页码（从 1 开始）

        Returns:
            Dict，包含 movies 列表和 has_next 布尔值
        """
        url = f"{self._get_base_url()}/star/{actor_id}"
        if page > 1:
            url += f"/{page}"

        for retry in range(self.max_retries):
            try:
                self.random_delay()

                if self.session:
                    response = self.session.get(url)
                else:
                    import httpx
                    response = httpx.get(url, timeout=self.timeout)

                status_code = response.status_code

                if status_code == 403:
                    if self._handle_error(Exception("403 Forbidden"), retry):
                        continue
                    return {"movies": [], "has_next": False, "error": "403 Forbidden"}

                if status_code != 200:
                    err = Exception(f"HTTP {status_code}")
                    if self._handle_error(err, retry):
                        continue
                    return {"movies": [], "has_next": False, "error": f"HTTP {status_code}"}

                return self._parse_actor_page(response.text, page)

            except Exception as e:
                logger.error(f"Error fetching actor page {url}: {e}")
                if self._handle_error(e, retry):
                    continue
                return {"movies": [], "has_next": False, "error": str(e)}

        return {"movies": [], "has_next": False, "error": "Max retries exceeded"}

    def _parse_actor_page(self, html: str, page: int) -> Dict[str, Any]:
        """解析演员页面 HTML

        Args:
            html: HTML 内容
            page: 当前页码

        Returns:
            Dict，包含 movies 列表和 has_next
        """
        movies = []

        try:
            # 匹配电影项目
            # JavBus 页面结构: <a class="movie-box" href="...">...<date>CODE</date>...<date>DATE</date>...
            pattern = r'<a\s+class="movie-box"[^>]*href="([^"]+)"[^>]*>.*?<date>([^<]+)</date>.*?<date>([^<]+)</date>'
            matches = re.findall(pattern, html, re.DOTALL)

            for match in matches:
                url, code_or_title, date = match
                # 第一个 date 通常是标题，第二个是发行日期
                code_match = re.match(r"^([A-Z]+-\d+)", code_or_title)

                if code_match:
                    code = code_match.group(1)
                    movies.append({
                        "code": code,
                        "title": code_or_title.strip(),
                        "release_date": date.strip(),
                        "source_type": "javbus"
                    })

            # 备选方案：简单匹配
            if not movies:
                pattern2 = r'<a\s+class="movie-box"[^>]*>.*?<date>([A-Z]+-\d+)</date>'
                matches2 = re.findall(pattern2, html, re.DOTALL)
                for code in matches2:
                    movies.append({
                        "code": code,
                        "title": "",
                        "release_date": "",
                        "source_type": "javbus"
                    })

            # 检查是否有下一页
            has_next = "下页" in html or "next" in html.lower()

            # 检查是否有"无更多"
            if "没有找到" in html or "no result" in html.lower():
                has_next = False

        except Exception as e:
            logger.error(f"Error parsing actor page: {e}")

        return {
            "movies": movies,
            "has_next": has_next,
            "page": page
        }

    def search_movie(self, code: str) -> Optional[Dict[str, Any]]:
        """搜索电影

        Args:
            code: 电影番号

        Returns:
            电影信息 Dict 或 None
        """
        url = f"{self._get_base_url()}/search/{code}"

        for retry in range(self.max_retries):
            try:
                self.random_delay()

                if self.session:
                    response = self.session.get(url)
                else:
                    import httpx
                    response = httpx.get(url, timeout=self.timeout)

                if response.status_code == 403:
                    if self._handle_error(Exception("403 Forbidden"), retry):
                        continue
                    return None

                if response.status_code != 200:
                    if self._handle_error(Exception(f"HTTP {response.status_code}"), retry):
                        continue
                    return None

                return self._parse_search_results(response.text, code)

            except Exception as e:
                logger.error(f"Error searching movie {code}: {e}")
                if self._handle_error(e, retry):
                    continue
                return None

        return None

    def _parse_search_results(self, html: str, code: str) -> Optional[Dict[str, Any]]:
        """解析搜索结果"""
        try:
            pattern = r'<a\s+class="movie-box"[^>]*href="([^"]+)"[^>]*>.*?<date>([A-Z]+-\d+)</date>.*?<date>([^<]+)</date>'
            matches = re.findall(pattern, html, re.DOTALL)

            for url, found_code, date in matches:
                if found_code.upper() == code.upper():
                    return {
                        "code": found_code,
                        "title": found_code,
                        "release_date": date.strip(),
                        "source_type": "javbus"
                    }

            # 备选
            if code.upper() in html:
                code_pattern = r'<a\s+class="movie-box"[^>]*href="([^"]+)"[^>]*>.*?<date>([A-Z]+-\d+)</date>'
                matches2 = re.findall(code_pattern, html, re.DOTALL)
                for url, found_code in matches2:
                    if found_code.upper() == code.upper():
                        return {
                            "code": found_code,
                            "title": found_code,
                            "release_date": "",
                            "source_type": "javbus"
                        }

        except Exception as e:
            logger.error(f"Error parsing search results: {e}")

        return None

    def close(self):
        """关闭 session"""
        if self.session:
            try:
                self.session.close()
            except Exception:
                pass
            self.session = None


def fetch_actor_releases(actor_id: str, javbus_id: str, limit_pages: int = 2) -> Dict[str, Any]:
    """获取演员新片

    Args:
        actor_id: 数据库中 actor 的 id
        javbus_id: JavBus 演员 ID
        limit_pages: 限制爬取页数（最新内容）

    Returns:
        结果 Dict，包含 success、items_added 等
    """
    from app import db
    from models import Actor, ActorRelease, Movie

    actor = db.session.query(Actor).get(actor_id)
    if not actor:
        return {"success": False, "error": "Actor not found", "actor_id": actor_id}

    if not javbus_id:
        return {"success": False, "error": "No javbus_id", "actor_id": actor_id}

    scraper = JavBusScraper()
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

    try:
        for page in range(1, limit_pages + 1):
            result = scraper.get_actor_page(javbus_id, page)
            movies = result.get('movies', [])

            for movie in movies:
                if movie['code'] not in existing_codes:
                    new_items.append(movie)
                    existing_codes.add(movie['code'])  # 防止同一页重复

            if not result.get('has_next'):
                break

        # 保存新影片
        for movie in new_items:
            # 检查是否已存在于 movies 表
            existing_movie = db.session.query(Movie).filter_by(code=movie['code']).first()

            release = ActorRelease(
                actor_id=actor_id,
                code=movie['code'],
                title=movie.get('title', ''),
                release_date=movie.get('release_date', ''),
                source_type='javbus',
                is_released=existing_movie is not None,
                detected_at=__import__('datetime').datetime.utcnow()
            )
            db.session.add(release)

        db.session.commit()
        logger.info(f"Fetched {len(new_items)} new releases for actor {actor.name}")

    except Exception as e:
        logger.error(f"Error fetching actor releases: {e}")
        db.session.rollback()
        return {"success": False, "error": str(e), "actor_id": actor_id}
    finally:
        scraper.close()

    return {
        "success": True,
        "items_added": len(new_items),
        "actor_id": actor_id,
        "actor_name": actor.name
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    scraper = JavBusScraper()

    # 测试
    print("Testing get_actor_page...")
    result = scraper.get_actor_page("9ay", page=1)
    print(f"Movies found: {len(result.get('movies', []))}")
    print(f"Has next: {result.get('has_next')}")
    print(f"First 3 movies: {result.get('movies', [])[:3]}")

    scraper.close()
