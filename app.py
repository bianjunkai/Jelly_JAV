#!/usr/bin/env python3
import sqlite3
import requests
import re
import os
from flask import Flask, render_template, jsonify, request, Response
from config import JELLYFIN_URL, JELLYFIN_API_KEY

app = Flask(__name__)
DB_PATH = "data.db"

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
                INSERT OR REPLACE INTO movies (code, title, year, actors, date_added, jellyfin_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (code, title, year, actors, date_added, jellyfin_id),
            )
            count += 1

        conn.commit()
        conn.close()
        return count
    except Exception as e:
        print(f"Sync error: {e}")
        return -1


def get_movies_with_tags():
    csv_codes = load_csv_codes()
    conn = get_db()
    cursor = conn.execute("SELECT code, title, year, actors, jellyfin_id FROM movies ORDER BY code")
    movies = []
    for row in cursor:
        code = row["code"]
        tags = []
        for label, codes in csv_codes.items():
            if code in codes:
                tags.append(label)

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
        "SELECT code, title, year, actors, jellyfin_id FROM movies WHERE actors LIKE ?",
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
            }
        )

    conn.close()
    return jsonify(movies)


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


if __name__ == "__main__":
    init_db()
    print("Syncing Jellyfin on startup...")
    count = sync_jellyfin()
    print(f"Synced {count} movies")
    app.run(host="0.0.0.0", port=5002, debug=False, use_reloader=False)
