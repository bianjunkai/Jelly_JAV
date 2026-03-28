import json
from datetime import datetime, timedelta


def generate_weekly_report():
    """生成周报：本周关注演员新片"""
    # 延迟导入
    from app import db
    from models import Movie, Actor, Report

    # 上周一到周日
    today = datetime.utcnow().date()
    days_since_monday = today.weekday()
    last_monday = today - timedelta(days=days_since_monday + 7)
    last_sunday = last_monday + timedelta(days=6)

    # 关注演员名单
    followed_actors = [a.name for a in Actor.query.filter_by(is_followed=True).all()]

    if not followed_actors:
        return {'type': 'weekly', 'total_count': 0, 'movies': []}

    # 本周发现的影片（按演员分组）
    movies = Movie.query.filter(
        Movie.discovered_at >= datetime.combine(last_monday, datetime.min.time()),
        Movie.discovered_at <= datetime.combine(last_sunday, datetime.max.time())
    ).all()

    # 筛选关注演员的影片
    result_movies = []
    by_actor = {}

    for movie in movies:
        actors = movie.actors.split(',') if movie.actors else []
        for actor_name in actors:
            if actor_name in followed_actors:
                result_movies.append(movie.to_dict())
                by_actor.setdefault(actor_name, []).append(movie.to_dict())
                break

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
    db.session.add(report)
    db.session.commit()

    return report.to_dict()


def generate_monthly_report():
    """生成月报：本月分数上升旧片"""
    # 延迟导入
    from app import db
    from models import Movie, Actor, Report, ScoreHistory

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
    followed_actors = [a.name for a in Actor.query.filter_by(is_followed=True).all()]

    # 分数上升记录
    score_changes = ScoreHistory.query.filter(
        ScoreHistory.changed_at >= datetime.combine(last_month_start, datetime.min.time()),
        ScoreHistory.changed_at <= datetime.combine(last_month_end, datetime.max.time()),
        ScoreHistory.curr_score >= 4.3,
        ScoreHistory.prev_score < 4.0
    ).all()

    # 筛选关注演员的影片
    result = []
    for change in score_changes:
        movie = change.movie
        actors = movie.actors.split(',') if movie.actors else []
        if any(a in followed_actors for a in actors):
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
    db.session.add(report)
    db.session.commit()

    return report.to_dict()


def generate_annual_report():
    """生成年报：榜单缺口推荐"""
    # 延迟导入
    from app import db
    from models import Movie, Actor, Report, ChartItem

    # 关注演员
    followed_actors = [a.name for a in Actor.query.filter_by(is_followed=True).all()]

    # 获取 JavDB TOP250
    chart_items = ChartItem.query.filter_by(chart_id=1).all()  # 假设第一个是 TOP250
    local_codes = {m.code for m in Movie.query.all()}

    missing = []
    for item in chart_items:
        if item.code not in local_codes:
            actors = item.actors.split(',') if item.actors else []
            is_followed = any(a in followed_actors for a in actors)

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
        'followed_missing': followed_missing[:20],  # 只保留前20
        'high_score_missing': high_score_missing[:20]
    }

    report = Report(
        type='annual',
        title=f'年度榜单缺口 ({len(missing)}部缺失)',
        data=json.dumps(report_data)
    )
    db.session.add(report)
    db.session.commit()

    return report.to_dict()
