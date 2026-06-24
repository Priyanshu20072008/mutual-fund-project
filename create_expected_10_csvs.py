from pathlib import Path
import random
import pandas as pd

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

FUND_MASTER_PATH = RAW_DIR / "01_fund_master.csv"
NAV_HISTORY_PATH = RAW_DIR / "02_nav_history.csv"


def load_base_files():
    fund_master = pd.read_csv(FUND_MASTER_PATH)
    nav_history = pd.read_csv(NAV_HISTORY_PATH)

    nav_history["date"] = pd.to_datetime(nav_history["date"], errors="coerce")
    nav_history["nav"] = pd.to_numeric(nav_history["nav"], errors="coerce")

    return fund_master, nav_history


def create_03_aum_by_fund_house(fund_master):
    rows = []

    for fund_house in fund_master["fund_house"].dropna().unique():
        rows.append({
            "fund_house": fund_house,
            "aum_crore": random.randint(5000, 90000),
            "month": "2026-06"
        })

    pd.DataFrame(rows).to_csv(RAW_DIR / "03_aum_by_fund_house.csv", index=False)


def create_04_monthly_sip():
    months = pd.date_range("2025-07-01", "2026-06-01", freq="MS")
    rows = []

    amount = 18000

    for month in months:
        amount += random.randint(100, 900)

        rows.append({
            "month": month.strftime("%Y-%m"),
            "sip_contribution_crore": amount,
            "sip_accounts_lakh": random.randint(800, 1000)
        })

    pd.DataFrame(rows).to_csv(RAW_DIR / "04_monthly_sip.csv", index=False)


def create_05_category_inflows(fund_master):
    rows = []

    for category in fund_master["scheme_category"].dropna().unique():
        gross_inflow = random.randint(1000, 8000)
        gross_outflow = random.randint(500, 5000)

        rows.append({
            "scheme_category": category,
            "month": "2026-06",
            "gross_inflow_crore": gross_inflow,
            "gross_outflow_crore": gross_outflow,
            "net_inflow_crore": gross_inflow - gross_outflow
        })

    pd.DataFrame(rows).to_csv(RAW_DIR / "05_category_inflows.csv", index=False)


def create_06_folio_count(fund_master):
    rows = []

    for _, row in fund_master.iterrows():
        rows.append({
            "scheme_code": row["scheme_code"],
            "scheme_name": row["scheme_name"],
            "fund_house": row["fund_house"],
            "folio_count": random.randint(50000, 5000000),
            "month": "2026-06"
        })

    pd.DataFrame(rows).to_csv(RAW_DIR / "06_folio_count.csv", index=False)


def create_07_scheme_performance(fund_master, nav_history):
    rows = []

    for scheme_code in fund_master["scheme_code"].dropna().unique():
        scheme_nav = nav_history[nav_history["scheme_code"] == scheme_code].sort_values("date")

        if len(scheme_nav) < 2:
            continue

        latest_nav = scheme_nav.iloc[-1]["nav"]
        first_nav = scheme_nav.iloc[0]["nav"]

        one_year_cutoff = scheme_nav["date"].max() - pd.DateOffset(years=1)
        three_year_cutoff = scheme_nav["date"].max() - pd.DateOffset(years=3)

        one_year_data = scheme_nav[scheme_nav["date"] >= one_year_cutoff]
        three_year_data = scheme_nav[scheme_nav["date"] >= three_year_cutoff]

        one_year_return = None
        three_year_return = None

        if len(one_year_data) >= 2:
            one_year_return = ((latest_nav - one_year_data.iloc[0]["nav"]) / one_year_data.iloc[0]["nav"]) * 100

        if len(three_year_data) >= 2:
            three_year_return = ((latest_nav - three_year_data.iloc[0]["nav"]) / three_year_data.iloc[0]["nav"]) * 100

        total_return = ((latest_nav - first_nav) / first_nav) * 100

        rows.append({
            "scheme_code": scheme_code,
            "latest_nav": latest_nav,
            "first_nav": first_nav,
            "one_year_return_percent": round(one_year_return, 2) if one_year_return is not None else None,
            "three_year_return_percent": round(three_year_return, 2) if three_year_return is not None else None,
            "total_return_percent": round(total_return, 2)
        })

    pd.DataFrame(rows).to_csv(RAW_DIR / "07_scheme_performance.csv", index=False)


def create_08_transactions(fund_master):
    transaction_types = ["BUY", "SELL", "SIP", "REDEEM"]
    rows = []

    for i in range(1, 101):
        scheme = fund_master.sample(1).iloc[0]

        rows.append({
            "transaction_id": f"TXN{i:04d}",
            "investor_id": f"INV{random.randint(1000, 9999)}",
            "scheme_code": scheme["scheme_code"],
            "transaction_type": random.choice(transaction_types),
            "transaction_date": pd.Timestamp("2026-06-01") + pd.Timedelta(days=random.randint(0, 22)),
            "amount": random.randint(1000, 200000)
        })

    pd.DataFrame(rows).to_csv(RAW_DIR / "08_transactions.csv", index=False)


def create_09_holdings(fund_master):
    sectors = ["Banking", "IT", "Pharma", "Auto", "FMCG", "Energy", "Telecom"]
    stocks = ["HDFC Bank", "Infosys", "Reliance", "TCS", "ICICI Bank", "Bharti Airtel", "Larsen"]

    rows = []

    for _, scheme in fund_master.iterrows():
        for _ in range(5):
            rows.append({
                "scheme_code": scheme["scheme_code"],
                "scheme_name": scheme["scheme_name"],
                "stock_name": random.choice(stocks),
                "sector": random.choice(sectors),
                "holding_percent": round(random.uniform(1, 12), 2)
            })

    pd.DataFrame(rows).to_csv(RAW_DIR / "09_holdings.csv", index=False)


def create_10_benchmark(fund_master):
    benchmarks = ["NIFTY 50 TRI", "NIFTY 100 TRI", "NIFTY 500 TRI", "BSE 500 TRI"]
    rows = []

    for _, scheme in fund_master.iterrows():
        rows.append({
            "scheme_code": scheme["scheme_code"],
            "scheme_name": scheme["scheme_name"],
            "benchmark": random.choice(benchmarks),
            "benchmark_return_1y_percent": round(random.uniform(5, 25), 2),
            "benchmark_return_3y_percent": round(random.uniform(20, 70), 2)
        })

    pd.DataFrame(rows).to_csv(RAW_DIR / "10_benchmark.csv", index=False)


def main():
    fund_master, nav_history = load_base_files()

    create_03_aum_by_fund_house(fund_master)
    create_04_monthly_sip()
    create_05_category_inflows(fund_master)
    create_06_folio_count(fund_master)
    create_07_scheme_performance(fund_master, nav_history)
    create_08_transactions(fund_master)
    create_09_holdings(fund_master)
    create_10_benchmark(fund_master)

    print("Missing 8 CSV files created successfully inside data/raw/")

    expected_files = [
        "01_fund_master.csv",
        "02_nav_history.csv",
        "03_aum_by_fund_house.csv",
        "04_monthly_sip.csv",
        "05_category_inflows.csv",
        "06_folio_count.csv",
        "07_scheme_performance.csv",
        "08_transactions.csv",
        "09_holdings.csv",
        "10_benchmark.csv",
    ]

    print("\nFinal check:")

    for file_name in expected_files:
        file_path = RAW_DIR / file_name

        if file_path.exists():
            print(f"FOUND: {file_name}")
        else:
            print(f"MISSING: {file_name}")


if __name__ == "__main__":
    main()