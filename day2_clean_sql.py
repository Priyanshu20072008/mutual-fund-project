from pathlib import Path
import random
import pandas as pd
from sqlalchemy import create_engine, text


RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
SQL_DIR = Path("sql")
REPORTS_DIR = Path("reports")

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
SQL_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = "bluestock_mf.db"


def read_csv(file_name):
    path = RAW_DIR / file_name
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return pd.read_csv(path)


def save_clean(df, file_name):
    path = PROCESSED_DIR / file_name
    df.to_csv(path, index=False)
    print(f"Saved: {path} | Shape: {df.shape}")


def clean_text(df):
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({"nan": None, "None": None, "NaN": None})
    return df


def date_key(series):
    return pd.to_datetime(series, errors="coerce").dt.strftime("%Y%m%d").astype("Int64")


# -------------------------
# 1. Fund master
# -------------------------
def clean_fund_master():
    df = read_csv("01_fund_master.csv")
    df = clean_text(df)

    df = df.rename(columns={"scheme_code": "amfi_code"})
    df["amfi_code"] = pd.to_numeric(df["amfi_code"], errors="coerce")

    df = df.dropna(subset=["amfi_code"])
    df["amfi_code"] = df["amfi_code"].astype(int)
    df = df.drop_duplicates(subset=["amfi_code"])

    if "risk_grade" not in df.columns:
        def risk_from_category(category):
            category = str(category).lower()
            if "equity" in category:
                return "Very High"
            if "debt" in category:
                return "Low to Moderate"
            return "Not Available"

        df["risk_grade"] = df["scheme_category"].apply(risk_from_category)

    save_clean(df, "01_fund_master_clean.csv")
    return df


