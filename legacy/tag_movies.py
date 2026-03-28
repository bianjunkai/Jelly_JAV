#!/usr/bin/env python3
import csv
import re
import os

JELLYFIN_FILE = "jellyfin_movies.csv"
OUTPUT_FILE = "jellyfin_movies_tagged.csv"

LABEL_FILES = {
    "JavDB 2024 TOP250": "JAVDB 2024TOP250.csv",
    "JavDB 2025 TOP250": "JAVDB 2025TOP250.csv",
    "JavDB TOP250": "JAVDB TOP250.csv",
    "JavLibray TOP500": "JAVLIBTOP500.csv",
}


def extract_code(title):
    match = re.match(r"^([A-Z]+-\d+)", title)
    return match.group(1) if match else None


def load_codes_from_file(filepath, label):
    codes = set()
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("SUBSTR(name,0,40)", row.get("name", ""))
                if name:
                    code = extract_code(name)
                    if code:
                        codes.add(code)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    return codes


def main():
    all_codes = {}
    for label, filepath in LABEL_FILES.items():
        if os.path.exists(filepath):
            codes = load_codes_from_file(filepath, label)
            all_codes[label] = codes
            print(f"Loaded {len(codes)} codes from {filepath} for label '{label}'")
        else:
            print(f"File not found: {filepath}")

    print(f"\nProcessing {JELLYFIN_FILE}...")

    with open(JELLYFIN_FILE, "r", encoding="utf-8-sig", errors="ignore") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)

        for label in LABEL_FILES.keys():
            fieldnames.append(label)

        rows = []
        for row in reader:
            title = row.get("\ufeff标题", row.get("标题", ""))
            code = extract_code(title)

            for label in LABEL_FILES.keys():
                row[label] = "1" if code and code in all_codes.get(label, set()) else ""

            rows.append(row)

    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    tagged_count = sum(
        1 for r in rows if any(r.get(label) for label in LABEL_FILES.keys())
    )
    print(f"\nDone! Tagged {tagged_count} movies. Output saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
