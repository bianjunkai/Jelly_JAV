import json
import time
from datetime import datetime


def update_all_scores():
    """批量更新所有影片评分"""
    # 延迟导入
    from app import db, config
    from models import Movie, ScoreHistory, TaskLog
    from services.javdb_scraper import fetch_movie_score

    task = TaskLog(task_type='score_update', status='running', message='Starting score update')
    db.session.add(task)
    db.session.commit()

    try:
        movies = Movie.query.filter(Movie.code.isnot(None)).all()
        total = len(movies)
        processed = 0
        updated = 0
        errors = 0

        for movie in movies:
            try:
                old_score = movie.javdb_score
                new_score = fetch_movie_score(movie.code)

                if new_score and new_score != old_score:
                    # 记录分数变化
                    if old_score:
                        history = ScoreHistory(
                            movie_id=movie.id,
                            prev_score=old_score,
                            curr_score=new_score
                        )
                        db.session.add(history)

                    movie.javdb_score = new_score
                    movie.last_score_update = datetime.utcnow()
                    movie.score_fetch_count += 1
                    updated += 1

                processed += 1

            except Exception as e:
                errors += 1
                print(f"Error updating {movie.code}: {e}")

            # 更新进度
            task.progress = int(processed / total * 100)
            task.message = f'Processing: {movie.code}'
            task.details = json.dumps({
                'total': total,
                'processed': processed,
                'updated': updated,
                'errors': errors
            })
            db.session.commit()

        task.status = 'completed'
        task.progress = 100
        task.message = f'Completed: {updated} updated, {errors} errors'
        task.finished_at = datetime.utcnow()
        db.session.commit()

    except Exception as e:
        task.status = 'failed'
        task.message = f'Error: {str(e)}'
        task.finished_at = datetime.utcnow()
        db.session.commit()


def calculate_weighted_score(movie):
    """计算影片加权分"""
    from app import app, config
    from models import Actor

    score = config.WEIGHT_BASE  # 50

    # JavDB 评分调整
    javdb = movie.javdb_score or 0
    if javdb >= 4.5:
        score += config.WEIGHT_JAVDB_HIGH
    elif javdb >= 4.2:
        score += config.WEIGHT_JAVDB_MEDIUM
    elif javdb >= 3.9:
        pass  # 0
    elif javdb >= 3.5:
        score += config.WEIGHT_JAVDB_LOW
    else:
        score += config.WEIGHT_JAVDB_VERY_LOW

    # 榜单加分
    if movie.in_javdb_top250 and movie.in_javlib_top500:
        score += config.WEIGHT_DUAL_CHART
    elif movie.in_javdb_top250 or movie.in_javlib_top500:
        score += config.WEIGHT_SINGLE_CHART
    elif movie.in_year_chart:
        score += config.WEIGHT_YEAR_CHART

    # 多位演员
    actors = movie.actors.split(',') if movie.actors else []
    if len(actors) >= 2:
        score += config.WEIGHT_MULTI_ACTOR

    # 关注演员加分 - 需要在 app context 中查询
    with app.app_context():
        from app import db
        for actor_name in actors:
            actor = db.session.query(Actor).filter_by(name=actor_name).first()
            if actor and actor.is_followed:
                score += config.WEIGHT_FOLLOWED_ACTOR
                break

    return max(0, min(100, score))


def recalculate_all_weighted_scores():
    """重新计算所有影片的加权分（后台异步）"""
    from app import db, app
    from models import Movie, TaskLog

    with app.app_context():
        task = TaskLog(task_type='weighted_score_recalc', status='running', message='Starting weighted score recalculation')
        db.session.add(task)
        db.session.commit()

        try:
            movies = Movie.query.filter(Movie.code.isnot(None)).all()
            total = len(movies)
            processed = 0
            updated = 0

            for movie in movies:
                try:
                    old_score = movie.weighted_score
                    new_score = calculate_weighted_score(movie)
                    if old_score != new_score:
                        movie.weighted_score = new_score
                        updated += 1
                    processed += 1
                except Exception as e:
                    print(f"Error recalculating weighted score for {movie.code}: {e}")

                # 每100部更新一次进度
                if processed % 100 == 0:
                    task.progress = int(processed * 100 / total)
                    task.message = f'Processed {processed}/{total} movies'
                    db.session.commit()

            task.status = 'completed'
            task.progress = 100
            task.message = f'Completed: {updated} updated, {total} total'
            task.finished_at = datetime.utcnow()
            db.session.commit()

            print(f"[WeightedScore] Recalculation completed: {updated}/{total} updated")

        except Exception as e:
            task.status = 'failed'
            task.message = f'Error: {str(e)}'
            task.finished_at = datetime.utcnow()
            db.session.commit()
            print(f"[WeightedScore] Recalculation failed: {e}")
