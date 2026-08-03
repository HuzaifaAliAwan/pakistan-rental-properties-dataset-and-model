"""
Build Booking.com search-results URLs for each resolved Pakistani city,
using only the parameters confirmed to actually matter for the search
(ss, dest_id, dest_type, checkin/checkout, group params) - everything
else in a real browser URL (label, sid, aid, ac_*, ssne, etc.) is
session/tracking noise and is intentionally left out.

Usage (run from the project root):
    .venv/bin/python scripts/generate_city_urls.py \\
        --input data/reference/pakistan_cities_dest_ids.csv \\
        --output data/reference/pakistan_cities_search_urls.csv \\
        --checkin 2026-08-06 \\
        --checkout 2026-08-07
"""

import argparse
import csv
from urllib.parse import urlencode

BASE_URL = "https://www.booking.com/searchresults.en-gb.html"


def build_url(label, dest_id, checkin, checkout, group_adults, no_rooms, group_children):
    params = {
        "ss": label,
        "dest_id": dest_id,
        "dest_type": "city",
        "lang": "en-gb",
        "checkin": checkin,
        "checkout": checkout,
        "group_adults": group_adults,
        "no_rooms": no_rooms,
        "group_children": group_children,
    }
    return f"{BASE_URL}?{urlencode(params)}"


def main(input_file, output_file, checkin, checkout, group_adults, no_rooms, group_children):
    rows = []
    with open(input_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = build_url(
                label=row["label"],
                dest_id=row["dest_id"],
                checkin=checkin,
                checkout=checkout,
                group_adults=group_adults,
                no_rooms=no_rooms,
                group_children=group_children,
            )
            rows.append({
                "city": row["query"],
                "dest_id": row["dest_id"],
                "checkin": checkin,
                "checkout": checkout,
                "url": url,
            })

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["city", "dest_id", "checkin", "checkout", "url"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} search URLs -> {output_file}")
    for row in rows[:3]:
        print(f"  {row['city']}: {row['url']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/reference/pakistan_cities_dest_ids.csv")
    parser.add_argument("--output", default="data/reference/pakistan_cities_search_urls.csv")
    parser.add_argument("--checkin", default="2026-08-06")
    parser.add_argument("--checkout", default="2026-08-07")
    parser.add_argument("--group-adults", type=int, default=2)
    parser.add_argument("--no-rooms", type=int, default=1)
    parser.add_argument("--group-children", type=int, default=0)
    args = parser.parse_args()

    main(
        args.input, args.output,
        args.checkin, args.checkout,
        args.group_adults, args.no_rooms, args.group_children,
    )
