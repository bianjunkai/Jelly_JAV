import re
import httpx
from datetime import datetime


def sync_from_jellyfin():
    """从 Jellyfin 同步电影数据"""
    # 延迟导入
    from app import db, config
    from models import Movie, Actor, TaskLog

    task = TaskLog(task_type='sync', status='running', message='Starting Jellyfin sync')
    db.session.add(task)
    db.session.commit()

    try:
        headers = {'X-MediaBrowser-Token': config.JELLYFIN_API_KEY}
        base_url = config.JELLYFIN_URL.rstrip('/')

        # 获取所有电影
        movies_url = f"{base_url}/Items"
        params = {
            'IncludeItemTypes': 'Movie',
            'Recursive': 'true',
            'Fields': 'ProviderIds,PrimaryImageAspectRatio,OriginalTitle,ProductionYear',
            'StartIndex': 0,
            'Limit': 10000
        }

        resp = httpx.get(movies_url, headers=headers, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        items = data.get('Items', [])
        processed = 0
        added = 0

        for item in items:
            # 提取番号
            name = item.get('Name', '')
            provider_ids = item.get('ProviderIds', {})

            # 尝试从名称或提供商ID提取番号
            code = extract_code(name)

            if not code:
                # JELLYFIN 电影没有番号，跳过
                processed += 1
                continue

            # 检查是否已存在
            existing = Movie.query.filter_by(code=code).first()

            if existing:
                # 更新 Jellyfin 信息
                existing.jellyfin_id = item.get('Id')
                existing.jellyfin_path = item.get('Path')
                if item.get('DateCreated'):
                    existing.date_added = item.get('DateCreated')
                processed += 1
            else:
                # 新增影片
                movie = Movie(
                    code=code,
                    title=name,
                    original_title=item.get('OriginalTitle'),
                    year=item.get('ProductionYear'),
                    jellyfin_id=item.get('Id'),
                    jellyfin_path=item.get('Path'),
                    date_added=datetime.fromisoformat(item.get('DateCreated').replace('Z', '+00:00')) if item.get('DateCreated') else None
                )
                db.session.add(movie)
                added += 1
                processed += 1

            # 更新演员
            update_movie_actors(code, item.get('People', []))

            # 更新进度
            task.progress = int(processed / len(items) * 100)
            task.message = f'Processing: {code}'
            db.session.commit()

        # 清理任务日志
        task.status = 'completed'
        task.progress = 100
        task.message = f'Completed: {added} added, {processed} processed'
        task.finished_at = datetime.utcnow()
        db.session.commit()

    except Exception as e:
        task.status = 'failed'
        task.message = f'Error: {str(e)}'
        task.finished_at = datetime.utcnow()
        db.session.commit()


def extract_code(title):
    """从标题提取番号"""
    if not title:
        return None

    # 常见格式: ABC-123, ABC-1234, ABC123
    patterns = [
        r'([A-Z]{2,10}-\d{2,5})',  # ABC-123
        r'([A-Z]{2,10}\d{3,5})',    # ABC123
    ]

    for pattern in patterns:
        match = re.search(pattern, title.upper())
        if match:
            code = match.group(1)
            # 标准化格式
            code = re.sub(r'([A-Z]+)(\d+)', r'\1-\2', code)
            return code

    return None


def update_movie_actors(code, people):
    """更新影片演员信息"""
    # 延迟导入
    from app import db
    from models import Movie, Actor

    movie = Movie.query.filter_by(code=code).first()
    if not movie:
        return

    # 筛选演员
    actors = []
    for person in people:
        if person.get('Type') == 'Actor':
            actors.append(person.get('Name', ''))

    if actors:
        movie.actors = ','.join(actors)

        # 更新演员统计
        for actor_name in actors:
            actor = Actor.query.filter_by(name=actor_name).first()
            if not actor:
                actor = Actor(name=actor_name)
                db.session.add(actor)

            # 更新统计
            actor.movie_count = Movie.query.filter(
                Movie.actors.contains(actor_name)
            ).count()

            # 计算平均分
            movies = Movie.query.filter(Movie.actors.contains(actor_name)).all()
            scores = [m.javdb_score for m in movies if m.javdb_score]
            if scores:
                actor.avg_score = sum(scores) / len(scores)

    db.session.commit()
