import os
import json
from datetime import datetime
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler

import config
from models import Base

# Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = config.DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)
db = SQLAlchemy(app, model_class=Base)

# Scheduler
scheduler = BackgroundScheduler()

# ==================== API Routes ====================

@app.route('/api/movies', methods=['GET'])
def get_movies():
    """获取影片列表（分页、筛选、排序）"""
    from models import Movie

    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 24))
    sort = request.args.get('sort', 'date_added_desc')
    actor = request.args.get('actor')
    min_score = float(request.args.get('min_score', 0))
    chart = request.args.get('list')

    query = Movie.query

    # 筛选
    if actor:
        query = query.filter(Movie.actors.contains(actor))
    if min_score > 0:
        query = query.filter(Movie.javdb_score >= min_score)
    if chart == 'javdb250':
        query = query.filter(Movie.in_javdb_top250 == True)
    elif chart == 'javlib500':
        query = query.filter(Movie.in_javlib_top500 == True)

    # 排序
    if sort == 'weighted_desc':
        query = query.order_by(Movie.weighted_score.desc())
    elif sort == 'weighted_asc':
        query = query.order_by(Movie.weighted_score.asc())
    elif sort == 'javdb_desc':
        query = query.order_by(Movie.javdb_score.desc())
    elif sort == 'date_added_desc':
        query = query.order_by(Movie.date_added.desc())
    elif sort == 'date_added_asc':
        query = query.order_by(Movie.date_added.asc())

    # 分页
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'items': [m.to_dict() for m in pagination.items]
    })


@app.route('/api/movies/<code>', methods=['GET'])
def get_movie(code):
    """获取影片详情"""
    from models import Movie
    movie = Movie.query.filter_by(code=code).first()
    if not movie:
        return jsonify({'error': 'Movie not found'}), 404
    return jsonify(movie.to_dict())


@app.route('/api/movies/<code>/refresh', methods=['POST'])
def refresh_movie_score(code):
    """刷新单个影片评分"""
    from services.javdb_scraper import fetch_movie_score
    from models import Movie

    movie = Movie.query.filter_by(code=code).first()
    if not movie:
        return jsonify({'error': 'Movie not found'}), 404

    score = fetch_movie_score(code)
    if score:
        movie.javdb_score = score
        movie.last_score_update = datetime.utcnow()
        movie.score_fetch_count += 1
        db.session.commit()

    return jsonify({'code': code, 'javdb_score': score})


@app.route('/api/movies/<code>', methods=['DELETE'])
def delete_movie(code):
    """删除影片"""
    from models import Movie
    movie = Movie.query.filter_by(code=code).first()
    if not movie:
        return jsonify({'error': 'Movie not found'}), 404

    db.session.delete(movie)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/actors', methods=['GET'])
def get_actors():
    """获取演员列表"""
    from models import Actor

    followed_only = request.args.get('followed_only', 'false').lower() == 'true'
    sort = request.args.get('sort', 'movie_count_desc')
    search = request.args.get('search', '')

    query = Actor.query

    if followed_only:
        query = query.filter(Actor.is_followed == True)
    if search:
        query = query.filter(Actor.name.contains(search))

    if sort == 'movie_count_desc':
        query = query.order_by(Actor.movie_count.desc())
    elif sort == 'name':
        query = query.order_by(Actor.name)

    actors = query.all()
    return jsonify([a.to_dict() for a in actors])


@app.route('/api/actors/<name>', methods=['GET'])
def get_actor(name):
    """获取演员详情"""
    from models import Actor, Movie, ChartItem

    actor = Actor.query.filter_by(name=name).first()
    if not actor:
        return jsonify({'error': 'Actor not found'}), 404

    # 获取该演员的影片
    movies = Movie.query.filter(Movie.actors.contains(name)).all()

    # 获取榜单出现记录
    chart_appearances = []
    for movie in movies:
        items = ChartItem.query.filter_by(movie_id=movie.id).all()
        for item in items:
            chart = item.chart
            chart_appearances.append({
                'chart_name': chart.display_name or chart.name,
                'rank': item.rank,
                'code': item.code
            })

    # 获取缺失影片（榜单中有但本地库没有的）
    all_chart_items = ChartItem.query.filter(
        ChartItem.actors.contains(name),
        ChartItem.movie_id.is_(None)
    ).all()

    result = actor.to_dict()
    result['movies'] = [m.to_dict() for m in movies]
    result['chart_appearances'] = chart_appearances
    result['missing_in_charts'] = [i.to_dict() for i in all_chart_items]

    return jsonify(result)


