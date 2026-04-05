import csv
import glob
import os
import random
import re
import time
from bs4 import BeautifulSoup
from datetime import datetime
from curl_cffi import requests as curl_requests


def get_project_base_dir():
    """获取项目根目录（jav-manager 目录）"""
    # 当前文件路径: backend/services/chart_scraper.py
    # 项目根目录: backend/ 的上一级
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(current_dir)
    project_dir = os.path.dirname(backend_dir)
    return project_dir


def get_javlibrary_csv_path():
    """获取 JavLibrary CSV 文件路径

    优先从配置中读取，支持相对路径（相对于项目根目录）
    返回: CSV 文件路径 或 None
    """
    from app import config

    csv_path = getattr(config, 'JAVLIBRARY_CSV_PATH', '').strip()

    if not csv_path:
        print("[JavLibrary] CSV path not configured")
        return None

    # 如果是相对路径，转换为绝对路径（基于项目根目录）
    if not os.path.isabs(csv_path):
        project_dir = get_project_base_dir()
        csv_path = os.path.join(project_dir, csv_path)
        csv_path = os.path.normpath(csv_path)

    if not os.path.exists(csv_path):
        print(f"[JavLibrary] CSV file not found: {csv_path}")
        return None

    print(f"[JavLibrary] Using configured CSV file: {csv_path}")
    return csv_path


def parse_javlibrary_csv(csv_path):
    """解析 JavLibrary CSV 文件

    CSV 格式: 序号,页码,番号,完整标题,评分,链接,记录时间
    返回: list of dict with keys: rank, page, code, title, score, url, crawl_time
    """
    items = []

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for idx, row in enumerate(reader, start=1):
                try:
                    # 提取番号（如果没有番号则跳过）
                    code = row.get('番号', '').strip()
                    if not code:
                        continue

                    # 提取评分
                    score_str = row.get('评分', '0').strip()
                    try:
                        score = float(score_str) if score_str else None
                    except ValueError:
                        score = None

                    # 解析记录时间
                    crawl_time_str = row.get('记录时间', '').strip()
                    crawl_time = None
                    if crawl_time_str:
                        try:
                            # 处理 ISO 格式时间
                            crawl_time = datetime.fromisoformat(crawl_time_str.replace('Z', '+00:00'))
                        except:
                            pass

                    # 使用行号作为 rank（CSV 中的序号是每页独立的）
                    item = {
                        'rank': idx,
                        'page': int(row.get('页码', 0)),
                        'code': code,
                        'title': row.get('完整标题', '').strip(),
                        'score': score,
                        'url': row.get('链接', '').strip(),
                        'crawl_time': crawl_time
                    }
                    items.append(item)
                except Exception as e:
                    print(f"[JavLibrary] Error parsing row: {e}")
                    continue

        print(f"[JavLibrary] Parsed {len(items)} items from CSV")
        return items

    except Exception as e:
        print(f"[JavLibrary] Error reading CSV: {e}")
        return []


def import_javlibrary_from_csv(db, batch_id=None):
    """从 CSV 导入 JavLibrary 数据到数据库

    Args:
        db: SQLAlchemy 实例
        batch_id: 批次ID（可选，默认使用当前时间）

    Returns:
        list of items 或 None（如果没有找到 CSV）
    """
    from models import JavLibraryRawData

    csv_path = get_javlibrary_csv_path()
    if not csv_path:
        return None

    items = parse_javlibrary_csv(csv_path)
    if not items:
        return None

    if batch_id is None:
        batch_id = datetime.utcnow().strftime('%Y%m%d_%H%M%S')

    try:
        # 清空旧数据
        db.session.query(JavLibraryRawData).delete()

        # 保存到数据库
        for item in items:
            raw_data = JavLibraryRawData(
                rank=item['rank'],
                page=item['page'],
                code=item['code'],
                title=item['title'],
                score=item['score'],
                url=item['url'],
                crawl_time=item['crawl_time'],
                batch_id=batch_id
            )
            db.session.add(raw_data)

        db.session.commit()
        print(f"[JavLibrary] Imported {len(items)} items to database (batch: {batch_id})")
        return items

    except Exception as e:
        db.session.rollback()
        print(f"[JavLibrary] Error importing to database: {e}")
        raise


