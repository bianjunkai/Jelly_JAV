#!/usr/bin/env python3
import sqlite3
import requests
import re
import os
from flask import Flask, render_template, jsonify, request
from config import JELLYFIN_URL, JELLYFIN_API_KEY

app = Flask(__name__)
DB_PATH = "data.db"

CSV_FILES = {
    "JavDB TOP250": "JAVDB TOP250.csv",
    "JavDB 2024 TOP250": "JAVDB 2024TOP250.csv",
    "JavDB 2025 TOP250": "JAVDB 2025TOP250.csv",
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
            date_added TEXT
        )
    """)
    conn.commit()
    conn.close()


def extract_code(title):
    match = re.match(r"^([A-Z]+-\d+)", title)
    return match.group(1) if match else None


def load_csv_codes():
    codes = {label: set() for label in CSV_FILES}
    for label, filepath in CSV_FILES.items():
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                import csv

                reader = csv.DictReader(f)
                for row in reader:
                    name = row.get("SUBSTR(name,0,40)", row.get("name", ""))
                    if name:
                        code = extract_code(name)
                        if code:
                            codes[label].add(code)
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

            conn.execute(
                """
                INSERT OR REPLACE INTO movies (code, title, year, actors, date_added)
                VALUES (?, ?, ?, ?, ?)
            """,
                (code, title, year, actors, date_added),
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
    cursor = conn.execute("SELECT code, title, year, actors FROM movies ORDER BY code")
    movies = []
    for row in cursor:
        code = row["code"]
        tags = []
        for label, codes in csv_codes.items():
            if code in codes:
                tags.append(label)
        movies.append(
            {
                "code": code,
                "title": row["title"],
                "year": row["year"],
                "actors": row["actors"],
                "tags": tags,
                "all_tags": list(csv_codes.keys()),
            }
        )
    conn.close()
    return movies


def get_movies_by_list(list_name):
    csv_codes = load_csv_codes()
    codes = csv_codes.get(list_name, set())

    conn = get_db()
    all_jellyfin_codes = set(
        row["code"] for row in conn.execute("SELECT code FROM movies")
    )

    movies = []
    for code in sorted(codes):
        in_jellyfin = code in all_jellyfin_codes
        title = ""
        if in_jellyfin:
            row = conn.execute(
                "SELECT title, year, actors FROM movies WHERE code = ?", (code,)
            ).fetchone()
            if row:
                title = row["title"]
                year = row["year"]
                actors = row["actors"]
        movies.append(
            {
                "code": code,
                "title": title,
                "year": year if in_jellyfin else "",
                "actors": actors if in_jellyfin else "",
                "in_jellyfin": in_jellyfin,
            }
        )
    conn.close()
    return movies


def get_missing_movies():
    csv_codes = load_csv_codes()
    javdb_all = set()
    for label in ["JavDB TOP250", "JavDB 2024 TOP250", "JavDB 2025 TOP250"]:
        javdb_all.update(csv_codes[label])

    javlib_codes = csv_codes["JavLibray TOP500"]

    conn = get_db()
    jellyfin_codes = set(row["code"] for row in conn.execute("SELECT code FROM movies"))
    conn.close()

    javdb_missing = sorted(javdb_all - jellyfin_codes)
    javlib_missing = sorted(javlib_codes - jellyfin_codes)

    return {"javdb": javdb_missing, "javlib": javlib_missing}


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
    return jsonify(movies)


@app.route("/api/list/<list_name>")
def api_list(list_name):
    if list_name == "missing":
        return jsonify(get_missing_movies())
    return jsonify(get_movies_by_list(list_name))


@app.route("/api/sync", methods=["POST"])
def api_sync():
    count = sync_jellyfin()
    return jsonify({"success": count >= 0, "count": count})


@app.route("/api/stats")
def api_stats():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM movies").fetchone()[0]
    conn.close()

    csv_codes = load_csv_codes()
    stats = {"total": total}
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
        "SELECT code, title, year, actors FROM movies WHERE actors LIKE ?",
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

        movies.append(
            {
                "code": code,
                "title": row["title"],
                "year": row["year"],
                "actors": actors,
                "tags": tags,
                "all_tags": all_tags,
            }
        )

    conn.close()
    return jsonify(movies)


if __name__ == "__main__":
    init_db()
    print("Syncing Jellyfin on startup...")
    count = sync_jellyfin()
    print(f"Synced {count} movies")
    app.run(host="0.0.0.0", port=5002, debug=False, use_reloader=False)