@app.route('/api/actors/<int:actor_id>/follow', methods=['PUT'])
def toggle_actor_follow(actor_id):
    """切换关注状态"""
    from models import Actor

    actor = Actor.query.get(actor_id)
    if not actor:
        return jsonify({'error': 'Actor not found'}), 404

    actor.is_followed = not actor.is_followed
    db.session.commit()

    return jsonify({'id': actor.id, 'is_followed': actor.is_followed})


@app.route('/api/charts', methods=['GET'])
def get_charts():
    """获取榜单列表"""
    from models import Chart, ChartItem, Movie

    charts = Chart.query.filter_by(is_active=True).all()
    result = []

    for chart in charts:
        chart_dict = chart.to_dict()

        # 统计已收藏
        collected = ChartItem.query.filter_by(chart_id=chart.id).filter(
            ChartItem.movie_id.isnot(None)
        ).count()

        chart_dict['collected'] = collected
        chart_dict['missing'] = chart.total_count - collected
        chart_dict['coverage_percent'] = round(collected / chart.total_count * 100, 1) if chart.total_count > 0 else 0

        result.append(chart_dict)

    return jsonify(result)


@app.route('/api/charts/<name>', methods=['GET'])
def get_chart(name):
    """获取榜单详情"""
    from models import Chart, ChartItem

    chart = Chart.query.filter_by(name=name).first()
    if not chart:
        return jsonify({'error': 'Chart not found'}), 404

    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    filter_type = request.args.get('filter', 'all')  # all, collected, missing

    query = ChartItem.query.filter_by(chart_id=chart.id)

    if filter_type == 'collected':
        query = query.filter(ChartItem.movie_id.isnot(None))
    elif filter_type == 'missing':
        query = query.filter(ChartItem.movie_id.is_(None))

    query = query.order_by(ChartItem.rank)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # 统计
    collected = ChartItem.query.filter_by(chart_id=chart.id).filter(
        ChartItem.movie_id.isnot(None)
    ).count()

    return jsonify({
        'chart': chart.to_dict(),
        'total': chart.total_count,
        'collected': collected,
        'missing': chart.total_count - collected,
        'coverage_percent': round(collected / chart.total_count * 100, 1) if chart.total_count > 0 else 0,
        'page': page,
        'per_page': per_page,
        'items': [item.to_dict() for item in pagination.items]
    })


@app.route('/api/charts/<name>/gaps', methods=['GET'])
def get_chart_gaps(name):
    """获取榜单缺口分析"""
    from models import Chart, ChartItem, Movie, Actor

    chart = Chart.query.filter_by(name=name).first()
    if not chart:
        return jsonify({'error': 'Chart not found'}), 404

    # 所有榜单影片
    chart_items = ChartItem.query.filter_by(chart_id=chart.id).order_by(ChartItem.rank).all()

    # 本地库番号
    local_codes = {m.code for m in Movie.query.all()}

    missing = []
    for item in chart_items:
        if item.code not in local_codes:
            actors = item.actors.split(',') if item.actors else []
            is_followed = Actor.query.filter(
                Actor.name.in_(actors),
                Actor.is_followed == True
            ).first() is not None

            missing.append({
                'rank': item.rank,
                'code': item.code,
                'title': item.title,
                'score': item.score,
                'actors': actors,
                'is_followed_actor': is_followed
            })

    # 按关注演员分组
    by_followed_actor = {}
    for item in missing:
        if item['is_followed_actor']:
            for actor_name in item['actors']:
                if Actor.query.filter_by(name=actor_name, is_followed=True).first():
                    by_followed_actor.setdefault(actor_name, []).append(item)

    return jsonify({
        'chart_name': chart.display_name or chart.name,
        'total': len(chart_items),
        'collected': len(chart_items) - len(missing),
        'missing': len(missing),
        'coverage_percent': round((len(chart_items) - len(missing)) / len(chart_items) * 100, 1) if chart_items else 0,
        'by_score_range': {
            'high': [m for m in missing if m['score'] and m['score'] >= 4.5],
            'medium': [m for m in missing if m['score'] and 4.0 <= m['score'] < 4.5],
            'low': [m for m in missing if m['score'] and m['score'] < 4.0]
        },
        'by_followed_actor': by_followed_actor,
        'all_missing': missing
    })


