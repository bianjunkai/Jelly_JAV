import os
import json
from datetime import datetime
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler

import config
from models import Base
from sqlalchemy import event

# Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = config.DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# 配置 SQLite WAL 模式以支持更好的并发
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {
        'timeout': 30,
        'check_same_thread': False
    },
    'pool_pre_ping': True
}

CORS(app)
db = SQLAlchemy(app, model_class=Base)

# 启用 SQLite WAL 模式 - 在应用上下文中注册事件监听器
with app.app_context():
    @event.listens_for(db.engine, 'connect')
    def set_sqlite_pragma(dbapi_conn, connection_record):
        dbapi_conn.execute('PRAGMA journal_mode=WAL')
        dbapi_conn.execute('PRAGMA busy_timeout=30000')

# Scheduler
scheduler = BackgroundScheduler()

# ==================== Config Persistence ====================

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

def load_config_from_file():
    """从文件加载配置到 config 模块"""
    print(f"[CONFIG] Trying to load from {CONFIG_FILE}")
    print(f"[CONFIG] File exists: {os.path.exists(CONFIG_FILE)}")
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
            print(f"[CONFIG] Loaded data: {saved}")
            for key, value in saved.items():
                if hasattr(config, key):
                    setattr(config, key, value)
                    print(f"[CONFIG] Set {key} = {value}")
        except Exception as e:
            print(f"Failed to load config from file: {e}")

def save_config_to_file():
    """保存 config 模块到文件"""
    config_data = {
        'JELLYFIN_URL': config.JELLYFIN_URL,
        'JELLYFIN_API_KEY': config.JELLYFIN_API_KEY,
        'JAVDB_DOMAINS': config.JAVDB_DOMAINS,
        'JAVBUS_DOMAINS': config.JAVBUS_DOMAINS,
        'JAVLIBRARY_CSV_PATH': getattr(config, 'JAVLIBRARY_CSV_PATH', ''),
        'REQUEST_MIN_DELAY': config.REQUEST_MIN_DELAY,
        'REQUEST_MAX_DELAY': config.REQUEST_MAX_DELAY,
        'REQUEST_TIMEOUT': config.REQUEST_TIMEOUT,
        'ENABLE_SYSTEM_PROXY': config.ENABLE_SYSTEM_PROXY,
        'SYSTEM_PROXY_URL': config.SYSTEM_PROXY_URL,
        'WEIGHT_BASE': config.WEIGHT_BASE,
        'WEIGHT_JAVDB_HIGH': config.WEIGHT_JAVDB_HIGH,
        'WEIGHT_JAVDB_MEDIUM': config.WEIGHT_JAVDB_MEDIUM,
        'WEIGHT_JAVDB_LOW': config.WEIGHT_JAVDB_LOW,
        'WEIGHT_JAVDB_VERY_LOW': config.WEIGHT_JAVDB_VERY_LOW,
        'WEIGHT_DUAL_CHART': config.WEIGHT_DUAL_CHART,
        'WEIGHT_SINGLE_CHART': config.WEIGHT_SINGLE_CHART,
        'WEIGHT_YEAR_CHART': config.WEIGHT_YEAR_CHART,
        'WEIGHT_MULTI_ACTOR': config.WEIGHT_MULTI_ACTOR,
    }
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        print(f"[CONFIG] Saved config to {CONFIG_FILE}")
        print(f"[CONFIG] Saved data: {config_data}")
    except Exception as e:
        print(f"Failed to save config to file: {e}")

# 启动时加载已保存的配置
load_config_from_file()

# ==================== API Routes ====================

