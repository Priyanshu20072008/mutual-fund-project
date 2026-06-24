\# Mutual Fund Analytics Project



\## Day 1 — Project Setup + Data Ingestion



This project performs data ingestion and basic ETL for mutual fund datasets using Python and Pandas.



\## Completed Tasks



\* Created project folder structure:



&#x20; \* `data/raw`

&#x20; \* `data/processed`

&#x20; \* `notebooks`

&#x20; \* `sql`

&#x20; \* `dashboard`

&#x20; \* `reports`



\* Created Python virtual environment.



\* Installed required dependencies.



\* Created `requirements.txt`.



\* Fetched mutual fund NAV data using MFAPI.



\* Created 10 CSV datasets for Day 1 ETL.



\* Loaded all 10 CSV files using Pandas.



\* Printed shape, dtypes, and head for each dataset.



\* Checked missing values and duplicate rows.



\* Explored fund master data.



\* Printed unique fund houses, scheme types, and scheme categories.



\* Validated scheme codes between `fund\_master` and `nav\_history`.



\* Created data quality summary report.



\## CSV Files Used



1\. `01\_fund\_master.csv`

2\. `02\_nav\_history.csv`

3\. `03\_aum\_by\_fund\_house.csv`

4\. `04\_monthly\_sip.csv`

5\. `05\_category\_inflows.csv`

6\. `06\_folio\_count.csv`

7\. `07\_scheme\_performance.csv`

8\. `08\_transactions.csv`

9\. `09\_holdings.csv`

10\. `10\_benchmark.csv`



\## Main Python Files



\* `live\_nav\_fetch.py` — Fetches NAV data from MFAPI.

\* `create\_expected\_10\_csvs.py` — Creates the expected Day 1 CSV files.

\* `data\_ingestion.py` — Loads CSV files, checks quality, and validates scheme codes.



\## Reports Generated



\* `reports/day1\_data\_quality\_summary.txt`

\* `reports/live\_nav\_fetch\_summary.csv`



\## Data Quality Notes



\* `isin\_div\_reinvestment` has missing values in some schemes.

\* Risk grade column was not available in the generated fund master dataset.

\* Scheme code validation passed successfully.

\* Every `fund\_master` scheme code exists in `nav\_history`.



\## How to Run



```bash

pip install -r requirements.txt

python live\_nav\_fetch.py

python create\_expected\_10\_csvs.py

python data\_ingestion.py

```



\## Note



The initial 10 CSV files were not provided by the team. Therefore, the datasets were generated using public mutual fund data and MFAPI-based NAV history.



