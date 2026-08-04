# Pakistan Rental Properties Dataset (Booking.com)

A Playwright-based scraper that collects hotel/property listing data from Booking.com search results across major cities in Pakistan, intended as a dataset for downstream analysis and a price-prediction ML model.

## Project structure

```
.
├── data/
│   ├── raw/            # one CSV per city, straight from the scraper
│   ├── processed/       # all_cities_combined.csv (all cities concatenated) + future cleaned datasets
│   └── reference/       # city list + dest_id lookups + generated search URLs
├── notebooks/
│   ├── scrape_data_from_single_link.ipynb   # single-city scraper/prototype
│   └── scrape_data_of_all_cities.ipynb      # multi-city scraper (the one actually used to build data/raw)
├── scripts/
│   ├── resolve_city_dest_ids.py
│   └── generate_city_urls.py
├── models/              # trained model artifacts (empty for now)
├── reports/             # analysis write-ups / figures (empty for now)
├── requirements.txt
├── README.md
├── LICENSE
└── .gitignore
```

`models/` and `reports/` are placeholders for the upcoming analysis and price-prediction work, so those files have a home instead of piling up at the project root.

## What's in this repo

| Path | Purpose |
|---|---|
| `notebooks/scrape_data_from_single_link.ipynb` | Single-city scraper/prototype. Scrapes one Booking.com search-results URL end to end (load all results, extract fields, clean, save). Useful as a template or for testing selector changes against one city before running the full batch. |
| `notebooks/scrape_data_of_all_cities.ipynb` | Multi-city scraper. Loops through every URL in `data/reference/pakistan_cities_search_urls.csv`, reusing the same browser session, and saves one CSV per city into `data/raw/` plus a combined dataset in `data/processed/`. |
| `data/reference/pakistan_cities.txt` | Curated list of ~80 major Pakistani cities/towns (all provinces + AJK + Gilgit-Baltistan), hand-verified to avoid name collisions with same-named small villages. |
| `scripts/resolve_city_dest_ids.py` | Resolves each city name in `pakistan_cities.txt` to its Booking.com `dest_id` via the same GraphQL `AutoComplete` endpoint the live search box uses. Only accepts `BRICK`-sourced (Booking's own verified index) `CITY`+`pk` matches. |
| `data/reference/pakistan_cities_dest_ids.csv` | Output of the resolver: city name → `dest_id`, `dest_type`, coordinates, etc. |
| `scripts/generate_city_urls.py` | Builds a ready-to-scrape Booking.com search URL for each resolved city (stripped of session/tracking noise — only `ss`, `dest_id`, `dest_type`, `checkin`/`checkout`, and group params). |
| `data/reference/pakistan_cities_search_urls.csv` | Output of the URL generator: one search URL per city, consumed by `scrape_data_of_all_cities.ipynb`. |
| `data/raw/` | Scraper output — one CSV per city. |
| `data/processed/all_cities_combined.csv` | All cities concatenated with a `city` column — the file to start analysis from. |

## Pipeline

```
data/reference/pakistan_cities.txt
        │  scripts/resolve_city_dest_ids.py
        ▼
data/reference/pakistan_cities_dest_ids.csv
        │  scripts/generate_city_urls.py
        ▼
data/reference/pakistan_cities_search_urls.csv
        │  notebooks/scrape_data_of_all_cities.ipynb
        ▼
data/raw/*.csv + data/processed/all_cities_combined.csv
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Usage

All commands below are run from the **project root**.

1. **(Optional) Regenerate the city → dest_id mapping** if you change the city list:
   ```bash
   python scripts/resolve_city_dest_ids.py \
       --cities-file data/reference/pakistan_cities.txt \
       --output-file data/reference/pakistan_cities_dest_ids.csv
   ```
2. **(Optional) Regenerate search URLs** (e.g. with different dates):
   ```bash
   python scripts/generate_city_urls.py --checkin 2026-09-15 --checkout 2026-09-17
   ```
3. **Run the scraper**: open `notebooks/scrape_data_of_all_cities.ipynb` in Jupyter and run all cells. This launches a real (non-headless) Chromium window and works through every city in `data/reference/pakistan_cities_search_urls.csv`, writing into `data/raw/` and `data/processed/`.

## Current dataset snapshot

- 79 curated cities queried; 65 returned at least one property listing.
- ~5,087 property listings in `data/processed/all_cities_combined.csv`.
- Columns: `property_name`, `property_url`, `Price_pkr`, `review_score`, `review_count`, `address`, `distance_from_center_km`, `property_type`, `bed_type`, `breakfast_included`, `free_cancellation`, `reserve_without_payment`, `image`, `stars`, `city`.

## Known caveats (read before analyzing)

- **Browser must run non-headless.** Booking.com serves a static, card-less fallback page to headless browsers for popular destinations — `HEADLESS = False` is required for real results, not just faster scraping.
- **Sparse coverage for some cities is real, not a bug.** Smaller Pakistani towns (and even some larger ones like Quetta/Larkana) genuinely have very few Booking.com-listed properties — confirmed by re-testing with different dates and getting the same low counts.
- **`Shorkot` and `Kot Radha Kishan` are outliers.** Both returned far more listings than a small town should have (Booking silently widens the search radius when a destination has little inventory of its own), so their rows likely represent a broader surrounding area rather than the town itself. Worth excluding or flagging separately in analysis.
- **Dates are fixed at collection time** (`checkin`/`checkout` baked into `pakistan_cities_search_urls.csv`), so `Price_pkr` reflects pricing for that specific stay window, not a general average.
- Anti-bot pacing (delays between actions/cities) is intentional — reducing it risks Booking.com terminating the session mid-scrape.

## Next steps

- Exploratory analysis + report on `data/processed/all_cities_combined.csv` (goes in `reports/`).
- Price-prediction model using `Price_pkr` as the target (goes in `models/`).

## License & data provenance

The code in this repository (scrapers, notebooks, helper scripts) is licensed under the [MIT License](LICENSE).

That license covers the code only. The contents of `data/raw/` and `data/processed/` (property names, prices, review counts, images, etc.) are scraped from Booking.com and remain Booking.com's data, subject to Booking.com's own terms of service — the MIT license does not extend to it, and it is included here for personal/educational analysis, not for redistribution or commercial use.
