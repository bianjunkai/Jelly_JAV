import re
import httpx
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def sync_from_jellyfin():
    """从 Jellyfin 同步电影数据"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("sync_from_jellyfin started")

    # 直接从 app 模块获取 config，避免重复导入
    import sys
    from app import app, db, load_config_from_file
    from models import Movie, Actor, TaskLog

    # 同步前重新加载配置（确保获取最新值）
    load_config_from_file()

    # 通过 app 模块引用 config
    from app import config as config_module

    logger.info(f"[SYNC] JELLYFIN_URL: {config_module.JELLYFIN_URL}")
    logger.info(f"[SYNC] JELLYFIN_API_KEY: {'***' + config_module.JELLYFIN_API_KEY[-4:] if config_module.JELLYFIN_API_KEY else 'NOT SET'}")

    # 在应用上下文中运行
    with app.app_context():
        task = TaskLog(task_type='sync', status='running', message='Starting Jellyfin sync')
        db.session.add(task)
        db.session.commit()

        try:
            headers = {'X-MediaBrowser-Token': config_module.JELLYFIN_API_KEY}
            base_url = config_module.JELLYFIN_URL.rstrip('/')
            logger.info(f"Requesting movies from {base_url}")

            # 获取所有电影
            movies_url = f"{base_url}/Items"
            params = {
                'IncludeItemTypes': 'Movie',
                'Recursive': 'true',
                'Fields': 'ProviderIds,PrimaryImageAspectRatio,OriginalTitle,ProductionYear,People',
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

            # 关联榜单条目与影片
            link_movies_to_charts()

            # 清理任务日志
            task.status = 'completed'
            task.progress = 100
            task.message = f'Completed: {added} added, {processed} processed'
            task.finished_at = datetime.utcnow()
            db.session.commit()

        except Exception as e:
            logger.error(f"Sync error: {e}", exc_info=True)
            task.status = 'failed'
            task.message = f'Error: {str(e)}'
            task.finished_at = datetime.utcnow()
            db.session.commit()


def link_movies_to_charts():
    """关联榜单条目与影片数据库

    根据番号(code)匹配 ChartItem 和 Movie，更新 ChartItem.movie_id
    """
    from app import db
    from models import ChartItem, Movie

    logger.info("[LINK] Starting to link chart items to movies")

    # 获取所有未关联的榜单条目
    unlinked_items = ChartItem.query.filter(ChartItem.movie_id.is_(None)).all()

    linked_count = 0
    for item in unlinked_items:
        if not item.code:
            continue

        # 查找匹配的影片
        movie = Movie.query.filter_by(code=item.code).first()
        if movie:
            item.movie_id = movie.id
            linked_count += 1

    db.session.commit()
    logger.info(f"[LINK] Linked {linked_count} chart items to movies")


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


def update_movie_actors(code, people, jellyfin_item=None):
    """更新影片演员信息"""
    import json
    # 延迟导入
    from app import db, config as config_module
    from models import Movie, Actor

    movie = Movie.query.filter_by(code=code).first()
    if not movie:
        return

    # 筛选演员并收集头像信息
    actors = []
    actor_images = {}
    for person in people:
        if person.get('Type') == 'Actor':
            name = person.get('Name', '')
            if name:
                actors.append(name)
                # 获取演员头像 URL
                person_id = person.get('Id')
                # 尝试获取头像标签，可能是 PrimaryImageTag 或 ImageTags.Primary
                image_tag = person.get('PrimaryImageTag')
                if not image_tag:
                    image_tags = person.get('ImageTags', {})
                    image_tag = image_tags.get('Primary')
                if person_id and image_tag:
                    # 构建 Jellyfin 演员头像 URL
                    actor_images[name] = f'/api/actor-image/{person_id}?tag={image_tag}'

    if actors:
        movie.actors = ','.join(actors)
        # 总是更新 actor_images（新头像覆盖旧头像，没有的清空）
        movie.actor_images = json.dumps(actor_images)

        # 更新演员统计和头像
        for actor_name in actors:
            actor = Actor.query.filter_by(name=actor_name).first()
            if not actor:
                actor = Actor(name=actor_name)
                db.session.add(actor)

            # 更新演员头像（使用演员名字作为URL参数）
            import urllib.parse
            encoded_name = urllib.parse.quote(actor_name)
            actor.photo_url = f'/api/actor-image/{encoded_name}'

            # 更新统计（使用精确匹配）
            from sqlalchemy import or_
            exact_filter = or_(
                Movie.actors == actor_name,
                Movie.actors.startswith(f'{actor_name},'),
                Movie.actors.endswith(f',{actor_name}'),
                Movie.actors.contains(f',{actor_name},')
            )
            actor.movie_count = Movie.query.filter(exact_filter).count()

            # 计算平均分
            movies = Movie.query.filter(exact_filter).all()
            scores = [m.javdb_score for m in movies if m.javdb_score]
            if scores:
                actor.avg_score = sum(scores) / len(scores)

    db.session.commit()
