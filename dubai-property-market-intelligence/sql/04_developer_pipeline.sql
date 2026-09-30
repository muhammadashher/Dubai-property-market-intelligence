-- Developer pipeline: active (under-construction) projects, units, upcoming handovers, and sales momentum
WITH pipe AS (
    SELECT developer,
           COUNT(*)                                                          AS active_projects,
           SUM(total_units)                                                  AS pipeline_units,
           ROUND(AVG(completion), 1)                                         AS avg_completion_pct,
           SUM(CASE WHEN completion_date BETWEEN '2026-09-01' AND '2027-08-31'
                    THEN total_units ELSE 0 END)                             AS handover_units_12m
    FROM projects
    WHERE status = 'Active' AND completion < 100
    GROUP BY developer
)
SELECT d.name AS developer, p.active_projects, p.pipeline_units, p.avg_completion_pct,
       p.handover_units_12m, d.n AS sales_12m, d.n_yoy AS sales_yoy_pct, d.offplan_share,
       d.psf_median, d.n_projects AS total_projects
FROM pipe p JOIN developers d ON d.name = p.developer
ORDER BY p.pipeline_units DESC;
