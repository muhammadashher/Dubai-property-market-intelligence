-- Sales enablement fact cards: the numbers an account manager needs for each top community
SELECT c.name AS community, c.n AS sales_12m, c.price_median, c.psf_median, c.psf_yoy, c.price_yoy,
       c.n_yoy AS sales_yoy, c.offplan_share, r.contracts AS rent_contracts_12m, r.rent_median, c.yield_pct,
       c.top_area, c.url
FROM communities c
LEFT JOIN rents_by_community r ON r.name = c.name
ORDER BY c.n DESC
LIMIT 25;
