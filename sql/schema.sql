
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
