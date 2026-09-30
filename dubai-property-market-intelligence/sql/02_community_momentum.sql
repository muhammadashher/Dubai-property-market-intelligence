-- Community momentum: last 12 months vs prior 12 months (sales volume and price per sqft),
-- share of Dubai transactions, and volume rank / quartile
WITH latest AS (SELECT MAX(month) AS m FROM community_monthly),
bounds AS (
    SELECT STRFTIME('%Y-%m', DATE(m || '-01', '-11 months')) AS cur_start, m AS cur_end,
           STRFTIME('%Y-%m', DATE(m || '-01', '-23 months')) AS prev_start,
           STRFTIME('%Y-%m', DATE(m || '-01', '-12 months')) AS prev_end
    FROM latest
),
agg AS (
    SELECT c.community,
           SUM(CASE WHEN c.month BETWEEN b.cur_start AND b.cur_end THEN c.n_sales END)   AS sales_12m,
           SUM(CASE WHEN c.month BETWEEN b.prev_start AND b.prev_end THEN c.n_sales END) AS sales_prev_12m,
           AVG(CASE WHEN c.month BETWEEN b.cur_start AND b.cur_end THEN c.median END)    AS psf_12m,
           AVG(CASE WHEN c.month BETWEEN b.prev_start AND b.prev_end THEN c.median END)  AS psf_prev_12m
    FROM community_monthly c CROSS JOIN bounds b
    GROUP BY c.community
)
SELECT community,
       sales_12m, sales_prev_12m,
       ROUND(sales_12m * 1.0 / NULLIF(sales_prev_12m, 0) - 1, 4)          AS sales_growth,
       ROUND(psf_12m, 0)                                                  AS psf_12m,
       ROUND(psf_12m / NULLIF(psf_prev_12m, 0) - 1, 4)                    AS psf_growth,
       ROUND(sales_12m * 1.0 / SUM(sales_12m) OVER (), 4)                 AS share_of_sales,
       RANK() OVER (ORDER BY sales_12m DESC)                              AS volume_rank,
       NTILE(4) OVER (ORDER BY sales_12m DESC)                            AS volume_quartile
FROM agg
WHERE sales_12m > 0
ORDER BY sales_12m DESC;
