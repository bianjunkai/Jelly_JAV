#!/usr/bin/env python3
import sqlite3
import requests
import re
import os
import xml.etree.ElementTree as ET
import threading
import time
import queue
from datetime import datetime
from flask import Flask, render_template, jsonify, request, Response
from config import JELLYFIN_URL, JELLYFIN_API_KEY, RSSHUB_URL, JAVBUS_DOMAINS, JAVBUS_LANGUAGE, AUTO_REFRESH_ON_STARTUP, RSS_UPDATE_ON_STARTUP, RSS_REQUEST_DELAY, RSS_MAX_RETRIES, RSS_RETRY_BASE_DELAY
import javdb_scraper

app = Flask(__name__)
DB_PATH = "data.db"

# RSS Rate limiting configuration (loaded from config.py)
# RSS_REQUEST_DELAY = 2.0  # Delay between requests in seconds
# RSS_MAX_RETRIES = 3      # Max retries on 429
# RSS_RETRY_BASE_DELAY = 5  # Base delay for exponential backoff (seconds)

# Global RSS state
rss_update_state = {
    "is_running": False,
    "is_complete": False,
    "results": [],
    "start_time": None,
    "end_time": None,
}

# Global JavDB score fetch state
javdb_task_state = {
    "is_running": False,
    "is_complete": False,
    "results": [],
    "start_time": None,
    "end_time": None,
    "summary": None
}