class ChartScraper:
    """榜单爬虫"""

    def __init__(self):
        # 延迟导入，避免循环导入
        from app import config
        self.domains = config.JAVDB_DOMAINS
        self.current_domain = random.choice(self.domains)
        self.timeout = config.REQUEST_TIMEOUT
        # 榜单抓取使用更长延迟，避免被封
        self.min_delay = max(config.REQUEST_MIN_DELAY, 6)
        self.max_delay = max(config.REQUEST_MAX_DELAY, 10)
        self.enable_proxy = config.ENABLE_SYSTEM_PROXY
        self.proxy_url = config.SYSTEM_PROXY_URL
        self.cookie = config.JAVDB_COOKIE

    def get_base_url(self):
        return f"https://{self.current_domain}"

    def rotate_domain(self):
        try:
            current_idx = self.domains.index(self.current_domain)
        except ValueError:
            current_idx = 0
        next_idx = (current_idx + 1) % len(self.domains)
        self.current_domain = self.domains[next_idx]

    def fetch(self, path, retries=3, extra_delay=None):
        """抓取页面

        Args:
            path: URL路径
            retries: 重试次数
            extra_delay: 额外延迟（秒），用于榜单页面
        """
        for attempt in range(retries):
            try:
                url = f"{self.get_base_url()}{path}"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                }

                # 添加 cookie
                if self.cookie:
                    headers['Cookie'] = self.cookie

                proxies = {}
                if self.enable_proxy and self.proxy_url:
                    proxies = {'http': self.proxy_url, 'https': self.proxy_url}

                resp = curl_requests.get(
                    url,
                    headers=headers,
                    proxies=proxies,
                    impersonate='chrome110',
                    timeout=self.timeout
                )
                resp.raise_for_status()

                # 延迟
                delay = random.uniform(self.min_delay, self.max_delay)
                if extra_delay:
                    delay += extra_delay
                time.sleep(delay)

                return resp.text

            except Exception as e:
                if attempt < retries - 1:
                    self.rotate_domain()
                    time.sleep(2)

        return None

    def scrape_top250(self, page=1):
        """抓取 JavDB TOP250 (全站)
        URL: https://javdb.com/rankings/top
        """
        html = self.fetch(f"/rankings/top?page={page}", extra_delay=2)

        if not html:
            return []

        return self._parse_chart_items(html, page=page)

    def scrape_year_top250(self, year, page=1):
        """抓取 JavDB 年度 TOP250
        URL: https://javdb.com/rankings/top?t=y2026
        """
        html = self.fetch(f"/rankings/top?t=y{year}&page={page}", extra_delay=2)

        if not html:
            return []

        return self._parse_chart_items(html, page=page, year=year)

    def _parse_chart_items(self, html, page=1, year=None):
        """解析榜单页面

        Args:
            html: 页面 HTML
            page: 页码（用于计算 rank）
            year: 年份（可选）
        """
        soup = BeautifulSoup(html, 'html.parser')
        items = []
        items_per_page = 40

        # 榜单使用 .movie-list .item 结构
        for idx, item_elem in enumerate(soup.select('.movie-list .item')):
            # 查找标题和链接
            title_elem = item_elem.select_one('.video-title')
            if not title_elem:
                continue

            title = title_elem.text.strip()
            link = title_elem.select_one('a')
            href = link.get('href') if link else ''

            # 提取番号
            code = None
            code_match = re.search(r'([A-Z]+-\d+)', title.upper())
            if code_match:
                code = code_match.group(1)

            # 计算排名：基于页码和索引
            rank = (page - 1) * items_per_page + idx + 1

            # 提取评分
            score = None
            score_elem = item_elem.select_one('.score')
            if score_elem:
                score_text = score_elem.text.strip()
                score_match = re.search(r'([\d.]+)', score_text)
                if score_match:
                    score = float(score_match.group(1))

            # 提取演员
            actors = []
            for actor in item_elem.select('.actor a'):
                actors.append(actor.text.strip())

            item = {
                'rank': rank,
                'code': code,
                'title': title,
                'score': score,
                'actors': actors,
                'href': href
            }
            if year:
                item['year'] = year

            items.append(item)

        return items

    def scrape_all_top250(self):
        """抓取完整 TOP250（多页）"""
        all_items = []

        for page in range(1, 8):  # TOP250 需要7页才能覆盖250条（每页40条）
            items = self.scrape_top250(page)
            if not items:
                break
            all_items.extend(items)
            print(f"Scraped TOP250 page {page}: {len(items)} items")

        return all_items

    def scrape_all_year_top250(self, year):
        """抓取完整年度 TOP250（多页）"""
        all_items = []

        for page in range(1, 8):  # 年度榜也分7页
            items = self.scrape_year_top250(year, page)
            if not items:
                break
            all_items.extend(items)
            print(f"Scraped {year} TOP250 page {page}: {len(items)} items")

        return all_items


