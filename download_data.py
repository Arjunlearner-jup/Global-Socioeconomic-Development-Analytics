"""
download_data.py
----------------
Downloads all World Bank API datasets and saves them to the dataset/ folder.
Run this script ONCE before executing the notebook so the notebook
loads from local files instead of hitting the API every run.

Usage:
    F:\\venv\\Scripts\\python.exe download_data.py
"""

import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATASET_DIR = r"C:\Users\arjun\Downloads\APDV again\x24232335\x24232335\dataset"
WB_BASE_URL = "https://api.worldbank.org/v2"

ECONOMIC_INDICATORS = {
    "NY.GDP.PCAP.CD":     "gdp_per_capita",
    "SP.DYN.LE00.IN":     "life_expectancy",
    "SP.POP.TOTL":        "population",
    "SL.UEM.TOTL.ZS":    "unemployment_rate",
    "BX.KLT.DINV.CD.WD": "fdi_inflows",
}

EDUCATION_INDICATORS = {
    "SE.ADT.LITR.ZS":    "literacy_rate",
    "SE.PRM.ENRR":       "primary_enrollment",
    "SE.SEC.ENRR":       "secondary_enrollment",
    "SE.TER.ENRR":       "tertiary_enrollment",
    "SE.XPD.TOTL.GD.ZS": "edu_expenditure_pct_gdp",
}

START_YEAR = 2000
END_YEAR   = 2022

TIMEOUT    = 60
MAX_RETRY  = 5
BACKOFF    = 2.0

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_with_retry(url, params):
    """GET with exponential backoff retries on timeout / server errors."""
    delay = 2.0
    for attempt in range(1, MAX_RETRY + 1):
        try:
            resp = requests.get(url, params=params, timeout=TIMEOUT)
            resp.raise_for_status()
            return resp
        except requests.exceptions.Timeout:
            if attempt == MAX_RETRY:
                raise
            print(f"    Timeout (attempt {attempt}/{MAX_RETRY}), retrying in {delay:.0f}s ...")
            time.sleep(delay)
            delay *= BACKOFF
        except requests.exceptions.HTTPError as exc:
            if exc.response is not None and exc.response.status_code in (429, 500, 502, 503, 504):
                if attempt == MAX_RETRY:
                    raise
                print(f"    HTTP {exc.response.status_code} (attempt {attempt}/{MAX_RETRY}), retrying in {delay:.0f}s ...")
                time.sleep(delay)
                delay *= BACKOFF
            else:
                raise
    return None


def fetch_wb_data(indicator_code, start_year=START_YEAR, end_year=END_YEAR,
                  per_page=1000):
    """Fetch paginated World Bank indicator records for all countries."""
    all_records = []
    page        = 1
    total_pages = None

    while total_pages is None or page <= total_pages:
        url    = f"{WB_BASE_URL}/country/all/indicator/{indicator_code}"
        params = {
            "format"   : "json",
            "per_page" : per_page,
            "page"     : page,
            "date"     : f"{start_year}:{end_year}",
        }
        try:
            resp    = _get_with_retry(url, params)
            payload = resp.json()
        except (requests.RequestException, ValueError) as exc:
            print(f"  Warning: page {page} failed for {indicator_code} - {exc}")
            break

        if len(payload) < 2 or not payload[1]:
            break

        meta, records = payload[0], payload[1]
        all_records.extend(records)
        total_pages = meta.get("pages", 1)
        if page >= total_pages:
            break
        page += 1
        time.sleep(0.5)

    return all_records


def fetch_wb_countries():
    """Fetch country metadata from the World Bank API."""
    url  = f"{WB_BASE_URL}/country"
    resp = _get_with_retry(url, {"format": "json", "per_page": 500})
    payload = resp.json()
    return payload[1] if len(payload) > 1 else []


def is_valid_country(iso3):
    """Return True if iso3 is a real 3-alpha country code, not an aggregate."""
    return isinstance(iso3, str) and len(iso3) == 3 and iso3.isalpha()


def parse_wb_records(raw_records):
    """Parse raw World Bank API records into clean dicts; skip aggregates."""
    parsed = []
    for rec in raw_records:
        iso3 = rec.get("countryiso3code", "")
        if not is_valid_country(iso3):
            continue
        parsed.append({
            "country_code"   : iso3,
            "country_name"   : rec["country"]["value"],
            "indicator_code" : rec["indicator"]["id"],
            "indicator_name" : rec["indicator"]["value"],
            "year"           : int(rec["date"]),
            "value"          : (
                float(rec["value"]) if rec.get("value") is not None else None
            ),
        })
    return parsed


def save_json(data, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {filepath}  ({len(data):,} records)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    os.makedirs(DATASET_DIR, exist_ok=True)
    print(f"Dataset directory: {os.path.abspath(DATASET_DIR)}\n")

    # -- 1. Country metadata -----------------------------------------------
    countries_file = os.path.join(DATASET_DIR, "wb_countries.json")
    if os.path.exists(countries_file):
        print(f"[SKIP] wb_countries.json already exists.")
    else:
        print("[1/3] Fetching World Bank country metadata ...")
        raw = fetch_wb_countries()
        # Keep only actual countries
        countries = [c for c in raw if is_valid_country(c.get("id", ""))]
        save_json(countries, countries_file)

    # -- 2. Economic indicators --------------------------------------------
    econ_file = os.path.join(DATASET_DIR, "economic_indicators_raw.json")
    if os.path.exists(econ_file):
        print(f"[SKIP] economic_indicators_raw.json already exists.")
    else:
        print("\n[2/3] Fetching Economic Indicators ...")
        all_econ = []
        for code, col_name in ECONOMIC_INDICATORS.items():
            print(f"  {col_name} ({code}) ...")
            raw    = fetch_wb_data(code)
            parsed = parse_wb_records(raw)
            all_econ.extend(parsed)
            print(f"    {len(parsed):,} records")
        save_json(all_econ, econ_file)

    # -- 3. Education indicators -------------------------------------------
    edu_file = os.path.join(DATASET_DIR, "education_indicators_raw.json")
    if os.path.exists(edu_file):
        print(f"[SKIP] education_indicators_raw.json already exists.")
    else:
        print("\n[3/3] Fetching Education Indicators ...")
        all_edu = []
        for code, col_name in EDUCATION_INDICATORS.items():
            print(f"  {col_name} ({code}) ...")
            raw    = fetch_wb_data(code)
            parsed = parse_wb_records(raw)
            all_edu.extend(parsed)
            print(f"    {len(parsed):,} records")
        save_json(all_edu, edu_file)

    print("\nAll datasets downloaded successfully.")
    print("You can now run the notebook — it will load from local files.")


if __name__ == "__main__":
    main()
