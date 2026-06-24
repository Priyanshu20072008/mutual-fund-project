from pathlib import Path
import requests
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent

PROVIDED_DIR = BASE_DIR / "data" / "raw" / "provided"
PROVIDED_DIR.mkdir(parents=True, exist_ok=True)


SELECTED_SCHEMES = {
    "HDFC_Top_100_Direct": 125497,
    "SBI_Bluechip": 119551,
    "ICICI_Bluechip": 120503,
    "Nippon_Large_Cap": 118632,
    "Axis_Bluechip": 119092,
    "Kotak_Bluechip": 120841,
}


def get_json(url):
    response = requests.get(url, timeout=40)
    response.raise_for_status()
    return response.json()


def create_fund_master():
    print("Fetching full scheme list from MFAPI...")

    url = "https://api.mfapi.in/mf"
    data = get_json(url)

    df = pd.DataFrame(data)

    # MFAPI usually gives: schemeCode, schemeName
    df = df.rename(columns={
        "schemeCode": "scheme_code",
        "schemeName": "scheme_name"
    })

    df["scheme_code"] = df["scheme_code"].astype(str)

    # Add simple derived columns
    df["fund_house"] = df["scheme_name"].str.split(" ").str[0]
    df["is_direct_plan"] = df["scheme_name"].str.contains("Direct", case=False, na=False)
    df["is_growth_plan"] = df["scheme_name"].str.contains("Growth", case=False, na=False)

    output_path = PROVIDED_DIR / "fund_master.csv"
    df.to_csv(output_path, index=False)

    print(f"Created: {output_path}")
    return df


def create_nav_history_and_latest():
    all_nav_rows = []
    latest_rows = []
    selected_rows = []

    for scheme_key, scheme_code in SELECTED_SCHEMES.items():
        print(f"Fetching NAV history for {scheme_key} - {scheme_code}")

        url = f"https://api.mfapi.in/mf/{scheme_code}"
        json_data = get_json(url)

        meta = json_data.get("meta", {})
        nav_data = json_data.get("data", [])

        nav_df = pd.DataFrame(nav_data)

        if nav_df.empty:
            print(f"No NAV found for {scheme_code}")
            continue

        nav_df["scheme_code"] = str(scheme_code)
        nav_df["scheme_key"] = scheme_key
        nav_df["scheme_name"] = meta.get("scheme_name")
        nav_df["fund_house"] = meta.get("fund_house")
        nav_df["scheme_type"] = meta.get("scheme_type")
        nav_df["scheme_category"] = meta.get("scheme_category")

        nav_df["date"] = pd.to_datetime(nav_df["date"], format="%d-%m-%Y", errors="coerce")
        nav_df["nav"] = pd.to_numeric(nav_df["nav"], errors="coerce")

        nav_df = nav_df.sort_values("date", ascending=False)

        all_nav_rows.append(nav_df)

        latest_row = nav_df.iloc[0].to_dict()
        latest_rows.append(latest_row)

        selected_rows.append({
            "scheme_key": scheme_key,
            "scheme_code": str(scheme_code),
            "scheme_name": meta.get("scheme_name"),
            "fund_house": meta.get("fund_house"),
            "scheme_type": meta.get("scheme_type"),
            "scheme_category": meta.get("scheme_category"),
            "records_fetched": len(nav_df),
            "latest_date": nav_df["date"].max(),
            "latest_nav": nav_df.iloc[0]["nav"]
        })

    nav_history_df = pd.concat(all_nav_rows, ignore_index=True)
    latest_nav_df = pd.DataFrame(latest_rows)
    selected_schemes_df = pd.DataFrame(selected_rows)

    nav_history_df.to_csv(PROVIDED_DIR / "nav_history.csv", index=False)
    latest_nav_df.to_csv(PROVIDED_DIR / "latest_nav.csv", index=False)
    selected_schemes_df.to_csv(PROVIDED_DIR / "selected_schemes.csv", index=False)

    print(f"Created: {PROVIDED_DIR / 'nav_history.csv'}")
    print(f"Created: {PROVIDED_DIR / 'latest_nav.csv'}")
    print(f"Created: {PROVIDED_DIR / 'selected_schemes.csv'}")

    return nav_history_df, latest_nav_df, selected_schemes_df


