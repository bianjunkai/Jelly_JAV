from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class Movie(Base):
    """影片表"""
    __tablename__ = 'movies'

    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, index=True, nullable=False)
    title = Column(String(500))
    original_title = Column(String(500))
    year = Column(Integer)
    actors = Column(String(500))
    date_added = Column(DateTime)
    jellyfin_id = Column(String(50))
    jellyfin_path = Column(String(1000))

    # 评分相关
    javdb_score = Column(Float)
    javdb_id = Column(String(20))
    weighted_score = Column(Integer, default=50)
    discovered_at = Column(DateTime)

    # 榜单标记
    in_javdb_top250 = Column(Boolean, default=False)
    in_javlib_top500 = Column(Boolean, default=False)
    in_year_chart = Column(Boolean, default=False)

    # 统计
    score_fetch_count = Column(Integer, default=0)
    last_score_update = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # 关联
    todo_items = relationship("TodoItem", back_populates="movie")
    score_history = relationship("ScoreHistory", back_populates="movie")

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'title': self.title,
            'original_title': self.original_title,
            'year': self.year,
            'actors': self.actors.split(',') if self.actors else [],
            'date_added': self.date_added.isoformat() if self.date_added else None,
            'jellyfin_id': self.jellyfin_id,
            'jellyfin_path': self.jellyfin_path,
            'javdb_score': self.javdb_score,
            'javdb_id': self.javdb_id,
            'weighted_score': self.weighted_score,
            'discovered_at': self.discovered_at.isoformat() if self.discovered_at else None,
            'badges': self.get_badges(),
            'poster_url': f'/api/poster/{self.jellyfin_id}' if self.jellyfin_id else None,
            'in_library': True
        }

    def get_badges(self):
        badges = []
        if self.in_javdb_top250 and self.in_javlib_top500:
            badges.append('🔥')
        elif self.in_javdb_top250 or self.in_javlib_top500:
            badges.append('⭐')
        if self.in_year_chart:
            badges.append('💎')
        return badges


class Actor(Base):
    """演员表"""
    __tablename__ = 'actors'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    name_en = Column(String(100))
    javbus_id = Column(String(50))
    javdb_id = Column(String(50))
    photo_url = Column(String(500))

    # 关注状态
    is_followed = Column(Boolean, default=False)

    # 统计
    movie_count = Column(Integer, default=0)
    avg_score = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'name_en': self.name_en,
            'javbus_id': self.javbus_id,
            'javdb_id': self.javdb_id,
            'photo_url': self.photo_url,
            'is_followed': self.is_followed,
            'movie_count': self.movie_count,
            'avg_score': self.avg_score
        }


class Chart(Base):
    """榜单定义"""
    __tablename__ = 'charts'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(100))
    source = Column(String(50))
    description = Column(String(500))
    total_count = Column(Integer, default=0)
    year = Column(Integer)
    is_active = Column(Boolean, default=True)
    last_updated = Column(DateTime)

    items = relationship("ChartItem", back_populates="chart", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'source': self.source,
            'description': self.description,
            'total_count': self.total_count,
            'year': self.year,
            'is_active': self.is_active,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class ChartItem(Base):
    """榜单中的影片"""
    __tablename__ = 'chart_items'

    id = Column(Integer, primary_key=True)
    chart_id = Column(Integer, ForeignKey('charts.id'), nullable=False)
    rank = Column(Integer, nullable=False)
    code = Column(String(20), nullable=False)
    title = Column(String(500))
    score = Column(Float)
    actors = Column(String(500))
    year = Column(Integer)

    movie_id = Column(Integer, ForeignKey('movies.id'), nullable=True)
    movie = relationship("Movie")

    __table_args__ = (
        Index('idx_chart_rank', 'chart_id', 'rank'),
        Index('idx_chart_code', 'chart_id', 'code'),
    )

    chart = relationship("Chart", back_populates="items")

    def to_dict(self):
        return {
            'id': self.id,
            'chart_id': self.chart_id,
            'rank': self.rank,
            'code': self.code,
            'title': self.title,
            'score': self.score,
            'actors': self.actors.split(',') if self.actors else [],
            'year': self.year,
            'movie_id': self.movie_id,
            'in_library': self.movie_id is not None
        }


class Report(Base):
    """报告表"""
    __tablename__ = 'reports'

    id = Column(Integer, primary_key=True)
    type = Column(String(20), nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
    title = Column(String(200))
    data = Column(Text)
    is_read = Column(Boolean, default=False)

    __table_args__ = (
        Index('idx_report_type_date', 'type', 'generated_at'),
    )

    def to_dict(self):
        import json
        return {
            'id': self.id,
            'type': self.type,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
            'title': self.title,
            'data': json.loads(self.data) if self.data else None,
            'is_read': self.is_read
        }


class TodoItem(Base):
    """待看清单"""
    __tablename__ = 'todo_items'

    id = Column(Integer, primary_key=True)
    code = Column(String(20), nullable=False)
    title = Column(String(500))
    actors = Column(String(500))

    source = Column(String(20), nullable=False)
    source_detail = Column(String(100))

    movie_id = Column(Integer, ForeignKey('movies.id'), nullable=True)
    movie = relationship("Movie", back_populates="todo_items")

    status = Column(String(20), default='pending')
    added_at = Column(DateTime, default=datetime.utcnow)
    downloaded_at = Column(DateTime)
    user_note = Column(String(500))

    __table_args__ = (
        Index('idx_todo_status', 'status', 'added_at'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'title': self.title,
            'actors': self.actors.split(',') if self.actors else [],
            'source': self.source,
            'source_detail': self.source_detail,
            'movie_id': self.movie_id,
            'status': self.status,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'downloaded_at': self.downloaded_at.isoformat() if self.downloaded_at else None,
            'user_note': self.user_note
        }


class ScoreHistory(Base):
    """评分历史"""
    __tablename__ = 'score_history'

    id = Column(Integer, primary_key=True)
    movie_id = Column(Integer, ForeignKey('movies.id'), nullable=False)
    prev_score = Column(Float)
    curr_score = Column(Float)
    changed_at = Column(DateTime, default=datetime.utcnow)

    movie = relationship("Movie", back_populates="score_history")


class TaskLog(Base):
    """任务执行日志"""
    __tablename__ = 'task_logs'

    id = Column(Integer, primary_key=True)
    task_type = Column(String(50), nullable=False)
    status = Column(String(20), default='running')
    progress = Column(Integer, default=0)
    message = Column(String(500))
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime)
    details = Column(Text)

    def to_dict(self):
        import json
        return {
            'id': self.id,
            'task_type': self.task_type,
            'status': self.status,
            'progress': self.progress,
            'message': self.message,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
            'details': json.loads(self.details) if self.details else None
        }
