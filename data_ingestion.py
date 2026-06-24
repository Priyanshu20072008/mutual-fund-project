import pandas as pd
from pathlib import Path

# Folder paths
RAW_DIR = Path("data/raw")
REPORTS_DIR = Path("reports")

# Create reports folder if missing
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Expected 10 CSV files
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

dataframes = {}
summary_lines = []

print("=" * 80)
print("DAY 1 DATA INGESTION CHECK")
print("=" * 80)

# Load all 10 CSV files
for file_name in expected_files:
    file_path = RAW_DIR / file_name

    print("\n" + "-" * 80)
    print(f"Checking file: {file_name}")

    if not file_path.exists():
        message = f"MISSING FILE: {file_name}"
        print(message)
        summary_lines.append(message)
        continue

    try:
        df = pd.read_csv(file_path)
        dataframes[file_name] = df

        print(f"\nShape: {df.shape}")

        print("\nDtypes:")
        print(df.dtypes)

        print("\nHead:")
        print(df.head())

        missing_values = df.isnull().sum()
        duplicate_rows = df.duplicated().sum()

        print("\nMissing values:")
        missing_only = missing_values[missing_values > 0]

        if len(missing_only) > 0:
            print(missing_only)
        else:
            print("No missing values found.")

        print(f"\nDuplicate rows: {duplicate_rows}")

        summary_lines.append(
            f"{file_name}: Loaded successfully | Shape: {df.shape} | Duplicate rows: {duplicate_rows}"
        )

        if df.shape[0] == 0:
            summary_lines.append(f"ANOMALY: {file_name} has 0 rows.")

        if df.shape[1] == 0:
            summary_lines.append(f"ANOMALY: {file_name} has 0 columns.")

        if duplicate_rows > 0:
            summary_lines.append(f"ANOMALY: {file_name} has {duplicate_rows} duplicate rows.")

        if len(missing_only) > 0:
            summary_lines.append(f"NOTE: {file_name} has missing values.")

    except Exception as e:
        message = f"ERROR loading {file_name}: {e}"
        print(message)
        summary_lines.append(message)


# Fund master exploration
print("\n" + "=" * 80)
print("FUND MASTER EXPLORATION")
print("=" * 80)

fund_master = dataframes.get("01_fund_master.csv")

if fund_master is not None:
    print("\nColumns in fund_master:")
    print(fund_master.columns.tolist())

    if "fund_house" in fund_master.columns:
        print("\nUnique Fund Houses:")
        print(fund_master["fund_house"].dropna().unique())
    else:
        summary_lines.append("ANOMALY: fund_house column missing in fund_master.")

    if "scheme_type" in fund_master.columns:
        print("\nUnique Scheme Types:")
        print(fund_master["scheme_type"].dropna().unique())
    else:
        summary_lines.append("ANOMALY: scheme_type column missing in fund_master.")

    if "scheme_category" in fund_master.columns:
        print("\nUnique Categories / Sub-categories:")
        print(fund_master["scheme_category"].dropna().unique())
    else:
        summary_lines.append("ANOMALY: scheme_category column missing in fund_master.")

    risk_columns = [col for col in fund_master.columns if "risk" in col.lower()]

    if risk_columns:
        print("\nRisk Grade Columns Found:")
        for col in risk_columns:
            print(f"\n{col}:")
            print(fund_master[col].dropna().unique())
    else:
        print("\nRisk grade column not found in fund_master.")
        summary_lines.append("NOTE: risk grade column not found in fund_master.")

    if "scheme_code" in fund_master.columns:
        print("\nAMFI / MFAPI Scheme Code Structure:")
        print("Scheme codes are numeric identifiers used to map mutual fund schemes with NAV history.")
        print("\nExample Scheme Codes:")
        print(fund_master["scheme_code"].head())
    else:
        summary_lines.append("ANOMALY: scheme_code column missing in fund_master.")

else:
    print("fund_master file not available.")
    summary_lines.append("ERROR: 01_fund_master.csv not available for exploration.")


# Validate scheme codes
print("\n" + "=" * 80)
print("SCHEME CODE VALIDATION")
print("=" * 80)

nav_history = dataframes.get("02_nav_history.csv")

if fund_master is not None and nav_history is not None:
    if "scheme_code" in fund_master.columns and "scheme_code" in nav_history.columns:
        fund_codes = set(fund_master["scheme_code"].dropna().astype(str))
        nav_codes = set(nav_history["scheme_code"].dropna().astype(str))

        missing_in_nav = fund_codes - nav_codes
        extra_in_nav = nav_codes - fund_codes

        print(f"Total scheme codes in fund_master: {len(fund_codes)}")
        print(f"Total scheme codes in nav_history: {len(nav_codes)}")

        if len(missing_in_nav) == 0:
            print("\nValidation Passed: Every fund_master scheme_code exists in nav_history.")
            summary_lines.append("Validation Passed: Every fund_master scheme_code exists in nav_history.")
        else:
            print("\nValidation Failed: These fund_master codes are missing in nav_history:")
            print(missing_in_nav)
            summary_lines.append(f"Validation Failed: Missing in nav_history: {missing_in_nav}")

        if len(extra_in_nav) > 0:
            print("\nExtra scheme codes found in nav_history:")
            print(extra_in_nav)
            summary_lines.append(f"Extra scheme codes in nav_history: {extra_in_nav}")
        else:
            print("No extra scheme codes found in nav_history.")

    else:
        print("scheme_code column missing in fund_master or nav_history.")
        summary_lines.append("ERROR: scheme_code column missing in fund_master or nav_history.")
else:
    print("Cannot validate scheme codes because fund_master or nav_history is missing.")
    summary_lines.append("ERROR: Cannot validate scheme codes because fund_master or nav_history is missing.")


# Final data quality summary
print("\n" + "=" * 80)
print("DATA QUALITY SUMMARY")
print("=" * 80)

for line in summary_lines:
    print(line)

summary_path = REPORTS_DIR / "day1_data_quality_summary.txt"

with open(summary_path, "w", encoding="utf-8") as file:
    file.write("DAY 1 DATA QUALITY SUMMARY\n")
    file.write("=" * 80 + "\n\n")

    for line in summary_lines:
        file.write(line + "\n")

print(f"\nSaved summary to: {summary_path}")