def _fetch_chart_data(chart, db=None):
    """抓取榜单数据（在应用上下文外执行，避免长时间占用数据库连接）

    Args:
        chart: Chart 对象
        db: SQLAlchemy 实例（JavLibrary 需要，用于导入 CSV 到数据库）

    Returns:
        list of items 或 None（如果是 JavLibrary 且需要单独处理）
    """
    if chart.source == 'javdb':
        scraper = ChartScraper()
        year = getattr(chart, 'year', None)

        if year:
            print(f"[ChartScraper] Scraping {year} year chart...")
            items = scraper.scrape_all_year_top250(year)
        elif 'top' in chart.name.lower() or 'top250' in chart.name.lower():
            print(f"[ChartScraper] Scraping TOP250...")
            items = scraper.scrape_all_top250()
        else:
            items = scraper.scrape_top250(1)[:chart.total_count]
        return items

    elif chart.source == 'javlibrary':
        # JavLibrary 从 CSV 导入，需要在应用上下文内执行
        # 返回 None 表示需要单独处理
        print(f"[ChartScraper] JavLibrary chart {chart.display_name} will be imported from CSV")
        return None

    else:
        return []


def scrape_chart(chart, app=None, db=None):
    """抓取/导入指定榜单

    Args:
        chart: Chart 对象
        app: Flask app 实例（用于创建应用上下文）
        db: SQLAlchemy 实例（用于数据库操作）
    """
    # 保存 chart 信息，用于后续查询
    chart_id = chart.id
    chart_name = chart.display_name
    chart_source = chart.source

    # 如果没有传入，尝试导入
    if app is None:
        from app import app
    if db is None:
        from app import db

    # JavLibrary 榜单特殊处理：从 CSV 导入
    if chart_source == 'javlibrary':
        _scrape_javlibrary_chart(chart_id, chart_name, app, db)
        return

    # JavDB 榜单：正常爬取
    # 步骤1：在应用上下文外抓取数据（避免长时间占用数据库连接）
    items = _fetch_chart_data(chart)

    if items is None:
        print(f"[ChartScraper] No items fetched for {chart_name}")
        return

    # 步骤2：在应用上下文内快速写入数据库
    _save_chart_items(chart_id, chart_name, items, app, db)


def _scrape_javlibrary_chart(chart_id, chart_name, app, db):
    """处理 JavLibrary 榜单（从 CSV 导入）"""
    with app.app_context():
        from models import ChartItem, Chart

        try:
            # 从 CSV 导入数据到 JavLibraryRawData 表
            items = import_javlibrary_from_csv(db)

            if items is None:
                print(f"[ChartScraper] No CSV file found for JavLibrary chart")
                return

            if not items:
                print(f"[ChartScraper] CSV file is empty")
                return

            # 重新获取 chart 对象（在当前 session 中）
            chart_obj = db.session.query(Chart).filter_by(id=chart_id).first()
            if not chart_obj:
                print(f"[ChartScraper] Chart {chart_name} not found in database")
                return

            # 清空旧数据
            db.session.query(ChartItem).filter_by(chart_id=chart_id).delete()

            # 批量保存新数据（过滤掉没有番号的条目）
            valid_count = 0
            for item in items:
                if not item.get('code'):
                    print(f"[ChartScraper] Skipping item without code: {item.get('title', 'Unknown')}")
                    continue
                chart_item = ChartItem(
                    chart_id=chart_id,
                    rank=item['rank'],
                    code=item['code'],
                    title=item['title'],
                    score=item['score'],
                    actors=None,  # JavLibrary CSV 中没有演员信息
                    year=None
                )
                db.session.add(chart_item)
                valid_count += 1

            chart_obj.last_updated = datetime.utcnow()
            db.session.commit()

            print(f"Chart {chart_name} updated with {valid_count}/{len(items)} valid items (from CSV)")

            # 关联新导入的榜单条目与影片
            _link_chart_items_to_movies(db)

        except Exception as e:
            db.session.rollback()
            print(f"Error updating JavLibrary chart {chart_name}: {e}")
            raise


