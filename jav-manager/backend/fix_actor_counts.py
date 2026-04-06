#!/usr/bin/env python
"""修复演员 movie_count 缓存，使用精确匹配而非模糊匹配"""

import sys
sys.path.insert(0, '.')

from app import app, db
from models import Actor, Movie
from sqlalchemy import or_


def exact_actor_filter(actors_field, name):
    """构建精确匹配演员名的过滤器"""
    return or_(
        actors_field == name,
        actors_field.startswith(f'{name},'),
        actors_field.endswith(f',{name}'),
        actors_field.contains(f',{name},')
    )


def rebuild_actor_stats():
    with app.app_context():
        actors = db.session.query(Actor).all()
        print(f'正在修复 {len(actors)} 个演员的 movie_count...')

        for actor in actors:
            old_count = actor.movie_count
            exact_filter = exact_actor_filter(Movie.actors, actor.name)

            # 重新计算 movie_count
            actor.movie_count = Movie.query.filter(exact_filter).count()

            # 重新计算 avg_score
            movies = Movie.query.filter(exact_filter).all()
            scores = [m.javdb_score for m in movies if m.javdb_score]
            actor.avg_score = sum(scores) / len(scores) if scores else None

            if old_count != actor.movie_count:
                print(f'  {actor.name}: {old_count} -> {actor.movie_count}')

        db.session.commit()
        print('完成！')


if __name__ == '__main__':
    rebuild_actor_stats()
