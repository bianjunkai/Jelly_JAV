import json
from datetime import datetime, timedelta
from sqlalchemy import select


def generate_weekly_report(app=None, db=None):
    """生成周报：本周关注演员新片（JavBus）"""
    from models import Movie, Actor, Report, ActorRelease
    from services.javdb_scraper import fetch_movie_details

    if app is None:
        from app import app as current_app
        app = current_app

    if db is None:
        from app import db as current_db
        db = current_db

    with app.app_context():
        session = db.session

        # 上周一到周日
        today = datetime.utcnow().date()
        days_since_monday = today.weekday()
        last_monday = today - timedelta(days=days_since_monday + 7)
        last_sunday = last_monday + timedelta(days=6)

        # 关注演员名单
        followed_actors = session.execute(
            select(Actor).where(Actor.is_followed == True)
        ).scalars().all()
        followed_actor_ids = {a.id for a in followed_actors}
        followed_actor_names = {a.name for a in followed_actors}

        if not followed_actors:
            return {'type': 'weekly', 'total_count': 0, 'movies': []}

        # 从 actor_releases 获取本周发布的新片（按 release_date 筛选）
        releases = session.execute(
            select(ActorRelease).where(
                ActorRelease.actor_id.in_(followed_actor_ids),
                ActorRelease.release_date >= last_monday.strftime('%m/%d/%Y'),
                ActorRelease.release_date <= last_sunday.strftime('%m/%d/%Y')
            )
        ).scalars().all()

        # 按演员分组，同时获取影片详情
        result_movies = []
        by_actor = {}

        for release in releases:
            movie = session.execute(
                select(Movie).where(Movie.code == release.code)
            ).scalar_one_or_none()

            # 优先使用本地评分，否则从 JavDB 获取
            javdb_score = movie.javdb_score if movie else None
            javdb_id = movie.javdb_id if movie else None
            if javdb_score is None:
                # 从 JavDB 获取评分
                try:
                    detail = fetch_movie_details(release.code)
                    if detail:
                        javdb_score = detail.get('score')
                        javdb_id = detail.get('javdb_id')
                except Exception:
                    pass  # 忽略获取失败的情况

            movie_dict = {
                'code': release.code,
                'title': release.title or (movie.title if movie else ''),
                'release_date': release.release_date,
                'is_released': release.is_released,
                'javdb_score': javdb_score,
                'javdb_id': javdb_id,
            }

            result_movies.append(movie_dict)

            actor_name = release.actor.name if release.actor else 'Unknown'
            if actor_name not in by_actor:
                by_actor[actor_name] = []
            by_actor[actor_name].append(movie_dict)

        # 按检测时间排序
        result_movies.sort(key=lambda x: x.get('release_date', ''), reverse=True)

        # 保存报告
        report_data = {
            'type': 'weekly',
            'period': f'{last_monday} ~ {last_sunday}',
            'total_count': len(result_movies),
            'by_actor': by_actor,
            'movies': result_movies
        }

        report = Report(
            type='weekly',
            title=f'本周关注演员新片 ({len(result_movies)}部)',
            data=json.dumps(report_data)
        )
        session.add(report)
        session.commit()
        result = report.to_dict()
        return result


def generate_monthly_report(app=None, db=None):
    """生成月报：本月分数上升旧片"""
    from models import Movie, Actor, Report, ScoreHistory

    if app is None:
        from app import app as current_app
        app = current_app

    if db is None:
        from app import db as current_db
        db = current_db

    with app.app_context():
        session = db.session

        # 上个月
        today = datetime.utcnow().date()
        if today.month == 1:
            last_month_start = today.replace(year=today.year - 1, month=12, day=1)
        else:
            last_month_start = today.replace(month=today.month - 1, day=1)

        last_month_end = last_month_start.replace(day=28)
        while last_month_end.month == last_month_start.month:
            last_month_end += timedelta(days=1)
        last_month_end -= timedelta(days=1)

        # 关注演员
        followed_actors = session.execute(
            select(Actor).where(Actor.is_followed == True)
        ).scalars().all()
        followed_actor_names = {a.name for a in followed_actors}

        # 分数上升记录
        score_changes = session.execute(
            select(ScoreHistory).where(
                ScoreHistory.changed_at >= datetime.combine(last_month_start, datetime.min.time()),
                ScoreHistory.changed_at <= datetime.combine(last_month_end, datetime.max.time()),
                ScoreHistory.curr_score >= 4.3,
                ScoreHistory.prev_score < 4.0
            )
        ).scalars().all()

        # 筛选关注演员的影片
        result = []
        for change in score_changes:
            movie = change.movie
            actors = movie.actors.split(',') if movie.actors else []
            if any(a in followed_actor_names for a in actors):
                result.append({
                    'movie': movie.to_dict(),
                    'prev_score': change.prev_score,
                    'curr_score': change.curr_score,
                    'change': round(change.curr_score - change.prev_score, 1)
                })

        # 保存报告
        report_data = {
            'type': 'monthly',
            'period': f'{last_month_start} ~ {last_month_end}',
            'total_count': len(result),
            'items': result
        }

        report = Report(
            type='monthly',
            title=f'本月分数上升 ({len(result)}部)',
            data=json.dumps(report_data)
        )
        session.add(report)
        session.commit()
        result = report.to_dict()
        return result


def generate_annual_report(app=None, db=None):
    """生成年报：榜单缺口推荐"""
    from models import Movie, Actor, Report, ChartItem

    if app is None:
        from app import app as current_app
        app = current_app

    if db is None:
        from app import db as current_db
        db = current_db

    with app.app_context():
        session = db.session

        # 关注演员
        followed_actors = session.execute(
            select(Actor).where(Actor.is_followed == True)
        ).scalars().all()
        followed_actor_names = {a.name for a in followed_actors}

        # 获取 JavDB TOP250
        chart_items = session.execute(
            select(ChartItem).where(ChartItem.chart_id == 1)
        ).scalars().all()
        local_codes = {m.code for m in session.execute(select(Movie)).scalars().all()}

        missing = []
        for item in chart_items:
            if item.code not in local_codes:
                actors = item.actors.split(',') if item.actors else []
                is_followed = any(a in followed_actor_names for a in actors)

                missing.append({
                    'rank': item.rank,
                    'code': item.code,
                    'title': item.title,
                    'score': item.score,
                    'actors': actors,
                    'is_followed_actor': is_followed
                })

        # 关注演员的缺失
        followed_missing = [m for m in missing if m['is_followed_actor']]
        high_score_missing = [m for m in missing if m['score'] and m['score'] >= 4.5]

        # 保存报告
        report_data = {
            'type': 'annual',
            'period': f'{datetime.utcnow().year}',
            'total_missing': len(missing),
            'followed_missing_count': len(followed_missing),
            'high_score_missing_count': len(high_score_missing),
            'followed_missing': followed_missing[:20],
            'high_score_missing': high_score_missing[:20]
        }

        report = Report(
            type='annual',
            title=f'年度榜单缺口 ({len(missing)}部缺失)',
            data=json.dumps(report_data)
        )
        session.add(report)
        session.commit()
        result = report.to_dict()
        return result
