#!/usr/bin/env python3
"""
JavDB Scraper Module

使用 curl_cffi 模拟 Chrome 浏览器请求，从 JavDB 获取影片评分。
"""

import re
import time
import random
import logging
from typing import Optional, Dict, Any

try:
    from curl_cffi import requests as curl_requests
except ImportError:
    print("请安装 curl_cffi: pip install curl_cffi")
    raise

logger = logging.getLogger(__name__)

# JavDB URL
JAVDB_BASE_URL = "https://javdb.com"
JAVDB_API_URL = "https://javdb.com/api/v1"

# 请求间隔（秒）
MIN_DELAY = 3
MAX_DELAY = 5

# 重试次数
MAX_RETRIES = 3


def get_session():
    """创建一个模拟 Chrome 浏览器的会话"""
    session = curl_requests.Session(impersonate="chrome", timeout=15)
    return session


def random_delay():
    """随机延迟，防止被封"""
    delay = random.uniform(MIN_DELAY, MAX_DELAY)
    time.sleep(delay)


def search_javdb(code: str) -> Optional[Dict[str, Any]]:
    """
    在 JavDB 搜索影片

    Args:
        code: 影片番号（如 ABC-123）

    Returns:
        包含影片信息的字典，如果未找到返回 None
    """
    session = get_session()

    # 搜索页面
    search_url = f"{JAVDB_BASE_URL}/search?q={code}&f=all"

    for retry in range(MAX_RETRIES):
        try:
            random_delay()
            resp = session.get(search_url)

            if resp.status_code == 403:
                logger.warning(f"403 Forbidden for {code}, retry {retry + 1}/{MAX_RETRIES}")
                if retry < MAX_RETRIES - 1:
                    time.sleep(5 * (retry + 1))  # 指数退避
                    continue
                return None

            if resp.status_code != 200:
                logger.warning(f"Search failed for {code}: HTTP {resp.status_code}")
                return None

            # 解析搜索结果
            html = resp.text

            # 查找影片链接
            # 搜索结果页面中，影片链接模式：/v/XXXXX
            pattern = r'<a\s+href="(/v/[^"]+)"[^>]*class="box[^"]*"[^>]*>'
            matches = re.findall(pattern, html)

            if not matches:
                # 尝试其他模式
                pattern2 = r'<a\s+href="(/v/[^"]+)"[^>]*>'
                matches = re.findall(pattern2, html)

            if not matches:
                # 检查是否有"没有结果"的提示
                if "沒有結果" in html or "没有结果" in html:
                    logger.info(f"No results found for {code}")
                    return None
                logger.warning(f"Cannot find movie link for {code}")
                return None

            # 获取第一个结果
            movie_url = f"{JAVDB_BASE_URL}{matches[0]}"
            logger.info(f"Found movie: {movie_url}")

            # 访问影片页面获取详情
            return get_movie_detail(session, movie_url, code)

        except Exception as e:
            logger.error(f"Search error for {code}: {e}")
            if retry < MAX_RETRIES - 1:
                time.sleep(5 * (retry + 1))
                continue
            return None

    return None


def get_movie_detail(session, url: str, code: str) -> Optional[Dict[str, Any]]:
    """
    获取影片详情页面

    Args:
        session: curl_cffi Session
        url: 影片详情页 URL
        code: 影片番号

    Returns:
        包含影片评分的字典
    """
    for retry in range(MAX_RETRIES):
        try:
            random_delay()
            resp = session.get(url)

            if resp.status_code == 403:
                logger.warning(f"403 Forbidden for {url}, retry {retry + 1}/{MAX_RETRIES}")
                if retry < MAX_RETRIES - 1:
                    time.sleep(5 * (retry + 1))
                    continue
                return None

            if resp.status_code != 200:
                logger.warning(f"Detail page failed: HTTP {resp.status_code}")
                return None

            html = resp.text
            return parse_movie_page(html, code)

        except Exception as e:
            logger.error(f"Detail page error for {url}: {e}")
            if retry < MAX_RETRIES - 1:
                time.sleep(5 * (retry + 1))
                continue
            return None

    return None


def parse_movie_page(html: str, code: str) -> Optional[Dict[str, Any]]:
    """
    解析影片页面，提取评分

    Args:
        html: 影片页面 HTML
        code: 影片番号

    Returns:
        包含评分的字典
    """
    result = {
        "code": code,
        "javdb_score": None,
        "rating_count": 0,
        "url": None
    }

    # 查找评分
    # JavDB 评分格式：data-score="8.5" 或类似的属性
    # 评分显示：<span class="rating">8.5</span> 或 <span class="score">8.5</span>

    # 模式1: data-score 属性
    score_pattern = r'data-score="(\d+\.?\d*)"'
    match = re.search(score_pattern, html)
    if match:
        result["javdb_score"] = float(match.group(1))
        logger.info(f"Found score {result['javdb_score']} for {code}")
        return result

    # 模式2: 评分类包含数字
    score_pattern2 = r'<[^>]*class="[^"]*rating[^"]*"[^>]*>(\d+\.?\d*)'
    match = re.search(score_pattern2, html)
    if match:
        result["javdb_score"] = float(match.group(1))
        logger.info(f"Found score {result['javdb_score']} for {code}")
        return result

    # 模式3: 查找 5 分制的评分
    score_pattern3 = r'(\d+\.?\d*)\s*/\s*5'
    match = re.search(score_pattern3, html)
    if match:
        result["javdb_score"] = float(match.group(1))
        logger.info(f"Found score {result['javdb_score']}/5 for {code}")
        return result

    # 模式4: 查找包含 "score" 或 "评分" 的元素
    score_pattern4 = r'>([\d.]+)\s*分<'
    match = re.search(score_pattern4, html)
    if match:
        result["javdb_score"] = float(match.group(1))
        logger.info(f"Found score {result['javdb_score']} for {code}")
        return result

    logger.info(f"No score found for {code}")
    return result


def get_javdb_score(code: str) -> Optional[float]:
    """
    获取单个影片的 JavDB 评分

    Args:
        code: 影片番号（如 ABC-123）

    Returns:
        评分（0-10），如果未找到返回 None
    """
    logger.info(f"Fetching JavDB score for {code}")

    result = search_javdb(code)
    if result and result.get("javdb_score"):
        return result["javdb_score"]

    return None


def get_javdb_score_with_retry(code: str, max_retries: int = 3) -> Optional[float]:
    """
    带重试的获取评分

    Args:
        code: 影片番号
        max_retries: 最大重试次数

    Returns:
        评分或 None
    """
    for i in range(max_retries):
        score = get_javdb_score(code)
        if score is not None:
            return score

        if i < max_retries - 1:
            wait_time = (i + 1) * 10
            logger.info(f"Retrying {code} in {wait_time}s...")
            time.sleep(wait_time)

    return None


if __name__ == "__main__":
    # 测试
    logging.basicConfig(level=logging.INFO)

    # 测试获取评分
    test_codes = ["ABC-123", "SSIS-001", "MIAD-001"]

    for code in test_codes:
        print(f"\nTesting {code}...")
        score = get_javdb_score(code)
        print(f"Score: {score}")