def create_summary_files(fund_master_df, nav_history_df):
    print("Creating summary CSV files...")

    # 4. fund_houses.csv
    fund_houses_df = (
        fund_master_df.groupby("fund_house")
        .size()
        .reset_index(name="scheme_count")
        .sort_values("scheme_count", ascending=False)
    )
    fund_houses_df.to_csv(PROVIDED_DIR / "fund_houses.csv", index=False)

    # 5. fund_categories.csv
    fund_categories_df = (
        nav_history_df[["scheme_category"]]
        .dropna()
        .drop_duplicates()
        .sort_values("scheme_category")
    )
    fund_categories_df.to_csv(PROVIDED_DIR / "fund_categories.csv", index=False)

    # 6. scheme_type_summary.csv
    scheme_type_summary_df = (
        nav_history_df.groupby("scheme_type")
        .agg(
            scheme_count=("scheme_code", "nunique"),
            nav_records=("nav", "count"),
            avg_nav=("nav", "mean")
        )
        .reset_index()
    )
    scheme_type_summary_df.to_csv(PROVIDED_DIR / "scheme_type_summary.csv", index=False)

    # 7. scheme_category_summary.csv
    scheme_category_summary_df = (
        nav_history_df.groupby("scheme_category")
        .agg(
            scheme_count=("scheme_code", "nunique"),
            nav_records=("nav", "count"),
            min_nav=("nav", "min"),
            max_nav=("nav", "max"),
            avg_nav=("nav", "mean")
        )
        .reset_index()
        .sort_values("scheme_count", ascending=False)
    )
    scheme_category_summary_df.to_csv(PROVIDED_DIR / "scheme_category_summary.csv", index=False)

    # 9. nav_quality_report.csv
    nav_quality_report_df = (
        nav_history_df.groupby("scheme_code")
        .agg(
            scheme_name=("scheme_name", "first"),
            total_records=("nav", "count"),
            missing_nav=("nav", lambda x: x.isna().sum()),
            missing_date=("date", lambda x: x.isna().sum()),
            min_date=("date", "min"),
            max_date=("date", "max")
        )
        .reset_index()
    )
    nav_quality_report_df.to_csv(PROVIDED_DIR / "nav_quality_report.csv", index=False)

    print(f"Created: {PROVIDED_DIR / 'fund_houses.csv'}")
    print(f"Created: {PROVIDED_DIR / 'fund_categories.csv'}")
    print(f"Created: {PROVIDED_DIR / 'scheme_type_summary.csv'}")
    print(f"Created: {PROVIDED_DIR / 'scheme_category_summary.csv'}")
    print(f"Created: {PROVIDED_DIR / 'nav_quality_report.csv'}")


def create_amfi_latest_nav():
    print("Fetching AMFI latest NAV text file...")

    url = "https://www.amfiindia.com/spages/NAVAll.txt?t="
    response = requests.get(url, timeout=40)
    response.raise_for_status()

    lines = response.text.splitlines()

    rows = []

    for line in lines:
        if ";" not in line:
            continue

        parts = line.split(";")

        if len(parts) != 6:
            continue

        if parts[0].strip() == "Scheme Code":
            continue

        rows.append({
            "scheme_code": parts[0].strip(),
            "isin_growth_or_div_payout": parts[1].strip(),
            "isin_div_reinvestment": parts[2].strip(),
            "scheme_name": parts[3].strip(),
            "net_asset_value": parts[4].strip(),
            "date": parts[5].strip()
        })

    df = pd.DataFrame(rows)

    df["net_asset_value"] = pd.to_numeric(df["net_asset_value"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    output_path = PROVIDED_DIR / "amfi_latest_nav.csv"
    df.to_csv(output_path, index=False)

    print(f"Created: {output_path}")


def main():
    print("Creating 10 CSV files for Day 1 project...")

    fund_master_df = create_fund_master()
    nav_history_df, latest_nav_df, selected_schemes_df = create_nav_history_and_latest()
    create_summary_files(fund_master_df, nav_history_df)
    create_amfi_latest_nav()

    csv_files = list(PROVIDED_DIR.glob("*.csv"))

    print("\nCSV files created:")
    for file in csv_files:
        print("-", file.name)

    print(f"\nTotal CSV files in data/raw/provided/: {len(csv_files)}")

    if len(csv_files) >= 10:
        print("\nSUCCESS: You now have at least 10 CSV files.")
    else:
        print("\nWARNING: Less than 10 CSV files created.")


if __name__ == "__main__":
    main()