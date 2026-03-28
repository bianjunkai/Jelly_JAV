import httpx
import random
import re
import time
from bs4 import BeautifulSoup
from datetime import datetime


class ChartScraper:
    """榜单爬虫"""

    def __init__(self):
        # 延迟导入，避免循环导入
        from app import config
        self.domains = config.JAVDB_DOMAINS
        self.current_domain = random.choice(self.domains)
        self.timeout = config.REQUEST_TIMEOUT

    def get_base_url(self):
        return f"https://{self.current_domain}"

    def rotate_domain(self):
        try:
            current_idx = self.domains.index(self.current_domain)
        except ValueError:
            current_idx = 0
        next_idx = (current_idx + 1) % len(self.domains)
        self.current_domain = self.domains[next_idx]

    def fetch(self, path, retries=3):
        for attempt in range(retries):
            try:
                url = f"{self.get_base_url()}{path}"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                }

                resp = httpx.get(url, headers=headers, timeout=self.timeout)
                resp.raise_for_status()

                time.sleep(random.uniform(3, 6))

                return resp.text

            except Exception as e:
                if attempt < retries - 1:
                    self.rotate_domain()
                    time.sleep(1)

        return None

    def scrape_top250(self, page=1):
        """抓取 JavDB TOP250"""
        html = self.fetch(f"/charts/top?page={page}")

        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        items = []

        for row in soup.select('table tbody tr'):
            rank_elem = row.select_one('.rank')
            title_elem = row.select_one('.video-title')
            score_elem = row.select_one('.score')

            if title_elem:
                title = title_elem.text.strip()
                link = title_elem.select_one('a')
                href = link.get('href') if link else ''

                # 提取番号
                code = None
                code_match = re.search(r'([A-Z]+-\d+)', title.upper())
                if code_match:
                    code = code_match.group(1)

                # 提取演员
                actors = []
                for actor in row.select('.actor a'):
                    actors.append(actor.text.strip())

                # 提取评分
                score = None
                if score_elem:
                    score_text = score_elem.text.strip()
                    score_match = re.search(r'([\d.]+)', score_text)
                    if score_match:
                        score = float(score_match.group(1))

                items.append({
                    'rank': int(rank_elem.text.strip()) if rank_elem else 0,
                    'code': code,
                    'title': title,
                    'score': score,
                    'actors': actors,
                    'href': href
                })

        return items

    def scrape_all_top250(self):
        """抓取完整 TOP250（多页）"""
        all_items = []

        for page in range(1, 6):  # TOP250 分5页
            items = self.scrape_top250(page)
            all_items.extend(items)
            print(f"Scraped page {page}: {len(items)} items")

        return all_items


def scrape_chart(chart):
    """抓取指定榜单"""
    # 延迟导入
    from app import db
    from models import Chart, ChartItem

    scraper = ChartScraper()

    # 清空旧数据
    ChartItem.query.filter_by(chart_id=chart.id).delete()

    if chart.source == 'javdb':
        if 'top' in chart.name.lower() or 'top250' in chart.name.lower():
            items = scraper.scrape_all_top250()
        else:
            # 其他榜单
            items = scraper.scrape_top250(1)[:chart.total_count]
    else:
        # JavLibrary 等其他来源
        items = []

    # 保存到数据库
    for item in items:
        chart_item = ChartItem(
            chart_id=chart.id,
            rank=item['rank'],
            code=item['code'],
            title=item['title'],
            score=item['score'],
            actors=','.join(item['actors']) if item['actors'] else None
        )
        db.session.add(chart_item)

    chart.last_updated = datetime.utcnow()
    db.session.commit()

    print(f"Chart {chart.display_name} updated with {len(items)} items")


def init_default_charts():
    """初始化默认榜单"""
    # 延迟导入
    from app import db
    from models import Chart

    default_charts = [
        {
            'name': 'JavDB TOP250',
            'display_name': 'JavDB TOP250',
            'source': 'javdb',
            'description': 'JavDB 全站评分最高的 250 部影片',
            'total_count': 250
        },
        {
            'name': 'JavDB 2025 TOP250',
            'display_name': 'JavDB 2025 TOP250',
            'source': 'javdb',
            'description': 'JavDB 2025 年度评分最高的 250 部影片',
            'total_count': 250,
            'year': 2025
        },
        {
            'name': 'JavDB 2024 TOP250',
            'display_name': 'JavDB 2024 TOP250',
            'source': 'javdb',
            'description': 'JavDB 2024 年度评分最高的 250 部影片',
            'total_count': 250,
            'year': 2024
        },
        {
            'name': 'JavLibrary TOP500',
            'display_name': 'JavLibrary TOP500',
            'source': 'javlibrary',
            'description': 'JavLibrary 评分最高的 500 部影片',
            'total_count': 500
        }
    ]

    for chart_data in default_charts:
        existing = Chart.query.filter_by(name=chart_data['name']).first()
        if not existing:
            chart = Chart(**chart_data)
            db.session.add(chart)

    db.session.commit()
