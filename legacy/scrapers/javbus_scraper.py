"""
JavBus Scraper using curl_cffi.

Uses curl_cffi to bypass some Cloudflare protections.
"""

import re
import time
import random
import logging
from typing import Dict, Any, Optional, List

from .base import BaseScraper
from .exceptions import RateLimitError, DomainUnavailableError, ScrapingError

logger = logging.getLogger(__name__)

# Default domains for JavBus
DEFAULT_DOMAINS = ["javsee.cyou", "buscdn.bond", "javbus.com"]


class JavBusScraper(BaseScraper):
    """Scraper for JavBus using curl_cffi."""

    def __init__(
        self,
        domains: Optional[List[str]] = None,
        min_delay: float = 3.0,
        max_delay: float = 6.0,
        timeout: int = 30,
        max_retries: int = 3
    ):
        super().__init__(domains or DEFAULT_DOMAINS, min_delay, max_delay)
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = None
        self._init_session()

    def _init_session(self):
        """Initialize the curl_cffi session."""
        try:
            from curl_cffi import requests as curl_requests
            self.curl_requests = curl_requests
            self.session = curl_requests.Session(impersonate="chrome", timeout=self.timeout)
        except ImportError:
            logger.error("curl_cffi not installed. Install with: pip install curl_cffi")
            raise

    def random_delay(self):
        """Random delay between requests to avoid blocking."""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)

    def _get_base_url(self) -> str:
        """Get the current base URL."""
        return f"https://{self.get_current_domain()}"

    def _handle_error(self, error: Exception, retry_count: int, url: str) -> bool:
        """Handle errors with domain rotation and retry logic.

        Returns True if should retry, False otherwise.
        """
        error_str = str(error).lower()
        status_code = getattr(error, 'response', None)

        # Check for rate limit
        if status_code == 429 or "rate" in error_str or "too many" in error_str:
            logger.warning(f"Rate limited on {self.get_current_domain()}, rotating domain...")
            self.rotate_domain()
            if retry_count < self.max_retries:
                time.sleep(5 * (retry_count + 1))
                return True
            return False

        # Check for 403/Forbidden
        if status_code == 403 or "403" in error_str or "forbidden" in error_str:
            logger.warning(f"403 Forbidden on {self.get_current_domain()}, rotating domain...")
            self.rotate_domain()
            if retry_count < self.max_retries:
                time.sleep(2 * (retry_count + 1))
                return True
            return False

        # Check for timeout
        if "timeout" in error_str or "timed out" in error_str:
            logger.warning(f"Timeout on {self.get_current_domain()}, rotating domain...")
            self.rotate_domain()
            if retry_count < self.max_retries:
                return True
            return False

        return False

    def get_actor_page(self, actor_id: str, page: int = 1) -> Dict[str, Any]:
        """Get actor's movie page.

        Args:
            actor_id: JavBus actor ID
            page: Page number (1-based)

        Returns:
            Dict with movies list, has_next boolean
        """
        url = f"{self._get_base_url()}/star/{actor_id}"
        if page > 1:
            url += f"/{page}"

        for retry in range(self.max_retries):
            try:
                self.random_delay()
                response = self.session.get(url)

                if response.status_code == 403:
                    if self._handle_error(Exception("403 Forbidden"), retry, url):
                        continue
                    return {"movies": [], "has_next": False, "error": "403 Forbidden"}

                if response.status_code != 200:
                    if self._handle_error(Exception(f"HTTP {response.status_code}"), retry, url):
                        continue
                    return {"movies": [], "has_next": False, "error": f"HTTP {response.status_code}"}

                return self._parse_actor_page(response.text, page)

            except Exception as e:
                logger.error(f"Error fetching actor page {url}: {e}")
                if self._handle_error(e, retry, url):
                    continue
                return {"movies": [], "has_next": False, "error": str(e)}

        return {"movies": [], "has_next": False, "error": "Max retries exceeded"}

    def _parse_actor_page(self, html: str, page: int) -> Dict[str, Any]:
        """Parse actor page HTML to extract movies.

        Args:
            html: HTML content
            page: Current page number

        Returns:
            Dict with movies list and has_next
        """
        movies = []

        try:
            # Try to find movie items
            # JavBus actor page movie item pattern
            # <a class="movie-box" href="...">...<date>ABC-123</date>...<date>2023-01-01</date>...
            pattern = r'<a\s+class="movie-box"[^>]*href="([^"]+)"[^>]*>.*?<date>([^<]+)</date>.*?<date>([^<]+)</date>'
            matches = re.findall(pattern, html, re.DOTALL)

            for match in matches:
                url, code_or_title, date = match
                # First date is usually the code/title, second is release date
                code_match = re.match(r"^([A-Z]+-\d+)", code_or_title)

                if code_match:
                    code = code_match.group(1)
                    movies.append({
                        "code": code,
                        "title": code_or_title,
                        "release_date": date.strip(),
                        "source_type": "javbus"
                    })

            # Fallback: try simpler pattern if above doesn't work
            if not movies:
                # Pattern: <date>CODE</date> appears in the movie-box
                pattern2 = r'<a\s+class="movie-box"[^>]*>.*?<date>([A-Z]+-\d+)</date>'
                matches2 = re.findall(pattern2, html, re.DOTALL)
                for code in matches2:
                    movies.append({
                        "code": code,
                        "title": "",
                        "release_date": "",
                        "source_type": "javbus"
                    })

            # Check if there's a next page
            has_next = "下页" in html or "next" in html.lower()

        except Exception as e:
            logger.error(f"Error parsing actor page: {e}")

        return {
            "movies": movies,
            "has_next": has_next,
            "page": page
        }

    def search_movie(self, code: str) -> Optional[Dict[str, Any]]:
        """Search for a movie by code.

        Args:
            code: Movie code (e.g., ABC-123)

        Returns:
            Movie info dict or None if not found
        """
        url = f"{self._get_base_url()}/search/{code}"

        for retry in range(self.max_retries):
            try:
                self.random_delay()
                response = self.session.get(url)

                if response.status_code == 403:
                    if self._handle_error(Exception("403 Forbidden"), retry, url):
                        continue
                    return None

                if response.status_code != 200:
                    if self._handle_error(Exception(f"HTTP {response.status_code}"), retry, url):
                        continue
                    return None

                return self._parse_search_results(response.text, code)

            except Exception as e:
                logger.error(f"Error searching movie {code}: {e}")
                if self._handle_error(e, retry, url):
                    continue
                return None

        return None

    def _parse_search_results(self, html: str, code: str) -> Optional[Dict[str, Any]]:
        """Parse search results page.

        Args:
            html: HTML content
            code: Searched code

        Returns:
            Movie info dict or None
        """
        try:
            # Look for movie items with similar pattern
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

            # Fallback: check if code appears anywhere
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

    def get_movie_detail(self, url: str) -> Optional[Dict[str, Any]]:
        """Get movie detail from a JavBus URL.

        Args:
            url: Full JavBus movie URL

        Returns:
            Movie detail dict or None
        """
        for retry in range(self.max_retries):
            try:
                self.random_delay()
                response = self.session.get(url)

                if response.status_code == 403:
                    if self._handle_error(Exception("403 Forbidden"), retry, url):
                        continue
                    return None

                if response.status_code != 200:
                    if self._handle_error(Exception(f"HTTP {response.status_code}"), retry, url):
                        continue
                    return None

                return self._parse_movie_detail(response.text)

            except Exception as e:
                logger.error(f"Error fetching movie detail {url}: {e}")
                if self._handle_error(e, retry, url):
                    continue
                return None

        return None

    def _parse_movie_detail(self, html: str) -> Dict[str, Any]:
        """Parse movie detail page.

        Args:
            html: HTML content

        Returns:
            Movie detail dict
        """
        result = {
            "code": None,
            "title": None,
            "release_date": None,
            "genres": [],
            "director": None,
            "studio": None,
            "source_type": "javbus"
        }

        try:
            # Get title from h3
            title_match = re.search(r'<h3>([^<]+)</h3>', html)
            if title_match:
                result["title"] = title_match.group(1).strip()

            # Extract code from title
            if result["title"]:
                code_match = re.match(r"^([A-Z]+-\d+)", result["title"])
                if code_match:
                    result["code"] = code_match.group(1)

            # Get info from table
            # Pattern: <tr><th>xxx</th><td>yyy</td></tr>
            row_pattern = r'<tr>\s*<th[^>]*>([^<]+)</th>\s*<td[^>]*>([^<]+)</td>\s*</tr>'
            rows = re.findall(row_pattern, html)
            for th, td in rows:
                th = th.strip()
                td = td.strip()

                if "发行日期" in th or "Release Date" in th:
                    result["release_date"] = td
                elif "导演" in th or "Director" in th:
                    result["director"] = td
                elif "制作商" in th or "Studio" in th:
                    result["studio"] = td
                elif "类别" in th or "Genre" in th:
                    # Genres might be linked
                    genre_pattern = r'<a[^>]*>([^<]+)</a>'
                    result["genres"] = re.findall(genre_pattern, td)

        except Exception as e:
            logger.error(f"Error parsing movie detail: {e}")

        return result

    def close(self):
        """Close the scraper session."""
        if self.session:
            try:
                self.session.close()
            except Exception:
                pass
            self.session = None


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)

    scraper = JavBusScraper()

    # Test with an actor ID
    print("Testing get_actor_page...")
    result = scraper.get_actor_page("9ay", page=1)
    print(f"Movies found: {len(result.get('movies', []))}")
    print(f"Has next: {result.get('has_next')}")
    print(f"First 3 movies: {result.get('movies', [])[:3]}")

    scraper.close()
