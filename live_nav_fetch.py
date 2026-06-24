import requests
import pandas as pd
from pathlib import Path

RAW_DIR = Path("data/raw")
NAV_DIR = RAW_DIR / "nav"
REPORTS_DIR = Path("reports")

RAW_DIR.mkdir(parents=True, exist_ok=True)
NAV_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

schemes = {
    125497: "HDFC Top 100 Direct",
    119551: "SBI Bluechip",
    120503: "ICICI Bluechip",
    118632: "Nippon Large Cap",
    119092: "Axis Bluechip",
    120841: "Kotak Bluechip",
}

all_nav_rows = []
fund_master_rows = []
summary_rows = []

for scheme_code, scheme_label in schemes.items():
    print(f"\nFetching NAV for {scheme_label} | Code: {scheme_code}")

    url = f"https://api.mfapi.in/mf/{scheme_code}"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch {scheme_code}: {e}")
        continue

    json_data = response.json()

    meta = json_data.get("meta", {})
    nav_data = json_data.get("data", [])

    if not nav_data:
        print(f"No NAV data found for {scheme_code}")
        continue

    fund_master_rows.append({
        "scheme_code": scheme_code,
        "scheme_label": scheme_label,
        "fund_house": meta.get("fund_house"),
        "scheme_type": meta.get("scheme_type"),
        "scheme_category": meta.get("scheme_category"),
        "scheme_name": meta.get("scheme_name"),
        "isin_growth": meta.get("isin_growth"),
        "isin_div_reinvestment": meta.get("isin_div_reinvestment"),
    })

    scheme_nav_rows = []

    for item in nav_data:
        row = {
            "scheme_code": scheme_code,
            "scheme_label": scheme_label,
            "scheme_name": meta.get("scheme_name"),
            "fund_house": meta.get("fund_house"),
            "scheme_type": meta.get("scheme_type"),
            "scheme_category": meta.get("scheme_category"),
            "date": item.get("date"),
            "nav": item.get("nav"),
        }

        scheme_nav_rows.append(row)
        all_nav_rows.append(row)

    scheme_nav_df = pd.DataFrame(scheme_nav_rows)

    scheme_nav_df["date"] = pd.to_datetime(
        scheme_nav_df["date"],
        dayfirst=True,
        errors="coerce"
    )

    scheme_nav_df["nav"] = pd.to_numeric(
        scheme_nav_df["nav"],
        errors="coerce"
    )

    scheme_nav_df = scheme_nav_df.sort_values("date", ascending=False)

    scheme_file = NAV_DIR / f"live_nav_{scheme_code}.csv"
    scheme_nav_df.to_csv(scheme_file, index=False)

    print(f"Saved individual NAV file: {scheme_file}")
    print("Shape:", scheme_nav_df.shape)

    summary_rows.append({
        "scheme_code": scheme_code,
        "scheme_label": scheme_label,
        "api_scheme_name": meta.get("scheme_name"),
        "fund_house": meta.get("fund_house"),
        "scheme_type": meta.get("scheme_type"),
        "scheme_category": meta.get("scheme_category"),
        "records_fetched": scheme_nav_df.shape[0],
        "latest_date": scheme_nav_df["date"].max(),
        "latest_nav": scheme_nav_df.iloc[0]["nav"],
        "output_file": str(scheme_file)
    })


fund_master_df = pd.DataFrame(fund_master_rows)
nav_history_df = pd.DataFrame(all_nav_rows)
summary_df = pd.DataFrame(summary_rows)

nav_history_df["date"] = pd.to_datetime(
    nav_history_df["date"],
    dayfirst=True,
    errors="coerce"
)

nav_history_df["nav"] = pd.to_numeric(
    nav_history_df["nav"],
    errors="coerce"
)

fund_master_df.to_csv(RAW_DIR / "01_fund_master.csv", index=False)
nav_history_df.to_csv(RAW_DIR / "02_nav_history.csv", index=False)
summary_df.to_csv(REPORTS_DIR / "live_nav_fetch_summary.csv", index=False)

print("\nNAV fetch complete.")

print("\nSaved:")
print("data/raw/01_fund_master.csv")
print("data/raw/02_nav_history.csv")
print("reports/live_nav_fetch_summary.csv")

print("\nFund Master Shape:", fund_master_df.shape)
print("NAV History Shape:", nav_history_df.shape)
print("Summary Shape:", summary_df.shape)

print("\nFund Master Head:")
print(fund_master_df.head())

print("\nNAV History Head:")
print(nav_history_df.head())

print("\nFetch Summary:")
print(summary_df)