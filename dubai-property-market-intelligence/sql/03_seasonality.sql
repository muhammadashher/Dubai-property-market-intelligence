-- Seasonality index: each calendar month's transactions vs that year's monthly average (full years 2010-2025)
WITH m AS (
    SELECT SUBSTR(month, 1, 4) AS yr, CAST(SUBSTR(month, 6, 2) AS INTEGER) AS mon, sales_count
    FROM index_monthly
    WHERE month BETWEEN '2010-01' AND '2025-12'
),
idx AS (
    SELECT yr, mon, sales_count * 1.0 / AVG(sales_count) OVER (PARTITION BY yr) AS ratio FROM m
)
SELECT mon AS calendar_month, ROUND(AVG(ratio), 3) AS seasonality_index, COUNT(*) AS years
FROM idx GROUP BY mon ORDER BY mon;