def _link_chart_items_to_movies(db):
    """关联榜单条目与影片"""
    from models import ChartItem, Movie

    # 获取所有未关联的榜单条目
    unlinked_items = db.session.query(ChartItem).filter(ChartItem.movie_id.is_(None)).all()

    linked_count = 0
    for item in unlinked_items:
        if not item.code:
            continue
        movie = db.session.query(Movie).filter_by(code=item.code).first()
        if movie:
            item.movie_id = movie.id
            linked_count += 1

    db.session.commit()
    print(f"[ChartScraper] Linked {linked_count} chart items to movies")


def _save_chart_items(chart_id, chart_name, items, app, db):
    """保存榜单条目到数据库（通用方法）"""
    with app.app_context():
        from models import ChartItem, Chart

        try:
            # 重新获取 chart 对象（在当前 session 中）
            chart_obj = db.session.query(Chart).filter_by(id=chart_id).first()
            if not chart_obj:
                print(f"[ChartScraper] Chart {chart_name} not found in database")
                return

            # 清空旧数据
            db.session.query(ChartItem).filter_by(chart_id=chart_id).delete()

            # 批量保存新数据（过滤掉没有番号的条目）
            valid_count = 0
            for item in items:
                if not item.get('code'):
                    print(f"[ChartScraper] Skipping item without code: {item.get('title', 'Unknown')}")
                    continue
                chart_item = ChartItem(
                    chart_id=chart_id,
                    rank=item['rank'],
                    code=item['code'],
                    title=item['title'],
                    score=item['score'],
                    actors=','.join(item['actors']) if item['actors'] else None,
                    year=item.get('year')
                )
                db.session.add(chart_item)
                valid_count += 1

            chart_obj.last_updated = datetime.utcnow()
            db.session.commit()

            print(f"Chart {chart_name} updated with {valid_count}/{len(items)} valid items")

            # 关联新导入的榜单条目与影片
            _link_chart_items_to_movies(db)

        except Exception as e:
            db.session.rollback()
            print(f"Error updating chart {chart_name}: {e}")
            raise


def init_default_charts(db):
    """初始化默认榜单"""
    from models import Chart
    from config import JAVDB_YEAR_CHART_YEARS

    # 构建年份榜单列表
    year_charts = [
        {
            'name': f'JavDB {year} TOP250',
            'display_name': f'JavDB {year} TOP250',
            'source': 'javdb',
            'description': f'JavDB {year} 年度评分最高的 250 部影片',
            'total_count': 250,
            'year': year
        }
        for year in JAVDB_YEAR_CHART_YEARS
    ]

    default_charts = [
        {
            'name': 'JavDB TOP250',
            'display_name': 'JavDB TOP250',
            'source': 'javdb',
            'description': 'JavDB 全站评分最高的 250 部影片',
            'total_count': 250
        },
        {
            'name': 'JavLibrary TOP500',
            'display_name': 'JavLibrary TOP500',
            'source': 'javlibrary',
            'description': 'JavLibrary 评分最高的 500 部影片（通过 CSV 导入）',
            'total_count': 500
        }
    ] + year_charts

    for chart_data in default_charts:
        existing = db.session.query(Chart).filter_by(name=chart_data['name']).first()
        if not existing:
            chart = Chart(**chart_data)
            db.session.add(chart)

    db.session.commit()
