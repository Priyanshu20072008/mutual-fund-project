
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