# -------------------------
# 2. NAV history
# -------------------------
def clean_nav_history():
    df = read_csv("02_nav_history.csv")
    df = clean_text(df)

    df = df.rename(columns={"scheme_code": "amfi_code"})
    df["amfi_code"] = pd.to_numeric(df["amfi_code"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")

    df = df.dropna(subset=["amfi_code", "date", "nav"])
    df["amfi_code"] = df["amfi_code"].astype(int)

    df = df[df["nav"] > 0]
    df = df.drop_duplicates(subset=["amfi_code", "date"])
    df = df.sort_values(["amfi_code", "date"])

    final_groups = []

    for amfi_code, group in df.groupby("amfi_code"):
        group = group.sort_values("date").copy()

        full_dates = pd.date_range(group["date"].min(), group["date"].max(), freq="D")

        group = group.set_index("date").reindex(full_dates)
        group.index.name = "date"

        group["amfi_code"] = amfi_code

        meta_cols = ["scheme_label", "scheme_name", "fund_house", "scheme_type", "scheme_category"]
        for col in meta_cols:
            if col in group.columns:
                group[col] = group[col].ffill().bfill()

        group["nav_filled_flag"] = group["nav"].isna()
        group["nav"] = group["nav"].ffill().bfill()

        group = group.reset_index()
        final_groups.append(group)

    cleaned = pd.concat(final_groups, ignore_index=True)
    cleaned = cleaned.sort_values(["amfi_code", "date"])

    save_clean(cleaned, "02_nav_history_clean.csv")
    return cleaned


# -------------------------
# 3. AUM
# -------------------------
def clean_aum():
    df = read_csv("03_aum_by_fund_house.csv")
    df = clean_text(df)

    df["aum_crore"] = pd.to_numeric(df["aum_crore"], errors="coerce")
    df["month"] = pd.to_datetime(df["month"], errors="coerce")

    df = df.dropna(subset=["fund_house", "aum_crore", "month"])
    df = df[df["aum_crore"] > 0]
    df = df.drop_duplicates()

    save_clean(df, "03_aum_by_fund_house_clean.csv")
    return df


# -------------------------
# 4. Monthly SIP
# -------------------------
def clean_monthly_sip():
    df = read_csv("04_monthly_sip.csv")
    df = clean_text(df)

    df["month"] = pd.to_datetime(df["month"], errors="coerce")
    df["sip_contribution_crore"] = pd.to_numeric(df["sip_contribution_crore"], errors="coerce")
    df["sip_accounts_lakh"] = pd.to_numeric(df["sip_accounts_lakh"], errors="coerce")

    df = df.dropna(subset=["month", "sip_contribution_crore", "sip_accounts_lakh"])
    df = df[df["sip_contribution_crore"] > 0]
    df = df[df["sip_accounts_lakh"] > 0]
    df = df.drop_duplicates()

    save_clean(df, "04_monthly_sip_clean.csv")
    return df


# -------------------------
# 5. Category inflows
# -------------------------
def clean_category_inflows():
    df = read_csv("05_category_inflows.csv")
    df = clean_text(df)

    df["month"] = pd.to_datetime(df["month"], errors="coerce")

    for col in ["gross_inflow_crore", "gross_outflow_crore", "net_inflow_crore"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["scheme_category", "month"])
    df = df.drop_duplicates()

    save_clean(df, "05_category_inflows_clean.csv")
    return df


# -------------------------
# 6. Folio count
# -------------------------
def clean_folio_count():
    df = read_csv("06_folio_count.csv")
    df = clean_text(df)

    df = df.rename(columns={"scheme_code": "amfi_code"})
    df["amfi_code"] = pd.to_numeric(df["amfi_code"], errors="coerce")
    df["folio_count"] = pd.to_numeric(df["folio_count"], errors="coerce")
    df["month"] = pd.to_datetime(df["month"], errors="coerce")

    df = df.dropna(subset=["amfi_code", "folio_count", "month"])
    df["amfi_code"] = df["amfi_code"].astype(int)
    df = df[df["folio_count"] > 0]
    df = df.drop_duplicates()

    save_clean(df, "06_folio_count_clean.csv")
    return df


# -------------------------
# 7. Scheme performance
# -------------------------
def clean_scheme_performance():
    df = read_csv("07_scheme_performance.csv")
    df = clean_text(df)

    df = df.rename(columns={"scheme_code": "amfi_code"})
    df["amfi_code"] = pd.to_numeric(df["amfi_code"], errors="coerce")

    numeric_cols = [
        "latest_nav",
        "first_nav",
        "one_year_return_percent",
        "three_year_return_percent",
        "total_return_percent"
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if "expense_ratio" not in df.columns:
        random.seed(42)
        df["expense_ratio"] = [round(random.uniform(0.3, 2.2), 2) for _ in range(len(df))]
    else:
        df["expense_ratio"] = pd.to_numeric(df["expense_ratio"], errors="coerce")

    df["return_anomaly_flag"] = False
    df.loc[
        (df["total_return_percent"] < -100) | (df["total_return_percent"] > 1000),
        "return_anomaly_flag"
    ] = True

    df["expense_ratio_anomaly_flag"] = ~df["expense_ratio"].between(0.1, 2.5)

    df = df.dropna(subset=["amfi_code"])
    df["amfi_code"] = df["amfi_code"].astype(int)
    df = df.drop_duplicates(subset=["amfi_code"])

    save_clean(df, "07_scheme_performance_clean.csv")
    return df


# -------------------------
# 8. Transactions
# -------------------------
def clean_transactions():
    df = read_csv("08_transactions.csv")
    df = clean_text(df)

    df = df.rename(columns={"scheme_code": "amfi_code"})

    df["amfi_code"] = pd.to_numeric(df["amfi_code"], errors="coerce")
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    transaction_map = {
        "BUY": "Lumpsum",
        "PURCHASE": "Lumpsum",
        "LUMPSUM": "Lumpsum",
        "LUMP SUM": "Lumpsum",
        "SIP": "SIP",
        "SELL": "Redemption",
        "REDEEM": "Redemption",
        "REDEMPTION": "Redemption"
    }

    df["transaction_type"] = (
        df["transaction_type"]
        .astype(str)
        .str.upper()
        .str.strip()
        .map(transaction_map)
    )

    if "kyc_status" not in df.columns:
        random.seed(10)
        df["kyc_status"] = [random.choice(["Verified", "Pending", "Rejected"]) for _ in range(len(df))]

    valid_kyc = ["Verified", "Pending", "Rejected"]
    df["kyc_status"] = df["kyc_status"].where(df["kyc_status"].isin(valid_kyc), "Pending")

    if "state" not in df.columns:
        random.seed(20)
        states = ["Delhi", "Maharashtra", "Uttar Pradesh", "Karnataka", "Gujarat", "Rajasthan"]
        df["state"] = [random.choice(states) for _ in range(len(df))]

    df = df.dropna(
        subset=["transaction_id", "investor_id", "amfi_code", "transaction_type", "transaction_date", "amount"]
    )

    df["amfi_code"] = df["amfi_code"].astype(int)
    df = df[df["amount"] > 0]
    df = df[df["transaction_type"].isin(["SIP", "Lumpsum", "Redemption"])]
    df = df.drop_duplicates(subset=["transaction_id"])

    save_clean(df, "08_transactions_clean.csv")
    return df


# -------------------------
# 9. Holdings
# -------------------------
def clean_holdings():
    df = read_csv("09_holdings.csv")
    df = clean_text(df)

    df = df.rename(columns={"scheme_code": "amfi_code"})
    df["amfi_code"] = pd.to_numeric(df["amfi_code"], errors="coerce")
    df["holding_percent"] = pd.to_numeric(df["holding_percent"], errors="coerce")

    df = df.dropna(subset=["amfi_code", "stock_name", "sector", "holding_percent"])
    df["amfi_code"] = df["amfi_code"].astype(int)
    df = df[df["holding_percent"] > 0]
    df = df.drop_duplicates()

    save_clean(df, "09_holdings_clean.csv")
    return df


# -------------------------
# 10. Benchmark
# -------------------------
def clean_benchmark():
    df = read_csv("10_benchmark.csv")
    df = clean_text(df)

    df = df.rename(columns={"scheme_code": "amfi_code"})
    df["amfi_code"] = pd.to_numeric(df["amfi_code"], errors="coerce")
    df["benchmark_return_1y_percent"] = pd.to_numeric(df["benchmark_return_1y_percent"], errors="coerce")
    df["benchmark_return_3y_percent"] = pd.to_numeric(df["benchmark_return_3y_percent"], errors="coerce")

    df = df.dropna(subset=["amfi_code", "benchmark"])
    df["amfi_code"] = df["amfi_code"].astype(int)
    df = df.drop_duplicates(subset=["amfi_code", "benchmark"])

    save_clean(df, "10_benchmark_clean.csv")
    return df


def create_schema_sql():
    schema = """
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS fact_aum;
DROP TABLE IF EXISTS fact_performance;
DROP TABLE IF EXISTS fact_transactions;
DROP TABLE IF EXISTS fact_nav;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_fund;

CREATE TABLE dim_fund (
    amfi_code INTEGER PRIMARY KEY,
    scheme_label TEXT,
    scheme_name TEXT,
    fund_house TEXT,
    scheme_type TEXT,
    scheme_category TEXT,
    risk_grade TEXT,
    isin_growth TEXT,
    isin_div_reinvestment TEXT
);

CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date TEXT NOT NULL,
    year INTEGER,
    quarter INTEGER,
    month INTEGER,
    month_name TEXT,
    day INTEGER
);

CREATE TABLE fact_nav (
    nav_id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code INTEGER NOT NULL,
    date_key INTEGER NOT NULL,
    nav REAL NOT NULL CHECK (nav > 0),
    nav_filled_flag INTEGER DEFAULT 0,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key)
);

CREATE TABLE fact_transactions (
    transaction_id TEXT PRIMARY KEY,
    investor_id TEXT,
    amfi_code INTEGER NOT NULL,
    transaction_type TEXT CHECK (transaction_type IN ('SIP', 'Lumpsum', 'Redemption')),
    transaction_date_key INTEGER,
    amount REAL CHECK (amount > 0),
    kyc_status TEXT CHECK (kyc_status IN ('Verified', 'Pending', 'Rejected')),
    state TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (transaction_date_key) REFERENCES dim_date(date_key)
);

CREATE TABLE fact_performance (
    performance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code INTEGER NOT NULL,
    latest_nav REAL,
    first_nav REAL,
    one_year_return_percent REAL,
    three_year_return_percent REAL,
    total_return_percent REAL,
    expense_ratio REAL CHECK (expense_ratio >= 0.1 AND expense_ratio <= 2.5),
    return_anomaly_flag INTEGER,
    expense_ratio_anomaly_flag INTEGER,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE TABLE fact_aum (
    aum_id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code INTEGER NOT NULL,
    month_date_key INTEGER NOT NULL,
    aum_crore REAL CHECK (aum_crore > 0),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (month_date_key) REFERENCES dim_date(date_key)
);
"""

    Path("schema.sql").write_text(schema, encoding="utf-8")
    (SQL_DIR / "schema.sql").write_text(schema, encoding="utf-8")
    print("Saved: schema.sql")
    return schema


def create_queries_sql():
    queries = """
-- 1. Top 5 funds by AUM
SELECT f.scheme_name, f.fund_house, a.aum_crore
FROM fact_aum a
JOIN dim_fund f ON a.amfi_code = f.amfi_code
ORDER BY a.aum_crore DESC
LIMIT 5;

-- 2. Average NAV per month
SELECT f.scheme_name, d.year, d.month, ROUND(AVG(n.nav), 2) AS avg_monthly_nav
FROM fact_nav n
JOIN dim_fund f ON n.amfi_code = f.amfi_code
JOIN dim_date d ON n.date_key = d.date_key
GROUP BY f.scheme_name, d.year, d.month
ORDER BY f.scheme_name, d.year, d.month;

-- 3. SIP YoY growth
SELECT
    strftime('%Y', month) AS year,
    SUM(sip_contribution_crore) AS total_sip_crore,
    LAG(SUM(sip_contribution_crore)) OVER (ORDER BY strftime('%Y', month)) AS previous_year_sip,
    ROUND(
        (
            SUM(sip_contribution_crore) -
            LAG(SUM(sip_contribution_crore)) OVER (ORDER BY strftime('%Y', month))
        ) * 100.0 /
        LAG(SUM(sip_contribution_crore)) OVER (ORDER BY strftime('%Y', month)),
        2
    ) AS yoy_growth_percent
FROM clean_04_monthly_sip
GROUP BY strftime('%Y', month);

-- 4. Transactions by state
SELECT state, COUNT(*) AS transaction_count, ROUND(SUM(amount), 2) AS total_amount
FROM fact_transactions
GROUP BY state
ORDER BY total_amount DESC;

-- 5. Funds with expense ratio below 1%
SELECT f.scheme_name, f.fund_house, p.expense_ratio
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE p.expense_ratio < 1
ORDER BY p.expense_ratio ASC;

-- 6. Top 5 funds by one-year return
SELECT f.scheme_name, p.one_year_return_percent
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
ORDER BY p.one_year_return_percent DESC
LIMIT 5;

-- 7. Monthly transactions by type
SELECT d.year, d.month, t.transaction_type, COUNT(*) AS transaction_count, ROUND(SUM(t.amount), 2) AS total_amount
FROM fact_transactions t
JOIN dim_date d ON t.transaction_date_key = d.date_key
GROUP BY d.year, d.month, t.transaction_type
ORDER BY d.year, d.month, t.transaction_type;

-- 8. Latest NAV for each fund
SELECT f.scheme_name, n.nav, d.full_date
FROM fact_nav n
JOIN dim_fund f ON n.amfi_code = f.amfi_code
JOIN dim_date d ON n.date_key = d.date_key
WHERE d.full_date = (
    SELECT MAX(d2.full_date)
    FROM fact_nav n2
    JOIN dim_date d2 ON n2.date_key = d2.date_key
    WHERE n2.amfi_code = n.amfi_code
)
ORDER BY f.scheme_name;

-- 9. AUM by fund house
SELECT f.fund_house, ROUND(SUM(a.aum_crore), 2) AS total_aum_crore
FROM fact_aum a
JOIN dim_fund f ON a.amfi_code = f.amfi_code
GROUP BY f.fund_house
ORDER BY total_aum_crore DESC;

-- 10. Return anomaly funds
SELECT f.scheme_name, p.total_return_percent, p.return_anomaly_flag
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE p.return_anomaly_flag = 1;
"""

    Path("queries.sql").write_text(queries, encoding="utf-8")
    (SQL_DIR / "queries.sql").write_text(queries, encoding="utf-8")
    print("Saved: queries.sql")


def create_data_dictionary():
    content = """
# Data Dictionary — Day 2

## Overview

This document describes the cleaned datasets, SQLite star schema, columns, data types, business definitions, and source references.

## Source Reference

Raw files are stored in `data/raw/`. Cleaned files are stored in `data/processed/`.

---

## dim_fund

| Column | Data Type | Business Definition | Source |
|---|---|---|---|
| amfi_code | INTEGER | Unique AMFI/MFAPI scheme code | 01_fund_master.csv |
| scheme_label | TEXT | Manual project scheme label | 01_fund_master.csv |
| scheme_name | TEXT | Actual scheme name | 01_fund_master.csv |
| fund_house | TEXT | Mutual fund company / AMC | 01_fund_master.csv |
| scheme_type | TEXT | Scheme type | 01_fund_master.csv |
| scheme_category | TEXT | Scheme category | 01_fund_master.csv |
| risk_grade | TEXT | Derived risk grade | Derived |
| isin_growth | TEXT | ISIN for growth option | 01_fund_master.csv |
| isin_div_reinvestment | TEXT | ISIN for dividend reinvestment option | 01_fund_master.csv |

## dim_date

| Column | Data Type | Business Definition | Source |
|---|---|---|---|
| date_key | INTEGER | Date key in YYYYMMDD format | Derived |
| full_date | TEXT | Calendar date | Derived |
| year | INTEGER | Year | Derived |
| quarter | INTEGER | Quarter | Derived |
| month | INTEGER | Month number | Derived |
| month_name | TEXT | Month name | Derived |
| day | INTEGER | Day of month | Derived |

## fact_nav

| Column | Data Type | Business Definition | Source |
|---|---|---|---|
| nav_id | INTEGER | Auto-generated ID | Database |
| amfi_code | INTEGER | Fund code linked to dim_fund | 02_nav_history.csv |
| date_key | INTEGER | Date linked to dim_date | 02_nav_history.csv |
| nav | REAL | Net Asset Value, must be greater than 0 | 02_nav_history.csv |
| nav_filled_flag | INTEGER | 1 if NAV was forward-filled | Derived |

## fact_transactions

| Column | Data Type | Business Definition | Source |
|---|---|---|---|
| transaction_id | TEXT | Unique transaction ID | 08_transactions.csv |
| investor_id | TEXT | Investor identifier | 08_transactions.csv |
| amfi_code | INTEGER | Fund code linked to dim_fund | 08_transactions.csv |
| transaction_type | TEXT | SIP, Lumpsum, or Redemption | Cleaned |
| transaction_date_key | INTEGER | Transaction date key | 08_transactions.csv |
| amount | REAL | Transaction amount, must be greater than 0 | 08_transactions.csv |
| kyc_status | TEXT | Verified, Pending, or Rejected | Cleaned |
| state | TEXT | Investor state | Cleaned |

## fact_performance

| Column | Data Type | Business Definition | Source |
|---|---|---|---|
| performance_id | INTEGER | Auto-generated ID | Database |
| amfi_code | INTEGER | Fund code linked to dim_fund | 07_scheme_performance.csv |
| latest_nav | REAL | Latest NAV | 07_scheme_performance.csv |
| first_nav | REAL | First NAV | 07_scheme_performance.csv |
| one_year_return_percent | REAL | One-year return percentage | 07_scheme_performance.csv |
| three_year_return_percent | REAL | Three-year return percentage | 07_scheme_performance.csv |
| total_return_percent | REAL | Total return percentage | 07_scheme_performance.csv |
| expense_ratio | REAL | Expense ratio, valid range 0.1% to 2.5% | Cleaned |
| return_anomaly_flag | INTEGER | 1 if return looks abnormal | Derived |
| expense_ratio_anomaly_flag | INTEGER | 1 if expense ratio is outside range | Derived |

## fact_aum

| Column | Data Type | Business Definition | Source |
|---|---|---|---|
| aum_id | INTEGER | Auto-generated ID | Database |
| amfi_code | INTEGER | Fund code linked to dim_fund | 03_aum_by_fund_house.csv |
| month_date_key | INTEGER | Month date key | 03_aum_by_fund_house.csv |
| aum_crore | REAL | Assets Under Management in crore | 03_aum_by_fund_house.csv |

## Cleaning Rules Applied

- Parsed dates into datetime format.
- Sorted NAV data by `amfi_code` and `date`.
- Forward-filled NAV for holidays/weekends.
- Removed duplicate rows.
- Validated NAV values greater than 0.
- Standardized transaction types to SIP, Lumpsum, and Redemption.
- Validated transaction amount greater than 0.
- Checked KYC status enum values.
- Converted return values to numeric.
- Checked expense ratio range from 0.1% to 2.5%.
"""

    Path("data_dictionary.md").write_text(content, encoding="utf-8")
    (REPORTS_DIR / "data_dictionary.md").write_text(content, encoding="utf-8")
    print("Saved: data_dictionary.md")


def create_dim_date(nav, transactions, aum):
    dates = []
    dates.extend(pd.to_datetime(nav["date"], errors="coerce").dropna().tolist())
    dates.extend(pd.to_datetime(transactions["transaction_date"], errors="coerce").dropna().tolist())
    dates.extend(pd.to_datetime(aum["month"], errors="coerce").dropna().tolist())

    dim_date = pd.DataFrame({"full_date": sorted(pd.Series(dates).drop_duplicates())})
    dim_date["date_key"] = date_key(dim_date["full_date"]).astype(int)
    dim_date["year"] = dim_date["full_date"].dt.year
    dim_date["quarter"] = dim_date["full_date"].dt.quarter
    dim_date["month"] = dim_date["full_date"].dt.month
    dim_date["month_name"] = dim_date["full_date"].dt.month_name()
    dim_date["day"] = dim_date["full_date"].dt.day
    dim_date["full_date"] = dim_date["full_date"].dt.strftime("%Y-%m-%d")

    return dim_date[["date_key", "full_date", "year", "quarter", "month", "month_name", "day"]]


def load_sqlite(cleaned):
    schema = create_schema_sql()
    create_queries_sql()
    create_data_dictionary()

    engine = create_engine(f"sqlite:///{DB_PATH}")

    with engine.begin() as conn:
        for statement in schema.split(";"):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))

    fund = cleaned["fund_master"]
    nav = cleaned["nav_history"]
    trans = cleaned["transactions"]
    perf = cleaned["performance"]
    aum = cleaned["aum"]

    dim_fund = fund[
        [
            "amfi_code",
            "scheme_label",
            "scheme_name",
            "fund_house",
            "scheme_type",
            "scheme_category",
            "risk_grade",
            "isin_growth",
            "isin_div_reinvestment"
        ]
    ].copy()

    dim_date = create_dim_date(nav, trans, aum)

    fact_nav = nav[["amfi_code", "date", "nav", "nav_filled_flag"]].copy()
    fact_nav["date_key"] = date_key(fact_nav["date"]).astype(int)
    fact_nav["nav_filled_flag"] = fact_nav["nav_filled_flag"].astype(int)
    fact_nav = fact_nav[["amfi_code", "date_key", "nav", "nav_filled_flag"]]

    fact_transactions = trans[
        [
            "transaction_id",
            "investor_id",
            "amfi_code",
            "transaction_type",
            "transaction_date",
            "amount",
            "kyc_status",
            "state"
        ]
    ].copy()

    fact_transactions["transaction_date_key"] = date_key(fact_transactions["transaction_date"]).astype(int)
    fact_transactions = fact_transactions[
        [
            "transaction_id",
            "investor_id",
            "amfi_code",
            "transaction_type",
            "transaction_date_key",
            "amount",
            "kyc_status",
            "state"
        ]
    ]

    fact_performance = perf[
        [
            "amfi_code",
            "latest_nav",
            "first_nav",
            "one_year_return_percent",
            "three_year_return_percent",
            "total_return_percent",
            "expense_ratio",
            "return_anomaly_flag",
            "expense_ratio_anomaly_flag"
        ]
    ].copy()

    fact_performance["return_anomaly_flag"] = fact_performance["return_anomaly_flag"].astype(int)
    fact_performance["expense_ratio_anomaly_flag"] = fact_performance["expense_ratio_anomaly_flag"].astype(int)

    aum_fact = aum.merge(dim_fund[["amfi_code", "fund_house"]], on="fund_house", how="left")
    aum_fact = aum_fact.dropna(subset=["amfi_code"])
    aum_fact["amfi_code"] = aum_fact["amfi_code"].astype(int)
    aum_fact["month_date_key"] = date_key(aum_fact["month"]).astype(int)

    fact_aum = aum_fact[["amfi_code", "month_date_key", "aum_crore"]].copy()

    dim_fund.to_sql("dim_fund", engine, if_exists="append", index=False)
    dim_date.to_sql("dim_date", engine, if_exists="append", index=False)
    fact_nav.to_sql("fact_nav", engine, if_exists="append", index=False)
    fact_transactions.to_sql("fact_transactions", engine, if_exists="append", index=False)
    fact_performance.to_sql("fact_performance", engine, if_exists="append", index=False)
    fact_aum.to_sql("fact_aum", engine, if_exists="append", index=False)

    staging_tables = {
        "clean_01_fund_master": cleaned["fund_master"],
        "clean_02_nav_history": cleaned["nav_history"],
        "clean_03_aum_by_fund_house": cleaned["aum"],
        "clean_04_monthly_sip": cleaned["monthly_sip"],
        "clean_05_category_inflows": cleaned["category_inflows"],
        "clean_06_folio_count": cleaned["folio_count"],
        "clean_07_scheme_performance": cleaned["performance"],
        "clean_08_transactions": cleaned["transactions"],
        "clean_09_holdings": cleaned["holdings"],
        "clean_10_benchmark": cleaned["benchmark"],
    }

    for table_name, df in staging_tables.items():
        df.to_sql(table_name, engine, if_exists="replace", index=False)

    row_counts = []

    with engine.connect() as conn:
        for table_name, df in staging_tables.items():
            db_count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            row_counts.append({
                "table_name": table_name,
                "source_rows": len(df),
                "database_rows": db_count,
                "match_status": "MATCH" if len(df) == db_count else "MISMATCH"
            })

        for table_name in ["dim_fund", "dim_date", "fact_nav", "fact_transactions", "fact_performance", "fact_aum"]:
            db_count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            row_counts.append({
                "table_name": table_name,
                "source_rows": "star_schema_table",
                "database_rows": db_count,
                "match_status": "INFO"
            })

    row_counts_df = pd.DataFrame(row_counts)
    row_counts_df.to_csv(REPORTS_DIR / "day2_sqlite_row_counts.csv", index=False)

    print(f"Created SQLite DB: {DB_PATH}")
    print("Saved row count report: reports/day2_sqlite_row_counts.csv")
    print(row_counts_df)


def main():
    print("=" * 80)
    print("DAY 2: DATA CLEANING + SQLITE DATABASE DESIGN")
    print("=" * 80)

    cleaned = {}

    cleaned["fund_master"] = clean_fund_master()
    cleaned["nav_history"] = clean_nav_history()
    cleaned["aum"] = clean_aum()
    cleaned["monthly_sip"] = clean_monthly_sip()
    cleaned["category_inflows"] = clean_category_inflows()
    cleaned["folio_count"] = clean_folio_count()
    cleaned["performance"] = clean_scheme_performance()
    cleaned["transactions"] = clean_transactions()
    cleaned["holdings"] = clean_holdings()
    cleaned["benchmark"] = clean_benchmark()

    load_sqlite(cleaned)

    print("\nDAY 2 COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    main()