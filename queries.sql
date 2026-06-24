
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