CSV_FILES = {
    "JavDB TOP250": "JAVDB TOP250.csv",
    "JavDB 2025 TOP250": "JAVDB 2025TOP250.csv",
    "JavDB 2024 TOP250": "JAVDB 2024TOP250.csv",
    "JavDB 2023 TOP250": "JAVDB 2023TOP250.csv",
    "JavLibray TOP500": "JAVLIBTOP500.csv",
}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            title TEXT,
            year TEXT,
            actors TEXT,
            date_added TEXT,
            jellyfin_id TEXT
        )
    """)
    # Add jellyfin_id column if it doesn't exist (for existing databases)
    try:
        conn.execute("ALTER TABLE movies ADD COLUMN jellyfin_id TEXT")
    except:
        pass  # Column already exists

    # Add score column if it doesn't exist
    try:
        conn.execute("ALTER TABLE movies ADD COLUMN score INTEGER DEFAULT 50")
    except:
        pass  # Column already exists

    # Add javdb_score column if it doesn't exist
    try:
        conn.execute("ALTER TABLE movies ADD COLUMN javdb_score REAL")
    except:
        pass  # Column already exists

    # 1. actors 表 - 演员 JAVBus ID 关联
    conn.execute("""
        CREATE TABLE IF NOT EXISTS actors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            javbus_id TEXT,
            rss_url TEXT,
            is_watched BOOLEAN DEFAULT 0,
            last_updated TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. rss_items 表 - RSS 抓取的影片记录
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rss_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor_id INTEGER NOT NULL,
            code TEXT NOT NULL,
            title TEXT,
            javbus_url TEXT,
            pub_date TEXT,
            is_watched BOOLEAN DEFAULT 0,
            score INTEGER DEFAULT 50,
            detected_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(actor_id, code)
        )
    """)

    # 3. actor_tags 表 - 演员榜单标签
    conn.execute("""
        CREATE TABLE IF NOT EXISTS actor_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor_id INTEGER NOT NULL,
            tag_name TEXT NOT NULL,
            UNIQUE(actor_id, tag_name)
        )
    """)

    conn.commit()
    conn.close()


def extract_code(title):
    match = re.match(r"^([A-Z]+-\d+)", title)
    return match.group(1) if match else None


def load_csv_codes():
    codes = {label: {} for label in CSV_FILES}  # 改为 dict 存储 {code: rank}
    for label, filepath in CSV_FILES.items():
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                import csv

                reader = csv.DictReader(f)
                for row in reader:
                    name = row.get("SUBSTR(name,0,40)", row.get("name", ""))
                    number = row.get("number", "")
                    if name:
                        code = extract_code(name)
                        if code:
                            # 存储排名，如果重复取最小排名
                            if code not in codes[label]:
                                codes[label][code] = int(number) if number.isdigit() else 0
                            else:
                                codes[label][code] = min(codes[label][code], int(number) if number.isdigit() else 0)
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
    return codes


def sync_jellyfin():
    headers = {"X-Emby-Token": JELLYFIN_API_KEY}
    url = f"{JELLYFIN_URL}Items"
    params = {
        "Recursive": True,
        "IncludeItemTypes": "Movie",
        "Fields": "ProviderIds,ProductionYear,DateCreated,Overview,People",
        "Limit": 10000,
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        items = resp.json().get("Items", [])

        conn = get_db()
        count = 0
        for item in items:
            title = item.get("Name", "")
            code = extract_code(title)
            if not code:
                continue

            year = item.get("ProductionYear", "")
            date_added = (
                item.get("DateCreated", "")[:10] if item.get("DateCreated") else ""
            )

            actors = ",".join(
                [a["Name"] for a in item.get("People", []) if a.get("Type") == "Actor"]
            )

            jellyfin_id = item.get("Id", "")

            conn.execute(
                """
                INSERT OR REPLACE INTO movies (code, title, year, actors, date_added, jellyfin_id, score, javdb_score)
                VALUES (?, ?, ?, ?, ?, ?, COALESCE((SELECT score FROM movies WHERE code = ?), 50), (SELECT javdb_score FROM movies WHERE code = ?))
            """,
                (code, title, year, actors, date_added, jellyfin_id, code, code),
            )
            count += 1

        conn.commit()
        conn.close()
        return count
    except Exception as e:
        print(f"Sync error: {e}")
        return -1


def import_actors_from_jellyfin():
    """从 Jellyfin 电影中提取演员列表并导入到 actors 表"""
    conn = get_db()
    cursor = conn.execute("SELECT DISTINCT actors FROM movies WHERE actors != ''")

    existing_actors = set(row["name"] for row in conn.execute("SELECT name FROM actors"))

    new_actors = []
    for row in cursor:
        if row["actors"]:
            for actor in row["actors"].split(","):
                actor = actor.strip()
                if actor and actor not in existing_actors:
                    new_actors.append(actor)
                    existing_actors.add(actor)

    for actor in new_actors:
        conn.execute("INSERT INTO actors (name) VALUES (?)", (actor,))

    conn.commit()
    conn.close()
    return len(new_actors)


def calculate_movie_score(code, actors_str, javdb_score=None):
    """计算影片权重分数

    Args:
        code: 影片番号
        actors_str: 演员列表字符串
        javdb_score: JavDB评分，如果为None则从数据库获取
    """
    score = 50  # 初始分

    # 获取JavDB评分（如果未传入）
    if javdb_score is None:
        conn = get_db()
        row = conn.execute("SELECT javdb_score FROM movies WHERE code = ?", (code,)).fetchone()
        conn.close()
        if row:
            javdb_score = row["javdb_score"]

    # 根据JavDB评分调整分数
    if javdb_score is not None:
        if javdb_score >= 4.5:
            score += 20
        elif javdb_score >= 4.2:
            score += 10
        elif javdb_score >= 3.9:
            score += 0  # 不加不减
        elif javdb_score >= 3.5:
            score -= 15
        else:  # < 3.5
            score -= 25

    csv_codes = load_csv_codes()

    # 检查上榜情况
    in_javdb = code in csv_codes.get("JavDB TOP250", {})
    in_javlib = code in csv_codes.get("JavLibray TOP500", {})

    # 同时上榜 JAVDB + JAVLibrary
    if in_javdb and in_javlib:
        score += 30
    # 单独上榜
    elif in_javdb or in_javlib:
        score += 20

    # 检查是否在 JAVDB 年度榜单
    for label in ["JavDB 2025 TOP250", "JavDB 2024 TOP250", "JavDB 2023 TOP250"]:
        if code in csv_codes.get(label, {}):
            score += 10
            break

    # 多位演员
    if actors_str:
        actors_list = [a.strip() for a in actors_str.split(",") if a.strip()]
        if len(actors_list) >= 2:
            score += 5

    # 检查演员是否有 JAVBus ID
    if actors_str:
        conn = get_db()
        actors_list = [a.strip() for a in actors_str.split(",") if a.strip()]
        for actor in actors_list:
            actor_row = conn.execute(
                "SELECT javbus_id FROM actors WHERE name = ? AND javbus_id IS NOT NULL AND javbus_id != ''",
                (actor,)
            ).fetchone()
            if actor_row:
                score += 15
                break  # 只需要有一个演员有 JAVBus ID 即可加分
        conn.close()

    return score


def build_rss_url(javbus_id):
    """构建 RSS 订阅链接，支持多个域名"""
    if not javbus_id:
        return None

    lang = JAVBUS_LANGUAGE if JAVBUS_LANGUAGE else ""
    url = f"{RSSHUB_URL}/javbus/star/{javbus_id}"
    params = []
    # 支持多个域名，RSSHub 会自动尝试下一个
    if JAVBUS_DOMAINS:
        for domain in JAVBUS_DOMAINS:
            params.append(f"domain={domain}")
    if lang:
        params.append(f"lang={lang}")
    if params:
        url += "?" + "&".join(params)
    return url


def fetch_rss(actor_id, retry_count=0, domain_index=0):
    """抓取指定演员的 RSS 订阅，带有 429/503 防护机制和域名轮换"""
    conn = get_db()
    actor = conn.execute("SELECT id, name, javbus_id FROM actors WHERE id = ?", (actor_id,)).fetchone()

    if not actor or not actor["javbus_id"]:
        conn.close()
        return {"success": False, "error": "Actor not found or no javbus_id", "actor_id": actor_id}

    # 使用当前域名构建URL
    current_domains = JAVBUS_DOMAINS if JAVBUS_DOMAINS else ["busjav.cyou"]
    current_domain = current_domains[domain_index] if domain_index < len(current_domains) else current_domains[0]

    lang = JAVBUS_LANGUAGE if JAVBUS_LANGUAGE else ""
    rss_url = f"{RSSHUB_URL}/javbus/star/{actor['javbus_id']}"
    params = []
    if current_domain:
        params.append(f"domain={current_domain}")
    if lang:
        params.append(f"lang={lang}")
    if params:
        rss_url += "?" + "&".join(params)

    if not rss_url:
        conn.close()
        return {"success": False, "error": "Invalid RSS URL", "actor_id": actor_id}

    try:
        resp = requests.get(rss_url, timeout=30)

        # Handle HTTP errors that should trigger retry
        retryable_errors = {
            429: "Rate limited (429)",
            503: "Service unavailable (503)",
            502: "Bad gateway (502)",
            504: "Gateway timeout (504)"
        }

        if resp.status_code in retryable_errors:
            if retry_count < RSS_MAX_RETRIES:
                delay = RSS_RETRY_BASE_DELAY * (2 ** retry_count)  # 5, 10, 20 seconds
                error_name = retryable_errors[resp.status_code]
                print(f"{error_name} for actor {actor_id}, retrying in {delay}s (attempt {retry_count + 1}/{RSS_MAX_RETRIES})")
                conn.close()
                time.sleep(delay)
                return fetch_rss(actor_id, retry_count + 1)
            else:
                conn.close()
                return {"success": False, "error": f"{retryable_errors[resp.status_code]} - max retries exceeded", "actor_id": actor_id, "retry_count": retry_count}

        resp.raise_for_status()

        # 解析 RSS XML
        root = ET.fromstring(resp.content)
        items_added = 0

        # Get all existing codes from movies table for this actor
        existing_codes = set()
        cursor = conn.execute("SELECT code, actors FROM movies")
        for row in cursor:
            if row["actors"]:
                actors = [a.strip() for a in row["actors"].split(",")]
                if actor["name"] in actors:
                    existing_codes.add(row["code"])

        for item in root.findall(".//item"):
            title = item.find("title")
            title_text = title.text if title is not None else ""

            link = item.find("link")
            link_text = link.text if link is not None else ""

            pub_date = item.find("pubDate")
            pub_date_text = pub_date.text if pub_date is not None else ""

            # 从标题提取番号
            code = extract_code(title_text)

            if code:
                # Check if this code exists in the movies table for this actor
                is_watched = 1 if code in existing_codes else 0

                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO rss_items (actor_id, code, title, javbus_url, pub_date, detected_at, is_watched)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (actor_id, code, title_text, link_text, pub_date_text, datetime.now().isoformat(), is_watched))
                    items_added += 1
                except Exception as e:
                    pass  # 忽略重复

        # 更新 actor 的 last_updated
        conn.execute("UPDATE actors SET last_updated = ? WHERE id = ?", (datetime.now().isoformat(), actor_id))
        conn.commit()
        conn.close()

        return {"success": True, "items_added": items_added, "actor_id": actor_id}
    except requests.exceptions.RequestException as e:
        # 检查是否是超时错误，尝试下一个域名
        if "timeout" in str(e).lower() and domain_index < len(JAVBUS_DOMAINS) - 1:
            print(f"Timeout for actor {actor_id} with domain {current_domain}, trying next domain...")
            return fetch_rss(actor_id, 0, domain_index + 1)

        # 网络错误也尝试重试
        if retry_count < RSS_MAX_RETRIES:
            delay = RSS_RETRY_BASE_DELAY * (2 ** retry_count)
            print(f"Network error for actor {actor_id}: {e}, retrying in {delay}s (attempt {retry_count + 1}/{RSS_MAX_RETRIES})")
            time.sleep(delay)
            return fetch_rss(actor_id, retry_count + 1, domain_index)
        conn.close()
        print(f"RSS fetch error for actor {actor_id}: {e}")
        return {"success": False, "error": f"Network error: {str(e)}", "actor_id": actor_id}
    except Exception as e:
        # 其他错误也尝试重试
        if retry_count < RSS_MAX_RETRIES:
            delay = RSS_RETRY_BASE_DELAY * (2 ** retry_count)
            print(f"Error for actor {actor_id}: {e}, retrying in {delay}s (attempt {retry_count + 1}/{RSS_MAX_RETRIES})")
            time.sleep(delay)
            return fetch_rss(actor_id, retry_count + 1, domain_index)
        conn.close()
        print(f"RSS fetch error for actor {actor_id}: {e}")
        return {"success": False, "error": str(e), "actor_id": actor_id}


def fetch_all_rss_background():
    """后台抓取所有已配置 JAVBus ID 的演员 RSS（在后台线程中运行）"""
    global rss_update_state

    rss_update_state["is_running"] = True
    rss_update_state["is_complete"] = False
    rss_update_state["start_time"] = datetime.now().isoformat()
    rss_update_state["results"] = []

    conn = get_db()
    actors = conn.execute("SELECT id, name, javbus_id FROM actors WHERE javbus_id IS NOT NULL AND javbus_id != ''").fetchall()
    conn.close()

    total_actors = len(actors)
    success_count = 0
    fail_count = 0

    for idx, actor in enumerate(actors):
        # Add delay between requests (skip first request)
        if idx > 0:
            time.sleep(RSS_REQUEST_DELAY)

        result = fetch_rss(actor["id"])
        is_success = result.get("success", False)

        if is_success:
            success_count += 1
        else:
            fail_count += 1

        rss_update_state["results"].append({
            "actor_id": actor["id"],
            "actor_name": actor["name"],
            "success": is_success,
            "items_added": result.get("items_added", 0),
            "error": result.get("error", ""),
            "retry_count": result.get("retry_count", 0)
        })

    rss_update_state["is_running"] = False
    rss_update_state["is_complete"] = True
    rss_update_state["end_time"] = datetime.now().isoformat()
    rss_update_state["summary"] = {
        "total": total_actors,
        "success": success_count,
        "fail": fail_count
    }

    print(f"RSS background fetch completed: {success_count}/{total_actors} actors updated, {fail_count} failed")


def fetch_all_rss():
    """抓取所有已配置 JAVBus ID 的演员 RSS"""
    conn = get_db()
    actors = conn.execute("SELECT id, name, javbus_id FROM actors WHERE javbus_id IS NOT NULL AND javbus_id != ''").fetchall()
    conn.close()

    results = []
    for actor in actors:
        result = fetch_rss(actor["id"])
        results.append({
            "actor_id": actor["id"],
            "actor_name": actor["name"],
            "result": result
        })

    return results


def get_movies_with_tags():
    csv_codes = load_csv_codes()
    conn = get_db()
    cursor = conn.execute("SELECT code, title, year, actors, jellyfin_id, score, javdb_score FROM movies ORDER BY code")
    movies = []
    for row in cursor:
        code = row["code"]
        actors_str = row["actors"] or ""
        tags = []
        for label, codes in csv_codes.items():
            if code in codes:
                tags.append(label)

        # Use stored score if available, otherwise calculate
        javdb_score = row["javdb_score"]
        score = row["score"] if row["score"] is not None else calculate_movie_score(code, actors_str, javdb_score)

        # Build Jellyfin poster URL
        poster_url = None
        if row["jellyfin_id"]:
            poster_url = f"/api/poster/{row['jellyfin_id']}"

        movies.append(
            {
                "code": code,
                "title": row["title"],
                "year": row["year"],
                "actors": row["actors"],
                "tags": tags,
                "all_tags": list(csv_codes.keys()),
                "poster_url": poster_url,
                "score": score,
                "javdb_score": row["javdb_score"],
            }
        )
    conn.close()
    return movies


def get_movies_by_list(list_name):
    csv_codes = load_csv_codes()
    codes_dict = csv_codes.get(list_name, {})

    conn = get_db()
    all_jellyfin_codes = set(
        row["code"] for row in conn.execute("SELECT code FROM movies")
    )

    movies = []
    for code, rank in codes_dict.items():
        in_jellyfin = code in all_jellyfin_codes
        title = ""
        poster_url = None
        if in_jellyfin:
            row = conn.execute(
                "SELECT title, year, actors, jellyfin_id FROM movies WHERE code = ?", (code,)
            ).fetchone()
            if row:
                title = row["title"]
                year = row["year"]
                actors = row["actors"]
                if row["jellyfin_id"]:
                    poster_url = f"/api/poster/{row['jellyfin_id']}"
        movies.append(
            {
                "code": code,
                "title": title,
                "year": year if in_jellyfin else "",
                "actors": actors if in_jellyfin else "",
                "in_jellyfin": in_jellyfin,
                "rank": rank,
                "poster_url": poster_url,
            }
        )
    # 按排名排序
    movies.sort(key=lambda x: x["rank"])
    conn.close()
    return movies


def get_missing_movies():
    csv_codes = load_csv_codes()

    # JavDB 只统计总榜 TOP250
    javdb_all = csv_codes.get("JavDB TOP250", {})

    javlib_codes = csv_codes["JavLibray TOP500"]

    conn = get_db()
    jellyfin_codes = set(row["code"] for row in conn.execute("SELECT code FROM movies"))
    conn.close()

    # 计算未收录
    javdb_missing = {code: rank for code, rank in javdb_all.items() if code not in jellyfin_codes}
    javlib_missing = {code: rank for code, rank in javlib_codes.items() if code not in jellyfin_codes}

    # 转换为列表并排序
    javdb_list = []
    for code, rank in javdb_missing.items():
        javdb_list.append({
            "code": code,
            "rank": rank,
            "labels": ["JavDB TOP250"]
        })
    javdb_list.sort(key=lambda x: x["rank"])

    javlib_list = []
    for code, rank in javlib_missing.items():
        javlib_list.append({
            "code": code,
            "rank": rank,
            "labels": ["JavLibray TOP500"]
        })
    javlib_list.sort(key=lambda x: x["rank"])

    # 检查重复（在javdb和javlib中都存在）
    both_missing = set(javdb_missing.keys()) & set(javlib_missing.keys())

    return {
        "javdb": javdb_list,
        "javlib": javlib_list,
        "both": list(both_missing)
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/movies")
def api_movies():
    movies = get_movies_with_tags()
    search = request.args.get("search", "").lower()
    if search:
        movies = [
            m
            for m in movies
            if search in m["code"].lower() or search in m["actors"].lower()
        ]

    # 分页
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 50))
    total = len(movies)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = movies[start:end]

    return jsonify({
        "data": paginated,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    })


@app.route("/api/list/<list_name>")
def api_list(list_name):
    if list_name == "missing":
        return jsonify(get_missing_movies())

    movies = get_movies_by_list(list_name)

    # 分页
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 50))
    total = len(movies)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = movies[start:end]

    return jsonify({
        "data": paginated,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    })


@app.route("/api/sync", methods=["POST"])
def api_sync():
    count = sync_jellyfin()
    return jsonify({"success": count >= 0, "count": count})


@app.route("/api/calc_scores", methods=["POST"])
def api_calc_scores():
    """手动计算所有影片的权重分"""
    csv_codes = load_csv_codes()
    conn = get_db()

    cursor = conn.execute("SELECT id, code, actors, javdb_score FROM movies")
    updated = 0

    for row in cursor:
        score = calculate_movie_score(row["code"], row["actors"], row["javdb_score"])
        conn.execute("UPDATE movies SET score = ? WHERE id = ?", (score, row["id"]))
        updated += 1

    conn.commit()
    conn.close()

    return jsonify({"success": True, "updated": updated})


@app.route("/api/stats")
def api_stats():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM movies").fetchone()[0]

    # Get counts of movies that are in Jellyfin AND in the respective lists
    csv_codes = load_csv_codes()

    # Movies in JavDB TOP250 that are in Jellyfin
    javdb_codes = set(csv_codes.get('JavDB TOP250', {}).keys())
    javdb_movies = conn.execute("SELECT code FROM movies").fetchall()
    javdb_count = sum(1 for m in javdb_movies if m['code'] in javdb_codes)

    # Movies in JavLibrary TOP500 that are in Jellyfin
    javlib_codes = set(csv_codes.get('JavLibray TOP500', {}).keys())
    javlib_movies = conn.execute("SELECT code FROM movies").fetchall()
    javlib_count = sum(1 for m in javlib_movies if m['code'] in javlib_codes)

    conn.close()

    stats = {
        "total": total,
        "javdb_count": javdb_count,
        "javlib_count": javlib_count
    }
    for label in CSV_FILES:
        stats[label] = len(csv_codes[label])
    return jsonify(stats)


@app.route("/api/actors")
def api_actors():
    csv_codes = load_csv_codes()
    all_tags = list(CSV_FILES.keys())

    conn = get_db()
    cursor = conn.execute("SELECT code, actors FROM movies WHERE actors != ''")

    actor_count = {}
    for row in cursor:
        code = row["code"]
        actors = row["actors"]
        if actors:
            for actor in actors.split(","):
                actor = actor.strip()
                if actor:
                    if actor not in actor_count:
                        actor_count[actor] = {"count": 0, "codes": []}
                    actor_count[actor]["count"] += 1
                    actor_count[actor]["codes"].append(code)

    actors_list = []
    for actor, data in actor_count.items():
        actors_list.append(
            {"name": actor, "count": data["count"], "codes": data["codes"]}
        )

    actors_list.sort(key=lambda x: x["count"], reverse=True)
    conn.close()
    return jsonify(actors_list)


@app.route("/api/actor/<path:actor_name>")
def api_actor(actor_name):
    import urllib.parse

    actor_name = urllib.parse.unquote(actor_name)

    csv_codes = load_csv_codes()
    all_tags = list(CSV_FILES.keys())

    conn = get_db()
    cursor = conn.execute(
        "SELECT code, title, year, actors, jellyfin_id, score, javdb_score FROM movies WHERE actors LIKE ?",
        (f"%{actor_name}%",),
    )

    movies = []
    for row in cursor:
        code = row["code"]
        actors = row["actors"] or ""
        if actor_name not in [a.strip() for a in actors.split(",")]:
            continue

        tags = []
        for label, codes in csv_codes.items():
            if code in codes:
                tags.append(label)

        # Use stored score if available, otherwise calculate
        javdb_score = row["javdb_score"]
        score = row["score"] if row["score"] is not None else calculate_movie_score(code, actors, javdb_score)

        # Build Jellyfin poster URL
        poster_url = None
        if row["jellyfin_id"]:
            poster_url = f"/api/poster/{row['jellyfin_id']}"

        movies.append(
            {
                "code": code,
                "title": row["title"],
                "year": row["year"],
                "actors": actors,
                "tags": tags,
                "all_tags": all_tags,
                "poster_url": poster_url,
                "score": score,
                "javdb_score": row["javdb_score"],
            }
        )

    conn.close()
    return jsonify(movies)


@app.route("/api/actor/<path:actor_name>/detail")
def api_actor_detail(actor_name):
    """Get actor detail info including avatar, JAVBus ID, RSS info"""
    import urllib.parse
    actor_name = urllib.parse.unquote(actor_name)

    conn = get_db()

    # Get actor info from actors table
    actor = conn.execute(
        "SELECT id, name, javbus_id, rss_url, last_updated FROM actors WHERE name = ?",
        (actor_name,)
    ).fetchone()

    # Get movie count for this actor
    movie_count = 0
    cursor = conn.execute("SELECT actors FROM movies WHERE actors LIKE ?", (f"%{actor_name}%",))
    for row in cursor:
        actors = row["actors"] or ""
        if actor_name in [a.strip() for a in actors.split(",")]:
            movie_count += 1

    # Get actor avatar from Jellyfin
    avatar_url = f"/api/actor/{urllib.parse.quote(actor_name)}/poster"

    conn.close()

    if not actor:
        return jsonify({"error": "Actor not found"}), 404

    return jsonify({
        "name": actor["name"],
        "javbus_id": actor["javbus_id"],
        "rss_url": actor["rss_url"],
        "last_updated": actor["last_updated"],
        "movie_count": movie_count,
        "avatar_url": avatar_url,
        "actor_id": actor["id"]
    })


@app.route("/api/actor/<path:actor_name>/fetch_javdb_scores", methods=["POST"])
def api_actor_fetch_javdb_scores(actor_name):
    """批量获取演员所有影片的JavDB评分"""
    import urllib.parse
    actor_name = urllib.parse.unquote(actor_name)

    conn = get_db()

    # 获取该演员所有没有JavDB评分的影片
    cursor = conn.execute(
        "SELECT id, code, javdb_score FROM movies WHERE actors LIKE ? AND (javdb_score IS NULL OR javdb_score = '')",
        (f"%{actor_name}%",)
    )
    movies = cursor.fetchall()
    conn.close()

    total = len(movies)
    success_count = 0
    fail_count = 0

    for idx, movie in enumerate(movies):
        # 添加延迟避免被封
        if idx > 0:
            time.sleep(2)

        code = movie["code"]
        movie_id = movie["id"]

        try:
            score = javdb_scraper.get_javdb_score(code)
            if score is not None:
                conn = get_db()
                conn.execute("UPDATE movies SET javdb_score = ? WHERE id = ?", (score, movie_id))
                conn.commit()
                conn.close()
                success_count += 1
                print(f"[JavDB] {code}: {score}")
            else:
                fail_count += 1
                print(f"[JavDB] {code}: Not found")
        except Exception as e:
            fail_count += 1
            print(f"[JavDB] {code}: Error - {e}")

    return jsonify({
        "success": True,
        "total": total,
        "success_count": success_count,
        "fail_count": fail_count
    })


@app.route("/api/actor/<path:actor_name>/poster")
def api_actor_poster(actor_name):
    """Get actor avatar from Jellyfin People API"""
    import urllib.parse
    actor_name = urllib.parse.unquote(actor_name)
    actor_name_encoded = urllib.parse.quote(actor_name)

    headers = {"X-Emby-Token": JELLYFIN_API_KEY}

    # Method 1: Use /Items/ByName/People/{name}
    try:
        byname_url = f"{JELLYFIN_URL}Items/ByName/People/{actor_name_encoded}"
        resp = requests.get(byname_url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("Id"):
                person_id = data.get("Id")
                image_url = f"{JELLYFIN_URL}Items/{person_id}/Images/Primary?maxWidth=200"
                img_resp = requests.get(image_url, headers=headers, timeout=10)
                if img_resp.status_code == 200:
                    content_type = img_resp.headers.get('Content-Type', 'image/jpeg')
                    return Response(img_resp.content, mimetype=content_type)
    except Exception as e:
        print(f"Actor poster error: {e}")

    # Method 2: Use /Persons search
    try:
        persons_url = f"{JELLYFIN_URL}Persons"
        params = {"searchTerm": actor_name, "limit": 10}
        resp = requests.get(persons_url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("Items", []):
                if item.get("Name") == actor_name:
                    person_id = item.get("Id")
                    if person_id:
                        image_url = f"{JELLYFIN_URL}Items/{person_id}/Images/Primary?maxWidth=200"
                        img_resp = requests.get(image_url, headers=headers, timeout=10)
                        if img_resp.status_code == 200:
                            content_type = img_resp.headers.get('Content-Type', 'image/jpeg')
                            return Response(img_resp.content, mimetype=content_type)
    except Exception as e:
        print(f"Actor poster /Persons error: {e}")

    return "", 404


# Proxy endpoint for Jellyfin images (adds authentication)
@app.route("/api/poster/<jellyfin_id>")
def api_poster(jellyfin_id):
    headers = {"X-Emby-Token": JELLYFIN_API_KEY}
    # Remove query params if any
    jellyfin_id = jellyfin_id.split('?')[0]
    url = f"{JELLYFIN_URL}Items/{jellyfin_id}/Images/Primary?maxWidth=400"

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        # Return the image with proper content type
        content_type = resp.headers.get('Content-Type', 'image/jpeg')
        return Response(resp.content, mimetype=content_type)
    except Exception as e:
        print(f"Poster fetch error: {e}")
        return "", 404


# ========== RSS API Endpoints ==========

@app.route("/api/rss/actors", methods=["GET"])
def api_rss_actors():
    """获取演员列表（包含 JAVBus ID 配置状态）"""
    conn = get_db()
    actors = conn.execute("""
        SELECT a.id, a.name, a.javbus_id, a.rss_url, a.is_watched, a.last_updated,
               (SELECT COUNT(*) FROM rss_items WHERE actor_id = a.id) as item_count,
               (SELECT COUNT(*) FROM rss_items WHERE actor_id = a.id AND is_watched = 0) as unwatched_count
        FROM actors a
        ORDER BY a.name
    """).fetchall()
    conn.close()

    return jsonify([{
        "id": row["id"],
        "name": row["name"],
        "javbus_id": row["javbus_id"],
        "rss_url": row["rss_url"],
        "is_watched": row["is_watched"],
        "last_updated": row["last_updated"],
        "item_count": row["item_count"],
        "unwatched_count": row["unwatched_count"],
        "has_rss": bool(row["javbus_id"])
    } for row in actors])


@app.route("/api/rss/actors", methods=["POST"])
def api_rss_actors_add():
    """添加演员"""
    data = request.get_json()
    name = data.get("name", "").strip()

    if not name:
        return jsonify({"error": "Name is required"}), 400

    conn = get_db()
    try:
        conn.execute("INSERT INTO actors (name) VALUES (?)", (name,))
        conn.commit()
        actor_id = conn.execute("SELECT id FROM actors WHERE name = ?", (name,)).fetchone()["id"]
        conn.close()
        return jsonify({"success": True, "id": actor_id})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Actor already exists"}), 400


@app.route("/api/rss/actors/<int:actor_id>", methods=["PUT"])
def api_rss_actor_update(actor_id):
    """更新演员 JAVBus ID"""
    data = request.get_json()
    javbus_id = data.get("javbus_id", "").strip()

    rss_url = build_rss_url(javbus_id) if javbus_id else None

    conn = get_db()
    conn.execute("""
        UPDATE actors SET javbus_id = ?, rss_url = ?, last_updated = ?
        WHERE id = ?
    """, (javbus_id, rss_url, datetime.now().isoformat() if javbus_id else None, actor_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True})


@app.route("/api/rss/actors/<int:actor_id>", methods=["DELETE"])
def api_rss_actor_delete(actor_id):
    """删除演员"""
    conn = get_db()
    conn.execute("DELETE FROM rss_items WHERE actor_id = ?", (actor_id,))
    conn.execute("DELETE FROM actor_tags WHERE actor_id = ?", (actor_id,))
    conn.execute("DELETE FROM actors WHERE id = ?", (actor_id,))
    conn.commit()
    conn.close()

    return jsonify({"success": True})


@app.route("/api/rss/items")
def api_rss_items():
    """获取 RSS 影片列表"""
    actor_id = request.args.get("actor_id", type=int)
    view_mode = request.args.get("view", "all")  # all | by_actor

    csv_codes = load_csv_codes()

    conn = get_db()

    if actor_id:
        items = conn.execute("""
            SELECT r.id, r.actor_id, r.code, r.title, r.javbus_url, r.pub_date,
                   r.is_watched, r.score, r.detected_at, a.name as actor_name
            FROM rss_items r
            JOIN actors a ON r.actor_id = a.id
            WHERE r.actor_id = ?
            ORDER BY r.is_watched ASC, r.pub_date DESC
        """, (actor_id,)).fetchall()
    else:
        items = conn.execute("""
            SELECT r.id, r.actor_id, r.code, r.title, r.javbus_url, r.pub_date,
                   r.is_watched, r.score, r.detected_at, a.name as actor_name
            FROM rss_items r
            JOIN actors a ON r.actor_id = a.id
            ORDER BY r.is_watched ASC, r.pub_date DESC
        """).fetchall()

    conn.close()

    result = []
    for row in items:
        # 计算权重分
        score = row["score"]

        # 从数据库获取演员信息来计算额外分数
        conn = get_db()
        movie = conn.execute("SELECT actors, javdb_score FROM movies WHERE code = ?", (row["code"],)).fetchone()
        actors_str = movie["actors"] if movie else ""
        javdb_score = movie["javdb_score"] if movie else None
        conn.close()

        # 重新计算分数（因为初始插入时可能没有演员信息）
        score = calculate_movie_score(row["code"], actors_str, javdb_score)

        result.append({
            "id": row["id"],
            "actor_id": row["actor_id"],
            "actor_name": row["actor_name"],
            "code": row["code"],
            "title": row["title"],
            "javbus_url": row["javbus_url"],
            "pub_date": row["pub_date"],
            "is_watched": row["is_watched"],
            "score": score,
            "detected_at": row["detected_at"]
        })

    if view_mode == "by_actor":
        # 按演员分组
        grouped = {}
        for item in result:
            actor_name = item["actor_name"]
            if actor_name not in grouped:
                grouped[actor_name] = []
            grouped[actor_name].append(item)
        return jsonify(grouped)

    return jsonify(result)


@app.route("/api/rss/items/<int:item_id>/watch", methods=["POST"])
def api_rss_item_watch(item_id):
    """标记已阅"""
    data = request.get_json()
    is_watched = data.get("is_watched", True)

    conn = get_db()
    conn.execute("UPDATE rss_items SET is_watched = ? WHERE id = ?", (is_watched, item_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True})


@app.route("/api/rss/items/watch", methods=["POST"])
def api_rss_items_watch():
    """批量标记已阅"""
    data = request.get_json()
    item_ids = data.get("item_ids", [])
    actor_id = data.get("actor_id")  # 可选：标记该演员所有未阅

    conn = get_db()

    if actor_id is not None:
        conn.execute("UPDATE rss_items SET is_watched = 1 WHERE actor_id = ?", (actor_id,))
    elif item_ids:
        placeholders = ",".join("?" * len(item_ids))
        conn.execute(f"UPDATE rss_items SET is_watched = 1 WHERE id IN ({placeholders})", item_ids)

    conn.commit()
    conn.close()

    return jsonify({"success": True})


@app.route("/api/rss/refresh", methods=["POST"])
def api_rss_refresh():
    """手动刷新 RSS（后台运行）"""
    global rss_update_state

    # 如果已经在运行，返回当前状态
    if rss_update_state["is_running"]:
        return jsonify({
            "success": False,
            "message": "RSS refresh is already running",
            "is_running": True
        })

    # 启动后台线程
    rss_thread = threading.Thread(target=fetch_all_rss_background, daemon=True)
    rss_thread.start()

    return jsonify({
        "success": True,
        "message": "RSS refresh started in background"
    })


@app.route("/api/rss/refresh/sync", methods=["POST"])
def api_rss_refresh_sync():
    """手动刷新 RSS（同步阻塞模式，不推荐用于大量演员）"""
    results = fetch_all_rss()
    return jsonify({"success": True, "results": results})


@app.route("/api/rss/refresh/<int:actor_id>", methods=["POST"])
def api_rss_refresh_actor(actor_id):
    """刷新单个演员的 RSS"""
    result = fetch_rss(actor_id)
    return jsonify(result)


@app.route("/api/rss/status", methods=["GET"])
def api_rss_status():
    """获取 RSS 更新状态"""
    return jsonify({
        "is_running": rss_update_state["is_running"],
        "is_complete": rss_update_state["is_complete"],
        "start_time": rss_update_state["start_time"],
        "end_time": rss_update_state["end_time"],
        "summary": rss_update_state.get("summary", None),
        "results": rss_update_state["results"][-50:] if rss_update_state["results"] else []  # Return last 50 results
    })


# ========== JavDB Score API Endpoints ==========

def fetch_javdb_scores_background():
    """后台获取所有影片的 JavDB 评分"""
    global javdb_task_state

    javdb_task_state["is_running"] = True
    javdb_task_state["is_complete"] = False
    javdb_task_state["start_time"] = datetime.now().isoformat()
    javdb_task_state["results"] = []

    conn = get_db()
    # 只获取没有 javdb_score 的影片
    movies = conn.execute("SELECT id, code FROM movies WHERE javdb_score IS NULL OR javdb_score = ''").fetchall()
    conn.close()

    total = len(movies)
    success_count = 0
    fail_count = 0

    for idx, movie in enumerate(movies):
        # 添加延迟避免被封
        if idx > 0:
            time.sleep(2)

        movie_id = movie["id"]
        code = movie["code"]

        try:
            score = javdb_scraper.get_javdb_score(code)

            if score is not None:
                conn = get_db()
                conn.execute("UPDATE movies SET javdb_score = ? WHERE id = ?", (score, movie_id))
                conn.commit()
                conn.close()
                success_count += 1
                javdb_task_state["results"].append({
                    "code": code,
                    "movie_id": movie_id,
                    "score": score,
                    "success": True
                })
                print(f"[JavDB] {code}: {score}")
            else:
                fail_count += 1
                javdb_task_state["results"].append({
                    "code": code,
                    "movie_id": movie_id,
                    "score": None,
                    "success": False,
                    "error": "Not found or error"
                })
                print(f"[JavDB] {code}: Not found")

        except Exception as e:
            fail_count += 1
            javdb_task_state["results"].append({
                "code": code,
                "movie_id": movie_id,
                "score": None,
                "success": False,
                "error": str(e)
            })
            print(f"[JavDB] {code}: Error - {e}")

    javdb_task_state["is_running"] = False
    javdb_task_state["is_complete"] = True
    javdb_task_state["end_time"] = datetime.now().isoformat()
    javdb_task_state["summary"] = {
        "total": total,
        "success": success_count,
        "fail": fail_count
    }

    print(f"JavDB score fetch completed: {success_count}/{total} succeeded, {fail_count} failed")


@app.route("/api/fetch_javdb_scores", methods=["POST"])
def api_fetch_javdb_scores():
    """启动后台获取 JavDB 评分"""
    global javdb_task_state

    # 如果已经在运行，返回当前状态
    if javdb_task_state["is_running"]:
        return jsonify({
            "success": False,
            "message": "JavDB score fetch is already running",
            "is_running": True
        })

    # 启动后台线程
    javdb_thread = threading.Thread(target=fetch_javdb_scores_background, daemon=True)
    javdb_thread.start()

    return jsonify({
        "success": True,
        "message": "JavDB score fetch started in background"
    })


@app.route("/api/javdb_task_status", methods=["GET"])
def api_javdb_task_status():
    """获取 JavDB 评分获取任务状态"""
    return jsonify({
        "is_running": javdb_task_state["is_running"],
        "is_complete": javdb_task_state["is_complete"],
        "start_time": javdb_task_state["start_time"],
        "end_time": javdb_task_state["end_time"],
        "summary": javdb_task_state.get("summary", None),
        "results": javdb_task_state["results"][-50:] if javdb_task_state["results"] else []
    })


def fetch_single_javdb_score_background(code):
    """后台获取单个影片的 JavDB 评分"""
    global javdb_task_state
    task_id = f"single_{code}_{int(datetime.now().timestamp())}"

    # 添加到结果列表
    result = {
        "task_id": task_id,
        "code": code,
        "score": None,
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }
    javdb_task_state["results"].append(result)

    # 在后台线程中创建数据库连接
    db_conn = None
    try:
        db_conn = get_db()
        print(f"[JavDB] Fetching score for: {code}")
        score = javdb_scraper.get_javdb_score(code)
        print(f"[JavDB] Raw score result: {score}")
        # 保存到数据库
        if score is not None:
            db_conn.execute("UPDATE movies SET javdb_score = ? WHERE code = ?", (score, code))
            db_conn.commit()
            result["score"] = score
            result["status"] = "success"
            print(f"[JavDB] {code}: Success - {score}")
        else:
            result["status"] = "not_found"
            print(f"[JavDB] {code}: Not found in JavDB")
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        print(f"[JavDB] {code}: Error - {e}")
    finally:
        if db_conn:
            db_conn.close()

    # 更新摘要
    success_count = sum(1 for r in javdb_task_state["results"] if r.get("status") == "success")
    fail_count = sum(1 for r in javdb_task_state["results"] if r.get("status") in ("error", "not_found"))
    javdb_task_state["summary"] = {
        "total": len(javdb_task_state["results"]),
        "success": success_count,
        "fail": fail_count
    }


@app.route("/api/test_javdb/<code>", methods=["GET"])
def api_test_javdb(code):
    """获取单个影片的 JavDB 评分（后台执行）"""
    global javdb_task_state

    # 启动后台线程获取评分
    thread = threading.Thread(target=fetch_single_javdb_score_background, args=(code,), daemon=True)
    thread.start()

    return jsonify({
        "success": True,
        "message": "JavDB score fetch started in background",
        "code": code
    })


if __name__ == "__main__":
    init_db()
    print("Syncing Jellyfin on startup...")
    count = sync_jellyfin()
    print(f"Synced {count} movies")

    # 导入演员列表
    print("Importing actors from Jellyfin...")
    actor_count = import_actors_from_jellyfin()
    print(f"Imported {actor_count} new actors")

    # 自动抓取 RSS（在后台运行，不阻塞网页启动）
    if AUTO_REFRESH_ON_STARTUP and RSS_UPDATE_ON_STARTUP:
        print("Starting background RSS fetch (will not block web access)...")
        rss_thread = threading.Thread(target=fetch_all_rss_background, daemon=True)
        rss_thread.start()

    # 启动 Flask 应用
    print("Starting web server on http://0.0.0.0:5002")
    app.run(host="0.0.0.0", port=5002, debug=False, use_reloader=False)