@app.route('/api/charts/<name>/refresh', methods=['POST'])
def refresh_chart(name):
    """重新抓取榜单"""
    from services.chart_scraper import scrape_chart
    from models import Chart

    chart = Chart.query.filter_by(name=name).first()
    if not chart:
        return jsonify({'error': 'Chart not found'}), 404

    # 后台任务
    import threading
    thread = threading.Thread(target=scrape_chart, args=(chart,))
    thread.daemon = True
    thread.start()

    return jsonify({'status': 'started', 'message': f'Started refreshing {chart.display_name}'})


@app.route('/api/reports', methods=['GET'])
def get_reports():
    """获取报告列表"""
    from models import Report

    reports = Report.query.order_by(Report.generated_at.desc()).limit(20).all()
    return jsonify([r.to_dict() for r in reports])


@app.route('/api/reports/latest', methods=['GET'])
def get_latest_reports():
    """获取最新报告"""
    from models import Report

    weekly = Report.query.filter_by(type='weekly').order_by(Report.generated_at.desc()).first()
    monthly = Report.query.filter_by(type='monthly').order_by(Report.generated_at.desc()).first()
    annual = Report.query.filter_by(type='annual').order_by(Report.generated_at.desc()).first()

    return jsonify({
        'weekly': weekly.to_dict() if weekly else None,
        'monthly': monthly.to_dict() if monthly else None,
        'annual': annual.to_dict() if annual else None
    })


@app.route('/api/reports/generate', methods=['POST'])
def generate_report():
    """手动生成报告"""
    from services.report_generator import generate_weekly_report, generate_monthly_report, generate_annual_report

    report_type = request.json.get('type', 'weekly')

    if report_type == 'weekly':
        result = generate_weekly_report()
    elif report_type == 'monthly':
        result = generate_monthly_report()
    elif report_type == 'annual':
        result = generate_annual_report()
    else:
        return jsonify({'error': 'Invalid report type'}), 400

    return jsonify(result)


@app.route('/api/reports/<int:report_id>/read', methods=['PUT'])
def mark_report_read(report_id):
    """标记报告已读"""
    from models import Report

    report = Report.query.get(report_id)
    if not report:
        return jsonify({'error': 'Report not found'}), 404

    report.is_read = True
    db.session.commit()

    return jsonify({'success': True})


@app.route('/api/todos', methods=['GET'])
def get_todos():
    """获取待看清单"""
    from models import TodoItem

    status = request.args.get('status', 'pending')

    query = TodoItem.query
    if status != 'all':
        query = query.filter_by(status=status)

    items = query.order_by(TodoItem.added_at.desc()).all()

    # 按来源分组
    groups = {}
    for item in items:
        key = f"{item.source}-{item.source_detail or ''}"
        if key not in groups:
            groups[key] = {
                'source': item.source,
                'source_detail': item.source_detail,
                'items': []
            }
        groups[key]['items'].append(item.to_dict())
        groups[key]['count'] = len(groups[key]['items'])

    return jsonify({
        'groups': list(groups.values()),
        'total_pending': TodoItem.query.filter_by(status='pending').count(),
        'total_downloaded': TodoItem.query.filter_by(status='downloaded').count()
    })


@app.route('/api/todos', methods=['POST'])
def add_todo():
    """添加待看项"""
    from models import TodoItem

    data = request.json
    code = data.get('code')
    title = data.get('title', code)
    actors = data.get('actors', '')
    source = data.get('source', 'manual')
    source_detail = data.get('source_detail')

    # 检查是否已存在
    existing = TodoItem.query.filter_by(code=code, source=source).first()
    if existing:
        return jsonify({'error': 'Already in todo list'}), 400

    todo = TodoItem(
        code=code,
        title=title,
        actors=actors,
        source=source,
        source_detail=source_detail
    )
    db.session.add(todo)
    db.session.commit()

    return jsonify(todo.to_dict())


@app.route('/api/todos/<int:todo_id>/status', methods=['PUT'])
def update_todo_status(todo_id):
    """更新待看项状态"""
    from models import TodoItem

    todo = TodoItem.query.get(todo_id)
    if not todo:
        return jsonify({'error': 'Todo not found'}), 404

    new_status = request.json.get('status', 'pending')
    todo.status = new_status
    if new_status == 'downloaded':
        todo.downloaded_at = datetime.utcnow()

    db.session.commit()

    return jsonify(todo.to_dict())


