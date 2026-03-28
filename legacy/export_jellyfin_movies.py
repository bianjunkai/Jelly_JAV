#!/usr/bin/env python3
import requests
import csv
import sys
from datetime import datetime

JELLYFIN_URL = "http://192.168.50.20:8096"
API_KEY = "f7885a8704d94788883acc69d20e3780"
OUTPUT_FILE = "jellyfin_movies.csv"

HEADERS = {"X-MediaBrowser-Token": API_KEY, "Content-Type": "application/json"}


def get_user_id():
    resp = requests.get(f"{JELLYFIN_URL}/Users", headers=HEADERS)
    resp.raise_for_status()
    users = resp.json()
    if not users:
        raise Exception("No users found")
    return users[0]["Id"]


def get_movies(user_id):
    movies = []
    start_index = 0
    limit = 100

    while True:
        url = f"{JELLYFIN_URL}/Users/{user_id}/Items"
        params = {
            "IncludeItemTypes": "Movie",
            "Recursive": "true",
            "StartIndex": start_index,
            "Limit": limit,
            "Fields": "ProviderIds,PremiereDate,ProductionYear,People",
        }
        resp = requests.get(url, headers=HEADERS, params=params)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("Items", [])
        movies.extend(items)

        print(f"已获取 {len(movies)} / {data.get('TotalRecordCount', '?')} 部电影")

        if len(items) < limit:
            break
        start_index += limit

    return movies


def extract_actors(people):
    actors = [p["Name"] for p in people if p.get("Type") == "Actor"]
    return ", ".join(actors[:10])


def main():
    print("=" * 50)
    print("Jellyfin 电影元数据导出工具")
    print("=" * 50)

    print("\n[1/2] 获取电影列表...")
    user_id = get_user_id()
    print(f"用户ID: {user_id}")
    movies = get_movies(user_id)
    print(f"共获取 {len(movies)} 部电影")

    if not movies:
        print("没有找到电影")
        return

    print("\n[2/2] 导出CSV...")
    print("-" * 40)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["标题", "发行年份", "发行日期", "评分", "是否观看", "是否收藏", "演员"]
        )

        for i, movie in enumerate(movies):
            name = movie.get("Name", "")
            year = movie.get("ProductionYear", "")
            premiere = (
                movie.get("PremiereDate", "")[:10] if movie.get("PremiereDate") else ""
            )
            rating = movie.get("CommunityRating")
            played = "是" if movie.get("UserData", {}).get("Played") else "否"
            favorite = "是" if movie.get("UserData", {}).get("IsFavorite") else "否"
            actors = extract_actors(movie.get("People", []))

            writer.writerow([name, year, premiere, rating, played, favorite, actors])
            print(f"  [{i + 1}/{len(movies)}] {name}")

    print("-" * 40)
    print(f"\n完成！已保存到: {OUTPUT_FILE}")
    print(f"共导出 {len(movies)} 部电影")


if __name__ == "__main__":
    main()
