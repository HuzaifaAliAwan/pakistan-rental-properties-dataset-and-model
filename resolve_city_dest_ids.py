"""
Resolve Booking.com `dest_id` values for a list of city names using the
same GraphQL AutoComplete endpoint the real search box calls.

Usage:
    .venv/bin/python resolve_city_dest_ids.py \\
        --cities-file pakistan_cities.txt \\
        --output-file pakistan_cities_dest_ids.csv \\
        --delay 2.5

This is intentionally kept separate from main.ipynb.
"""

import argparse
import asyncio
import csv
import json
import secrets
import time
from pathlib import Path

from playwright.async_api import async_playwright

AUTOCOMPLETE_QUERY = """
query AutoComplete($input: AutoCompleteRequestInput!) {
  autoCompleteSuggestions(input: $input) {
    results {
      destination {
        countryCode
        destId
        destType
        latitude
        longitude
      }
      displayInfo {
        title
        subTitle
        label
      }
      metaData {
        autocompleteResultSource
      }
    }
  }
}
"""


async def resolve_city(page, city_name, country_code="pk"):
    pageview_id = secrets.token_hex(8)

    response = await page.request.post(
        "https://www.booking.com/dml/graphql?lang=en-gb",
        data=json.dumps({
            "operationName": "AutoComplete",
            "variables": {
                "input": {
                    "prefixQuery": city_name,
                    "requestConfig": {"enableRequestContextBoost": True},
                    "requestContext": {
                        "pageviewId": pageview_id,
                        "location": None,
                        "page": "INDEX",
                    },
                    "nbSuggestions": 5,
                    "fallbackConfig": {
                        "mergeResults": True,
                        "nbMaxMergedResults": 6,
                        "nbMaxThirdPartyResults": 3,
                        "sources": ["GOOGLE", "HERE"],
                    },
                }
            },
            "extensions": {},
            "query": AUTOCOMPLETE_QUERY,
        }),
        headers={"Content-Type": "application/json"},
    )

    if response.status != 200:
        return None

    payload = await response.json()
    results = (
        payload.get("data", {})
        .get("autoCompleteSuggestions", {})
        .get("results", [])
    )

    for r in results:
        dest = r.get("destination") or {}
        meta = r.get("metaData") or {}
        if (
            dest.get("destType") == "CITY"
            and dest.get("countryCode") == country_code
            and meta.get("autocompleteResultSource") == "BRICK"
        ):
            display = r.get("displayInfo", {})
            return {
                "query": city_name,
                "matched_title": display.get("title"),
                "label": display.get("label"),
                "dest_id": dest.get("destId"),
                "dest_type": dest.get("destType"),
                "country_code": dest.get("countryCode"),
                "source": meta.get("autocompleteResultSource"),
                "latitude": dest.get("latitude"),
                "longitude": dest.get("longitude"),
            }

    return None


async def main(cities_file, output_file, delay_seconds, headless):
    cities = [
        line.strip()
        for line in Path(cities_file).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    results = []
    failures = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(locale="en-US")
        page = await context.new_page()

        # Load the homepage once so the request carries real cookies/session
        # context, rather than firing bare unauthenticated HTTP calls.
        await page.goto("https://www.booking.com/index.en-gb.html")
        await page.wait_for_load_state("networkidle")

        for i, city in enumerate(cities):
            try:
                match = await resolve_city(page, city)
            except Exception as e:
                match = None
                print(f"[{i + 1}/{len(cities)}] {city}: ERROR {e}")

            if match:
                print(f"[{i + 1}/{len(cities)}] {city} -> dest_id={match['dest_id']} ({match['label']})")
                results.append(match)
            else:
                print(f"[{i + 1}/{len(cities)}] {city} -> NOT FOUND")
                failures.append(city)

            await page.wait_for_timeout(int(delay_seconds * 1000))

        await browser.close()

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "query", "matched_title", "label", "dest_id",
                "dest_type", "country_code", "source", "latitude", "longitude",
            ],
        )
        writer.writeheader()
        writer.writerows(results)

    print(f"\nResolved {len(results)}/{len(cities)} cities. Saved to {output_file}")
    if failures:
        print("Failed to resolve:", failures)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cities-file", default="pakistan_cities.txt")
    parser.add_argument("--output-file", default="pakistan_cities_dest_ids.csv")
    parser.add_argument("--delay", type=float, default=2.5, help="Seconds to wait between lookups")
    parser.add_argument("--headless", action="store_true", default=True)
    args = parser.parse_args()

    asyncio.run(main(args.cities_file, args.output_file, args.delay, args.headless))