@app.route('/api/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    """删除待看项"""
    from models import TodoItem

    todo = TodoItem.query.get(todo_id)
    if not todo:
        return jsonify({'error': 'Todo not found'}), 404

    db.session.delete(todo)
    db.session.commit()

    return jsonify({'success': True})


@app.route('/api/todos/batch', methods=['POST'])
def batch_add_todos():
    """批量添加待看项"""
    from models import TodoItem

    items = request.json.get('items', [])
    added = []

    for item in items:
        code = item.get('code')
        existing = TodoItem.query.filter_by(code=code).first()
        if existing:
            continue

        todo = TodoItem(
            code=code,
            title=item.get('title', code),
            actors=item.get('actors', ''),
            source=item.get('source', 'manual'),
            source_detail=item.get('source_detail')
        )
        db.session.add(todo)
        added.append(todo)

    db.session.commit()

    return jsonify({'added': len(added)})


@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """获取任务状态"""
    from models import TaskLog

    running = TaskLog.query.filter_by(status='running').all()
    recent = TaskLog.query.filter_by(status='completed').order_by(
        TaskLog.finished_at.desc()
    ).limit(10).all()

    return jsonify({
        'running': [t.to_dict() for t in running],
        'recent_completed': [t.to_dict() for t in recent]
    })


@app.route('/api/tasks/sync', methods=['POST'])
def sync_jellyfin():
    """触发 Jellyfin 同步"""
    from services.jellyfin import sync_from_jellyfin

    import threading
    thread = threading.Thread(target=sync_from_jellyfin)
    thread.daemon = True
    thread.start()

    return jsonify({'status': 'started', 'message': 'Jellyfin sync started'})


@app.route('/api/tasks/scores', methods=['POST'])
def update_scores():
    """触发评分更新"""
    from services.score_updater import update_all_scores

    import threading
    thread = threading.Thread(target=update_all_scores)
    thread.daemon = True
    thread.start()

    return jsonify({'status': 'started', 'message': 'Score update started'})


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取统计数据"""
    from models import Movie, Actor, TodoItem

    total_movies = Movie.query.count()
    avg_score = db.session.query(db.func.avg(Movie.javdb_score)).scalar() or 0

    followed_actors = Actor.query.filter_by(is_followed=True).count()
    total_actors = Actor.query.count()

    pending_todos = TodoItem.query.filter_by(status='pending').count()

    return jsonify({
        'total_movies': total_movies,
        'avg_score': round(avg_score, 2),
        'followed_actors': followed_actors,
        'total_actors': total_actors,
        'pending_todos': pending_todos
    })


@app.route('/api/poster/<jellyfin_id>', methods=['GET'])
def get_poster(jellyfin_id):
    """获取 Jellyfin 海报"""
    import requests as req
    from flask import Response

    url = f"{config.JELLYFIN_URL}Items/{jellyfin_id}/Images/Primary"
    headers = {'X-MediaBrowser-Token': config.JELLYFIN_API_KEY}

    try:
        resp = req.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return Response(resp.content, mimetype='image/jpeg')
    except Exception:
        pass

    # 返回占位 SVG
    placeholder_svg = b'<svg xmlns="http://www.w3.org/2000/svg" width="200" height="300" viewBox="0 0 200 300"><rect fill="#2a2a2a" width="200" height="300"/><text x="100" y="150" text-anchor="middle" fill="#666" font-size="48">🎬</text></svg>'
    return Response(placeholder_svg, mimetype='image/svg+xml')


# ==================== 静态文件 ====================

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(app.static_folder, path)


# ==================== 初始化 ====================

def init_db():
    """初始化数据库"""
    with app.app_context():
        db.create_all()
        # 初始化默认榜单
        from services.chart_scraper import init_default_charts
        init_default_charts()


def init_scheduler():
    """初始化定时任务"""
    from services.report_generator import generate_weekly_report, generate_monthly_report, generate_annual_report

    # 每周一 09:00
    scheduler.add_job(
        generate_weekly_report,
        'cron',
        day_of_week='mon',
        hour=9,
        minute=0,
        id='weekly_report'
    )

    # 每月1日 09:00
    scheduler.add_job(
        generate_monthly_report,
        'cron',
        day=1,
        hour=9,
        minute=0,
        id='monthly_report'
    )

    # 每半年（1月和7月）生成年报
    scheduler.add_job(
        generate_annual_report,
        'cron',
        month='1,7',
        day=1,
        hour=9,
        minute=0,
        id='annual_report'
    )

    scheduler.start()


if __name__ == '__main__':
    init_db()

    if config.AUTO_SYNC_ON_STARTUP:
        from services.jellyfin import sync_from_jellyfin
        import threading
        thread = threading.Thread(target=sync_from_jellyfin)
        thread.daemon = True
        thread.start()

    try:
        init_scheduler()
    except:
        pass

    app.run(host='0.0.0.0', port=5000, debug=True)