@app.route('/api/movies', methods=['GET'])
def get_movies():
    """获取影片列表（分页、筛选、排序）"""
    from models import Movie, Chart

    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 24))
    sort = request.args.get('sort', 'date_added_desc')
    search = request.args.get('search', '')
    actor = request.args.get('actor')
    min_score = float(request.args.get('min_score', 0))
    chart = request.args.get('list')

    query = db.session.query(Movie)

    # 搜索（番号或演员）
    if search:
        search_pattern = f'%{search}%'
        query = query.filter(
            db.or_(
                Movie.code.ilike(search_pattern),
                Movie.title.ilike(search_pattern),
                Movie.actors.ilike(search_pattern)
            )
        )
    if actor:
        query = query.filter(Movie.actors.contains(actor))
    if min_score > 0:
        query = query.filter(Movie.javdb_score >= min_score)

    # 榜单筛选
    if chart:
        from models import ChartItem
        chart_obj = db.session.query(Chart).filter_by(name=chart).first()
        if chart_obj:
            chart_items = db.session.query(ChartItem).filter_by(chart_id=chart_obj.id).all()
            codes = [item.code for item in chart_items]
            query = query.filter(Movie.code.in_(codes))

    # 排序
    if sort == 'weighted_score_desc':
        query = query.order_by(Movie.weighted_score.desc())
    elif sort == 'weighted_score_asc':
        query = query.order_by(Movie.weighted_score.asc())
    elif sort == 'javdb_score_desc':
        query = query.order_by(Movie.javdb_score.desc())
    elif sort == 'javdb_score_asc':
        query = query.order_by(Movie.javdb_score.asc())
    elif sort == 'release_date_desc':
        query = query.order_by(Movie.year.desc().nullslast())
    elif sort == 'release_date_asc':
        query = query.order_by(Movie.year.asc().nullslast())
    elif sort == 'date_added_desc':
        query = query.order_by(Movie.date_added.desc().nullslast())
    elif sort == 'date_added_asc':
        query = query.order_by(Movie.date_added.asc().nullslast())

    # 分页
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'items': [m.to_dict() for m in pagination.items]
    })


@app.route('/api/movies/top-actors', methods=['GET'])
def get_top_actors():
    """获取影片数量最多的演员"""
    from models import Actor

    limit = int(request.args.get('limit', 20))
    actors = db.session.query(Actor).order_by(Actor.movie_count.desc()).limit(limit).all()

    return jsonify({
        'actors': [a.name for a in actors]
    })


@app.route('/api/movies/<code>', methods=['GET'])
def get_movie(code):
    """获取影片详情"""
    from models import Movie
    movie = db.session.query(Movie).filter_by(code=code).first()
    if not movie:
        return jsonify({'error': 'Movie not found'}), 404
    return jsonify(movie.to_dict())


