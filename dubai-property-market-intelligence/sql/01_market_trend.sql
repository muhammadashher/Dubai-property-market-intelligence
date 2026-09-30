-- Dubai-wide monthly transactions and prices (2008 -> latest) with rolling 12-month volume and YoY change
SELECT month,
       sales_count,
       median_aed_per_sqft,
       SUM(sales_count) OVER (ORDER BY month ROWS BETWEEN 11 PRECEDING AND CURRENT ROW)        AS sales_rolling_12m,
       ROUND(sales_count * 1.0 / LAG(sales_count, 12) OVER (ORDER BY month) - 1, 4)              AS sales_yoy,
       ROUND(ma5_aed_per_sqft * 1.0 / LAG(ma5_aed_per_sqft, 12) OVER (ORDER BY month) - 1, 4)    AS psf_yoy
FROM index_monthly
ORDER BY month;