@app.route('/api/movies/<code>/refresh', methods=['POST'])
def refresh_movie_score(code):
    """刷新单个影片评分"""
    from services.javdb_scraper import fetch_movie_score
    from models import Movie

    movie = db.session.query(Movie).filter_by(code=code).first()
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
    movie = db.session.query(Movie).filter_by(code=code).first()
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

    query = db.session.query(Actor)

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

    actor = db.session.query(Actor).filter_by(name=name).first()
    if not actor:
        return jsonify({'error': 'Actor not found'}), 404

    # 获取该演员的影片
    movies = db.session.query(Movie).filter(Movie.actors.contains(name)).all()

    # 获取榜单出现记录
    chart_appearances = []
    for movie in movies:
        items = db.session.query(ChartItem).filter_by(movie_id=movie.id).all()
        for item in items:
            chart = item.chart
            chart_appearances.append({
                'chart_name': chart.display_name or chart.name,
                'rank': item.rank,
                'code': item.code
            })

    # 获取缺失影片（榜单中有但本地库没有的）
    all_chart_items = db.session.query(ChartItem).filter(
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

    actor = db.session.get(Actor, actor_id)
    if not actor:
        return jsonify({'error': 'Actor not found'}), 404

    actor.is_followed = not actor.is_followed
    db.session.commit()

    return jsonify({'id': actor.id, 'is_followed': actor.is_followed})


@app.route('/api/actors/refresh-photos', methods=['POST'])
def refresh_actor_photos():
    """刷新所有演员的头像URL

    遍历所有演员，设置 photo_url 为 /api/actor-image/{encoded_name}
    用于初始化或修复缺失的头像URL
    """
    import urllib.parse
    from models import Actor

    actors = db.session.query(Actor).all()
    count = 0
    for actor in actors:
        encoded_name = urllib.parse.quote(actor.name)
        actor.photo_url = f'/api/actor-image/{encoded_name}'
        count += 1

    db.session.commit()
    return jsonify({'success': True, 'count': count})


@app.route('/api/actors/<int:actor_id>/releases', methods=['GET'])
def get_actor_releases(actor_id):
    """获取演员的新片列表（JavBus）"""
    from models import Actor, ActorRelease, Movie

    actor = db.session.get(Actor, actor_id)
    if not actor:
        return jsonify({'error': 'Actor not found'}), 404

    releases = db.session.query(ActorRelease).filter_by(actor_id=actor_id).order_by(ActorRelease.detected_at.desc()).all()

    # 获取所有本地影片的番号，用于标记已入库
    local_codes = {m.code for m in db.session.query(Movie).all()}

    releases_data = []
    for r in releases:
        data = r.to_dict()
        data['in_library'] = r.code in local_codes
        releases_data.append(data)

    return jsonify({
        'actor_id': actor_id,
        'actor_name': actor.name,
        'javbus_id': actor.javbus_id,
        'releases': releases_data,
        'total': len(releases_data)
    })


@app.route('/api/actors/<int:actor_id>/fetch-releases', methods=['POST'])
def fetch_actor_releases(actor_id):
    """从 JavDB 获取演员新片

    在后台线程中运行
    """
    from models import Actor

    actor = db.session.get(Actor, actor_id)
    if not actor:
        return jsonify({'error': 'Actor not found'}), 404

    # 检查该演员是否有本地影片（用于查找 JavDB 链接）
    from models import Movie
    movies_with_actor = db.session.query(Movie).filter(Movie.actors.contains(actor.name)).all()
    if not movies_with_actor:
        return jsonify({'error': 'Actor has no movies in library'}), 400

    import threading
    import logging

    def background_fetch():
        logger = logging.getLogger(__name__)
        logger.info(f"[ActorReleases] Starting background fetch for actor_id={actor_id}")
        result = _fetch_actor_releases_thread(actor_id, app, db)
        logger.info(f"[ActorReleases] Background fetch completed for actor_id={actor_id}: {result}")

    thread = threading.Thread(target=background_fetch)
    thread.daemon = True
    thread.start()

    return jsonify({'status': 'started', 'message': f'Fetching releases for actor {actor_id}'})


def _fetch_actor_releases_thread(actor_id: int, app=None, db=None) -> dict:
    """后台线程中从 JavDB 获取演员新片"""
    from services.javdb_scraper import fetch_actor_releases as javdb_fetch_actor_releases

    if app is None:
        from app import app as current_app
        app = current_app
    if db is None:
        from app import db as current_db
        db = current_db

    with app.app_context():
        return javdb_fetch_actor_releases(actor_id, db=db, limit_months=3)


@app.route('/api/actors/fetch-all-releases', methods=['POST'])
def fetch_all_actor_releases():
    """为所有已关注演员获取新片（从 JavDB）

    在后台线程中运行
    """
    import threading

    def background_fetch():
        _fetch_all_releases_thread(app, db)

    thread = threading.Thread(target=background_fetch)
    thread.daemon = True
    thread.start()

    return jsonify({'status': 'started', 'message': 'Fetching releases for all followed actors'})


def _fetch_all_releases_thread(app=None, db=None):
    """后台线程中执行的全量爬取（从 JavDB）"""
    import logging
    from services.javdb_scraper import fetch_actor_releases as javdb_fetch_actor_releases

    if app is None:
        from app import app as current_app
        app = current_app
    if db is None:
        from app import db as current_db
        db = current_db

    logger = logging.getLogger(__name__)

    with app.app_context():
        from models import Actor, Movie

        logger.info("[ActorReleases] Starting background fetch for all followed actors from JavDB")

        # 获取所有已关注的演员（需要有本地影片才能查找 JavDB 链接）
        actors = db.session.query(Actor).filter(Actor.is_followed == True).all()

        # 过滤出有本地影片的演员
        actors_with_movies = []
        for actor in actors:
            movies_with_actor = db.session.query(Movie).filter(Movie.actors.contains(actor.name)).first()
            if movies_with_actor:
                actors_with_movies.append(actor)

        logger.info(f"[ActorReleases] Found {len(actors_with_movies)} actors to fetch")

        total_added = 0
        for actor in actors_with_movies:
            try:
                result = javdb_fetch_actor_releases(actor.id, db=db, limit_months=3)
                if result.get('success') and result.get('items_added', 0) > 0:
                    total_added += result['items_added']
                    logger.info(f"[ActorReleases] {actor.name}: added {result['items_added']} releases")
            except Exception as e:
                logger.error(f"Error fetching actor {actor.name}: {e}")

        logger.info(f"[ActorReleases] Background fetch completed. Total added: {total_added}")


@app.route('/api/charts', methods=['GET'])
def get_charts():
    """获取榜单列表"""
    from models import Chart, ChartItem, Movie

    charts = db.session.query(Chart).filter_by(is_active=True).all()
    result = []

    for chart in charts:
        chart_dict = chart.to_dict()

        # 统计实际条目数（从数据库中实际获取的数量）
        actual_count = db.session.query(ChartItem).filter_by(chart_id=chart.id).count()

        # 统计已收藏
        collected = db.session.query(ChartItem).filter_by(chart_id=chart.id).filter(
            ChartItem.movie_id.isnot(None)
        ).count()

        chart_dict['actual_count'] = actual_count
        chart_dict['collected'] = collected
        chart_dict['missing'] = actual_count - collected
        chart_dict['coverage_percent'] = round(collected / actual_count * 100, 1) if actual_count > 0 else 0

        result.append(chart_dict)

    return jsonify(result)


@app.route('/api/charts/<name>', methods=['GET'])
def get_chart(name):
    """获取榜单详情"""
    from models import Chart, ChartItem

    chart = db.session.query(Chart).filter_by(name=name).first()
    if not chart:
        return jsonify({'error': 'Chart not found'}), 404

    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    filter_type = request.args.get('filter', 'all')  # all, collected, missing

    query = db.session.query(ChartItem).filter_by(chart_id=chart.id)

    if filter_type == 'collected':
        query = query.filter(ChartItem.movie_id.isnot(None))
    elif filter_type == 'missing':
        query = query.filter(ChartItem.movie_id.is_(None))

    query = query.order_by(ChartItem.rank)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # 统计
    collected = db.session.query(ChartItem).filter_by(chart_id=chart.id).filter(
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

    chart = db.session.query(Chart).filter_by(name=name).first()
    if not chart:
        return jsonify({'error': 'Chart not found'}), 404

    # 所有榜单影片
    chart_items = db.session.query(ChartItem).filter_by(chart_id=chart.id).order_by(ChartItem.rank).all()

    # 本地库番号
    local_codes = {m.code for m in db.session.query(Movie).all()}

    missing = []
    for item in chart_items:
        if item.code not in local_codes:
            actors = item.actors.split(',') if item.actors else []
            is_followed = db.session.query(Actor).filter(
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
                if db.session.query(Actor).filter_by(name=actor_name, is_followed=True).first():
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

    chart = db.session.query(Chart).filter_by(name=name).first()
    if not chart:
        return jsonify({'error': 'Chart not found'}), 404

    # 后台任务 - 传递 app 和 db 实例
    import threading
    thread = threading.Thread(target=scrape_chart, args=(chart, app, db))
    thread.daemon = True
    thread.start()

    return jsonify({'status': 'started', 'message': f'Started refreshing {chart.display_name}'})


@app.route('/api/reports', methods=['GET'])
def get_reports():
    """获取报告列表"""
    from models import Report

    reports = db.session.query(Report).order_by(Report.generated_at.desc()).limit(20).all()
    return jsonify([r.to_dict() for r in reports])


@app.route('/api/reports/latest', methods=['GET'])
def get_latest_reports():
    """获取最新报告"""
    from models import Report

    weekly = db.session.query(Report).filter_by(type='weekly').order_by(Report.generated_at.desc()).first()
    monthly = db.session.query(Report).filter_by(type='monthly').order_by(Report.generated_at.desc()).first()
    annual = db.session.query(Report).filter_by(type='annual').order_by(Report.generated_at.desc()).first()

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
        result = generate_weekly_report(app, db)
    elif report_type == 'monthly':
        result = generate_monthly_report(app, db)
    elif report_type == 'annual':
        result = generate_annual_report(app, db)
    else:
        return jsonify({'error': 'Invalid report type'}), 400

    return jsonify(result)


@app.route('/api/reports/<int:report_id>/read', methods=['PUT'])
def mark_report_read(report_id):
    """标记报告已读"""
    from models import Report

    report = db.session.get(Report, report_id)
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

    query = db.session.query(TodoItem)
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
        'total_pending': db.session.query(TodoItem).filter_by(status='pending').count(),
        'total_downloaded': db.session.query(TodoItem).filter_by(status='downloaded').count()
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
    existing = db.session.query(TodoItem).filter_by(code=code, source=source).first()
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

    todo = db.session.get(TodoItem,todo_id)
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

    todo = db.session.get(TodoItem,todo_id)
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
        existing = db.session.query(TodoItem).filter_by(code=code).first()
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

    running = db.session.query(TaskLog).filter_by(status='running').all()
    recent = db.session.query(TaskLog).filter_by(status='completed').order_by(
        TaskLog.finished_at.desc()
    ).limit(10).all()

    return jsonify({
        'running': [t.to_dict() for t in running],
        'recent_completed': [t.to_dict() for t in recent]
    })


@app.route('/api/tasks/sync', methods=['POST'])
def sync_jellyfin():
    """触发 Jellyfin 同步"""
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    from services.jellyfin import sync_from_jellyfin
    import config as config_module

    logger.info(f"JELLYFIN_URL: {config_module.JELLYFIN_URL}")
    logger.info(f"JELLYFIN_API_KEY set: {bool(config_module.JELLYFIN_API_KEY)}")

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


@app.route('/api/tasks/weighted-scores', methods=['POST'])
def recalculate_weighted_scores():
    """重新计算所有影片的加权分"""
    from services.score_updater import calculate_weighted_score

    movies = db.session.query(Movie).filter(Movie.code.isnot(None)).all()
    updated = 0
    for movie in movies:
        old_score = movie.weighted_score
        new_score = calculate_weighted_score(movie)
        if old_score != new_score:
            movie.weighted_score = new_score
            updated += 1

    db.session.commit()

    return jsonify({'status': 'completed', 'updated': updated, 'total': len(movies)})


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取统计数据"""
    from models import Movie, Actor, TodoItem

    total_movies = db.session.query(Movie).count()
    avg_score = db.session.query(db.func.avg(Movie.javdb_score)).scalar() or 0

    followed_actors = db.session.query(Actor).filter_by(is_followed=True).count()
    total_actors = db.session.query(Actor).count()

    pending_todos = db.session.query(TodoItem).filter_by(status='pending').count()

    return jsonify({
        'total_movies': total_movies,
        'avg_score': round(avg_score, 2),
        'followed_actors': followed_actors,
        'total_actors': total_actors,
        'pending_todos': pending_todos
    })


@app.route('/api/config', methods=['GET'])
def get_config():
    """获取配置"""
    # 尝试从持久化文件加载配置
    load_config_from_file()
    return jsonify({
        'jellyfin_url': config.JELLYFIN_URL,
        'jellyfin_api_key': config.JELLYFIN_API_KEY,
        'javdb_domains': config.JAVDB_DOMAINS,
        'javbus_domains': config.JAVBUS_DOMAINS,
        'javlibrary_csv_path': getattr(config, 'JAVLIBRARY_CSV_PATH', ''),
        'request_min_delay': config.REQUEST_MIN_DELAY,
        'request_max_delay': config.REQUEST_MAX_DELAY,
        'request_timeout': config.REQUEST_TIMEOUT,
        'enable_system_proxy': config.ENABLE_SYSTEM_PROXY,
        'system_proxy_url': config.SYSTEM_PROXY_URL,
        'weight_base': config.WEIGHT_BASE,
        'weight_javdb_high': config.WEIGHT_JAVDB_HIGH,
        'weight_javdb_medium': config.WEIGHT_JAVDB_MEDIUM,
        'weight_javdb_low': config.WEIGHT_JAVDB_LOW,
        'weight_javdb_very_low': config.WEIGHT_JAVDB_VERY_LOW,
        'weight_dual_chart': config.WEIGHT_DUAL_CHART,
        'weight_single_chart': config.WEIGHT_SINGLE_CHART,
        'weight_year_chart': config.WEIGHT_YEAR_CHART,
        'weight_multi_actor': config.WEIGHT_MULTI_ACTOR
    })


@app.route('/api/config', methods=['PUT'])
def update_config():
    """更新配置"""
    import logging
    logger = logging.getLogger(__name__)

    data = request.json
    logger.info(f"PUT /api/config received: {data}")

    # 更新 config 模块的属性
    if 'jellyfin_url' in data:
        old_url = config.JELLYFIN_URL
        config.JELLYFIN_URL = data['jellyfin_url']
        logger.info(f"Updated JELLYFIN_URL: {old_url} -> {config.JELLYFIN_URL}")
    if 'jellyfin_api_key' in data:
        old_key = config.JELLYFIN_API_KEY
        config.JELLYFIN_API_KEY = data['jellyfin_api_key']
        logger.info(f"Updated JELLYFIN_API_KEY: {'***' + str(old_key)[-4:] if old_key else 'None'} -> {'***' + config.JELLYFIN_API_KEY[-4:] if config.JELLYFIN_API_KEY else 'NOT SET'}")
    if 'javdb_domains' in data:
        config.JAVDB_DOMAINS = data['javdb_domains']
    if 'javbus_domains' in data:
        config.JAVBUS_DOMAINS = data['javbus_domains']
    if 'javlibrary_csv_path' in data:
        config.JAVLIBRARY_CSV_PATH = data['javlibrary_csv_path']
    if 'request_min_delay' in data:
        config.REQUEST_MIN_DELAY = data['request_min_delay']
    if 'request_max_delay' in data:
        config.REQUEST_MAX_DELAY = data['request_max_delay']
    if 'request_timeout' in data:
        config.REQUEST_TIMEOUT = data['request_timeout']
    if 'enable_system_proxy' in data:
        config.ENABLE_SYSTEM_PROXY = data['enable_system_proxy']
    if 'system_proxy_url' in data:
        config.SYSTEM_PROXY_URL = data['system_proxy_url']
    if 'weight_base' in data:
        config.WEIGHT_BASE = data['weight_base']
    if 'weight_javdb_high' in data:
        config.WEIGHT_JAVDB_HIGH = data['weight_javdb_high']
    if 'weight_javdb_medium' in data:
        config.WEIGHT_JAVDB_MEDIUM = data['weight_javdb_medium']
    if 'weight_javdb_low' in data:
        config.WEIGHT_JAVDB_LOW = data['weight_javdb_low']
    if 'weight_javdb_very_low' in data:
        config.WEIGHT_JAVDB_VERY_LOW = data['weight_javdb_very_low']
    if 'weight_dual_chart' in data:
        config.WEIGHT_DUAL_CHART = data['weight_dual_chart']
    if 'weight_single_chart' in data:
        config.WEIGHT_SINGLE_CHART = data['weight_single_chart']
    if 'weight_year_chart' in data:
        config.WEIGHT_YEAR_CHART = data['weight_year_chart']
    if 'weight_multi_actor' in data:
        config.WEIGHT_MULTI_ACTOR = data['weight_multi_actor']

    # 持久化到文件
    save_config_to_file()
    logger.info("Config saved to file")

    return jsonify({'success': True})


@app.route('/api/config/test-csv', methods=['POST'])
def test_csv_path():
    """测试 JavLibrary CSV 文件路径是否有效"""
    data = request.json
    csv_path = data.get('path', '')

    if not csv_path:
        return jsonify({'valid': False, 'error': '路径不能为空'}), 400

    # 如果是相对路径，转换为绝对路径（基于项目根目录）
    if not os.path.isabs(csv_path):
        from services.chart_scraper import get_project_base_dir
        project_dir = get_project_base_dir()
        csv_path = os.path.join(project_dir, csv_path)
        csv_path = os.path.normpath(csv_path)

    if not os.path.exists(csv_path):
        return jsonify({'valid': False, 'error': f'文件不存在: {csv_path}'}), 400

    try:
        # 尝试解析 CSV 文件
        from services.chart_scraper import parse_javlibrary_csv
        items = parse_javlibrary_csv(csv_path)

        if items is None or len(items) == 0:
            return jsonify({'valid': False, 'error': '无法解析 CSV 文件或文件为空'}), 400

        return jsonify({
            'valid': True,
            'count': len(items),
            'resolved_path': csv_path,
            'first_item': items[0] if items else None
        })

    except Exception as e:
        return jsonify({'valid': False, 'error': str(e)}), 400


@app.route('/api/config/charts', methods=['GET'])
def get_config_charts():
    """获取已配置的可爬取榜单"""
    from config import JAVDB_YEAR_CHART_YEARS

    # 构建年份榜单列表
    year_charts = [
        {'name': f'JavDB {year} TOP250', 'source': 'javdb', 'type': 'year', 'year': year, 'total': 250}
        for year in JAVDB_YEAR_CHART_YEARS
    ]

    return jsonify([
        {'name': 'JavDB TOP250', 'source': 'javdb', 'type': 'all', 'total': 250},
    ] + year_charts + [
        {'name': 'JavLibrary TOP500', 'source': 'javlibrary', 'type': 'all', 'total': 500}
    ])


@app.route('/api/charts', methods=['POST'])
def create_chart():
    """添加新榜单"""
    from models import Chart

    data = request.json
    name = data.get('name')
    display_name = data.get('display_name', name)
    source = data.get('source', 'javdb')
    description = data.get('description', '')
    total_count = data.get('total_count', 250)
    year = data.get('year')

    if not name:
        return jsonify({'error': 'Chart name is required'}), 400

    # 检查是否已存在
    existing = db.session.query(Chart).filter_by(name=name).first()
    if existing:
        return jsonify({'error': 'Chart already exists'}), 400

    chart = Chart(
        name=name,
        display_name=display_name,
        source=source,
        description=description,
        total_count=total_count,
        year=year
    )
    db.session.add(chart)
    db.session.commit()

    return jsonify(chart.to_dict())


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
    placeholder_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="300" viewBox="0 0 200 300"><rect fill="#2a2a2a" width="200" height="300"/><text x="100" y="150" text-anchor="middle" fill="#666" font-size="48">&#127909;</text></svg>'
    return Response(placeholder_svg.encode('utf-8'), mimetype='image/svg+xml')


@app.route('/api/actor-image/<path:actor_name>', methods=['GET'])
def get_actor_image(actor_name):
    """获取 Jellyfin 演员头像

    通过演员名字查询 Jellyfin People API 获取头像
    参考 legacy 版本实现
    """
    import requests as req
    from flask import Response
    import urllib.parse

    # 确保加载最新配置
    load_config_from_file()

    actor_name_decoded = urllib.parse.unquote(actor_name)
    actor_name_encoded = urllib.parse.quote(actor_name_decoded)

    # 使用 X-Emby-Token (legacy 版本兼容)
    headers = {'X-Emby-Token': config.JELLYFIN_API_KEY}
    base_url = config.JELLYFIN_URL.rstrip('/')

    # 方法1: 使用 /Items/ByName/People/{name} (legacy 版本方式)
    try:
        byname_url = f"{base_url}/Items/ByName/People/{actor_name_encoded}"
        resp = req.get(byname_url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("Id"):
                person_id = data.get("Id")
                # 使用 maxWidth=200 (legacy 版本方式)
                image_url = f"{base_url}/Items/{person_id}/Images/Primary?maxWidth=200"
                img_resp = req.get(image_url, headers=headers, timeout=10)
                if img_resp.status_code == 200:
                    content_type = img_resp.headers.get('Content-Type', 'image/jpeg')
                    return Response(img_resp.content, mimetype=content_type)
    except Exception as e:
        print(f"Actor image error (ByName): {e}")

    # 方法2: 使用 /Persons 搜索 (legacy 版本 fallback)
    try:
        persons_url = f"{base_url}/Persons"
        params = {"searchTerm": actor_name_decoded, "limit": 10}
        resp = req.get(persons_url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("Items", []):
                if item.get("Name") == actor_name_decoded:
                    person_id = item.get("Id")
                    if person_id:
                        # 使用 maxWidth=200 (legacy 版本方式)
                        image_url = f"{base_url}/Items/{person_id}/Images/Primary?maxWidth=200"
                        img_resp = req.get(image_url, headers=headers, timeout=10)
                        if img_resp.status_code == 200:
                            content_type = img_resp.headers.get('Content-Type', 'image/jpeg')
                            return Response(img_resp.content, mimetype=content_type)
    except Exception as e:
        print(f"Actor image error (Persons): {e}")

    # 返回占位 SVG（人物头像）
    placeholder_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"><rect fill="#333" width="100" height="100" rx="50"/><circle cx="50" cy="35" r="18" fill="#666"/><ellipse cx="50" cy="80" rx="30" ry="20" fill="#666"/></svg>'
    return Response(placeholder_svg.encode('utf-8'), mimetype='image/svg+xml')


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
        init_default_charts(db)


def init_scheduler():
    """初始化定时任务"""
    from services.report_generator import generate_weekly_report, generate_monthly_report, generate_annual_report

    # 每周一 09:00
    scheduler.add_job(
        lambda: generate_weekly_report(app, db),
        'cron',
        day_of_week='mon',
        hour=9,
        minute=0,
        id='weekly_report'
    )

    # 每月1日 09:00
    scheduler.add_job(
        lambda: generate_monthly_report(app, db),
        'cron',
        day=1,
        hour=9,
        minute=0,
        id='monthly_report'
    )

    # 每半年（1月和7月）生成年报
    scheduler.add_job(
        lambda: generate_annual_report(app, db),
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

    app.run(host='0.0.0.0', port=5000, debug=False)
